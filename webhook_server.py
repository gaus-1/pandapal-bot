"""
🌐 WEBHOOK СЕРВЕР ДЛЯ RENDER
Обработка webhook запросов от Telegram с интеграцией системы 24/7
"""

import asyncio
import json
import os
from typing import Any, Dict

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import ClientSession, web
from loguru import logger

from bot.config import settings
from bot.handlers import routers
from bot.services.bot_24_7_service import Bot24_7Service
from bot.services.health_monitor import health_monitor

# Глобальные переменные
bot: Bot = None
dp: Dispatcher = None
bot_24_7_service: Bot24_7Service = None


async def init_bot():
    """Инициализация бота и диспетчера"""
    global bot, dp, bot_24_7_service

    # Инициализация бота
    bot = Bot(
        token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Инициализация диспетчера
    dp = Dispatcher()

    # Регистрация обработчиков
    for router in routers:
        dp.include_router(router)

    # Инициализация сервиса 24/7
    bot_24_7_service = Bot24_7Service(bot, dp)

    logger.info("🤖 Бот инициализирован для webhook режима")


async def on_startup(app: web.Application):
    """Событие запуска приложения"""
    logger.info("🚀 Запуск webhook сервера...")

    # Инициализация бота
    await init_bot()

    # Запуск системы мониторинга
    try:
        await health_monitor.start_monitoring()
        logger.info("🛡️ Система мониторинга здоровья запущена")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска мониторинга: {e}")

    # Настройка команд бота
    await bot.set_my_commands(
        [
            {"command": "start", "description": "Начать работу с ботом"},
            {"command": "help", "description": "Помощь по использованию"},
            {"command": "status", "description": "Статус системы 24/7"},
            {"command": "health", "description": "Проверка здоровья сервисов"},
            {"command": "ai_status", "description": "Статус AI провайдеров"},
            {"command": "admin", "description": "Административные команды"},
        ]
    )

    logger.success("✅ Webhook сервер готов к работе")


async def on_shutdown(app: web.Application):
    """Событие остановки приложения"""
    logger.info("⏹️ Остановка webhook сервера...")

    # Остановка системы мониторинга
    try:
        await health_monitor.stop_monitoring()
        logger.info("🛡️ Система мониторинга остановлена")
    except Exception as e:
        logger.error(f"❌ Ошибка остановки мониторинга: {e}")

    # Остановка сервиса 24/7
    if bot_24_7_service:
        try:
            await bot_24_7_service.stop_24_7_mode()
            logger.info("🤖 Сервис 24/7 остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка остановки 24/7: {e}")

    # Закрытие сессии бота
    if bot:
        await bot.session.close()

    logger.success("👋 Webhook сервер остановлен")


async def health_check_handler(request: web.Request) -> web.Response:
    """Обработчик проверки здоровья сервера"""
    try:
        # Проверяем состояние системы
        system_healthy = True
        details = {}

        if bot_24_7_service:
            health_status = bot_24_7_service.get_health_status()
            system_healthy = health_status["is_running"]
            details["bot_status"] = health_status
        else:
            system_healthy = False
            details["error"] = "Bot 24/7 service not initialized"

        if health_monitor:
            health_info = health_monitor.get_overall_health()
            details["services_health"] = health_info
            if health_info["overall_status"] != "healthy":
                system_healthy = False

        response_data = {
            "status": "healthy" if system_healthy else "unhealthy",
            "timestamp": asyncio.get_event_loop().time(),
            "details": details,
        }

        status_code = 200 if system_healthy else 503

        return web.json_response(response_data, status=status_code)

    except Exception as e:
        logger.error(f"❌ Ошибка health check: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def webhook_handler(request: web.Request) -> web.Response:
    """Обработчик webhook от Telegram"""
    try:
        # Получаем данные от Telegram
        data = await request.json()

        # Логируем входящий webhook
        update_id = data.get("update_id", "unknown")
        logger.debug(f"📨 Получен webhook: update_id={update_id}")

        # Обрабатываем через сервис 24/7
        if bot_24_7_service and bot_24_7_service.health.is_running:
            # Добавляем в очередь обработки
            from datetime import datetime

            from bot.services.bot_24_7_service import QueuedMessage

            queued_msg = QueuedMessage(
                update_id=update_id,
                update_data=data,
                timestamp=datetime.now(),
                priority=1,  # Высокий приоритет для webhook
            )

            # Добавляем в очередь если есть место
            if len(bot_24_7_service.message_queue) < bot_24_7_service.max_queue_size:
                bot_24_7_service.message_queue.append(queued_msg)
                logger.debug(f"✅ Webhook добавлен в очередь обработки")
            else:
                logger.warning("⚠️ Очередь webhook переполнена")
                return web.Response(status=503)
        else:
            logger.warning("⚠️ Сервис 24/7 недоступен, обрабатываем напрямую")

            # Прямая обработка через dispatcher
            from aiogram.types import Update

            update = Update.model_validate(data)
            await dp.feed_update(bot, update)

        return web.Response(status=200)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return web.Response(status=500)


async def status_handler(request: web.Request) -> web.Response:
    """Обработчик получения статуса системы"""
    try:
        status_data = {}

        if bot_24_7_service:
            status_data["bot_24_7"] = bot_24_7_service.get_health_status()

        if health_monitor:
            status_data["health_monitor"] = health_monitor.get_overall_health()

        return web.json_response(status_data)

    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса: {e}")
        return web.json_response({"error": str(e)}, status=500)


def create_app() -> web.Application:
    """Создание и настройка приложения"""
    app = web.Application()

    # Регистрация событий
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Регистрация маршрутов
    app.router.add_get("/health", health_check_handler)
    app.router.add_post("/webhook", webhook_handler)
    app.router.add_get("/status", status_handler)

    # Основной маршрут
    app.router.add_get("/", lambda request: web.Response(text="PandaPal Bot Webhook Server"))

    return app


async def main():
    """Главная функция запуска webhook сервера"""
    logger.info("🌐 Запуск PandaPal Webhook Server...")

    # Создание приложения
    app = create_app()

    # Настройка webhook URL
    webhook_url = f"https://pandapal-bot.onrender.com/webhook"

    # Получение порта
    port = int(os.getenv("PORT", "8000"))

    logger.info(f"🔗 Webhook URL: {webhook_url}")
    logger.info(f"🌐 Порт: {port}")

    try:
        # Запуск сервера
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

        logger.success(f"✅ Webhook сервер запущен на порту {port}")
        logger.info(f"🎯 Готов принимать webhook запросы от Telegram")

        # Бесконечный цикл
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка webhook сервера: {e}")
    finally:
        # Очистка ресурсов
        try:
            await runner.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    """Точка входа для запуска webhook сервера"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До встречи!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
