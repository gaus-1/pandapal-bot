#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Статический веб-сервер для фронтенда PandaPal.

Раздает статические файлы из папки frontend/dist.
Используется для деплоя на Railway.app.
"""

import os
import sys
from pathlib import Path

from aiohttp import web
from loguru import logger

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO",
)


class FrontendServer:
    """Статический веб-сервер для фронтенда."""

    def __init__(self):
        """Инициализация сервера."""
        self.static_dir = Path(__file__).parent / "frontend" / "dist"

        if not self.static_dir.exists():
            raise FileNotFoundError(
                f"Папка dist не найдена: {self.static_dir}. "
                "Запустите 'npm run build' в папке frontend."
            )

        logger.info(f"📁 Статические файлы: {self.static_dir}")

    def create_app(self) -> web.Application:
        """Создание aiohttp приложения."""
        app = web.Application()

        # Health check
        async def health_check(request: web.Request) -> web.Response:
            """Health check endpoint."""
            return web.json_response(
                {
                    "status": "ok",
                    "service": "frontend",
                    "static_dir": str(self.static_dir),
                }
            )

        app.router.add_get("/health", health_check)

        # Статические файлы
        app.router.add_static("/assets", self.static_dir / "assets", name="assets")
        app.router.add_get("/", self._serve_index)
        app.router.add_get("/{path:.*}", self._serve_index)

        logger.info("✅ Веб-приложение создано")
        return app

    async def _serve_index(self, request: web.Request) -> web.Response:
        """Раздача index.html для всех маршрутов (SPA)."""
        index_path = self.static_dir / "index.html"
        return web.FileResponse(index_path)

    async def run(self) -> None:
        """Запуск веб-сервера."""
        port = int(os.getenv("PORT", "3000"))
        host = os.getenv("HOST", "0.0.0.0")

        logger.info(f"🌐 Запуск frontend сервера на {host}:{port}")

        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, host, port)
        await site.start()

        logger.info(f"✅ Frontend доступен на порту {port}")
        logger.info("📡 Ожидание запросов...")

        # Ждем бесконечно
        import asyncio

        await asyncio.Event().wait()


async def main() -> None:
    """Главная функция."""
    server = FrontendServer()
    await server.run()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Завершение работы frontend сервера")
        sys.exit(0)
