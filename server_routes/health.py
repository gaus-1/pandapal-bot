"""
Регистрация health check и внутренних endpoints.

server — экземпляр PandaPalBotServer (передаётся для доступа к bot, settings, _check_*).
"""

import asyncio
from typing import Any

from aiohttp import web


def setup_health_routes(app: web.Application, server: Any) -> None:
    """Настройка health check endpoints."""

    async def health_check(_request: web.Request) -> web.Response:
        return web.json_response(
            {"status": "ok", "service": "pandapal-bot", "mode": "webhook"},
            status=200,
        )

    async def test_news_webhook(_request: web.Request) -> web.Response:
        webhook_status = {}
        if server.news_bot_enabled and server.news_bot:
            try:
                webhook_info = await server.news_bot.get_webhook_info()
                webhook_status = {
                    "url": webhook_info.url or "",
                    "pending_updates": webhook_info.pending_update_count,
                    "last_error": webhook_info.last_error_message,
                    "ip_address": webhook_info.ip_address,
                }
            except Exception as e:
                webhook_status = {"error": str(e)}
        return web.json_response(
            {
                "status": "ok",
                "path": "/webhook/news",
                "message": "News bot webhook endpoint is accessible",
                "bot_enabled": server.news_bot_enabled,
                "bot_initialized": server.news_bot is not None,
                "webhook_info": webhook_status,
            },
            status=200,
        )

    async def trigger_collect_news(request: web.Request) -> web.Response:
        auth = request.headers.get("Authorization") or request.query.get("key", "")
        key = auth.replace("Bearer ", "").strip()
        if not key or key != server.settings.secret_key:
            return web.json_response({"error": "unauthorized"}, status=401)
        asyncio.create_task(server._collect_news_now())
        return web.json_response({"status": "ok", "message": "collection started"})

    async def health_check_detailed(_request: web.Request) -> web.Response:
        components = {}
        overall_status = "ok"
        bot_status, bot_data = await server._check_bot_health()
        components.update(bot_data)
        if bot_status == "error":
            overall_status = "error"
        elif bot_status == "degraded" and overall_status == "ok":
            overall_status = "degraded"
        bot_info = bot_data.get("bot_info")
        db_status, db_data = server._check_database_health()
        components.update(db_data)
        if db_status == "error":
            overall_status = "error"
        webhook_status, webhook_data = await server._check_webhook_health()
        components.update(webhook_data)
        if webhook_status == "degraded" and overall_status == "ok":
            overall_status = "degraded"
        status_code = 200 if overall_status == "ok" else (503 if overall_status == "error" else 200)
        webhook_url = f"https://{server.settings.webhook_domain}/webhook"
        return web.json_response(
            {
                "status": overall_status,
                "mode": "webhook",
                "webhook_url": webhook_url,
                "bot_username": bot_info.username if bot_info else None,
                "components": components,
            },
            status=status_code,
        )

    app.router.add_get("/health", health_check)
    app.router.add_get("/health/detailed", health_check_detailed)
    app.router.add_get("/test/news-webhook", test_news_webhook)
    app.router.add_route("*", "/internal/collect-news", trigger_collect_news)
