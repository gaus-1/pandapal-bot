"""
API endpoints для игр PandaPalGo
"""

from aiohttp import web
from loguru import logger
from pydantic import BaseModel, ValidationError

from bot.api.validators import validate_telegram_id
from bot.database import get_db
from bot.services.games_service import GamesService, HangmanAI


class CreateGameRequest(BaseModel):  # noqa: D101
    """Request для создания игры"""

    game_type: str  # 'tic_tac_toe', 'hangman', '2048'


class TicTacToeMoveRequest(BaseModel):  # noqa: D101
    """Request для хода в крестики-нолики"""

    position: int  # 0-8


class HangmanGuessRequest(BaseModel):  # noqa: D101
    """Request для угадывания буквы в виселице"""

    letter: str  # одна буква


class Game2048MoveRequest(BaseModel):  # noqa: D101
    """Request для хода в 2048"""

    direction: str  # 'up', 'down', 'left', 'right'


async def create_game(request: web.Request) -> web.Response:
    """
    Создать новую игровую сессию.

    POST /api/miniapp/games/create
    Body: { "game_type": "tic_tac_toe" | "hangman" | "2048" }
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

        try:
            validated = CreateGameRequest(**data)
        except ValidationError as e:
            return web.json_response(
                {"error": "Invalid request", "details": e.errors()}, status=400
            )

        if validated.game_type not in ["tic_tac_toe", "hangman", "2048"]:
            return web.json_response({"error": "Invalid game_type"}, status=400)

        with get_db() as db:
            games_service = GamesService(db)

            # Инициализация состояния игры
            initial_state = {}
            if validated.game_type == "tic_tac_toe":
                initial_state = {"board": [None] * 9}
            elif validated.game_type == "hangman":
                # Получаем возраст пользователя для выбора слова
                from bot.services import UserService

                user_service = UserService(db)
                user = user_service.get_user_by_telegram_id(telegram_id)
                age = user.age if user else None

                hangman_ai = HangmanAI()
                word = hangman_ai.get_word(age)
                initial_state = {
                    "word": word,
                    "guessed_letters": [],
                    "mistakes": 0,
                }
            elif validated.game_type == "2048":
                initial_state = {"board": games_service._init_2048_board(), "score": 0}

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
            result = games_service.tic_tac_toe_make_move(session_id, validated.position)
            db.commit()

        return web.json_response({"success": True, **result})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid move: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка хода: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def hangman_guess(request: web.Request) -> web.Response:
    """
    Угадать букву в виселице.

    POST /api/miniapp/games/hangman/{session_id}/guess
    Body: { "letter": "а" }
    """
    try:
        session_id = int(request.match_info["session_id"])
        data = await request.json()

        try:
            validated = HangmanGuessRequest(**data)
        except ValidationError as e:
            return web.json_response(
                {"error": "Invalid request", "details": e.errors()}, status=400
            )

        if len(validated.letter) != 1 or not validated.letter.isalpha():
            return web.json_response(
                {"error": "Letter must be a single alphabetic character"}, status=400
            )

        with get_db() as db:
            games_service = GamesService(db)
            result = games_service.hangman_guess_letter(session_id, validated.letter)
            db.commit()

        return web.json_response({"success": True, **result})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid guess: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка угадывания: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


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


async def get_game_stats(request: web.Request) -> web.Response:
    """
    Получить статистику игр пользователя.

    GET /api/miniapp/games/{telegram_id}/stats
    Query: ?game_type=tic_tac_toe (опционально)
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])
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


def setup_games_routes(app: web.Application) -> None:
    """Регистрация роутов игр"""
    app.router.add_post("/api/miniapp/games/{telegram_id}/create", create_game)
    app.router.add_post("/api/miniapp/games/tic-tac-toe/{session_id}/move", tic_tac_toe_move)
    app.router.add_post("/api/miniapp/games/hangman/{session_id}/guess", hangman_guess)
    app.router.add_post("/api/miniapp/games/2048/{session_id}/move", game_2048_move)
    app.router.add_get("/api/miniapp/games/{telegram_id}/stats", get_game_stats)
    app.router.add_get("/api/miniapp/games/session/{session_id}", get_game_session)

    logger.info("✅ Games API routes зарегистрированы")
