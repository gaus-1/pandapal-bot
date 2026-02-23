"""
API endpoints для «Моя панда» (тамагочи).
"""

from aiohttp import web
from loguru import logger

from bot.api.validators import require_owner, validate_telegram_id
from bot.database import get_db
from bot.services.panda_pet_service import PandaPetService


async def get_panda_pet_state(request: web.Request) -> web.Response:
    """
    GET /api/miniapp/panda-pet/{telegram_id}
    Возвращает состояние панды. Требует X-Telegram-Init-Data (require_owner).
    """
    try:
        telegram_id_str = request.match_info.get("telegram_id")
        if not telegram_id_str:
            return web.json_response({"error": "telegram_id not found"}, status=400)
        telegram_id = validate_telegram_id(telegram_id_str)

        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            service = PandaPetService(db)
            state = service.get_state(telegram_id)

        return web.json_response(state)

    except ValueError as e:
        if "User not found" in str(e):
            return web.json_response({"error": "User not found"}, status=404)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("get_panda_pet_state error: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def feed_panda_pet(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda-pet/{telegram_id}/feed
    Body: {} или пустой. Требует require_owner.
    """
    try:
        telegram_id_str = request.match_info.get("telegram_id")
        if not telegram_id_str:
            return web.json_response({"error": "telegram_id not found"}, status=400)
        telegram_id = validate_telegram_id(telegram_id_str)

        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            service = PandaPetService(db)
            state = service.feed(telegram_id)

        return web.json_response(state)

    except ValueError as e:
        if "User not found" in str(e):
            return web.json_response({"error": "User not found"}, status=404)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("feed_panda_pet error: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def play_panda_pet(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda-pet/{telegram_id}/play
    """
    try:
        telegram_id_str = request.match_info.get("telegram_id")
        if not telegram_id_str:
            return web.json_response({"error": "telegram_id not found"}, status=400)
        telegram_id = validate_telegram_id(telegram_id_str)

        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            service = PandaPetService(db)
            state = service.play(telegram_id)

        return web.json_response(state)

    except ValueError as e:
        if "User not found" in str(e):
            return web.json_response({"error": "User not found"}, status=404)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("play_panda_pet error: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def sleep_panda_pet(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda-pet/{telegram_id}/sleep
    """
    try:
        telegram_id_str = request.match_info.get("telegram_id")
        if not telegram_id_str:
            return web.json_response({"error": "telegram_id not found"}, status=400)
        telegram_id = validate_telegram_id(telegram_id_str)

        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            service = PandaPetService(db)
            state = service.sleep(telegram_id)

        return web.json_response(state)

    except ValueError as e:
        if "User not found" in str(e):
            return web.json_response({"error": "User not found"}, status=404)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("sleep_panda_pet error: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def toilet_panda_pet(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda-pet/{telegram_id}/toilet
    Хочет в туалет — кулдаун 20 мин, после нажатия 10 сек показ довольной панды. Требует require_owner.
    """
    try:
        telegram_id_str = request.match_info.get("telegram_id")
        if not telegram_id_str:
            return web.json_response({"error": "telegram_id not found"}, status=400)
        telegram_id = validate_telegram_id(telegram_id_str)

        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            service = PandaPetService(db)
            state = service.toilet(telegram_id)

        return web.json_response(state)

    except ValueError as e:
        if "User not found" in str(e):
            return web.json_response({"error": "User not found"}, status=404)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("toilet_panda_pet error: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def climb_panda_pet(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda-pet/{telegram_id}/climb
    Панда залезла на дерево — кулдаун 1 час. Требует require_owner.
    """
    try:
        telegram_id_str = request.match_info.get("telegram_id")
        if not telegram_id_str:
            return web.json_response({"error": "telegram_id not found"}, status=400)
        telegram_id = validate_telegram_id(telegram_id_str)

        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            service = PandaPetService(db)
            state = service.climb(telegram_id)

        return web.json_response(state)

    except ValueError as e:
        if "User not found" in str(e):
            return web.json_response({"error": "User not found"}, status=404)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("climb_panda_pet error: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def fall_from_tree_panda_pet(request: web.Request) -> web.Response:
    """
    POST /api/miniapp/panda-pet/{telegram_id}/fall-from-tree
    Панда упала с дерева — настроение падает до обиженной. Требует require_owner.
    """
    try:
        telegram_id_str = request.match_info.get("telegram_id")
        if not telegram_id_str:
            return web.json_response({"error": "telegram_id not found"}, status=400)
        telegram_id = validate_telegram_id(telegram_id_str)

        if error_response := require_owner(request, telegram_id):
            return error_response

        with get_db() as db:
            service = PandaPetService(db)
            state = service.fall_from_tree(telegram_id)

        return web.json_response(state)

    except ValueError as e:
        if "User not found" in str(e):
            return web.json_response({"error": "User not found"}, status=404)
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("fall_from_tree_panda_pet error: %s", e, exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


def setup_panda_pet_routes(app: web.Application) -> None:
    """Регистрация роутов panda-pet."""
    app.router.add_get("/api/miniapp/panda-pet/{telegram_id}", get_panda_pet_state)
    app.router.add_post("/api/miniapp/panda-pet/{telegram_id}/feed", feed_panda_pet)
    app.router.add_post("/api/miniapp/panda-pet/{telegram_id}/play", play_panda_pet)
    app.router.add_post("/api/miniapp/panda-pet/{telegram_id}/sleep", sleep_panda_pet)
    app.router.add_post("/api/miniapp/panda-pet/{telegram_id}/climb", climb_panda_pet)
    app.router.add_post(
        "/api/miniapp/panda-pet/{telegram_id}/fall-from-tree", fall_from_tree_panda_pet
    )
    app.router.add_post("/api/miniapp/panda-pet/{telegram_id}/toilet", toilet_panda_pet)
    logger.info("Panda pet API routes зарегистрированы")
