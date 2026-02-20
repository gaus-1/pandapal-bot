"""Предварительные проверки запроса: парсинг, валидация, лимиты."""

import json

from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import AIChatRequest
from bot.database import get_db
from bot.services import UserService
from bot.services.premium_features_service import PremiumFeaturesService


async def parse_and_validate_request_early(
    request: web.Request,
) -> tuple[dict | None, web.Response | None]:
    """
    Парсинг и валидация тела запроса до открытия SSE.
    Возвращает (parsed_dict, None) при успехе или (None, error_response) при ошибке.
    Используется для возврата 400/403 до response.prepare().
    """
    try:
        data = await request.json()
        logger.info(
            f"📦 Stream: получен JSON запрос: telegram_id={data.get('telegram_id')}, "
            f"has_message={bool(data.get('message'))}, "
            f"has_photo={bool(data.get('photo_base64'))}, "
            f"has_audio={bool(data.get('audio_base64'))}"
        )
    except Exception as json_error:
        err_str = str(json_error)
        logger.error(f"❌ Stream: ошибка парсинга JSON: {json_error}", exc_info=True)
        if "Content Too Large" in err_str or "too large" in err_str.lower():
            return (
                None,
                web.json_response(
                    {
                        "error": "Фото или аудио слишком большие. Уменьши размер фото или длину голосового."
                    },
                    status=413,
                ),
            )
        return (None, web.json_response({"error": "Invalid JSON"}, status=400))

    try:
        validated = AIChatRequest(**data)
    except ValidationError as e:
        logger.warning(f"⚠️ Stream: Invalid request: {e}")
        return (None, web.json_response({"error": "Invalid request data"}, status=400))

    return (
        {
            "telegram_id": validated.telegram_id,
            "message": validated.message or "",
            "photo_base64": validated.photo_base64,
            "audio_base64": validated.audio_base64,
            "language_code": validated.language_code,
        },
        None,
    )


async def parse_and_validate_request(
    request: web.Request, response: web.StreamResponse
) -> dict | None:
    """Парсинг JSON и валидация Pydantic. Возвращает dict с полями или None (ошибка отправлена)."""
    try:
        data = await request.json()
        logger.info(
            f"📦 Stream: получен JSON запрос: telegram_id={data.get('telegram_id')}, "
            f"has_message={bool(data.get('message'))}, "
            f"has_photo={bool(data.get('photo_base64'))}, "
            f"has_audio={bool(data.get('audio_base64'))}"
        )
    except Exception as json_error:
        err_str = str(json_error)
        logger.error(f"❌ Stream: ошибка парсинга JSON: {json_error}", exc_info=True)
        if "Content Too Large" in err_str or "too large" in err_str.lower():
            msg = '{"error": "Фото или аудио слишком большие. Уменьши размер фото или длину голосового."}'
            await response.write(f"event: error\ndata: {msg}\n\n".encode())
        else:
            await response.write(b'event: error\ndata: {"error": "Invalid JSON"}\n\n')
        return None

    try:
        validated = AIChatRequest(**data)
    except ValidationError as e:
        logger.warning(f"⚠️ Stream: Invalid request: {e}")
        await response.write(b'event: error\ndata: {"error": "Invalid request data"}\n\n')
        return None

    return {
        "telegram_id": validated.telegram_id,
        "message": validated.message or "",
        "photo_base64": validated.photo_base64,
        "audio_base64": validated.audio_base64,
        "language_code": validated.language_code,
    }


async def check_premium_and_lazy(
    telegram_id: int, response: web.StreamResponse, raw_message: str = ""
) -> bool:
    """Проверка лимита и ленивости панды. Возвращает True если можно продолжать."""
    with get_db() as db:
        user_service = UserService(db)
        premium_service = PremiumFeaturesService(db)
        user = user_service.get_user_by_telegram_id(telegram_id)
        if not user:
            await response.write(b'event: error\ndata: {"error": "User not found"}\n\n')
            return False

        can_request, limit_reason = premium_service.can_make_ai_request(
            telegram_id, username=user.username
        )
        if not can_request:
            logger.warning(
                f"🚫 Stream: AI запрос заблокирован для user={telegram_id} (до audio/photo): {limit_reason}"
            )
            err_escaped = limit_reason.replace('"', '\\"').replace("\n", " ")
            await response.write(
                f'event: error\ndata: {{"error": "{err_escaped}", "error_code": "RATE_LIMIT_EXCEEDED"}}\n\n'.encode()
            )
            return False

        from bot.api.miniapp.stream_handlers._routing import BAMBOO_EAT_PATTERN
        from bot.services.panda_chat_reactions import get_chat_reaction
        from bot.services.panda_lazy_service import PandaLazyService

        # Не перехватываем фидбек и явные «поешь/перекуси» ранней веткой ленивости.
        msg = (raw_message or "").strip()
        is_feedback = bool(get_chat_reaction(msg)) if msg else False
        is_explicit_bamboo = bool(BAMBOO_EAT_PATTERN.search(msg)) if msg else False

        if not is_feedback and not is_explicit_bamboo:
            lazy_service = PandaLazyService(db)
            is_lazy, lazy_message = lazy_service.check_and_update_lazy_state(telegram_id)
            if is_lazy and lazy_message:
                logger.info(f"😴 Mini App Stream: Панда 'ленива' для пользователя {telegram_id}")
                event_data = json.dumps({"content": lazy_message}, ensure_ascii=False)
                await response.write(f"event: message\ndata: {event_data}\n\n".encode())
                await response.write(b"event: done\ndata: {}\n\n")
                return False

    return True
