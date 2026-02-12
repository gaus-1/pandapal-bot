"""
Регистрация health check endpoints.

server — экземпляр PandaPalBotServer (передаётся для доступа к bot, settings, _check_*).
"""

from typing import Any

from aiohttp import web


def setup_health_routes(app: web.Application, server: Any) -> None:
    """Настройка health check endpoints."""

    async def health_check(_request: web.Request) -> web.Response:
        return web.json_response(
            {"status": "ok", "service": "pandapal-bot", "mode": "webhook"},
            status=200,
        )

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
                "bot_username": bot_info.get("username")
                if isinstance(bot_info, dict)
                else (bot_info.username if bot_info else None),
                "components": components,
            },
            status=status_code,
        )

    app.router.add_get("/health", health_check)
    app.router.add_get("/health/detailed", health_check_detailed)
