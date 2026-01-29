"""
API endpoints для игр PandaPalGo
"""

from aiohttp import web
from loguru import logger
from pydantic import BaseModel, ValidationError

from bot.api.validators import require_owner, validate_telegram_id
from bot.database import get_db
from bot.services.games_service import GamesService


class CreateGameRequest(BaseModel):  # noqa: D101
    """Request для создания игры"""

    game_type: str  # 'tic_tac_toe', 'checkers', '2048'


class TicTacToeMoveRequest(BaseModel):  # noqa: D101
    """Request для хода в крестики-нолики"""

    position: int  # 0-8


class CheckersMoveRequest(BaseModel):  # noqa: D101
    """Request для хода в шашках"""

    from_row: int  # 0-7
    from_col: int  # 0-7
    to_row: int  # 0-7
    to_col: int  # 0-7


class Game2048MoveRequest(BaseModel):  # noqa: D101
    """Request для хода в 2048"""

    direction: str  # 'up', 'down', 'left', 'right'


class EruditePlaceTileRequest(BaseModel):  # noqa: D101
    """Request для размещения фишки в Эрудите"""

    row: int  # Строка (0-14)
    col: int  # Колонка (0-14)
    letter: str  # Буква


def _initialize_game_state(game_type: str) -> dict:
    """
    Инициализация начального состояния игры.

    Args:
        game_type: Тип игры ('tic_tac_toe', 'checkers', '2048')

    Returns:
        dict: Начальное состояние игры
    """
    if game_type == "tic_tac_toe":
        from bot.services.game_engines import TicTacToe

        game = TicTacToe()
        state = game.get_state()
        return {"board": state["board"]}

    elif game_type == "checkers":
        from bot.services.game_engines import CheckersGame

        game = CheckersGame()
        state = game.get_board_state()
        return {
            "board": state["board"],
            "kings": state.get("kings"),
            "current_player": state["current_player"],
        }

    elif game_type == "2048":
        from bot.services.game_engines import Game2048

        game = Game2048()
        state = game.get_state()
        return {
            "board": state["board"],
            "score": state["score"],
            "won": state["won"],
            "game_over": state["game_over"],
        }

    elif game_type == "erudite":
        from bot.services.game_engines import EruditeGame

        game = EruditeGame()
        state = game.get_state()
        return {
            "board": state["board"],
            "bonus_cells": state["bonus_cells"],
            "player_tiles": state["player_tiles"],
            "ai_tiles": state["ai_tiles"],
            "player_score": state["player_score"],
            "ai_score": state["ai_score"],
            "current_player": state["current_player"],
            "game_over": state["game_over"],
            "first_move": state["first_move"],
            "current_move": state["current_move"],
            "bag_count": state["bag_count"],
        }

    return {}


