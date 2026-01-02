"""
Обфусцированные модули конфигурации.

ВАЖНО: Этот пакет содержит обфусцированные версии критичных конфигурационных файлов.
Используется для защиты интеллектуальной собственности проекта.

Для разработчиков и ИИ:
- Оригинальные файлы: bot/config/prompts.py, bot/config/forbidden_patterns.py
- Обфусцированные версии: bot/config/_obfuscated/prompts.py, bot/config/_obfuscated/forbidden_patterns.py
- Обфускация выполнена с помощью PyArmor
- Runtime: pyarmor_runtime_000000

Примечание: При изменении обфусцированных файлов необходимо пересоздать их через scripts/obfuscate_config.py
"""

# Импортируем обфусцированные модули
try:
    from bot.config._obfuscated.forbidden_patterns import FORBIDDEN_PATTERNS
    from bot.config._obfuscated.prompts import AI_SYSTEM_PROMPT
except ImportError as e:
    # Fallback на оригинальные файлы если обфусцированные недоступны
    import warnings

    warnings.warn(f"Failed to import obfuscated modules: {e}. Using original files.", ImportWarning)
    from bot.config.forbidden_patterns import FORBIDDEN_PATTERNS
    from bot.config.prompts import AI_SYSTEM_PROMPT

__all__ = ["AI_SYSTEM_PROMPT", "FORBIDDEN_PATTERNS"]
