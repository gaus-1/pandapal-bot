"""
API endpoints для аутентификации через Telegram Login Widget.

Обрабатывает авторизацию пользователей через виджет Telegram на веб-сайте.
"""

import os

from aiohttp import web
from loguru import logger

from bot.database import get_db
from bot.services.session_service import SESSION_TTL_DAYS, get_session_service
from bot.services.telegram_auth_service import TelegramAuthService

# Cookie для веб-авторизации (HTTP-only, снижает риск кражи при XSS)
TELEGRAM_SESSION_COOKIE = "telegram_session"
SESSION_COOKIE_MAX_AGE = SESSION_TTL_DAYS * 24 * 3600


def _get_session_token(request: web.Request) -> str | None:
    """Токен сессии из cookie или заголовка Authorization Bearer (обратная совместимость)."""
    token = request.cookies.get(TELEGRAM_SESSION_COOKIE)
    if token:
        return token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "").strip()
    return None


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

            payload = {
                "success": True,
                "session_token": session_token,
                "user": {
                    "telegram_id": user.telegram_id,
                    "full_name": user.full_name,
                    "username": user.username,
                    "is_premium": user.is_premium,
                },
            }
            response = web.json_response(payload)
            # HTTP-only cookie для снижения риска кражи сессии при XSS; JSON с токеном сохранён для обратной совместимости
            response.headers["Set-Cookie"] = (
                f"{TELEGRAM_SESSION_COOKIE}={session_token}; "
                "HttpOnly; Secure; SameSite=Strict; "
                f"Path=/api; Max-Age={SESSION_COOKIE_MAX_AGE}"
            )
            return response

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
        session_token = _get_session_token(request)
        if not session_token:
            return web.json_response({"success": False, "error": "No token provided"}, status=401)

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
        session_token = _get_session_token(request)
        if not session_token:
            return web.json_response({"success": False, "error": "No token provided"}, status=401)

        session_service = get_session_service()
        session = await session_service.get_session(session_token)

        if session:
            await session_service.delete_session(session_token)
            logger.info(f"👋 Пользователь {session.telegram_id} вышел из системы")

        response = web.json_response({"success": True})
        # Удаляем cookie сессии в браузере
        response.headers["Set-Cookie"] = (
            f"{TELEGRAM_SESSION_COOKIE}=; HttpOnly; Secure; SameSite=Strict; "
            "Path=/api; Max-Age=0"
        )
        return response

    except Exception as e:
        logger.error(f"❌ Ошибка выхода из системы: {e}", exc_info=True)
        return web.json_response({"success": False, "error": "Internal server error"}, status=500)


# Разрешённые IP для GET /api/auth/stats (только localhost по умолчанию)
AUTH_STATS_ALLOWED_IPS = frozenset(
    os.getenv("AUTH_STATS_ALLOWED_IPS", "127.0.0.1,::1").replace(" ", "").split(",")
)


def _is_auth_stats_allowed(request: web.Request) -> bool:
    """Проверка допуска к endpoint статистики сессий (localhost или внутренний секрет)."""
    remote = request.remote or ""
    if remote in AUTH_STATS_ALLOWED_IPS:
        return True
    secret = os.getenv("AUTH_STATS_SECRET")
    return bool(secret and request.headers.get("X-Internal-Monitor") == secret)


async def session_stats(request: web.Request) -> web.Response:
    """
    Статистика по сессиям (для мониторинга).

    GET /api/auth/stats
    Доступ только с localhost или с заголовком X-Internal-Monitor (см. AUTH_STATS_SECRET).

    Response:
        {
            "storage": "Redis" | "In-Memory",
            "total_sessions": 10,
            "redis_connected": true
        }
    """
    if not _is_auth_stats_allowed(request):
        logger.warning(f"🚫 Доступ к /api/auth/stats отклонён: remote={request.remote}")
        return web.json_response({"error": "Forbidden"}, status=403)
    try:
        session_service = get_session_service()
        stats = await session_service.get_stats()
        logger.info(f"📊 Статистика сессий: {stats}")
        return web.json_response({"success": True, "stats": stats})

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}", exc_info=True)
        return web.json_response({"success": False, "error": "Internal server error"}, status=500)
