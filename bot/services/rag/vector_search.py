"""Семантический поиск по векторному хранилищу образовательного контента.

Использует pgvector + Yandex Embeddings API для поиска релевантных материалов
по вопросу пользователя.
"""

import hashlib
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from bot.database import get_db
from bot.services.embeddings_service import get_embedding_service
from bot.services.web_scraper import EducationalContent


def _row_to_content(row: tuple) -> EducationalContent:
    """Преобразовать строку БД в EducationalContent."""
    extracted_at = row[6]
    if isinstance(extracted_at, str):
        try:
            extracted_at = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))
        except ValueError:
            extracted_at = datetime.now(UTC)
    elif extracted_at is None:
        extracted_at = datetime.now(UTC)
    return EducationalContent(
        title=row[1] or "",
        content=row[2] or "",
        subject=row[3] or "общее",
        difficulty="средний",
        source_url=row[4] or "",
        extracted_at=extracted_at,
        tags=["vector_search"],
    )


def _content_source_hash(title: str, source_url: str) -> str:
    """Хеш для дедупликации по источнику."""
    raw = f"{title.strip()}|{source_url.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


class VectorSearchService:
    """
    Семантический поиск по knowledge_embeddings.

    Использует text-search-query для запроса и text-search-doc для документов.
    Поиск по косинусному сходству (pgvector <=>).
    """

    def __init__(
        self,
        min_similarity: float = 0.4,
        default_top_k: int = 10,
    ):
        self.min_similarity = min_similarity
        self.default_top_k = default_top_k
        self._embedding_service = None

    def _get_embedding_service(self):
        if self._embedding_service is None:
            try:
                self._embedding_service = get_embedding_service()
            except Exception as e:
                logger.debug(f"EmbeddingService недоступен: {e}")
        return self._embedding_service

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        min_similarity: float | None = None,
        subject_filter: str | None = None,
    ) -> list[EducationalContent]:
        """
        Семантический поиск по вопросу.

        Args:
            query: Вопрос пользователя.
            top_k: Максимум результатов.
            min_similarity: Минимальный порог косинусного сходства (0–1).
            subject_filter: Опциональный фильтр по предмету.

        Returns:
            Список EducationalContent, отсортированных по релевантности.
        """
        svc = self._get_embedding_service()
        if not svc:
            return []

        try:
            embedding = await svc.embed_query(query)
        except Exception as e:
            logger.debug(f"Embedding запроса недоступен: {e}")
            return []

        if not embedding or len(embedding) == 0:
            return []

        k = top_k if top_k is not None else self.default_top_k
        th = min_similarity if min_similarity is not None else self.min_similarity
        vec_str = "[" + ",".join(str(x) for x in embedding) + "]"

        try:
            with get_db() as db:
                from sqlalchemy import text

                sql = """
                    SELECT id, title, content, subject, source_url, 1 - (embedding <=> CAST(:vec AS vector)) as sim, created_at
                    FROM knowledge_embeddings
                    WHERE embedding IS NOT NULL
                    AND (1 - (embedding <=> CAST(:vec AS vector))) >= :th
                    {subject_filter}
                    ORDER BY embedding <=> CAST(:vec AS vector)
                    LIMIT :limit
                """.format(subject_filter="AND subject = :subject" if subject_filter else "")
                params: dict[str, Any] = {"vec": vec_str, "th": th, "limit": k}
                if subject_filter:
                    params["subject"] = subject_filter

                rows = db.execute(text(sql), params).fetchall()

                return [_row_to_content(row) for row in rows]
        except Exception as e:
            logger.debug(f"Vector search error: {e}")
            return []

    async def index_content(self, content: EducationalContent) -> bool:
        """
        Индексировать контент: эмбеддинг + вставка в knowledge_embeddings.

        Args:
            content: EducationalContent для индексации.

        Returns:
            True если успешно, False при ошибке.
        """
        svc = self._get_embedding_service()
        if not svc:
            return False

        text_to_embed = f"{content.title}\n\n{content.content}"[:8000]

        try:
            embedding = await svc.embed_document(text_to_embed)
        except Exception as e:
            logger.debug(f"Embedding документа недоступен: {e}")
            return False

        if not embedding or len(embedding) == 0:
            return False

        source_hash = _content_source_hash(content.title, content.source_url)
        vec_str = "[" + ",".join(str(x) for x in embedding) + "]"

        try:
            with get_db() as db:
                from sqlalchemy import text

                db.execute(
                    text(
                        """
                        INSERT INTO knowledge_embeddings (title, content, subject, source_url, embedding, source_hash)
                        VALUES (:title, :content, :subject, :source_url, CAST(:vec AS vector), :source_hash)
                        ON CONFLICT (source_hash) WHERE source_hash IS NOT NULL DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            created_at = now()
                        """
                    ),
                    {
                        "title": content.title,
                        "content": content.content,
                        "subject": content.subject,
                        "source_url": content.source_url,
                        "vec": vec_str,
                        "source_hash": source_hash,
                    },
                )
                db.commit()
            logger.debug(f"Indexed: {content.title[:50]}")
            return True
        except Exception as e:
            logger.debug(f"Index insert error: {e}")
            try:
                with get_db() as db:
                    from sqlalchemy import text

                    db.execute(
                        text(
                            """
                            INSERT INTO knowledge_embeddings (title, content, subject, source_url, embedding, source_hash)
                            VALUES (:title, :content, :subject, :source_url, CAST(:vec AS vector), :source_hash)
                            """
                        ),
                        {
                            "title": content.title,
                            "content": content.content,
                            "subject": content.subject,
                            "source_url": content.source_url,
                            "vec": vec_str,
                            "source_hash": source_hash,
                        },
                    )
                    db.commit()
                return True
            except Exception as e2:
                logger.debug(f"Index insert fallback error: {e2}")
                return False

    def stats(self) -> dict:
        """Статистика векторного хранилища."""
        try:
            with get_db() as db:
                from sqlalchemy import text

                count = db.execute(
                    text("SELECT COUNT(*) FROM knowledge_embeddings WHERE embedding IS NOT NULL")
                ).scalar()
                return {"indexed_count": count or 0}
        except Exception:
            return {"indexed_count": 0}
