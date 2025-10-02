"""
Простой HTTP endpoint для health check
Убирает предупреждения Render о портах
"""

from aiohttp import web
import asyncio
import os
from loguru import logger


async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "PandaPal Bot",
        "timestamp": asyncio.get_event_loop().time()
    })


async def init_app():
    """Инициализация HTTP приложения"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    return app


if __name__ == '__main__':
    logger.info("🌐 Запуск HTTP сервера для health check")
    app = asyncio.run(init_app())
    web.run_app(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
