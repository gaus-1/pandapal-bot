"""
Источник новостей из World News API.

API ключ: 0e70d6a927c547c3878bdd85b72e3232
Endpoint: https://api.worldnewsapi.com/search-news
"""

import os
from datetime import datetime
from typing import Any

from loguru import logger

from bot.services.news.sources.base import BaseNewsSource


class WorldNewsAPISource(BaseNewsSource):
    """
    Источник новостей из World News API.

    Фильтрует новости по детским темам на русском языке.
    """

    def __init__(self):
        """Инициализация источника."""
        super().__init__(timeout=30.0, max_retries=3)
        self.api_key = os.getenv("WORLD_NEWS_API_KEY", "0e70d6a927c547c3878bdd85b72e3232")
        self.base_url = "https://api.worldnewsapi.com/search-news"

    def get_source_name(self) -> str:
        """Получить название источника."""
        return "world_news_api"

    async def fetch_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Получить новости из World News API.

        Args:
            limit: Максимальное количество новостей

        Returns:
            List[dict]: Список новостей
        """
        try:
            params = {
                "api-key": self.api_key,
                "source-country": "ru",
                "language": "ru",
                "text": "дети OR детский OR школьник OR образование OR игры OR спорт OR животные",
                "number": limit,
                "sort": "publish-time",
                "sort-direction": "DESC",
            }

            data = await self._fetch_with_retry(self.base_url, params=params)

            news_list = []
            if "news" in data:
                for item in data["news"][:limit]:
                    try:
                        published_date = None
                        if "publish_date" in item:
                            try:  # noqa: SIM105
                                published_date = datetime.fromisoformat(
                                    item["publish_date"].replace("Z", "+00:00")
                                )
                            except (ValueError, AttributeError):
                                pass

                        news_item = {
                            "title": item.get("title", ""),
                            "content": item.get("text", ""),
                            "url": item.get("url"),
                            "source": self.get_source_name(),
                            "published_date": published_date,
                            "image_url": item.get("image"),
                        }

                        if news_item["title"] and news_item["content"]:
                            news_list.append(news_item)

                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка обработки новости из World News API: {e}")
                        continue

            logger.info(f"✅ Получено {len(news_list)} новостей из World News API")
            return news_list

        except Exception as e:
            logger.error(f"❌ Ошибка получения новостей из World News API: {e}")
            return []
