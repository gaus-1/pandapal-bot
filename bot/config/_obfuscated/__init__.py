"""
Оптимизированные модули конфигурации для продакшена.

Этот пакет содержит оптимизированные версии критичных конфигурационных файлов
для использования в продакшене. Оригинальные файлы остаются для разработки.

Для разработчиков:
- Оригинальные файлы: bot/config/prompts.py, bot/config/forbidden_patterns.py
- Оптимизированные версии: bot/config/_obfuscated/prompts.py, bot/config/_obfuscated/forbidden_patterns.py
- Runtime: pyarmor_runtime_000000

Примечание: При изменении оригинальных файлов необходимо пересоздать оптимизированные версии
через scripts/optimize_config.py
"""

# Импортируем оптимизированные модули
try:
    from bot.config._obfuscated.forbidden_patterns import FORBIDDEN_PATTERNS
    from bot.config._obfuscated.prompts import AI_SYSTEM_PROMPT
except ImportError as e:
    # Fallback на оригинальные файлы если оптимизированные недоступны
    import warnings

    warnings.warn(f"Failed to import optimized modules: {e}. Using original files.", ImportWarning)
    from bot.config.forbidden_patterns import FORBIDDEN_PATTERNS
    from bot.config.prompts import AI_SYSTEM_PROMPT

__all__ = ["AI_SYSTEM_PROMPT", "FORBIDDEN_PATTERNS"]
