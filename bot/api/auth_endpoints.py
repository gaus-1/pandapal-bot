"""
API endpoints для аутентификации через Telegram Login Widget.

Обрабатывает авторизацию пользователей через виджет Telegram на веб-сайте.
"""

import secrets
from datetime import datetime, timedelta
from typing import Dict

from aiohttp import web
from loguru import logger

from bot.database import get_db
from bot.services.telegram_auth_service import TelegramAuthService

# Хранилище сессий (в production использовать Redis!)
# Формат: {session_token: {telegram_id, expires_at, user_data}}
_sessions: Dict[str, dict] = {}


def setup_auth_routes(app: web.Application) -> None:
    """
    Регистрация маршрутов для аутентификации.

    Args:
        app: Экземпляр aiohttp приложения
    """
    app.router.add_post("/api/auth/telegram/login", telegram_login)
    app.router.add_get("/api/auth/telegram/verify", verify_session)
    app.router.add_post("/api/auth/telegram/logout", logout)

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

            # Генерируем session token
            session_token = secrets.token_urlsafe(32)

            # Сохраняем сессию (TTL: 30 дней)
            expires_at = datetime.utcnow() + timedelta(days=30)
            _sessions[session_token] = {
                "telegram_id": user.telegram_id,
                "expires_at": expires_at,
                "user_data": {
                    "telegram_id": user.telegram_id,
                    "full_name": user.full_name,
                    "username": user.username,
                    "is_premium": user.is_premium,
                },
            }

            logger.info(
                f"✅ Telegram авторизация успешна: user={user.telegram_id} ({user.full_name})"
            )

            # Очищаем старые сессии
            _cleanup_expired_sessions()

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

        # Проверяем сессию
        session = _sessions.get(session_token)
        if not session:
            return web.json_response(
                {"success": False, "error": "Invalid or expired session"}, status=401
            )

        # Проверяем срок действия
        if datetime.utcnow() > session["expires_at"]:
            _sessions.pop(session_token, None)
            return web.json_response({"success": False, "error": "Session expired"}, status=401)

        # Обновляем данные пользователя из БД
        with get_db() as db:
            from bot.services.user_service import UserService

            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(session["telegram_id"])

            if not user:
                return web.json_response({"success": False, "error": "User not found"}, status=404)

            # Обновляем данные в сессии
            session["user_data"] = {
                "telegram_id": user.telegram_id,
                "full_name": user.full_name,
                "username": user.username,
                "is_premium": user.is_premium,
            }

            return web.json_response({"success": True, "user": session["user_data"]})

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

        # Удаляем сессию
        if session_token in _sessions:
            telegram_id = _sessions[session_token]["telegram_id"]
            _sessions.pop(session_token)
            logger.info(f"👋 Пользователь {telegram_id} вышел из системы")

        return web.json_response({"success": True})

    except Exception as e:
        logger.error(f"❌ Ошибка выхода из системы: {e}", exc_info=True)
        return web.json_response({"success": False, "error": "Internal server error"}, status=500)


def _cleanup_expired_sessions() -> None:
    """Очистка истекших сессий из памяти."""
    now = datetime.utcnow()
    expired_tokens = [token for token, session in _sessions.items() if now > session["expires_at"]]

    for token in expired_tokens:
        _sessions.pop(token, None)

    if expired_tokens:
        logger.debug(f"🧹 Очищено {len(expired_tokens)} истёкших сессий")
