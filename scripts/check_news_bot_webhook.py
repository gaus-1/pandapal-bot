#!/usr/bin/env python3
"""
Скрипт для проверки webhook новостного бота через Telegram Bot API.

Использование:
    python scripts/check_news_bot_webhook.py
    python scripts/check_news_bot_webhook.py YOUR_BOT_TOKEN

Альтернативно через curl:
    curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from aiogram import Bot
from loguru import logger

from bot.config.news_bot_settings import news_bot_settings


async def check_webhook():
    """Проверить webhook новостного бота."""
    # Пытаемся получить токен из переменных окружения или настроек
    token = os.getenv("NEWS_BOT_TOKEN") or news_bot_settings.news_bot_token

    if not token:
        logger.error("❌ NEWS_BOT_TOKEN не установлен")
        logger.info("💡 Установите переменную окружения: export NEWS_BOT_TOKEN=your_token")
        logger.info("💡 Или передайте токен как аргумент: python check_news_bot_webhook.py YOUR_TOKEN")
        return

    bot = Bot(token=token)

    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот: @{bot_info.username} ({bot_info.first_name})")

        # Получаем информацию о webhook
        webhook_info = await bot.get_webhook_info()
        logger.info("\n📊 Webhook Info:")
        logger.info(f"  URL: {webhook_info.url}")
        logger.info(f"  Pending updates: {webhook_info.pending_update_count}")
        logger.info(f"  Last error: {webhook_info.last_error_message}")
        logger.info(f"  Last error date: {webhook_info.last_error_date}")
        logger.info(f"  IP address: {webhook_info.ip_address}")
        logger.info(f"  Max connections: {webhook_info.max_connections}")
        logger.info(f"  Allowed updates: {webhook_info.allowed_updates}")

        # Проверяем, установлен ли webhook
        if webhook_info.url:
            logger.info(f"\n✅ Webhook установлен: {webhook_info.url}")
            if webhook_info.last_error_message:
                logger.error(f"❌ Есть ошибка webhook: {webhook_info.last_error_message}")
            else:
                logger.info("✅ Ошибок webhook нет")
        else:
            logger.warning("⚠️ Webhook не установлен")

        # Проверяем ожидающие обновления
        if webhook_info.pending_update_count > 0:
            logger.warning(
                f"⚠️ Есть {webhook_info.pending_update_count} ожидающих обновлений"
            )

    except Exception as e:
        logger.error(f"❌ Ошибка проверки webhook: {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Можно передать токен как аргумент
    if len(sys.argv) > 1:
        os.environ["NEWS_BOT_TOKEN"] = sys.argv[1]

    asyncio.run(check_webhook())
