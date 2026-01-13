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

# Экспортируем все endpoints для обратной совместимости
# Ленивый импорт auth модуля для обработки ошибок импорта
try:
    from bot.api.miniapp.auth import (
        miniapp_auth,
        miniapp_get_user,
        miniapp_update_user,
    )
except ImportError as e:
    logger.error(f"❌ Ошибка импорта bot.api.miniapp.auth: {e}", exc_info=True)
    # Создаем заглушки, чтобы модуль мог загрузиться
    miniapp_auth = None
    miniapp_get_user = None
    miniapp_update_user = None
from bot.api.miniapp.chat import miniapp_ai_chat
from bot.api.miniapp.helpers import (
    extract_user_name_from_message,
    format_achievements,
    process_audio_message,
    process_photo_message,
    send_achievements_event,
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
    # Аутентификация
    if miniapp_auth is None:
        logger.error("❌ miniapp_auth не импортирован, пропускаем регистрацию /api/miniapp/auth")
    else:
        app.router.add_post("/api/miniapp/auth", miniapp_auth)
        logger.info("✅ POST /api/miniapp/auth зарегистрирован")

    # Пользователь
    if miniapp_get_user is not None:
        app.router.add_get("/api/miniapp/user/{telegram_id}", miniapp_get_user)
    if miniapp_update_user is not None:
        app.router.add_patch("/api/miniapp/user/{telegram_id}", miniapp_update_user)

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
