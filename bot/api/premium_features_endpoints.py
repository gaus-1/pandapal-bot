"""
API endpoints для Premium функций.

Предоставляет доступ к:
- Персональному плану обучения
- Бонусным урокам (VIP)
- Статусу Premium функций
"""

from aiohttp import web
from loguru import logger

from bot.api.validators import validate_telegram_id
from bot.database import get_db
from bot.services import (
    BonusLessonsService,
    PersonalTutorService,
    PremiumFeaturesService,
    PrioritySupportService,
)


async def miniapp_get_learning_plan(request: web.Request) -> web.Response:
    """
    Получить персональный план обучения (Premium функция).

    GET /api/miniapp/premium/learning-plan/{telegram_id}
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        with get_db() as db:
            premium_service = PremiumFeaturesService(db)

            # Проверяем premium статус
            if not premium_service.is_premium_active(telegram_id):
                return web.json_response(
                    {
                        "error": "Premium subscription required",
                        "error_code": "PREMIUM_REQUIRED",
                    },
                    status=403,
                )

            # Получаем персональный план
            tutor_service = PersonalTutorService(db)
            learning_plan = tutor_service.get_learning_plan(telegram_id)

            return web.json_response({"success": True, "learning_plan": learning_plan})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения плана обучения: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_bonus_lessons(request: web.Request) -> web.Response:
    """
    Получить список бонусных уроков (VIP функция).

    GET /api/miniapp/premium/bonus-lessons/{telegram_id}
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        with get_db() as db:
            bonus_service = BonusLessonsService(db)

            # Проверяем доступ (только годовая подписка)
            if not bonus_service.can_access_bonus_lessons(telegram_id):
                return web.json_response(
                    {
                        "error": "Yearly Premium subscription required for bonus lessons",
                        "error_code": "VIP_REQUIRED",
                    },
                    status=403,
                )

            lessons = bonus_service.get_available_lessons(telegram_id)

            return web.json_response({"success": True, "lessons": lessons})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения бонусных уроков: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_bonus_lesson_content(request: web.Request) -> web.Response:
    """
    Получить содержание бонусного урока (VIP функция).

    GET /api/miniapp/premium/bonus-lessons/{telegram_id}/{lesson_id}
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        lesson_id = request.match_info.get("lesson_id")

        if not lesson_id:
            return web.json_response({"error": "lesson_id required"}, status=400)

        with get_db() as db:
            bonus_service = BonusLessonsService(db)

            # Проверяем доступ
            if not bonus_service.can_access_bonus_lessons(telegram_id):
                return web.json_response(
                    {
                        "error": "Yearly Premium subscription required",
                        "error_code": "VIP_REQUIRED",
                    },
                    status=403,
                )

            lesson_content = bonus_service.get_lesson_content(telegram_id, lesson_id)

            if not lesson_content:
                return web.json_response({"error": "Lesson not found"}, status=404)

            return web.json_response({"success": True, "lesson": lesson_content})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения урока: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_premium_features_status(request: web.Request) -> web.Response:
    """
    Получить статус всех Premium функций.

    GET /api/miniapp/premium/features/{telegram_id}
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        with get_db() as db:
            premium_service = PremiumFeaturesService(db)
            features_status = premium_service.get_premium_features_status(telegram_id)

            return web.json_response({"success": True, "features": features_status})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса функций: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_support_queue_status(request: web.Request) -> web.Response:
    """
    Получить информацию о позиции пользователя в очереди поддержки.

    GET /api/miniapp/premium/support-queue/{telegram_id}
    """
    try:
        telegram_id = validate_telegram_id(request.match_info["telegram_id"])

        with get_db() as db:
            support_service = PrioritySupportService(db)
            queue_info = support_service.get_queue_info(telegram_id)

            return web.json_response({"success": True, "queue": queue_info})

    except ValueError as e:
        logger.warning(f"⚠️ Invalid telegram_id: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"❌ Ошибка получения очереди поддержки: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)
