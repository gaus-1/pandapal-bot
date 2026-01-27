"""
Источник приколов и шуток с umorashka.ru.

Парсит детские приколы, шутки, загадки с сайта umorashka.ru.
"""

import re
from typing import Any

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from bot.security import validate_url_safety
from bot.services.news.sources.base import BaseNewsSource


class HumorSiteSource(BaseNewsSource):
    """
    Источник приколов и шуток с umorashka.ru.

    Парсит детский юмористический контент.
    """

    def __init__(self):
        """Инициализация источника."""
        super().__init__(timeout=30.0, max_retries=3)
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.base_url = "https://umorashka.ru"

    def get_source_name(self) -> str:
        """Получить название источника."""
        return "umorashka_ru"

    async def _safe_get(self, url: str) -> aiohttp.ClientResponse | None:
        """Безопасный HTTP GET запрос."""
        if not validate_url_safety(url):
            logger.warning(f"⚠️ Небезопасный URL заблокирован: {url}")
            return None

        session = await self._ensure_session()
        try:
            response = await session.get(
                url, headers={"User-Agent": self.user_agent}, allow_redirects=True
            )
            return response
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к {url}: {e}")
            return None

    async def _scrape_umorashka(self, limit: int) -> list[dict[str, Any]]:
        """
        Парсить приколы и шутки с umorashka.ru.

        Args:
            limit: Максимальное количество элементов

        Returns:
            List[dict]: Список приколов/шуток
        """
        items = []
        try:
            # Пробуем разные разделы сайта
            urls = [
                f"{self.base_url}/",
                f"{self.base_url}/anekdoty/",
                f"{self.base_url}/zagadki/",
            ]

            for url in urls:
                if len(items) >= limit:
                    break

                response = await self._safe_get(url)
                if not response or response.status != 200:
                    continue

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Ищем контент (структура может отличаться)
                content_blocks = soup.find_all(
                    "div", class_=re.compile("content|text|joke|anekdot")
                ) or soup.find_all("p")

                for block in content_blocks[: limit - len(items)]:
                    try:
                        text = block.get_text(strip=True)
                        if len(text) < 20 or len(text) > 500:
                            continue

                        # Проверяем, что это действительно прикол/шутка
                        if any(
                            word in text.lower()
                            for word in ["?", "!", "шутка", "прикол", "загадка"]
                        ):
                            items.append(
                                {
                                    "title": text[:100] + "..." if len(text) > 100 else text,
                                    "content": text,
                                    "url": url,
                                    "source": self.get_source_name(),
                                    "published_date": None,
                                    "image_url": None,
                                }
                            )

                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка обработки контента с umorashka.ru: {e}")
                        continue

            logger.info(f"✅ Получено {len(items)} приколов/шуток с umorashka.ru")
            return items

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга umorashka.ru: {e}")
            return items

    async def fetch_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Получить приколы и шутки.

        Args:
            limit: Максимальное количество элементов

        Returns:
            List[dict]: Список приколов/шуток
        """
        return await self._scrape_umorashka(limit)
