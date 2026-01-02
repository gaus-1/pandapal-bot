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
    # Fallback на оригинальные файлы
    # ВАЖНО: В production обфусцированные файлы должны создаваться через nixpacks.toml build phase
    # Если их нет - используем оригинальные файлы (временно, для стабильности)
    import os
    from pathlib import Path

    # Проверяем, находимся ли мы в production (Railway)
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY"))

    # Логируем предупреждение, но не падаем
    if is_railway:
        import sys

        print(
            "⚠️ WARNING: Optimized config files not found in production. "
            "Using original files. Check build logs for obfuscation script errors.",
            file=sys.stderr,
        )

    # Используем оригинальные файлы (fallback)
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
