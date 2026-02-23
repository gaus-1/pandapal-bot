#!/usr/bin/env python3
"""
Локальный запуск только фронтенда (без бота и БД).
Порт по умолчанию 10001. Mini App: http://localhost:10001/miniapp
Переопределить порт: PORT=10000 python scripts/serve_frontend_local.py

Запуск из корня проекта: python scripts/serve_frontend_local.py
"""
import asyncio
import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from aiohttp import web


async def health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "pandapal-frontend-local"})


def main() -> None:
    # По умолчанию 10001, чтобы не конфликтовать с web_server.py (10000)
    port = int(os.getenv("PORT", "10001"))
    host = os.getenv("HOST", "0.0.0.0")

    app = web.Application()
    app.router.add_get("/health", health)

    from server_routes.static import setup_frontend_static

    setup_frontend_static(app, root_dir)

    async def run() -> None:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        print(f"Frontend: http://localhost:{port}/")
        print(f"Mini App: http://localhost:{port}/miniapp")
        while True:
            await asyncio.sleep(3600)

    asyncio.run(run())


if __name__ == "__main__":
    main()
