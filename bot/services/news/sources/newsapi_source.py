"""
Источник новостей из NewsAPI.org.

API ключ: 73663febf6264874b425c9b5b9ae0b08
Endpoint: https://newsapi.org/v2/everything
"""

import os
from datetime import datetime
from typing import Any

from loguru import logger

from bot.services.news.sources.base import BaseNewsSource


class NewsAPISource(BaseNewsSource):
    """
    Источник новостей из NewsAPI.org.

    Фильтрует новости по детским темам на русском языке.
    Требуется дополнительная фильтрация (API возвращает не только детские новости).
    """

    def __init__(self):
        """Инициализация источника."""
        super().__init__(timeout=30.0, max_retries=3)
        self.api_key = os.getenv("NEWSAPI_KEY", "73663febf6264874b425c9b5b9ae0b08")
        self.base_url = "https://newsapi.org/v2/everything"

    def get_source_name(self) -> str:
        """Получить название источника."""
        return "newsapi"

    async def fetch_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Получить новости из NewsAPI.org.

        Args:
            limit: Максимальное количество новостей

        Returns:
            List[dict]: Список новостей
        """
        try:
            params = {
                "apiKey": self.api_key,
                "q": "дети OR детский OR школьник OR образование",
                "language": "ru",
                "sortBy": "publishedAt",
                "pageSize": limit,
            }

            data = await self._fetch_with_retry(self.base_url, params=params)

            news_list = []
            if "articles" in data:
                for item in data["articles"][:limit]:
                    try:
                        published_date = None
                        if "publishedAt" in item:
                            try:  # noqa: SIM105
                                published_date = datetime.fromisoformat(
                                    item["publishedAt"].replace("Z", "+00:00")
                                )
                            except (ValueError, AttributeError):
                                pass

                        news_item = {
                            "title": item.get("title", ""),
                            "content": item.get("description", "") or item.get("content", ""),
                            "url": item.get("url"),
                            "source": self.get_source_name(),
                            "published_date": published_date,
                            "image_url": item.get("urlToImage"),
                        }

                        if news_item["title"] and news_item["content"]:
                            news_list.append(news_item)

                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка обработки новости из NewsAPI: {e}")
                        continue

            logger.info(f"✅ Получено {len(news_list)} новостей из NewsAPI")
            return news_list

        except Exception as e:
            logger.error(f"❌ Ошибка получения новостей из NewsAPI: {e}")
            return []
