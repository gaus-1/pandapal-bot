#!/usr/bin/env python3
"""
Веб-сервер для Render с запуском бота в фоне
"""

import asyncio
import os
import signal
import sys
from aiohttp import web
from aiohttp.web import Response
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint для Render"""
    return Response(
        text="PandaPal Bot is running! 🐼",
        content_type="text/plain",
        status=200
    )

async def start_bot_background():
    """Запускает бота в фоновом режиме"""
    try:
        # Проверяем переменные окружения
        required_vars = ['TELEGRAM_BOT_TOKEN', 'GEMINI_API_KEY', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"❌ Отсутствуют переменные окружения: {missing_vars}")
            return
        
        logger.info("✅ Все переменные окружения настроены")
        
        # Небольшая задержка для стабильности
        await asyncio.sleep(2)
        
        # Импортируем и запускаем бота
        from main import main as bot_main
        logger.info("🤖 Запускаем бота в фоновом режиме...")
        await bot_main()
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        logger.error(f"❌ Тип ошибки: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Подробности: {traceback.format_exc()}")

async def init_app():
    """Инициализирует веб-приложение"""
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    # Запускаем бота в фоновом режиме
    asyncio.create_task(start_bot_background())
    
    return app

async def main():
    """Основная функция"""
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