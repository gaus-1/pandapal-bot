"""
Endpoints для аутентификации и управления пользователем.
"""

from aiohttp import web
from loguru import logger
from pydantic import ValidationError

# Логирование каждого шага импорта для диагностики
logger.debug("🔍 [auth.py] Начало загрузки модуля")

try:
    logger.debug("🔍 [auth.py] Импорт bot.api.validators...")
    from bot.api.validators import AuthRequest, UpdateUserRequest, validate_telegram_id

    logger.debug("✅ [auth.py] bot.api.validators импортирован")
except Exception as e:
    logger.error(f"❌ [auth.py] Ошибка импорта bot.api.validators: {e}", exc_info=True)
    raise

try:
    logger.debug("🔍 [auth.py] Импорт bot.database...")
    from bot.database import get_db

    logger.debug("✅ [auth.py] bot.database импортирован")
except Exception as e:
    logger.error(f"❌ [auth.py] Ошибка импорта bot.database: {e}", exc_info=True)
    raise

try:
    logger.debug("🔍 [auth.py] Импорт bot.security.telegram_auth...")
    from bot.security.telegram_auth import TelegramWebAppAuth

    logger.debug("✅ [auth.py] bot.security.telegram_auth импортирован")
except Exception as e:
    logger.error(f"❌ [auth.py] Ошибка импорта bot.security.telegram_auth: {e}", exc_info=True)
    raise

try:
    logger.debug("🔍 [auth.py] Импорт bot.services...")
    from bot.services import UserService

    logger.debug("✅ [auth.py] bot.services импортирован")
except Exception as e:
    logger.error(f"❌ [auth.py] Ошибка импорта bot.services: {e}", exc_info=True)
    raise

logger.debug("✅ [auth.py] Все импорты успешны, модуль загружен")


async def miniapp_auth(request: web.Request) -> web.Response:
    """
    Аутентификация пользователя Mini App.

    POST /api/miniapp/auth
    Body: { "initData": "..." }

    Returns:
        200: { "success": true, "user": {...} }
        400: { "error": "..." }
        403: { "error": "Invalid initData" }
    """
    try:
        data = await request.json()

        # Валидация входных данных
        try:
            validated = AuthRequest(**data)
        except ValidationError as e:
            logger.warning(f"⚠️ Invalid auth request: {e.errors()}")
            return web.json_response(
                {"error": "Invalid request data", "details": e.errors()},
                status=400,
            )

        init_data = validated.initData

        logger.info(
            f"📡 Получен запрос аутентификации. initData length: {len(init_data) if init_data else 0}"
        )

        if not init_data:
            logger.warning("⚠️ initData отсутствует в запросе")
            return web.json_response({"error": "initData required"}, status=400)

        # Валидация данных от Telegram
        auth_validator = TelegramWebAppAuth()
        validated_data = auth_validator.validate_init_data(init_data)

        if not validated_data:
            logger.warning("⚠️ initData не прошёл валидацию")
            return web.json_response(
                {"error": "Invalid Telegram signature. Make sure app is opened via Telegram."},
                status=403,
            )

        # Извлекаем данные пользователя
        user_data = auth_validator.extract_user_data(validated_data)

        if not user_data:
            logger.error("❌ Не удалось извлечь user_data из validated_data")
            return web.json_response(
                {"error": "Failed to extract user data from initData"}, status=400
            )

        telegram_id = user_data.get("id")

        if not telegram_id:
            logger.error(f"❌ telegram_id отсутствует в user_data: {user_data}")
            return web.json_response({"error": "No user ID in initData"}, status=400)

        # Получаем или создаем пользователя
        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_or_create_user(
                telegram_id=telegram_id,
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
            )

            # Вызываем to_dict() ВНУТРИ сессии
            user_dict = user.to_dict()

        logger.info(f"✅ Пользователь {telegram_id} успешно аутентифицирован")

        # Возвращаем данные пользователя
        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        # Используем % для логирования чтобы избежать проблем с фигурными скобками в SQL
        logger.error("❌ Ошибка аутентификации Mini App: %s", str(e), exc_info=True)
        return web.json_response({"error": f"Server error: {str(e)}"}, status=500)


def _verify_resource_owner(
    request: web.Request, target_telegram_id: int
) -> tuple[bool, str | None]:
    """
    Проверка владельца ресурса (OWASP A01: Broken Access Control).

    Верифицирует, что пользователь из initData имеет право доступа к ресурсу.

    Args:
        request: HTTP запрос с заголовком X-Telegram-Init-Data
        target_telegram_id: ID ресурса к которому запрашивается доступ

    Returns:
        (allowed, error_message): Разрешен ли доступ и сообщение об ошибке
    """
    # Получаем initData из заголовка
    init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data:
        # Без initData - запрещаем доступ к защищенным ресурсам
        logger.warning("⚠️ Запрос без X-Telegram-Init-Data к защищенному ресурсу")
        return False, "Authorization required: X-Telegram-Init-Data header missing"

    # Валидируем initData
    auth_validator = TelegramWebAppAuth()
    validated_data = auth_validator.validate_init_data(init_data)

    if not validated_data:
        logger.warning("⚠️ Невалидный initData в заголовке")
        return False, "Invalid authorization data"

    # Извлекаем telegram_id из initData
    user_data = auth_validator.extract_user_data(validated_data)
    if not user_data or not user_data.get("id"):
        logger.warning("⚠️ Не удалось извлечь user_id из initData")
        return False, "Invalid user data in authorization"

    requester_id = user_data["id"]

    # Проверяем что запрашивающий == владелец ресурса
    if requester_id != target_telegram_id:
        logger.warning(
            f"🚫 Access denied: user {requester_id} tried to access resource of user {target_telegram_id}"
        )
        return False, "Access denied: you can only access your own resources"

    return True, None


async def miniapp_get_user(request: web.Request) -> web.Response:
    """
    Получить профиль пользователя.

    GET /api/miniapp/user/{telegram_id}

    Требует заголовок X-Telegram-Init-Data для проверки владельца ресурса.
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        # Проверка владельца ресурса (A01: Broken Access Control)
        allowed, error_msg = _verify_resource_owner(request, telegram_id)
        if not allowed:
            return web.json_response({"error": error_msg}, status=403)

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            user_dict = user.to_dict()

        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения пользователя: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_update_user(request: web.Request) -> web.Response:
    """
    Обновить профиль пользователя.

    PATCH /api/miniapp/user/{telegram_id}
    Body: { "age": 10, "grade": 4 }

    Требует заголовок X-Telegram-Init-Data для проверки владельца ресурса.
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        # Проверка владельца ресурса (A01: Broken Access Control)
        allowed, error_msg = _verify_resource_owner(request, telegram_id)
        if not allowed:
            return web.json_response({"error": error_msg}, status=403)

        # Валидация входных данных
        data = await request.json()
        try:
            validated = UpdateUserRequest(**data)
        except ValidationError as e:
            logger.warning(f"⚠️ Invalid update user request: {e.errors()}")
            return web.json_response(
                {"error": "Invalid request data", "details": e.errors()},
                status=400,
            )

        age = validated.age
        grade = validated.grade

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.update_user_profile(telegram_id=telegram_id, age=age, grade=grade)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            user_dict = user.to_dict()

        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка обновления пользователя: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
