"""
API endpoints для питомца-панды (тамагочи).

GET /api/miniapp/panda/{telegram_id}/state
POST /api/miniapp/panda/{telegram_id}/feed
POST /api/miniapp/panda/{telegram_id}/play
POST /api/miniapp/panda/{telegram_id}/sleep
"""

from aiohttp import web
from loguru import logger

from bot.api.validators import require_owner, validate_telegram_id
from bot.database import get_db
from bot.services import panda_service


async def get_panda_state(request: web.Request) -> web.Response:
    """
    GET /api/miniapp/panda/{telegram_id}/state
    Требует X-Telegram-Init-Data для проверки владельца.
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            state = panda_service.get_state(db, telegram_id)

        return web.json_response({"success": True, "state": state})
    except ValueError as e:
        logger.warning("⚠️ Invalid telegram_id: %s", e)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("❌ Ошибка получения состояния панды: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def panda_feed(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda/{telegram_id}/feed
    Покормить панду. Не чаще 2 раз в час.
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            result = panda_service.feed(db, telegram_id)

        return web.json_response(
            {"success": result["success"], "message": result["message"], "state": result["state"]}
        )
    except ValueError as e:
        logger.warning("⚠️ Invalid telegram_id: %s", e)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("❌ Ошибка кормления панды: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def panda_play(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda/{telegram_id}/play
    Поиграть с пандой.
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            result = panda_service.play(db, telegram_id)

        return web.json_response(
            {"success": result["success"], "message": result["message"], "state": result["state"]}
        )
    except ValueError as e:
        logger.warning("⚠️ Invalid telegram_id: %s", e)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("❌ Ошибка игры с пандой: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def panda_sleep(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda/{telegram_id}/sleep
    Уложить спать. Панда согласна только после еды.
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            result = panda_service.put_to_sleep(db, telegram_id)

        payload = {
            "success": result["success"],
            "message": result["message"],
            "state": result["state"],
        }
        if not result["success"] and result.get("need_feed_first"):
            payload["need_feed_first"] = True
        return web.json_response(payload)
    except ValueError as e:
        logger.warning("⚠️ Invalid telegram_id: %s", e)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("❌ Ошибка укладывания панды: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


def setup_panda_routes(app: web.Application) -> None:
    """Регистрация роутов панды."""
    app.router.add_get("/api/miniapp/panda/{telegram_id}/state", get_panda_state)
    app.router.add_post("/api/miniapp/panda/{telegram_id}/feed", panda_feed)
    app.router.add_post("/api/miniapp/panda/{telegram_id}/play", panda_play)
    app.router.add_post("/api/miniapp/panda/{telegram_id}/sleep", panda_sleep)
    logger.info("✅ Panda API routes зарегистрированы")
