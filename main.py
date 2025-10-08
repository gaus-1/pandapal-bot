"""
Главный файл запуска PandaPal Telegram Bot
Точка входа приложения (Polling режим для локальной разработки)
"""

import asyncio
import sys
import traceback
import re
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

try:
    import sentry_sdk
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK не установлен. Установите: pip install sentry-sdk")

from bot.config import settings
from bot.database import init_db, DatabaseService
from bot.handlers import routers
from bot.services.ai_service_solid import get_ai_service
from bot.services.simple_monitor import get_simple_monitor


# Функция для удаления эмодзи из логов (для Windows консоли)
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
logger.remove()  # Удаляем дефолтный handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
    filter=format_for_console  # Удаляем эмодзи для консоли
)
logger.add(
    "logs/pandapal_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Новый файл каждый день
    retention="30 days",  # Храним 30 дней
    level="INFO"
)


async def on_startup():
    """
    Действия при запуске бота
    - Проверка подключения к БД
    - Инициализация таблиц
    - Проверка API ключей
    - Запуск системы мониторинга 24/7
    """
    if SENTRY_AVAILABLE and hasattr(settings, 'sentry_dsn') and settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                AsyncioIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment="production" if "render.com" in str(settings.database_url) else "development",
        )
        logger.info("✅ Sentry monitoring активирован")
    
    logger.info("🚀 Запуск PandaPal Bot...")
    
    # Проверка подключения к БД
    if not DatabaseService.check_connection():
        logger.error("❌ Не удалось подключиться к базе данных!")
        sys.exit(1)
    
    # Инициализация БД (создание таблиц если нужно)
    try:
        init_db()
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        sys.exit(1)
    
    # Проверка Gemini API (SOLID)
    try:
        ai_service = get_ai_service()
        logger.info(f"✅ Gemini AI готов: {ai_service.get_model_info()}")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Gemini: {e}")
        sys.exit(1)
    
    # Запуск упрощенного мониторинга
    try:
        monitor = get_simple_monitor()
        await monitor.start_monitoring()
        logger.info("🛡️ Упрощенный мониторинг запущен")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска мониторинга: {e}")
    
    logger.success("✅ Бот запущен успешно!")


async def on_shutdown():
    """
    Действия при остановке бота
    Cleanup ресурсов
    """
    logger.info("⏹️ Остановка бота...")
    
    # Остановка упрощенного мониторинга
    try:
        monitor = get_simple_monitor()
        await monitor.stop_monitoring()
        logger.info("🛡️ Упрощенный мониторинг остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка остановки мониторинга: {e}")
    
    logger.success("👋 Бот остановлен")


async def main():
    """
    Главная функция запуска бота
    Инициализирует Bot, Dispatcher и запускает режим 24/7
    """
    # Инициализация бота
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML  # HTML по умолчанию
        )
    )
    
    # Инициализация диспетчера
    dp = Dispatcher()
    
    # Регистрация обработчиков (роутеров)
    for router in routers:
        dp.include_router(router)
    
    # Регистрация startup/shutdown хуков
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Включаем распознавание речи для голосовых сообщений
    await bot.set_my_commands([
        {"command": "start", "description": "Начать работу с ботом"},
        {"command": "help", "description": "Помощь по использованию"},
        {"command": "status", "description": "Статус системы 24/7"},
        {"command": "health", "description": "Проверка здоровья сервисов"}
    ])
    
    # Настраиваем бота для работы с голосовыми сообщениями
    logger.info("🎤 Настроено распознавание речи для голосовых сообщений")
    
    # ВРЕМЕННО ОТКЛЮЧАЕМ 24/7 СЕРВИС ИЗ-ЗА ПРОБЛЕМ С ДУБЛИРОВАНИЕМ
    logger.info("Запуск простого polling режима...")
    
    # Простой polling без 24/7 сервиса
    try:
        # Удаляем webhook если есть
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удален, запускаем polling...")
        
        # Запускаем polling напрямую
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # Корректная остановка
        await bot.session.close()


if __name__ == '__main__':
    """
    Точка входа при запуске python main.py
    ЭКСТРЕННАЯ ОСТАНОВКА - БОТ ОТКЛЮЧЕН
    """
    import os
    if os.getenv("EMERGENCY_STOP") == "true":
        print("🛑 ЭКСТРЕННАЯ ОСТАНОВКА - БОТ ОТКЛЮЧЕН")
        exit(0)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До встречи!")

