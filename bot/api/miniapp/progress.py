"""
Endpoints для прогресса, достижений и дашборда.
"""

from aiohttp import web
from loguru import logger
from sqlalchemy import func, select

from bot.api.validators import (
    DashboardStatsResponse,
    DetailedAnalyticsResponse,
    validate_telegram_id,
)
from bot.database import get_db
from bot.models import ChatHistory, LearningSession, UserProgress
from bot.services import UserService


async def miniapp_get_progress(request: web.Request) -> web.Response:
    """
    Получить прогресс обучения пользователя.

    GET /api/miniapp/progress/{telegram_id}
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Получаем прогресс из БД ВНУТРИ сессии
            progress_items = [p.to_dict() for p in user.progress]

        return web.json_response({"success": True, "progress": progress_items})

    except Exception as e:
        logger.error(f"❌ Ошибка получения прогресса: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_achievements(request: web.Request) -> web.Response:
    """
    Получить достижения пользователя с реальными данными из БД.

    GET /api/miniapp/achievements/{telegram_id}
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        with get_db() as db:
            from bot.services.gamification_service import GamificationService

            gamification_service = GamificationService(db)
            achievements_data = gamification_service.get_achievements_with_progress(telegram_id)

        # Преобразуем в формат для API
        achievements = []
        for ach in achievements_data:
            achievement_dict = {
                "id": ach["id"],
                "title": ach["title"],
                "description": ach["description"],
                "icon": ach["icon"],
                "unlocked": ach["unlocked"],
                "xp_reward": ach["xp_reward"],
                "progress": ach["progress"],
                "progress_max": ach["progress_max"],
            }
            if ach["unlocked"] and ach.get("unlock_date"):
                achievement_dict["unlock_date"] = ach["unlock_date"]
            achievements.append(achievement_dict)

        return web.json_response({"success": True, "achievements": achievements})

    except Exception as e:
        logger.error(f"❌ Ошибка получения достижений: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_dashboard(request: web.Request) -> web.Response:
    """
    Получить статистику для дашборда.

    GET /api/miniapp/dashboard/{telegram_id}
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Проверяем premium для детальной аналитики
            from bot.services.premium_features_service import PremiumFeaturesService

            premium_service = PremiumFeaturesService(db)
            is_premium = premium_service.is_premium_active(telegram_id)

            # Базовая статистика (доступна всем)
            # Оптимизация: используем SQL COUNT/SUM вместо загрузки всех объектов
            messages_count = (
                db.execute(
                    select(func.count(ChatHistory.id)).where(
                        ChatHistory.user_telegram_id == telegram_id
                    )
                ).scalar()
                or 0
            )

            sessions_count = (
                db.execute(
                    select(func.count(LearningSession.id)).where(
                        LearningSession.user_telegram_id == telegram_id
                    )
                ).scalar()
                or 0
            )

            total_points = (
                db.execute(
                    select(func.coalesce(func.sum(UserProgress.points), 0)).where(
                        UserProgress.user_telegram_id == telegram_id
                    )
                ).scalar()
                or 0
            )

            subjects_count = (
                db.execute(
                    select(func.count(UserProgress.id)).where(
                        UserProgress.user_telegram_id == telegram_id
                    )
                ).scalar()
                or 0
            )

            # Детальная аналитика только для Premium
            detailed_analytics = None
            if is_premium:
                from bot.services.analytics_service import AnalyticsService

                analytics_service = AnalyticsService(db)
                detailed_analytics = DetailedAnalyticsResponse(
                    messages_per_day=analytics_service.get_messages_per_day(telegram_id),
                    most_active_subjects=analytics_service.get_most_active_subjects(telegram_id),
                    learning_trends=analytics_service.get_learning_trends(telegram_id),
                )

            stats = DashboardStatsResponse(
                total_messages=messages_count,
                learning_sessions=sessions_count,
                total_points=total_points,
                subjects_studied=subjects_count,
                current_streak=1,  # Временно hardcode
                detailed_analytics=detailed_analytics,
            )

            return web.json_response(
                {
                    "success": True,
                    "stats": stats.model_dump(exclude_none=True),
                    "is_premium": is_premium,
                }
            )

    except Exception as e:
        logger.error(f"❌ Ошибка получения дашборда: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
