#!/usr/bin/env python3
"""
Веб-сервер для Telegram webhook бота PandaPal.

Этот модуль запускает HTTP сервер для приема webhook запросов от Telegram API.
Используется для продакшн деплоя на Render.com вместо polling режима.

Основные возможности:
- Запуск HTTP сервера на порту из переменной окружения PORT
- Настройка webhook URL для Telegram API
- Интеграция с webhook_bot для обработки входящих сообщений
- Поддержка кастомных доменов (pandapal.ru)
- Профессиональная конфигурация для продакшена 24/7
"""

import asyncio
import logging
import os
import sys
import traceback

from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """
    Основная функция запуска веб-сервера.

    Настраивает и запускает HTTP сервер для приема webhook запросов от Telegram.
    Автоматически определяет порт из переменной окружения PORT и настраивает
    webhook URL для интеграции с Telegram API.

    Raises:
        SystemExit: При критических ошибках инициализации.
    """
    try:
        # Получаем порт из переменной окружения (Render использует PORT)
        port = int(os.environ.get("PORT", 10000))

        # Получаем параметры webhook
        webhook_domain = os.getenv("WEBHOOK_DOMAIN", "pandapal.ru")
        webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
        webhook_url = f"https://{webhook_domain}{webhook_path}"

        logger.info(f"🌐 Запускаем веб-сервер на порту {port}")
        logger.info(f"🔗 Webhook URL: {webhook_url}")

        # Импортируем webhook бота
        from webhook_bot import create_app

        # Создаем приложение с webhook
        app = create_app(webhook_url, webhook_path)

        # Запускаем сервер
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

        logger.info(f"✅ Веб-сервер запущен на порту {port}")
        logger.info("✅ Webhook бот инициализирован")
        logger.info("🎯 Render готов принимать запросы!")

        # Ждем бесконечно
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.error(f"❌ Подробности: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        if "runner" in locals():
            await runner.cleanup()


if __name__ == "__main__":
    """
    Точка входа в приложение.

    Запускает асинхронную функцию main() с обработкой исключений
    для корректного завершения работы сервера.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До встречи!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
