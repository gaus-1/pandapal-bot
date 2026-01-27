#!/usr/bin/env python3
"""
Скрипт для принудительной установки webhook новостного бота.

Использование:
    python scripts/setup_news_bot_webhook.py
    python scripts/setup_news_bot_webhook.py YOUR_BOT_TOKEN
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


async def setup_webhook():
    """Установить webhook для новостного бота."""
    # Пытаемся получить токен из переменных окружения или настроек
    token = os.getenv("NEWS_BOT_TOKEN") or news_bot_settings.news_bot_token

    if not token:
        logger.error("❌ NEWS_BOT_TOKEN не установлен")
        logger.info("💡 Установите переменную окружения: export NEWS_BOT_TOKEN=your_token")
        logger.info("💡 Или передайте токен как аргумент: python setup_news_bot_webhook.py YOUR_TOKEN")
        return

    # Получаем домен из переменных окружения или настроек
    webhook_domain = (
        os.getenv("WEBHOOK_DOMAIN")
        or os.getenv("NEWS_BOT_WEBHOOK_DOMAIN")
        or news_bot_settings.news_bot_webhook_domain
    )

    if not webhook_domain:
        logger.error("❌ WEBHOOK_DOMAIN не установлен")
        return

    webhook_url = f"https://{webhook_domain}/webhook/news"
    logger.info(f"🔗 Установка webhook: {webhook_url}")

    bot = Bot(token=token)

    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот: @{bot_info.username} ({bot_info.first_name})")

        # Получаем текущую информацию о webhook
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📊 Текущий webhook: {webhook_info.url or 'не установлен'}")

        # Удаляем старый webhook
        if webhook_info.url:
            logger.info("🗑️ Удаление старого webhook...")
            await bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(0.5)

        # Устанавливаем новый webhook
        logger.info(f"🔗 Установка webhook: {webhook_url}")
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "inline_query"],
        )

        # Проверяем результат
        await asyncio.sleep(1)
        webhook_info = await bot.get_webhook_info()
        logger.info(f"\n📊 Webhook Info после установки:")
        logger.info(f"  URL: {webhook_info.url}")
        logger.info(f"  Pending updates: {webhook_info.pending_update_count}")
        logger.info(f"  Last error: {webhook_info.last_error_message}")
        logger.info(f"  IP address: {webhook_info.ip_address}")

        if webhook_info.url == webhook_url:
            logger.info(f"\n✅ Webhook успешно установлен: {webhook_url}")
        else:
            logger.error(
                f"\n❌ Webhook не установлен правильно! "
                f"Ожидали: {webhook_url}, Получили: {webhook_info.url}"
            )

    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Можно передать токен как аргумент
    if len(sys.argv) > 1:
        os.environ["NEWS_BOT_TOKEN"] = sys.argv[1]

    asyncio.run(setup_webhook())
