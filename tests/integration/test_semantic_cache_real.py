"""
Тесты SemanticCache с реальным pgvector и Yandex Embeddings API.

Требует DATABASE_URL, YANDEX_CLOUD_API_KEY, YANDEX_CLOUD_FOLDER_ID.
Миграция pgvector должна быть применена.
Запуск: pytest tests/integration/test_semantic_cache_real.py -v
"""

import os

import pytest

from bot.services.rag import SemanticCache
from bot.services.web_scraper import EducationalContent
from datetime import datetime, UTC


@pytest.mark.integration
@pytest.mark.skipif(
    not all(
        os.getenv(k)
        for k in ("DATABASE_URL", "YANDEX_CLOUD_API_KEY", "YANDEX_CLOUD_FOLDER_ID")
    ),
    reason="Требуется DATABASE_URL и Yandex credentials",
)
class TestSemanticCacheReal:
    """Тесты SemanticCache с pgvector."""

    @pytest.fixture
    def cache(self):
        return SemanticCache(ttl_hours=24, threshold=0.85)

    @pytest.fixture
    def sample_result(self):
        return [
            EducationalContent(
                title="Квадратные корни",
                content="√1=1, √2≈1.41, √3≈1.73",
                subject="математика",
                difficulty="средний",
                source_url="https://example.com",
                extracted_at=datetime.now(UTC),
                tags=["алгебра"],
            )
        ]

    @pytest.mark.asyncio
    async def test_set_and_get_same_query(self, cache, sample_result):
        """set + get с тем же запросом возвращает результат."""
        query = "список квадратных корней"
        await cache.set(query, sample_result)
        result = await cache.get(query)
        assert result is not None
        assert len(result) == 1
        assert result[0].title == "Квадратные корни"

    @pytest.mark.asyncio
    async def test_similar_query_hit(self, cache, sample_result):
        """Похожий запрос находит кеш."""
        await cache.set("список квадратных корней", sample_result)
        result = await cache.get("таблица квадратных корней")
        assert result is not None

    @pytest.mark.asyncio
    async def test_different_query_miss(self, cache, sample_result):
        """Непохожий запрос не возвращает кеш."""
        await cache.set("список квадратных корней", sample_result)
        result = await cache.get("кто такой Пушкин")
        assert result is None
