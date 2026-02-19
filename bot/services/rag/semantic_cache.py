"""Semantic cache для RAG системы.

Векторный поиск через pgvector + Yandex Embeddings API.
При недоступности embeddings — fallback: get возвращает None, set не пишет.
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

from bot.database import get_db
from bot.services.embeddings_service import get_embedding_service
from bot.services.web_scraper import EducationalContent


def _content_to_dict(item: EducationalContent) -> dict[str, Any]:
    """Сериализация EducationalContent в dict для JSON."""
    return {
        "title": item.title,
        "content": item.content,
        "subject": item.subject,
        "difficulty": item.difficulty,
        "source_url": item.source_url,
        "extracted_at": item.extracted_at.isoformat() if item.extracted_at else None,
        "tags": item.tags,
    }


def _dict_to_content(data: dict[str, Any]) -> EducationalContent:
    """Десериализация dict в EducationalContent."""
    extracted_at = data.get("extracted_at")
    if isinstance(extracted_at, str):
        try:
            extracted_at = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))
        except ValueError:
            extracted_at = datetime.now(UTC)
    elif extracted_at is None:
        extracted_at = datetime.now(UTC)
    return EducationalContent(
        title=data.get("title", ""),
        content=data.get("content", ""),
        subject=data.get("subject", ""),
        difficulty=data.get("difficulty", ""),
        source_url=data.get("source_url", ""),
        extracted_at=extracted_at,
        tags=data.get("tags", []),
    )


class SemanticCache:
    """
    Кэш с векторным поиском через pgvector и Yandex Embeddings API.
    """

    def __init__(self, ttl_hours: int = 24, threshold: float = 0.85):
        self.ttl_hours = ttl_hours
        self.threshold = threshold
        self._embedding_service = None

    def _get_embedding_service(self):
        if self._embedding_service is None:
            try:
                self._embedding_service = get_embedding_service()
            except Exception as e:
                logger.debug(f"EmbeddingService недоступен: {e}")
        return self._embedding_service

    def _evict_expired(self, db) -> None:
        """Удалить устаревшие записи (created_at старше ttl_hours)."""
        try:
            from sqlalchemy import text

            cutoff = datetime.now(UTC) - timedelta(hours=self.ttl_hours)
            db.execute(
                text("DELETE FROM embedding_cache WHERE created_at < :cutoff"),
                {"cutoff": cutoff},
            )
        except Exception as e:
            logger.debug(f"Semantic cache evict_expired: {e}")

    async def get(
        self, query: str, threshold: float | None = None
    ) -> list[EducationalContent] | None:
        """
        Получить результат из кэша для семантически похожего запроса.

        Returns:
            list[EducationalContent] или None
        """
        svc = self._get_embedding_service()
        if not svc:
            return None
        try:
            embedding = await svc.embed_query(query)
        except Exception as e:
            logger.debug(f"Embedding запроса недоступен: {e}")
            return None

        if not embedding or len(embedding) == 0:
            return None

        th = threshold if threshold is not None else self.threshold
        vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
        cutoff = datetime.now(UTC) - timedelta(hours=self.ttl_hours)

        try:
            with get_db() as db:
                from sqlalchemy import text

                row = db.execute(
                    text(
                        """
                        SELECT query_text, result_json, 1 - (embedding <=> CAST(:vec AS vector)) as sim
                        FROM embedding_cache
                        WHERE embedding IS NOT NULL AND created_at > :cutoff
                        ORDER BY embedding <=> CAST(:vec AS vector)
                        LIMIT 1
                        """
                    ),
                    {"vec": vec_str, "cutoff": cutoff},
                ).fetchone()

                if not row:
                    return None
                _query_text, result_json, sim = row[0], row[1], float(row[2])
                if sim < th:
                    return None
                items = json.loads(result_json)
                return [_dict_to_content(item) for item in items]
        except Exception as e:
            logger.debug(f"Semantic cache get error: {e}")
            return None

    async def set(self, query: str, result: list[EducationalContent]) -> None:
        """Сохранить результат в кэш."""
        svc = self._get_embedding_service()
        if not svc:
            return
        try:
            embedding = await svc.embed_query(query)
        except Exception as e:
            logger.debug(f"Embedding для set недоступен: {e}")
            return

        if not embedding or len(embedding) == 0:
            return

        vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
        result_json = json.dumps([_content_to_dict(item) for item in result])

        try:
            with get_db() as db:
                from sqlalchemy import text

                self._evict_expired(db)
                db.commit()

                db.execute(
                    text(
                        """
                        INSERT INTO embedding_cache (query_text, embedding, result_json)
                        VALUES (:query_text, CAST(:vec AS vector), CAST(:result_json AS jsonb))
                        """
                    ),
                    {
                        "query_text": query,
                        "vec": vec_str,
                        "result_json": result_json,
                    },
                )
                db.commit()
        except Exception as e:
            logger.debug(f"Semantic cache set error: {e}")

    def clear(self) -> None:
        """Очистить кэш (удалить все записи)."""
        try:
            with get_db() as db:
                from sqlalchemy import text

                db.execute(text("DELETE FROM embedding_cache"))
                db.commit()
        except Exception as e:
            logger.debug(f"Semantic cache clear error: {e}")

    def stats(self) -> dict:
        """Статистика кэша."""
        try:
            with get_db() as db:
                from sqlalchemy import text

                count = db.execute(text("SELECT COUNT(*) FROM embedding_cache")).scalar()
                return {
                    "size": count or 0,
                    "ttl_hours": self.ttl_hours,
                    "threshold": self.threshold,
                }
        except Exception:
            return {"size": 0, "ttl_hours": self.ttl_hours, "threshold": self.threshold}
