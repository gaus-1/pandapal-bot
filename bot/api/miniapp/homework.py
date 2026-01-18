"""
Endpoints для проверки домашних заданий.
"""

import base64

from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import HomeworkCheckRequest, validate_telegram_id
from bot.database import get_db
from bot.services import UserService
from bot.services.homework_service import HomeworkService


async def miniapp_check_homework(request: web.Request) -> web.Response:
    """
    Проверить домашнее задание по фото.

    POST /api/miniapp/homework/check
    Body: {
        "telegram_id": 123,
        "photo_base64": "data:image/jpeg;base64,...",
        "subject": "математика",  # опционально
        "topic": "дроби",  # опционально
        "message": "Проверь это задание"  # опционально
    }
    """
    try:
        data = await request.json()

        # Валидация входных данных
        try:
            validated = HomeworkCheckRequest(**data)
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                error_dict = {
                    "type": error.get("type", "validation_error"),
                    "loc": error.get("loc", []),
                    "msg": error.get("msg", "Validation error"),
                }
                if "ctx" in error and error["ctx"]:
                    ctx = error["ctx"]
                    if isinstance(ctx, dict):
                        ctx = {k: str(v) if isinstance(v, Exception) else v for k, v in ctx.items()}
                        error_dict["ctx"] = ctx
                error_details.append(error_dict)

            logger.warning(f"⚠️ Invalid homework check request: {error_details}")
            return web.json_response(
                {"error": "Invalid request data", "details": error_details},
                status=400,
            )

        telegram_id = validated.telegram_id

        # Проверяем пользователя
        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Получаем возраст пользователя для адаптации ответа
            user_age = user.age

            # Декодируем фото из base64
            try:
                photo_base64 = validated.photo_base64
                # Убираем префикс data:image/...;base64, если есть
                if "," in photo_base64:
                    photo_base64 = photo_base64.split(",", 1)[1]

                image_data = base64.b64decode(photo_base64)
            except Exception as e:
                logger.error(f"❌ Ошибка декодирования фото: {e}")
                return web.json_response({"error": "Invalid photo_base64 format"}, status=400)

            # Проверяем ДЗ
            homework_service = HomeworkService(db)

            submission = await homework_service.check_homework_from_photo(
                telegram_id=telegram_id,
                image_data=image_data,
                subject=validated.subject,
                topic=validated.topic,
                user_message=validated.message,
                user_age=user_age,
            )

            db.commit()

            # Формируем ответ
            result = {
                "success": True,
                "submission": {
                    "id": submission.id,
                    "subject": submission.subject,
                    "topic": submission.topic,
                    "has_errors": submission.has_errors,
                    "errors_found": submission.errors_found.get("errors", [])
                    if submission.errors_found
                    else [],
                    "ai_feedback": submission.ai_feedback,
                    "original_text": submission.original_text,
                    "submitted_at": submission.submitted_at.isoformat()
                    if submission.submitted_at
                    else None,
                },
            }

            return web.json_response(result)

    except Exception as e:
        logger.error(f"❌ Ошибка проверки ДЗ: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_homework_history(request: web.Request) -> web.Response:
    """
    Получить историю проверок ДЗ.

    GET /api/miniapp/homework/history/{telegram_id}?limit=20&subject=математика
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        # Получаем параметры запроса
        limit = int(request.query.get("limit", 20))
        subject: str | None = request.query.get("subject") or None

        with get_db() as db:
            homework_service = HomeworkService(db)
            history = homework_service.get_homework_history(
                telegram_id=telegram_id, limit=limit, subject=subject
            )

            submissions = [s.to_dict() for s in history]

            return web.json_response({"success": True, "history": submissions})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории ДЗ: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_homework_statistics(request: web.Request) -> web.Response:
    """
    Получить статистику проверок ДЗ.

    GET /api/miniapp/homework/statistics/{telegram_id}
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        with get_db() as db:
            homework_service = HomeworkService(db)
            stats = homework_service.get_statistics(telegram_id=telegram_id)

            return web.json_response({"success": True, "statistics": stats})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики ДЗ: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)
