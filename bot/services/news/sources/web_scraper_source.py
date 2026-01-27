"""
Источник новостей через веб-скрапинг.

Поддержка: mel.fm (новости об образовании), deti.mail.ru (детские новости)
"""

import re
from typing import Any
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from bot.security import validate_url_safety
from bot.services.news.sources.base import BaseNewsSource


class WebScraperNewsSource(BaseNewsSource):
    """
    Источник новостей через веб-скрапинг.

    Парсит HTML страницы детских новостных сайтов.
    """

    def __init__(self):
        """Инициализация источника."""
        super().__init__(timeout=30.0, max_retries=3)
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

    def get_source_name(self) -> str:
        """Получить название источника."""
        return "web_scraper"

    async def _safe_get(self, url: str) -> aiohttp.ClientResponse | None:
        """
        Безопасный HTTP GET запрос с SSRF защитой.

        Args:
            url: URL для запроса

        Returns:
            Response объект или None если URL небезопасен
        """
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

    async def _scrape_mel_fm(self, limit: int) -> list[dict[str, Any]]:
        """
        Парсить новости с mel.fm.

        Args:
            limit: Максимальное количество новостей

        Returns:
            List[dict]: Список новостей
        """
        news_list = []
        try:
            url = "https://mel.fm/novosti"
            response = await self._safe_get(url)

            if not response or response.status != 200:
                logger.warning(
                    f"⚠️ Не удалось получить страницу mel.fm: {response.status if response else 'no response'}"
                )
                return news_list

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # Ищем статьи новостей (структура может отличаться, нужно адаптировать)
            articles = soup.find_all("article", limit=limit) or soup.find_all(
                "div", class_=re.compile("article|news|post"), limit=limit
            )

            for article in articles[:limit]:
                try:
                    title_elem = article.find("h1") or article.find("h2") or article.find("h3")
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    content_elem = article.find("p") or article.find(
                        "div", class_=re.compile("content|text|excerpt")
                    )
                    content = content_elem.get_text(strip=True) if content_elem else ""

                    link_elem = article.find("a", href=True)
                    url_full = link_elem["href"] if link_elem else None
                    if url_full and not url_full.startswith("http"):
                        url_full = urljoin("https://mel.fm", url_full)

                    if title and content:
                        news_list.append(
                            {
                                "title": title,
                                "content": content[:500],  # Ограничиваем длину
                                "url": url_full,
                                "source": "mel_fm",
                                "published_date": None,  # Парсинг даты требует дополнительной логики
                                "image_url": None,
                            }
                        )

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка обработки новости с mel.fm: {e}")
                    continue

            logger.info(f"✅ Получено {len(news_list)} новостей с mel.fm")
            return news_list

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга mel.fm: {e}")
            return news_list

    async def _scrape_deti_mail_ru(self, limit: int) -> list[dict[str, Any]]:
        """
        Парсить новости с deti.mail.ru.

        Args:
            limit: Максимальное количество новостей

        Returns:
            List[dict]: Список новостей
        """
        news_list = []
        try:
            url = "https://deti.mail.ru/news/"
            response = await self._safe_get(url)

            if not response or response.status != 200:
                logger.warning(
                    f"⚠️ Не удалось получить страницу deti.mail.ru: {response.status if response else 'no response'}"
                )
                return news_list

            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # Ищем статьи новостей
            articles = soup.find_all("article", limit=limit) or soup.find_all(
                "div", class_=re.compile("news|article|post"), limit=limit
            )

            for article in articles[:limit]:
                try:
                    title_elem = article.find("h1") or article.find("h2") or article.find("h3")
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    content_elem = article.find("p") or article.find(
                        "div", class_=re.compile("content|text|excerpt")
                    )
                    content = content_elem.get_text(strip=True) if content_elem else ""

                    link_elem = article.find("a", href=True)
                    url_full = link_elem["href"] if link_elem else None
                    if url_full and not url_full.startswith("http"):
                        url_full = urljoin("https://deti.mail.ru", url_full)

                    if title and content:
                        news_list.append(
                            {
                                "title": title,
                                "content": content[:500],
                                "url": url_full,
                                "source": "deti_mail_ru",
                                "published_date": None,
                                "image_url": None,
                            }
                        )

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка обработки новости с deti.mail.ru: {e}")
                    continue

            logger.info(f"✅ Получено {len(news_list)} новостей с deti.mail.ru")
            return news_list

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга deti.mail.ru: {e}")
            return news_list

    async def fetch_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Получить новости через веб-скрапинг.

        Args:
            limit: Максимальное количество новостей

        Returns:
            List[dict]: Список новостей
        """
        all_news = []

        # Парсим mel.fm
        mel_news = await self._scrape_mel_fm(limit // 2)
        all_news.extend(mel_news)

        # Парсим deti.mail.ru
        deti_news = await self._scrape_deti_mail_ru(limit // 2)
        all_news.extend(deti_news)

        return all_news[:limit]
