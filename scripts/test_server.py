#!/usr/bin/env python3
"""
Простой тестовый сервер для проверки работы на Render
"""

import asyncio
import os
from aiohttp import web
from aiohttp.web import Response
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint для Render"""
    return Response(
        text="PandaPal Test Server is running! 🐼",
        content_type="text/plain",
        status=200
    )

async def init_app():
    """Инициализирует веб-приложение"""
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    return app

async def main():
    """Основная функция"""
    # Получаем порт из переменной окружения (Render)
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"🌐 Запускаем тестовый сервер на порту {port}")
    
    # Создаем приложение
    app = await init_app()
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ Тестовый сервер запущен на порту {port}")
    logger.info("🎯 Render готов принимать запросы!")
    
    # Ждем бесконечно
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("👋 Сервер остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До встречи!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
