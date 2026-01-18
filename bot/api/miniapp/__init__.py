"""
Mini App API endpoints модуль.

Разделен на подмодули для лучшей организации:
- auth: аутентификация и управление пользователем
- progress: прогресс, достижения, дашборд
- chat: обычный чат (без streaming)
- chat_stream: streaming чат
- other: логи, предметы
- helpers: вспомогательные функции
"""

from aiohttp import web
from loguru import logger

from bot.api.miniapp.auth import (
    miniapp_auth,
    miniapp_get_user,
    miniapp_update_user,
)

# Импортируем только те модули, которые точно работают
from bot.api.miniapp.chat import miniapp_ai_chat
from bot.api.miniapp.helpers import (
    extract_user_name_from_message,
    format_achievements,
    process_audio_message,
    process_photo_message,
    send_achievements_event,
)
from bot.api.miniapp.homework import (
    miniapp_check_homework,
    miniapp_get_homework_history,
    miniapp_get_homework_statistics,
)
from bot.api.miniapp.other import (
    miniapp_add_greeting,
    miniapp_clear_chat_history,
    miniapp_get_chat_history,
    miniapp_get_subjects,
    miniapp_log,
)
from bot.api.miniapp.progress import (
    miniapp_get_achievements,
    miniapp_get_dashboard,
    miniapp_get_progress,
)

# Импортируем chat_stream только при необходимости (большой файл)
try:
    from bot.api.miniapp.chat_stream import miniapp_ai_chat_stream
except ImportError:
    miniapp_ai_chat_stream = None
    logger.warning("⚠️ chat_stream модуль недоступен")


def setup_miniapp_routes(app: web.Application) -> None:
    """
    Регистрация роутов Mini App в aiohttp приложении.

    Args:
        app: aiohttp приложение
    """
    # Ленивый импорт auth модуля для обработки ошибок
    try:
        # Пробуем относительный импорт сначала
        from .auth import (
            miniapp_auth,
            miniapp_get_user,
            miniapp_update_user,
        )

        # Аутентификация
        app.router.add_post("/api/miniapp/auth", miniapp_auth)
        logger.info("✅ POST /api/miniapp/auth зарегистрирован")
        # Пользователь
        app.router.add_get("/api/miniapp/user/{telegram_id}", miniapp_get_user)
        app.router.add_patch("/api/miniapp/user/{telegram_id}", miniapp_update_user)
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта .auth: {e}", exc_info=True)
        # Пробуем абсолютный импорт как fallback
        try:
            from bot.api.miniapp.auth import (
                miniapp_auth,
                miniapp_get_user,
                miniapp_update_user,
            )

            app.router.add_post("/api/miniapp/auth", miniapp_auth)
            app.router.add_get("/api/miniapp/user/{telegram_id}", miniapp_get_user)
            app.router.add_patch("/api/miniapp/user/{telegram_id}", miniapp_update_user)
            logger.info("✅ POST /api/miniapp/auth зарегистрирован (через абсолютный импорт)")
        except ImportError as e2:
            logger.error(f"❌ Ошибка абсолютного импорта bot.api.miniapp.auth: {e2}", exc_info=True)
            logger.warning("⚠️ Пропускаем регистрацию auth роутов")

    # Прогресс и достижения
    app.router.add_get("/api/miniapp/progress/{telegram_id}", miniapp_get_progress)
    app.router.add_get("/api/miniapp/achievements/{telegram_id}", miniapp_get_achievements)
    app.router.add_get("/api/miniapp/dashboard/{telegram_id}", miniapp_get_dashboard)

    # AI чат
    app.router.add_post("/api/miniapp/ai/chat", miniapp_ai_chat)
    if miniapp_ai_chat_stream:
        app.router.add_post("/api/miniapp/ai/chat-stream", miniapp_ai_chat_stream)
    app.router.add_get("/api/miniapp/chat/history/{telegram_id}", miniapp_get_chat_history)
    app.router.add_delete("/api/miniapp/chat/history/{telegram_id}", miniapp_clear_chat_history)
    app.router.add_post("/api/miniapp/chat/greeting/{telegram_id}", miniapp_add_greeting)

    # Предметы
    app.router.add_get("/api/miniapp/subjects", miniapp_get_subjects)

    # Premium функции
    from bot.api.premium_features_endpoints import (
        miniapp_get_bonus_lesson_content,
        miniapp_get_bonus_lessons,
        miniapp_get_learning_plan,
        miniapp_get_premium_features_status,
    )

    app.router.add_get(
        "/api/miniapp/premium/learning-plan/{telegram_id}", miniapp_get_learning_plan
    )
    app.router.add_get(
        "/api/miniapp/premium/bonus-lessons/{telegram_id}", miniapp_get_bonus_lessons
    )
    app.router.add_get(
        "/api/miniapp/premium/bonus-lessons/{telegram_id}/{lesson_id}",
        miniapp_get_bonus_lesson_content,
    )
    app.router.add_get(
        "/api/miniapp/premium/features/{telegram_id}", miniapp_get_premium_features_status
    )

    # Проверка домашних заданий
    app.router.add_post("/api/miniapp/homework/check", miniapp_check_homework)
    app.router.add_get("/api/miniapp/homework/history/{telegram_id}", miniapp_get_homework_history)
    app.router.add_get(
        "/api/miniapp/homework/statistics/{telegram_id}", miniapp_get_homework_statistics
    )

    # Логирование с фронтенда
    app.router.add_post("/api/miniapp/log", miniapp_log)

    logger.info("✅ Mini App API routes зарегистрированы")


__all__ = [
    # Auth
    "miniapp_auth",
    "miniapp_get_user",
    "miniapp_update_user",
    # Chat
    "miniapp_ai_chat",
    "miniapp_ai_chat_stream",
    # Progress
    "miniapp_get_progress",
    "miniapp_get_achievements",
    "miniapp_get_dashboard",
    # Other
    "miniapp_get_chat_history",
    "miniapp_clear_chat_history",
    "miniapp_add_greeting",
    "miniapp_get_subjects",
    "miniapp_log",
    # Helpers
    "process_audio_message",
    "process_photo_message",
    "format_achievements",
    "send_achievements_event",
    "extract_user_name_from_message",
    # Setup
    "setup_miniapp_routes",
]
