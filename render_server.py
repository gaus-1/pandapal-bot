#!/usr/bin/env python3
"""
УЛЬТРА-ПРОСТОЙ сервер для Render
Только health check без бота - для диагностики портов
"""

import os
import logging
from aiohttp import web
from aiohttp.web import Response

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint для Render"""
    return Response(
        text="PandaPal Render Server OK! 🐼",
        content_type="text/plain",
        status=200
    )

async def main():
    """Основная функция - ТОЛЬКО веб-сервер"""
    # Получаем порт из переменной окружения (Render)
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"🌐 Запускаем ПРОСТОЙ веб-сервер на порту {port}")
    
    # Создаем приложение
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ ПРОСТОЙ сервер запущен на порту {port}")
    logger.info("🎯 Render должен увидеть открытый порт!")
    
    # Ждем бесконечно
    try:
        import asyncio
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("👋 Сервер остановлен")

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До встречи!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import sys
        sys.exit(1)
