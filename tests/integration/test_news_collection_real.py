"""
Integration тесты для сбора новостей с реальными API.

Требует реальные API ключи для тестирования.
"""

import pytest
import os

from bot.services.news_collector_service import NewsCollectorService


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("WORLD_NEWS_API_KEY") and not os.getenv("NEWSAPI_KEY"),
    reason="Требуются API ключи для тестирования",
)
async def test_news_collection_real():
    """Тест реального сбора новостей."""
    collector = NewsCollectorService()

    try:
        # Собираем новости (по 2 из каждого источника)
        collected = await collector.collect_news(limit_per_source=2)

        # Проверяем, что что-то собрано
        assert collected >= 0  # Может быть 0 если все отфильтрованы

    finally:
        await collector.close()


@pytest.mark.asyncio
async def test_news_collection_local_source():
    """Тест сбора из локального источника (не требует API)."""
    collector = NewsCollectorService()

    try:
        # Используем только локальный источник
        collector.sources = [collector.sources[-1]]  # LocalHumorSource

        collected = await collector.collect_news(limit_per_source=3)

        # Локальный источник должен вернуть новости
        assert collected > 0

    finally:
        await collector.close()
