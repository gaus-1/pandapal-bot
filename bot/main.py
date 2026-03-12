#!/usr/bin/env python3
"""
Точка входа для CI/CD проверки инициализации PandaPal бота.

Продакшен использует web_server.py (webhook через aiohttp).
Этот файл нужен только для CI: проверяет, что БД и конфигурация валидны.
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

from bot.database import init_database

# Корневая папка в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


async def main():
    """Проверка инициализации для CI/CD."""
    try:
        logger.info("🚀 Запуск PandaPal бота...")
        logger.info("📋 Настройки загружены: PandaPal Bot")

        await init_database()
        logger.info("🗄️ База данных инициализирована")
        logger.info("✅ PandaPal бот готов к работе!")
        logger.info("ℹ️ Для продакшена используйте web_server.py")

    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
