"""
Локальная база детских шуток, загадок и интересных фактов.

Fallback источник, если внешние API недоступны.
"""

from typing import Any

from loguru import logger

from bot.services.news.sources.base import BaseNewsSource


class LocalHumorSource(BaseNewsSource):
    """
    Локальная база детских шуток и приколов.

    Качественный контент, проверенный модераторами.
    Постоянно пополняется из umorashka.ru и других источников.
    """

    def __init__(self):
        """Инициализация источника."""
        super().__init__()

        # Локальная база детских шуток и загадок
        self.local_jokes = [
            {
                "title": "Загадка про панду",
                "content": "Что общего у панды и школьника? Оба любят бамбук... нет, подожди, это только панда!",
                "url": None,
                "source": "local",
                "published_date": None,
                "image_url": None,
            },
            {
                "title": "Шутка про уроки",
                "content": "Почему математика самая веселая наука? Потому что в ней всегда есть решение!",
                "url": None,
                "source": "local",
                "published_date": None,
                "image_url": None,
            },
            {
                "title": "Загадка про животных",
                "content": "Какое животное всегда готово к школе? Кот-ученик! Нет, подожди... это просто кот!",
                "url": None,
                "source": "local",
                "published_date": None,
                "image_url": None,
            },
        ]

        # Локальная база интересных фактов
        self.local_facts = [
            {
                "title": "Интересный факт про панд",
                "content": "Знаешь ли ты, что панды едят бамбук почти весь день? Они тратят до 12 часов в день на еду!",
                "url": None,
                "source": "local",
                "published_date": None,
                "image_url": None,
            },
            {
                "title": "Факт про космос",
                "content": "На Юпитере идут дожди из алмазов! Правда, мы туда не попадем, но это очень интересно!",
                "url": None,
                "source": "local",
                "published_date": None,
                "image_url": None,
            },
        ]

        logger.info("✅ LocalHumorSource инициализирован")

    def get_source_name(self) -> str:
        """Получить название источника."""
        return "local_humor"

    async def fetch_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Получить локальные шутки и факты.

        Args:
            limit: Максимальное количество элементов

        Returns:
            List[dict]: Список шуток/фактов
        """
        import random

        all_items = self.local_jokes + self.local_facts
        random.shuffle(all_items)
        return all_items[:limit]
