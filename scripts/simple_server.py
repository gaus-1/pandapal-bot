#!/usr/bin/env python3
"""
Простой сервер для тестирования деплоя на Render
"""

import os
import asyncio
from aiohttp import web

async def health_check(request):
    """Health check endpoint"""
    return web.Response(
        text="PandaPal Bot is running! 🐼\nStatus: OK",
        content_type="text/plain",
        status=200
    )

async def main():
    """Основная функция"""
    # Получаем порт из переменной окружения
    port = int(os.environ.get('PORT', 8000))
    
    # Создаем приложение
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"✅ Сервер запущен на порту {port}")
    
    # Ждем бесконечно
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        print("👋 Сервер остановлен")

if __name__ == "__main__":
    asyncio.run(main())
