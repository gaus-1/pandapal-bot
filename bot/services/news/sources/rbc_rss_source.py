"""
Источник новостей из RSS фида RBC.

Парсит RSS фид https://rssexport.rbc.ru/rbcnews/news/30/full.rss
и извлекает новости с полным текстом из rbc_news:full-text.
"""

import html
import re
from typing import Any
from xml.etree import ElementTree

from loguru import logger

from bot.security import validate_url_safety
from bot.services.news.sources.base import BaseNewsSource

RBC_RSS_URL = "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"


class RbcRssSource(BaseNewsSource):
    """Источник новостей из RSS фида RBC."""

    def __init__(self):
        """Инициализация источника."""
        super().__init__(timeout=30.0, max_retries=3)
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

    def get_source_name(self) -> str:
        """Получить название источника."""
        return "rbc_rss"

    def _clean_html(self, text: str) -> str:
        """Очистить HTML теги и декодировать сущности."""
        if not text:
            return ""
        # Декодируем HTML сущности (&laquo; -> «, &nbsp; -> пробел, &mdash; -> —)
        text = html.unescape(text)
        # Убираем HTML теги
        text = re.sub(r"<[^>]+>", "", text)
        # Убираем множественные пробелы
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _map_category(self, rbc_category: str) -> str:
        """Маппинг категорий RBC в наши категории."""
        category_map = {
            "спорт": "спорт",
            "общество": "события",
            "политика": "события",  # Политика будет отфильтрована, но на всякий случай
        }
        return category_map.get(rbc_category.lower(), "события")

    def _parse_rss_item(self, item: ElementTree.Element) -> dict[str, Any] | None:
        """Парсить один элемент RSS."""
        try:
            # Заголовок
            title_elem = item.find("title")
            if title_elem is None or not title_elem.text:
                return None
            title = self._clean_html(title_elem.text)

            # Ссылка
            link_elem = item.find("link")
            link = link_elem.text if link_elem is not None and link_elem.text else ""

            # Категория
            category_elem = item.find("category")
            category = self._map_category(
                category_elem.text
                if category_elem is not None and category_elem.text
                else "события"
            )

            # Описание (краткое)
            description_elem = item.find("description")
            description = self._clean_html(
                description_elem.text
                if description_elem is not None and description_elem.text
                else ""
            )

            # Полный текст из rbc_news:full-text
            ns = {"rbc_news": "https://www.rbc.ru"}
            full_text_elem = item.find("rbc_news:full-text", ns)
            content = self._clean_html(
                full_text_elem.text
                if full_text_elem is not None and full_text_elem.text
                else description
            )

            # Если полного текста нет, используем описание
            if not content or len(content) < 50:
                content = description

            # Картинка из enclosure или rbc_news:image
            image_url = None
            enclosure_elem = item.find("enclosure")
            if enclosure_elem is not None and enclosure_elem.get("type") == "image/jpeg":
                image_url = enclosure_elem.get("url")

            if not image_url:
                image_elem = item.find("rbc_news:image", ns)
                if image_elem is not None:
                    url_elem = image_elem.find("rbc_news:url", ns)
                    if url_elem is not None and url_elem.text:
                        image_url = url_elem.text

            # GUID для дедупликации
            guid_elem = item.find("guid")
            guid = guid_elem.text if guid_elem is not None and guid_elem.text else link

            return {
                "title": title,
                "content": content,
                "category": category,
                "image_url": image_url,
                "source": self.get_source_name(),
                "source_url": link,
                "source_id": guid,
            }

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга RSS элемента: {e}")
            return None

    async def fetch_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Получить новости из RSS фида.

        Args:
            limit: Максимальное количество новостей

        Returns:
            list[dict]: Список новостей
        """
        if not validate_url_safety(RBC_RSS_URL):
            logger.warning(f"⚠️ Небезопасный URL заблокирован: {RBC_RSS_URL}")
            return []

        session = await self._ensure_session()
        news_list = []

        try:
            async with session.get(
                RBC_RSS_URL, headers={"User-Agent": self.user_agent}
            ) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ RBC RSS: статус {response.status}")
                    return news_list

                xml_content = await response.text()
                root = ElementTree.fromstring(xml_content)

                # Парсим элементы channel/item
                items = root.findall(".//item")
                for item in items[:limit]:
                    news_item = self._parse_rss_item(item)
                    if news_item:
                        news_list.append(news_item)

            logger.info(f"✅ RBC RSS: получено {len(news_list)} новостей")
            return news_list

        except Exception as e:
            logger.error(f"❌ Ошибка получения RSS от RBC: {e}")
            return []
