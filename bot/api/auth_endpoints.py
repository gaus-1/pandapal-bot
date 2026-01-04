"""
API endpoints для аутентификации через Telegram Login Widget.

Обрабатывает авторизацию пользователей через виджет Telegram на веб-сайте.
"""

from aiohttp import web
from loguru import logger

from bot.database import get_db
from bot.services.session_service import get_session_service
from bot.services.telegram_auth_service import TelegramAuthService


def setup_auth_routes(app: web.Application) -> None:
    """
    Регистрация маршрутов для аутентификации.

    Args:
        app: Экземпляр aiohttp приложения
    """
    app.router.add_post("/api/auth/telegram/login", telegram_login)
    app.router.add_get("/api/auth/telegram/verify", verify_session)
    app.router.add_post("/api/auth/telegram/logout", logout)
    app.router.add_get("/api/auth/stats", session_stats)

    logger.info("✅ Auth API routes зарегистрированы")


async def telegram_login(request: web.Request) -> web.Response:
    """
    Обработка авторизации через Telegram Login Widget.

    POST /api/auth/telegram/login

    Request body (URL-encoded параметры от Telegram):
        id: int - Telegram user ID
        first_name: str
        last_name: str (optional)
        username: str (optional)
        photo_url: str (optional)
        auth_date: int - Unix timestamp
        hash: str - Signature от Telegram

    Response:
        {
            "success": true,
            "session_token": "secure_random_token",
            "user": {
                "telegram_id": 123456,
                "full_name": "John Doe",
                "username": "johndoe",
                "is_premium": false
            }
        }
    """
    try:
        # Получаем данные от Telegram Login Widget
        data = await request.post()
        auth_data = dict(data)

        logger.info(f"📡 Получен запрос Telegram Login: user_id={auth_data.get('id')}")

        # Валидируем данные от Telegram
        auth_service = TelegramAuthService()
        if not auth_service.validate_telegram_auth(auth_data):
            logger.warning("⚠️ Невалидные данные от Telegram Login")
            return web.json_response(
                {"success": False, "error": "Invalid Telegram authentication"}, status=401
            )

        # Создаем/обновляем пользователя в БД
        with get_db() as db:
            user = auth_service.get_or_create_user(db, auth_data)

            # Создаём сессию через SessionService
            session_service = get_session_service()
            session_token = await session_service.create_session(
                telegram_id=user.telegram_id,
                user_data={
                    "telegram_id": user.telegram_id,
                    "full_name": user.full_name,
                    "username": user.username,
                    "is_premium": user.is_premium,
                },
            )

            logger.info(
                f"✅ Telegram авторизация успешна: user={user.telegram_id} ({user.full_name})"
            )

            return web.json_response(
                {
                    "success": True,
                    "session_token": session_token,
                    "user": {
                        "telegram_id": user.telegram_id,
                        "full_name": user.full_name,
                        "username": user.username,
                        "is_premium": user.is_premium,
                    },
                }
            )

    except Exception as e:
        logger.error(f"❌ Ошибка обработки Telegram Login: {e}", exc_info=True)
        return web.json_response({"success": False, "error": "Internal server error"}, status=500)


async def verify_session(request: web.Request) -> web.Response:
    """
    Проверка валидности сессии.

    GET /api/auth/telegram/verify

    Headers:
        Authorization: Bearer <session_token>

    Response:
        {
            "success": true,
            "user": {
                "telegram_id": 123456,
                "full_name": "John Doe",
                "username": "johndoe",
                "is_premium": false
            }
        }
    """
    try:
        # Получаем токен из заголовка
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return web.json_response({"success": False, "error": "No token provided"}, status=401)

        session_token = auth_header.replace("Bearer ", "")

        # Получаем сессию через SessionService
        session_service = get_session_service()
        session = await session_service.get_session(session_token)

        if not session:
            return web.json_response(
                {"success": False, "error": "Invalid or expired session"}, status=401
            )

        # Обновляем данные пользователя из БД
        with get_db() as db:
            from bot.services.user_service import UserService

            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(session.telegram_id)

            if not user:
                return web.json_response({"success": False, "error": "User not found"}, status=404)

            # Обновляем данные в сессии
            session.user_data = {
                "telegram_id": user.telegram_id,
                "full_name": user.full_name,
                "username": user.username,
                "is_premium": user.is_premium,
            }

            return web.json_response({"success": True, "user": session.user_data})

    except Exception as e:
        logger.error(f"❌ Ошибка проверки сессии: {e}", exc_info=True)
        return web.json_response({"success": False, "error": "Internal server error"}, status=500)


async def logout(request: web.Request) -> web.Response:
    """
    Выход из системы (удаление сессии).

    POST /api/auth/telegram/logout

    Headers:
        Authorization: Bearer <session_token>

    Response:
        {"success": true}
    """
    try:
        # Получаем токен из заголовка
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return web.json_response({"success": False, "error": "No token provided"}, status=401)

        session_token = auth_header.replace("Bearer ", "")

        # Удаляем сессию через SessionService
        session_service = get_session_service()
        session = await session_service.get_session(session_token)

        if session:
            await session_service.delete_session(session_token)
            logger.info(f"👋 Пользователь {session.telegram_id} вышел из системы")

        return web.json_response({"success": True})

    except Exception as e:
        logger.error(f"❌ Ошибка выхода из системы: {e}", exc_info=True)
        return web.json_response({"success": False, "error": "Internal server error"}, status=500)


async def session_stats(request: web.Request) -> web.Response:
    """
    Статистика по сессиям (для мониторинга).

    GET /api/auth/stats

    Response:
        {
            "storage": "Redis" | "In-Memory",
            "total_sessions": 10,
            "redis_connected": true
        }
    """
    try:
        session_service = get_session_service()
        stats = await session_service.get_stats()
        logger.info(f"📊 Статистика сессий: {stats}")
        return web.json_response({"success": True, "stats": stats})

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}", exc_info=True)
        return web.json_response({"success": False, "error": "Internal server error"}, status=500)
