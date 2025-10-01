"""
Главный файл запуска PandaPal Telegram Bot
Entry point приложения
@module main
"""

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from bot.config import settings
from bot.database import init_db, DatabaseService
from bot.handlers import routers


# Настройка логирования
logger.remove()  # Удаляем дефолтный handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True
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
    """
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
    
    # Проверка Gemini API
    try:
        from bot.services.ai_service import GeminiAIService
        ai_service = GeminiAIService()
        logger.info(f"✅ Gemini AI готов: {ai_service.get_model_info()}")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Gemini: {e}")
        sys.exit(1)
    
    logger.success("✅ Бот запущен успешно!")


async def on_shutdown():
    """
    Действия при остановке бота
    Cleanup ресурсов
    """
    logger.info("⏹️ Остановка бота...")
    logger.success("👋 Бот остановлен")


async def main():
    """
    Главная функция запуска бота
    Инициализирует Bot, Dispatcher и запускает polling
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
    
    # Удаляем вебхук (если был) и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("📡 Запуск polling...")
    
    # Запуск бота в режиме long polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("⌨️ Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    """
    Точка входа при запуске python main.py
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До встречи!")

