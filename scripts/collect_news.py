#!/usr/bin/env python3
"""
Скрипт для сбора новостей из всех источников.

Запускается периодически (например, через cron или scheduled task)
для пополнения базы данных новостями.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger

from bot.database import init_database
from bot.services.news_collector_service import NewsCollectorService
from bot.services.news.repository import NewsRepository
from bot.services.news.sources.humor_site_source import HumorSiteSource
from bot.services.news.sources.joke_api_source import JokeAPISource
from bot.services.news.sources.local_humor_source import LocalHumorSource
from bot.services.news.sources.newsapi_source import NewsAPISource
from bot.services.news.sources.web_scraper_source import WebScraperNewsSource
from bot.services.news.sources.world_news_api_source import WorldNewsAPISource


async def main():
    """Основная функция сбора новостей."""
    logger.info("📰 Запуск сбора новостей...")

    # Инициализация БД
    await init_database()
    logger.info("✅ База данных инициализирована")

    # Создаем все источники
    sources = [
        WorldNewsAPISource(),
        NewsAPISource(),
        WebScraperNewsSource(),
        HumorSiteSource(),
        JokeAPISource(),
        LocalHumorSource(),
    ]

    # Создаем сервис сбора
    collector = NewsCollectorService(sources=sources)

    try:
        # Собираем новости (по 5 из каждого источника)
        total_collected = await collector.collect_news(limit_per_source=5)
        logger.info(f"✅ Сбор завершен. Всего собрано: {total_collected} новостей")

        # Проверяем статистику в БД
        from bot.database import get_db

        with get_db() as db:
            repository = NewsRepository(db)
            total_in_db = repository.count_all()
            logger.info(f"📊 Всего новостей в БД: {total_in_db}")

    except Exception as e:
        logger.error(f"❌ Ошибка сбора новостей: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await collector.close()

    logger.info("✅ Скрипт завершен")


if __name__ == "__main__":
    asyncio.run(main())
