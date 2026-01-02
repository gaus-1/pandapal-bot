"""
Конфигурация приложения PandaPal Bot.

Этот пакет содержит все настройки приложения, разделенные по модулям:
- settings: Основной класс Settings и константы
- prompts: AI промпты для YandexGPT
- forbidden_patterns: Списки запрещенных паттернов для модерации

Для обратной совместимости все экспортируется из корня пакета.
"""

# Импортируем из оптимизированных модулей (production-ready версии)
# Примечание: Оптимизированные файлы находятся в bot/config/_obfuscated/
# Для разработчиков: см. bot/config/_obfuscated/__init__.py для деталей
_optimized_available = False
try:
    from bot.config._obfuscated import AI_SYSTEM_PROMPT, FORBIDDEN_PATTERNS

    _optimized_available = True
except ImportError:
    # Fallback на оригинальные файлы только для development
    # В production обфусцированные файлы обязательны (создаются через railway_build.sh)
    import os
    from pathlib import Path

    # Проверяем, находимся ли мы в production (Railway)
    # Railway автоматически устанавливает переменную RAILWAY_ENVIRONMENT
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY"))
    env = os.getenv("ENVIRONMENT", "production" if is_railway else "development").lower()

    # В production (Railway) обфусцированные файлы обязательны
    # Они создаются через railway_build.sh перед запуском
    if env == "production" or is_railway:
        raise ImportError(
            "Optimized configuration files are required in production. "
            "Please ensure railway_build.sh was executed during build. "
            "If running locally, set ENVIRONMENT=development to use original files."
        )

    # Для development используем оригинальные файлы
    from bot.config.forbidden_patterns import FORBIDDEN_PATTERNS  # noqa: E402
    from bot.config.prompts import AI_SYSTEM_PROMPT  # noqa: E402
from bot.config.settings import (  # noqa: E402
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
