"""
API endpoints для Telegram Mini App
Обеспечивает взаимодействие между React frontend и Python backend

⚠️ DEPRECATED: Этот файл оставлен для обратной совместимости.
Используйте bot.api.miniapp вместо bot.api.miniapp_endpoints
"""

# Re-export всех функций из модулей для обратной совместимости
from bot.api.miniapp import (
    miniapp_add_greeting,
    # Chat
    miniapp_ai_chat,
    miniapp_ai_chat_stream,
    # Auth
    miniapp_auth,
    miniapp_clear_chat_history,
    miniapp_get_achievements,
    # Other
    miniapp_get_chat_history,
    miniapp_get_dashboard,
    # Progress
    miniapp_get_progress,
    miniapp_get_subjects,
    miniapp_get_user,
    miniapp_log,
    miniapp_update_user,
    # Setup
    setup_miniapp_routes,
)

# Импортируем helpers для обратной совместимости
from bot.api.miniapp.helpers import (
    extract_user_name_from_message,
    format_achievements,
    process_audio_message,
    process_photo_message,
    send_achievements_event,
)
from bot.database import get_db

# Экспортируем helper функции с префиксом _ для обратной совместимости
_process_audio_message = process_audio_message
_process_photo_message = process_photo_message
_format_achievements = format_achievements
_send_achievements_event = send_achievements_event
_extract_user_name_from_message = extract_user_name_from_message

__all__ = [
    # DB helper (для тестов и обратной совместимости)
    "get_db",
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
    # Helpers (deprecated, но для обратной совместимости)
    "_process_audio_message",
    "_process_photo_message",
    "_format_achievements",
    "_send_achievements_event",
    "_extract_user_name_from_message",
    # Setup
    "setup_miniapp_routes",
]
