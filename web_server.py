#!/usr/bin/env python3
"""
Веб-сервер для Render с запуском бота в фоне
"""

import asyncio
import threading
import os
import signal
import sys
from aiohttp import web
from aiohttp.web import Response
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для бота
bot_task = None

async def health_check(request):
    """Health check endpoint для Render"""
    return Response(
        text="PandaPal Bot is running! 🐼",
        content_type="text/plain",
        status=200
    )

async def start_bot():
    """Запускает бота в фоновом режиме"""
    global bot_task
    
    try:
        # Импортируем и запускаем бота
        from main import main as bot_main
        logger.info("🤖 Запускаем бота в фоновом режиме...")
        await bot_main()
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")

async def init_bot():
    """Инициализирует бота в отдельном потоке"""
    global bot_task
    
    if bot_task is None or bot_task.done():
        logger.info("🚀 Создаем задачу для бота...")
        bot_task = asyncio.create_task(start_bot())
    else:
        logger.info("✅ Бот уже запущен")

async def init_app():
    """Инициализирует веб-приложение"""
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    # Инициализируем бота при старте
    await init_bot()
    
    return app

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info("🛑 Получен сигнал завершения...")
    
    if bot_task and not bot_task.done():
        bot_task.cancel()
        logger.info("⏹️ Бот остановлен")
    
    sys.exit(0)

async def main():
    """Основная функция"""
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Получаем порт из переменной окружения (Render)
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"🌐 Запускаем веб-сервер на порту {port}")
    
    # Создаем приложение
    app = await init_app()
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ Веб-сервер запущен на порту {port}")
    logger.info("🎯 Render готов принимать запросы!")
    
    # Ждем бесконечно
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("👋 Веб-сервер остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До встречи!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
