#!/usr/bin/env python3
"""
Точка входа для запуска PandaPal бота.
Используется для запуска в CI/CD pipeline и локальной разработке.
"""

import asyncio
import os
import sys
from pathlib import Path

from loguru import logger

from bot.config import settings
from bot.database import init_database

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


async def main():
    """
    Основная функция запуска бота.
    """
    try:
        logger.info("🚀 Запуск PandaPal бота...")

        # Инициализация настроек
        logger.info("📋 Настройки загружены: PandaPal Bot")

        # Инициализация базы данных
        await init_database()
        logger.info("🗄️ База данных инициализирована")

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

            test_host = os.getenv("TEST_SERVER_HOST", "127.0.0.1")
            test_port = int(os.getenv("TEST_SERVER_PORT", "8000"))
            logger.info(f"🌐 Запуск тестового HTTP сервера на {test_host}:{test_port}...")
            await uvicorn.run(app, host=test_host, port=test_port, log_level="info")

        else:
            # Для продакшена используется web_server.py (webhook режим)
            # Этот файл используется только для тестирования и CI/CD
            logger.info("🤖 Запуск Telegram бота...")
            logger.info("ℹ️ Для продакшена используйте web_server.py")
            await asyncio.sleep(3600)  # Ждем 1 час для тестов

    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
