"""
Unit тесты для источников новостей.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.news.sources.world_news_api_source import WorldNewsAPISource
from bot.services.news.sources.newsapi_source import NewsAPISource
from bot.services.news.sources.local_humor_source import LocalHumorSource


@pytest.mark.asyncio
async def test_world_news_api_source():
    """Тест WorldNewsAPISource."""
    source = WorldNewsAPISource()

    assert source.get_source_name() == "world_news_api"

    # Mock HTTP запрос
    with patch.object(source, "_fetch_with_retry") as mock_fetch:
        mock_fetch.return_value = {
            "news": [
                {
                    "title": "Тест",
                    "text": "Содержание",
                    "url": "https://test.com",
                    "publish_date": "2026-01-27T12:00:00Z",
                }
            ]
        }

        news = await source.fetch_news(limit=1)

        assert len(news) > 0
        assert news[0]["title"] == "Тест"
        assert news[0]["source"] == "world_news_api"

    await source.close()


@pytest.mark.asyncio
async def test_newsapi_source():
    """Тест NewsAPISource."""
    source = NewsAPISource()

    assert source.get_source_name() == "newsapi"

    # Mock HTTP запрос
    with patch.object(source, "_fetch_with_retry") as mock_fetch:
        mock_fetch.return_value = {
            "articles": [
                {
                    "title": "Тест",
                    "description": "Содержание",
                    "url": "https://test.com",
                    "publishedAt": "2026-01-27T12:00:00Z",
                }
            ]
        }

        news = await source.fetch_news(limit=1)

        assert len(news) > 0
        assert news[0]["title"] == "Тест"

    await source.close()


@pytest.mark.asyncio
async def test_local_humor_source():
    """Тест LocalHumorSource."""
    source = LocalHumorSource()

    assert source.get_source_name() == "local_humor"

    news = await source.fetch_news(limit=5)

    assert len(news) > 0
    assert all("title" in item and "content" in item for item in news)

    await source.close()
