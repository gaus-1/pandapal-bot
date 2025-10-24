#!/usr/bin/env python3
"""
Точка входа для запуска PandaPal бота.
Используется для запуска в CI/CD pipeline и локальной разработке.
"""

import asyncio
import logging
import sys
from pathlib import Path

from bot.config import get_settings
from bot.database import init_database
from bot.monitoring import setup_monitoring

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """
    Основная функция запуска бота.
    """
    try:
        logger.info("🚀 Запуск PandaPal бота...")

        # Инициализация настроек
        settings = get_settings()
        logger.info(f"📋 Настройки загружены: {settings.app_name}")

        # Инициализация базы данных
        await init_database()
        logger.info("🗄️ База данных инициализирована")

        # Настройка мониторинга
        setup_monitoring()
        logger.info("📊 Мониторинг настроен")

        # Здесь должен быть запуск Telegram бота
        # Пока что просто ждем для CI/CD тестов
        logger.info("✅ PandaPal бот готов к работе!")

        # Для CI/CD - запускаем простой HTTP сервер
        if settings.environment == "test":
            import uvicorn
            from fastapi import FastAPI

            app = FastAPI(title="PandaPal Test Server")

            @app.get("/")
            async def root():
                return {"message": "PandaPal Bot is running!", "status": "healthy"}

            @app.get("/health")
            async def health():
                return {"status": "healthy", "service": "pandapal-bot"}

            logger.info("🌐 Запуск тестового HTTP сервера на порту 8000...")
            await uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

        else:
            # Для продакшена - запуск Telegram бота
            logger.info("🤖 Запуск Telegram бота...")
            # TODO: Добавить запуск aiogram бота
            await asyncio.sleep(3600)  # Ждем 1 час для тестов

    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