async def create_game(request: web.Request) -> web.Response:
    """
    Создать новую игровую сессию.

    POST /api/miniapp/games/{telegram_id}/create
    Body: { "game_type": "tic_tac_toe" | "checkers" | "2048" }
    Требует заголовок X-Telegram-Init-Data для проверки владельца ресурса.
    """
    try:
        data = await request.json()
        # Получаем telegram_id из match_info или из заголовка
        telegram_id_str = request.match_info.get("telegram_id") or request.headers.get(
            "X-Telegram-ID"
        )
        if not telegram_id_str:
            return web.json_response({"error": "telegram_id not found"}, status=400)
        telegram_id = validate_telegram_id(telegram_id_str)

        # Проверка владельца ресурса (OWASP A01)
        if error_response := require_owner(request, telegram_id):
            return error_response

        try:
            validated = CreateGameRequest(**data)
        except ValidationError as e:
            return web.json_response(
                {"error": "Invalid request", "details": e.errors()}, status=400
            )

        if validated.game_type not in ["tic_tac_toe", "checkers", "2048", "erudite"]:
            return web.json_response({"error": "Invalid game_type"}, status=400)

        initial_state = _initialize_game_state(validated.game_type)

        with get_db() as db:
            games_service = GamesService(db)
            session = games_service.create_game_session(
                telegram_id, validated.game_type, initial_state
            )
            db.commit()

            # Сохраняем данные до закрытия сессии
            session_id = session.id
            game_type = session.game_type
            game_state = session.game_state

        return web.json_response(
            {
                "success": True,
                "session_id": session_id,
                "game_type": game_type,
                "game_state": game_state,
            }
        )

    except ValueError as e:
        logger.warning(f"⚠️ Invalid request: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка создания игры: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def tic_tac_toe_move(request: web.Request) -> web.Response:
    """
    Сделать ход в крестики-нолики.

    POST /api/miniapp/games/tic-tac-toe/{session_id}/move
    Body: { "position": 0-8 }
    """
    try:
        session_id = int(request.match_info["session_id"])
        data = await request.json()

        try:
            validated = TicTacToeMoveRequest(**data)
        except ValidationError as e:
            return web.json_response(
                {"error": "Invalid request", "details": e.errors()}, status=400
            )

        if validated.position < 0 or validated.position > 8:
            return web.json_response({"error": "Position must be 0-8"}, status=400)

        with get_db() as db:
            games_service = GamesService(db)
            result = await games_service.tic_tac_toe_make_move(session_id, validated.position)
            db.commit()

        return web.json_response({"success": True, **result})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid move: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка хода: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def checkers_move(request: web.Request) -> web.Response:
    """
    Сделать ход в шашках.

    POST /api/miniapp/games/checkers/{session_id}/move
    Body: { "from_row": 0-7, "from_col": 0-7, "to_row": 0-7, "to_col": 0-7 }
    """
    try:
        session_id = int(request.match_info["session_id"])
        data = await request.json()

        try:
            validated = CheckersMoveRequest(**data)
        except ValidationError as e:
            return web.json_response(
                {"error": "Invalid request", "details": e.errors()}, status=400
            )

        if not all(
            0 <= x < 8
            for x in [validated.from_row, validated.from_col, validated.to_row, validated.to_col]
        ):
            return web.json_response(
                {"error": "All coordinates must be between 0 and 7"}, status=400
            )

        with get_db() as db:
            games_service = GamesService(db)
            try:
                result = await games_service.checkers_move(
                    session_id,
                    validated.from_row,
                    validated.from_col,
                    validated.to_row,
                    validated.to_col,
                )
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"❌ Ошибка в checkers_move: {e}", exc_info=True)
                raise

        return web.json_response({"success": True, **result})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid move in checkers: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка хода в шашках: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def game_2048_move(request: web.Request) -> web.Response:
    """
    Сделать ход в 2048.

    POST /api/miniapp/games/2048/{session_id}/move
    Body: { "direction": "up" | "down" | "left" | "right" }
    """
    try:
        session_id = int(request.match_info["session_id"])
        data = await request.json()

        try:
            validated = Game2048MoveRequest(**data)
        except ValidationError as e:
            return web.json_response(
                {"error": "Invalid request", "details": e.errors()}, status=400
            )

        if validated.direction not in ["up", "down", "left", "right"]:
            return web.json_response({"error": "Invalid direction"}, status=400)

        with get_db() as db:
            games_service = GamesService(db)
            result = games_service.game_2048_move(session_id, validated.direction)
            db.commit()

        return web.json_response({"success": True, **result})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid move: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка хода: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def erudite_place_tile(request: web.Request) -> web.Response:
    """
    Разместить фишку в Эрудите.

    POST /api/miniapp/games/erudite/{session_id}/place-tile
    Body: { "row": int, "col": int, "letter": str }
    """
    try:
        session_id = int(request.match_info["session_id"])
        data = await request.json()

        try:
            validated = EruditePlaceTileRequest(**data)
        except ValidationError as e:
            return web.json_response(
                {"error": "Invalid request", "details": e.errors()}, status=400
            )

        with get_db() as db:
            games_service = GamesService(db)
            state = games_service.erudite_move(
                session_id, validated.row, validated.col, validated.letter
            )
            db.commit()

        return web.json_response({"success": True, **state})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid move: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка размещения фишки в Эрудите: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def erudite_clear_move(request: web.Request) -> web.Response:
    """
    Очистить текущий ход в Эрудите.

    POST /api/miniapp/games/erudite/{session_id}/clear-move
    """
    try:
        session_id = int(request.match_info["session_id"])

        with get_db() as db:
            games_service = GamesService(db)
            state = games_service.erudite_clear_move(session_id)
            db.commit()

        return web.json_response({"success": True, **state})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid move: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка очистки хода в Эрудите: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def erudite_confirm_move(request: web.Request) -> web.Response:
    """
    Подтвердить ход в Эрудите.

    POST /api/miniapp/games/erudite/{session_id}/confirm-move
    """
    try:
        session_id = int(request.match_info["session_id"])

        with get_db() as db:
            games_service = GamesService(db)
            state = games_service.erudite_confirm_move(session_id)
            db.commit()

        return web.json_response({"success": True, **state})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid move: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка подтверждения хода в Эрудите: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_game_stats(request: web.Request) -> web.Response:
    """
    Получить статистику игр пользователя.

    GET /api/miniapp/games/{telegram_id}/stats
    Query: ?game_type=tic_tac_toe (опционально)
    Требует заголовок X-Telegram-Init-Data для проверки владельца ресурса.
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        # Проверка владельца ресурса (OWASP A01)
        if error_response := require_owner(request, telegram_id):
            return error_response

        game_type = request.query.get("game_type")

        with get_db() as db:
            games_service = GamesService(db)
            stats = games_service.get_game_stats(telegram_id, game_type)

        return web.json_response({"success": True, "stats": stats})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_game_session(request: web.Request) -> web.Response:
    """
    Получить игровую сессию.

    GET /api/miniapp/games/session/{session_id}
    """
    try:
        session_id = int(request.match_info["session_id"])

        with get_db() as db:
            from bot.models import GameSession

            session = db.get(GameSession, session_id)
            if not session:
                return web.json_response({"error": "Session not found"}, status=404)

            # Сохраняем данные до закрытия сессии
            session_dict = session.to_dict()

        return web.json_response({"success": True, "session": session_dict})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid session_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения сессии: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_checkers_valid_moves(request: web.Request) -> web.Response:
    """
    Получить валидные ходы для шашек.

    GET /api/miniapp/games/checkers/{session_id}/valid-moves
    """
    try:
        session_id = int(request.match_info["session_id"])

        with get_db() as db:
            games_service = GamesService(db)
            result = games_service.get_checkers_valid_moves(session_id)

        return web.json_response(
            {
                "success": True,
                "valid_moves": result["valid_moves"],
                "current_player": result["current_player"],
            }
        )

    except ValueError as e:
        logger.warning(f"⚠️ Invalid session_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения валидных ходов: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


def setup_games_routes(app: web.Application) -> None:
    """Регистрация роутов игр"""
    app.router.add_post("/api/miniapp/games/{telegram_id}/create", create_game)
    app.router.add_post("/api/miniapp/games/tic-tac-toe/{session_id}/move", tic_tac_toe_move)
    app.router.add_post("/api/miniapp/games/checkers/{session_id}/move", checkers_move)
    app.router.add_get(
        "/api/miniapp/games/checkers/{session_id}/valid-moves", get_checkers_valid_moves
    )
    app.router.add_post("/api/miniapp/games/2048/{session_id}/move", game_2048_move)
    app.router.add_post("/api/miniapp/games/erudite/{session_id}/place-tile", erudite_place_tile)
    app.router.add_post("/api/miniapp/games/erudite/{session_id}/clear-move", erudite_clear_move)
    app.router.add_post(
        "/api/miniapp/games/erudite/{session_id}/confirm-move", erudite_confirm_move
    )
    app.router.add_get("/api/miniapp/games/{telegram_id}/stats", get_game_stats)
    app.router.add_get("/api/miniapp/games/session/{session_id}", get_game_session)

    logger.info("✅ Games API routes зарегистрированы")
