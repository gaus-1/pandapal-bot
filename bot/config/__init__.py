"""
Конфигурация приложения PandaPal Bot.

Этот пакет содержит все настройки приложения, разделенные по модулям:
- settings: Основной класс Settings и константы
- prompts: AI промпты для YandexGPT
- forbidden_patterns: Списки запрещенных паттернов для модерации

Для обратной совместимости все экспортируется из корня пакета.
"""

# Импортируем из обфусцированных модулей (защита интеллектуальной собственности)
# Примечание: Обфусцированные файлы находятся в bot/config/_obfuscated/
# Для разработчиков: см. bot/config/_obfuscated/__init__.py для деталей
try:
    from bot.config._obfuscated import AI_SYSTEM_PROMPT, FORBIDDEN_PATTERNS
except ImportError:
    # Fallback на оригинальные файлы для локальной разработки
    from bot.config.forbidden_patterns import FORBIDDEN_PATTERNS
    from bot.config.prompts import AI_SYSTEM_PROMPT
from bot.config.settings import (
    ALLOWED_FILE_TYPES,
    MAX_AGE,
    MAX_FILE_SIZE_MB,
    MAX_GRADE,
    MAX_MESSAGE_LENGTH,
    MIN_AGE,
    MIN_GRADE,
    Settings,
    settings,
)

# Экспорт для обратной совместимости
__all__ = [
    "Settings",
    "settings",
    "AI_SYSTEM_PROMPT",
    "FORBIDDEN_PATTERNS",
    "MIN_AGE",
    "MAX_AGE",
    "MIN_GRADE",
    "MAX_GRADE",
    "MAX_MESSAGE_LENGTH",
    "MAX_FILE_SIZE_MB",
    "ALLOWED_FILE_TYPES",
]
