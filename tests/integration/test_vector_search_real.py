"""
Тесты VectorSearchService с реальным Yandex Embeddings API и pgvector.

Требует: PostgreSQL с pgvector, YANDEX_CLOUD_API_KEY, YANDEX_CLOUD_FOLDER_ID.
Миграция 20260212_add_knowledge_embeddings должна быть применена.
Запуск: pytest tests/integration/test_vector_search_real.py -v
"""

import os
from datetime import datetime, UTC

import pytest

from bot.services.rag import VectorSearchService
from bot.services.web_scraper import EducationalContent


def _has_real_embeddings_api():
    k = os.getenv("YANDEX_CLOUD_API_KEY", "") or ""
    return k and k not in ("test_api_key", "AQVTEST_KEY_FOR_CI") and len(k) > 20


def _has_pgvector():
    db_url = os.getenv("DATABASE_URL", "") or ""
    return "postgresql" in db_url and "sqlite" not in db_url


def _has_knowledge_embeddings_table():
    """Проверка существования таблицы knowledge_embeddings (миграция применена)."""
    if not _has_pgvector():
        return False
    try:
        from sqlalchemy import create_engine, text
        url = os.getenv("DATABASE_URL", "")
        if "postgresql://" in url and "+psycopg" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM knowledge_embeddings LIMIT 1"))
        return True
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.skipif(
    not _has_real_embeddings_api(),
    reason="Требуется реальный Yandex API ключ",
)
@pytest.mark.skipif(
    not _has_pgvector(),
    reason="Требуется PostgreSQL с pgvector (SQLite не поддерживается)",
)
@pytest.mark.skipif(
    not _has_knowledge_embeddings_table(),
    reason="Требуется миграция knowledge_embeddings (pgvector на сервере)",
)
class TestVectorSearchReal:
    """Тесты VectorSearchService с реальным API и pgvector."""

    @pytest.fixture
    def vector_search(self):
        return VectorSearchService()

    @pytest.fixture
    def sample_content(self):
        return EducationalContent(
            title="Теорема Пифагора",
            content="В прямоугольном треугольнике квадрат гипотенузы равен сумме квадратов катетов. c² = a² + b².",
            subject="математика",
            difficulty="средний",
            source_url="https://ru.wikipedia.org/wiki/Теорема_Пифагора",
            extracted_at=datetime.now(UTC),
            tags=["геометрия"],
        )

    @pytest.mark.asyncio
    async def test_index_and_search(self, vector_search, sample_content):
        """index_content + search возвращает проиндексированный контент."""
        ok = await vector_search.index_content(sample_content)
        assert ok, "Индексация не удалась"

        results = await vector_search.search("теорема Пифагора гипотенуза", top_k=5)
        assert len(results) > 0, "Поиск не нашёл проиндексированный контент"
        titles = [r.title for r in results]
        assert "Теорема Пифагора" in titles or any(
            "пифагор" in t.lower() for t in titles
        )

    @pytest.mark.asyncio
    async def test_search_semantic_relevance(self, vector_search, sample_content):
        """Семантический поиск: похожий запрос находит релевантный контент."""
        await vector_search.index_content(sample_content)

        results = await vector_search.search(
            "как связаны катеты и гипотенуза в прямоугольном треугольнике",
            top_k=3,
            min_similarity=0.3,
        )
        assert len(results) > 0
        combined = " ".join(r.content for r in results).lower()
        assert any(
            w in combined for w in ["гипотенуза", "катет", "пифагор", "треугольник"]
        )

    @pytest.mark.asyncio
    async def test_stats(self, vector_search):
        """stats возвращает число проиндексированных записей."""
        stats = vector_search.stats()
        assert "indexed_count" in stats
        assert isinstance(stats["indexed_count"], int)
        assert stats["indexed_count"] >= 0
