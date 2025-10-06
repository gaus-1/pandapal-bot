"""
Главный файл запуска PandaPal Telegram Bot
Entry point приложения
@module main
"""

import asyncio
import sys
import traceback
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from bot.config import settings
from bot.database import init_db, DatabaseService
from bot.handlers import routers
from bot.services.health_monitor import health_monitor
from bot.services.ai_fallback_service import ai_fallback_service
from bot.services.error_recovery_service import error_recovery_service
from bot.services.bot_24_7_service import Bot24_7Service


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
    - Запуск системы мониторинга 24/7
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
    
    # Запуск системы мониторинга здоровья
    try:
        await health_monitor.start_monitoring()
        logger.info("🛡️ Система мониторинга здоровья запущена")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска мониторинга: {e}")
    
    logger.success("✅ Бот запущен успешно!")


async def on_shutdown():
    """
    Действия при остановке бота
    Cleanup ресурсов
    """
    logger.info("⏹️ Остановка бота...")
    
    # Остановка системы мониторинга
    try:
        await health_monitor.stop_monitoring()
        logger.info("🛡️ Система мониторинга остановлена")
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

