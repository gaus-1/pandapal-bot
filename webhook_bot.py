"""
Webhook режим для PandaPal Bot
Настройка для продакшена на Render.com
"""

import asyncio
import sys
import re
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from loguru import logger

try:
    import sentry_sdk
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from bot.config import settings
from bot.database import init_db, DatabaseService
from bot.handlers import routers
from bot.services.health_monitor import health_monitor


# Удаление эмодзи из логов
emoji_pattern = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE
)

def format_for_console(record):
    """Удаляет эмодзи из сообщений для консоли"""
    record["message"] = emoji_pattern.sub("", record["message"])
    return True

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
    filter=format_for_console
)
logger.add(
    "logs/pandapal_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    level="DEBUG",
    encoding="utf-8"
)

# Глобальные объекты
bot: Bot = None
dp: Dispatcher = None
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = None


async def on_startup(bot: Bot) -> None:
    """Вызывается при запуске бота"""
    try:
        logger.info("🚀 Запуск PandaPal Bot (Webhook режим)...")
        
        # Инициализация Sentry
        if SENTRY_AVAILABLE and settings.sentry_dsn:
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                integrations=[AsyncioIntegration(), SqlalchemyIntegration()],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment="production"
            )
            logger.info("✅ Sentry мониторинг активирован")
        
        # Проверка БД
        db_service = DatabaseService()
        if not db_service.check_connection():
            logger.error("❌ Не удалось подключиться к БД")
            sys.exit(1)
        
        # Инициализация БД
        try:
            init_db()
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            sys.exit(1)
        
        # Проверка Gemini API
        try:
            from bot.services.ai_service import get_ai_service
            ai_service = get_ai_service()
            logger.info(f"✅ Gemini AI готов: {ai_service.get_model_info()}")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Gemini: {e}")
            sys.exit(1)
        
        # Запуск мониторинга здоровья
        try:
            await health_monitor.start_monitoring()
            logger.info("🛡️ Система мониторинга здоровья запущена")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска мониторинга: {e}")
        
        # Устанавливаем webhook
        await bot.set_webhook(
            WEBHOOK_URL,
            drop_pending_updates=True,
            allowed_updates=dp.resolve_used_update_types()
        )
        
        logger.success("✅ Бот запущен успешно!")
        logger.info(f"🔗 Webhook URL: {WEBHOOK_URL}")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        sys.exit(1)


async def on_shutdown(bot: Bot) -> None:
    """Вызывается при остановке бота"""
    logger.info("⏹️ Остановка бота...")
    
    # Останавливаем мониторинг
    await health_monitor.stop_monitoring()
    logger.info("🛡️ Система мониторинга остановлена")
    
    # Удаляем webhook
    await bot.delete_webhook()
    logger.info("🔗 Webhook удален")
    
    logger.success("✅ Бот остановлен")


def create_app(webhook_url: str, webhook_path: str) -> web.Application:
    """
    Создает aiohttp приложение с webhook
    
    Args:
        webhook_url: Полный URL для webhook (https://your-domain.com/webhook)
        webhook_path: Путь для webhook (/webhook)
    """
    global bot, dp, WEBHOOK_URL
    
    WEBHOOK_URL = webhook_url
    
    # Создаем бота
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создаем диспетчер
    dp = Dispatcher()
    
    # Регистрируем хендлеры
    for router in routers:
        dp.include_router(router)
    
    # Регистрируем startup/shutdown хендлеры
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Создаем aiohttp приложение
    app = web.Application()
    
    # Настраиваем webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_handler.register(app, path=webhook_path)
    
    # Добавляем health check endpoint
    async def health_check(request):
        return web.json_response({
            "status": "ok",
            "mode": "webhook",
            "webhook_url": WEBHOOK_URL
        })
    
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)
    
    # Настраиваем приложение для работы с webhook
    setup_application(app, dp, bot=bot)
    
    return app


async def main():
    """Основная функция для запуска webhook бота"""
    import os
    
    # Получаем параметры из окружения
    webhook_domain = os.getenv("WEBHOOK_DOMAIN", "pandapal-bot.onrender.com")
    webhook_path = os.getenv("WEBHOOK_PATH", WEBHOOK_PATH)
    port = int(os.getenv("PORT", 8000))
    
    # Формируем полный URL для webhook
    webhook_url = f"https://{webhook_domain}{webhook_path}"
    
    logger.info(f"🌐 Настройка webhook для домена: {webhook_domain}")
    logger.info(f"🔗 Webhook URL: {webhook_url}")
    logger.info(f"🚪 Порт: {port}")
    
    # Создаем приложение
    app = create_app(webhook_url, webhook_path)
    
    # Запускаем веб-сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.success(f"🚀 Webhook сервер запущен на порту {port}")
    logger.info("✅ Бот готов принимать сообщения через webhook")
    
    # Ждем завершения
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Получен сигнал остановки")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До встречи!")

