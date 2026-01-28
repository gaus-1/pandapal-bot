"""
Источник новостей с Lenta.ru по рубрикам.

Рубрики: travel, science, autolenta, wellness, culture, world,
media/hackers, media/memes, media/factchecking.
"""

import re
from typing import Any
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from bot.security import validate_url_safety
from bot.services.news.sources.base import BaseNewsSource

LENTA_BASE = "https://lenta.ru"

# Пути рубрик (URL = LENTA_BASE + path)
LENTA_RUBRICS = [
    ("rubrics/travel/", "lenta_travel"),
    ("rubrics/science/", "lenta_science"),
    ("rubrics/autolenta/", "lenta_autolenta"),
    ("rubrics/wellness/", "lenta_wellness"),
    ("rubrics/culture/", "lenta_culture"),
    ("rubrics/world/", "lenta_world"),
    ("rubrics/media/hackers/", "lenta_media_hackers"),
    ("rubrics/media/memes/", "lenta_media_memes"),
    ("rubrics/media/factchecking/", "lenta_media_factchecking"),
]


class LentaRuSource(BaseNewsSource):
    """Источник новостей с Lenta.ru по списку рубрик."""

    def __init__(self):
        """Инициализация источника."""
        super().__init__(timeout=30.0, max_retries=3)
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

    def get_source_name(self) -> str:
        """Получить название источника."""
        return "lenta_ru"

    async def _safe_get(self, url: str) -> aiohttp.ClientResponse | None:
        """Безопасный GET с проверкой URL."""
        if not validate_url_safety(url):
            logger.warning(f"⚠️ Небезопасный URL заблокирован: {url}")
            return None
        session = await self._ensure_session()
        try:
            return await session.get(
                url, headers={"User-Agent": self.user_agent}, allow_redirects=True
            )
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к {url}: {e}")
            return None

    async def _scrape_rubric(
        self, path: str, source_label: str, limit: int
    ) -> list[dict[str, Any]]:
        """
        Парсить одну рубрику Lenta.ru.

        На странице: заголовки в h3, ссылки на материалы в /news/, /articles/, /extlink/, /brief/.
        """
        news_list = []
        url = urljoin(LENTA_BASE + "/", path)
        try:
            response = await self._safe_get(url)
            if not response or response.status != 200:
                logger.warning(f"⚠️ Lenta {path}: {response.status if response else 'no response'}")
                return news_list

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # Ссылки на материалы Lenta
            link_re = re.compile(r"^/(news|articles|extlink|brief)/")
            seen_urls: set[str] = set()

            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                if not link_re.match(href):
                    continue
                full_url = urljoin(LENTA_BASE + "/", href)
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Ищем заголовок: сначала предыдущий h3, потом родительский h3, потом текст ссылки
                title = ""
                prev_h3 = a.find_previous("h3")
                if prev_h3:
                    title = prev_h3.get_text(strip=True)
                else:
                    parent = a.parent
                    if parent:
                        parent_h3 = parent.find("h3")
                        if parent_h3:
                            title = parent_h3.get_text(strip=True)
                    if not title:
                        title = a.get_text(strip=True)

                # Убираем время и дату из конца заголовка
                title = re.sub(r"\d{1,2}:\d{2},?\s*\d{1,2}\s+\w+\s+\d{4}$", "", title).strip()
                title = re.sub(r"^\d{1,2}:\d{2},?\s*", "", title).strip()
                if not title or len(title) < 5:
                    continue

                news_list.append(
                    {
                        "title": title[:300],
                        "content": title[:500],
                        "url": full_url,
                        "source": source_label,
                        "published_date": None,
                        "image_url": None,
                    }
                )

                if len(news_list) >= limit:
                    break

            if news_list:
                logger.info(f"✅ Lenta {path}: {len(news_list)} новостей")
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга Lenta {path}: {e}")

        return news_list[:limit]

    async def fetch_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Собрать новости со всех рубрик Lenta.ru.

        Лимит распределяется по рубрикам (минимум 1 на рубрику).
        """
        per_rubric = max(1, limit // len(LENTA_RUBRICS))
        all_news = []

        for path, source_label in LENTA_RUBRICS:
            items = await self._scrape_rubric(path, source_label, per_rubric)
            all_news.extend(items)

        return all_news[:limit]
