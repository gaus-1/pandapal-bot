"""
Сервис сбора новостей для детского новостного бота.

Фасад для координации всех компонентов:
- Источники новостей
- Адаптеры контента
- Модерация
- Сохранение в БД
"""

from typing import Any

from loguru import logger

from bot.database import get_db
from bot.services.news.adapters.age_adapter import AgeNewsAdapter
from bot.services.news.adapters.category_classifier import NewsCategoryClassifier
from bot.services.news.adapters.content_enhancer import NewsContentEnhancer
from bot.services.news.adapters.content_filter import NewsContentFilter
from bot.services.news.moderators.content_moderator import NewsContentModerator
from bot.services.news.repository import NewsRepository
from bot.services.news.sources.humor_site_source import HumorSiteSource
from bot.services.news.sources.joke_api_source import JokeAPISource
from bot.services.news.sources.lenta_ru_source import LentaRuSource
from bot.services.news.sources.local_humor_source import LocalHumorSource
from bot.services.news.sources.newsapi_source import NewsAPISource
from bot.services.news.sources.rbc_rss_source import RbcRssSource
from bot.services.news.sources.web_scraper_source import WebScraperNewsSource
from bot.services.news.sources.world_news_api_source import WorldNewsAPISource
from bot.services.yandex_cloud_service import YandexCloudService


class NewsCollectorService:
    """
    Сервис сбора новостей.

    Координирует все компоненты pipeline:
    Сбор → Фильтрация → Адаптация → Улучшение → Модерация → Сохранение
    """

    def __init__(self, sources: list | None = None):
        """
        Инициализация сервиса.

        Args:
            sources: Список источников новостей (если None, используются источники по умолчанию)
        """
        # Yandex Cloud сервис (общий для всех адаптеров)
        yandex_service = YandexCloudService()

        # Источники новостей
        if sources is None:
            self.sources = [
                RbcRssSource(),
                WorldNewsAPISource(),
                NewsAPISource(),
                WebScraperNewsSource(),
                LentaRuSource(),
                HumorSiteSource(),
                JokeAPISource(),
                LocalHumorSource(),
            ]
        else:
            self.sources = sources

        # Адаптеры
        self.age_adapter = AgeNewsAdapter(yandex_service)
        self.category_classifier = NewsCategoryClassifier(yandex_service)
        self.content_filter = NewsContentFilter(yandex_service)
        self.content_enhancer = NewsContentEnhancer(yandex_service)

        # Модератор
        self.moderator = NewsContentModerator()

        logger.info("✅ NewsCollectorService инициализирован")

    async def collect_news(self, limit_per_source: int = 5) -> int:
        """
        Собрать новости из всех источников.

        Args:
            limit_per_source: Максимальное количество новостей из каждого источника

        Returns:
            int: Количество собранных и сохраненных новостей
        """
        total_collected = 0

        for source in self.sources:
            try:
                logger.info(f"📰 Сбор новостей из {source.get_source_name()}...")

                # Получаем новости из источника
                news_items = await source.fetch_news(limit=limit_per_source)

                for news_item in news_items:
                    try:
                        # Pipeline обработки
                        processed = await self._process_news_item(news_item)

                        if processed:
                            total_collected += 1

                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка обработки новости: {e}")
                        continue

                # Закрываем сессию источника
                await source.close()

            except Exception as e:
                logger.error(f"❌ Ошибка сбора новостей из {source.get_source_name()}: {e}")
                continue

        logger.info(f"✅ Всего собрано и сохранено новостей: {total_collected}")
        return total_collected

    async def _process_news_item(self, news_item: dict[str, Any]) -> bool:
        """
        Обработать одну новость через весь pipeline.

        Args:
            news_item: Новость в формате словаря

        Returns:
            bool: True если новость сохранена
        """
        try:
            # 1. Фильтрация контента
            should_keep, reason = await self.content_filter.filter(news_item)
            if not should_keep:
                logger.debug(f"⚠️ Новость отфильтрована: {reason}")
                return False

            # 2. Классификация категории
            category, is_relevant = await self.category_classifier.classify(
                news_item.get("title", ""), news_item.get("content", "")
            )
            if not is_relevant:
                logger.debug("⚠️ Новость не релевантна для детей")
                return False

            news_item["category"] = category

            # 3. Модерация
            is_safe, reason = await self.moderator.moderate(news_item)
            if not is_safe:
                logger.debug(f"⚠️ Новость не прошла модерацию: {reason}")
                return False

            # 4. Адаптация под возраст (средний возраст 10 лет, 5 класс)
            adapted_content = await self.age_adapter.adapt_content(
                news_item.get("content", ""), age=10, grade=5
            )
            news_item["content"] = adapted_content

            # 5. Улучшение качества
            news_item = await self.content_enhancer.enhance(news_item, age=10)

            # 6. Установка возрастных границ (для всех детей 6-15 лет, 1-9 класс)
            news_item["age_min"] = 6
            news_item["age_max"] = 15
            news_item["grade_min"] = 1
            news_item["grade_max"] = 9
            news_item["is_moderated"] = True

            # 7. Сохранение в БД
            with get_db() as db:
                repository = NewsRepository(db)
                repository.save(news_item)
                db.commit()

            logger.info(f"✅ Новость сохранена: {news_item.get('title', '')[:50]}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обработки новости: {e}")
            return False

    async def close(self) -> None:
        """Закрыть все источники."""
        for source in self.sources:
            try:
                await source.close()
            except Exception as e:
                logger.warning(f"⚠️ Ошибка закрытия источника {source.get_source_name()}: {e}")
