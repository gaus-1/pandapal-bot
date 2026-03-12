"""
Утилиты очистки и постобработки ответов AI.

Пакет разбит на модули:
- deduplication — удаление повторов и артефактов стриминга
- formatting — нормализация форматирования (bold, списки, абзацы)
- engagement — вовлекающие вопросы и уточняющая логика
- pipeline — главные точки входа (clean_ai_response, finalize_ai_response)

Все публичные функции и константы доступны из корня пакета
для обратной совместимости с `from bot.services.response_cleaner import ...`.
"""

# Дедупликация
from .deduplication import (
    _remove_duplicate_long_substrings,
    remove_duplicate_text,
)

# Вовлечение и уточнения
from .engagement import (
    _CLARIFICATION_MAX_MESSAGE_LEN,
    _CLARIFICATION_MIN_LAST_REPLY_LEN,
    _CLARIFICATION_PHRASES,
    _CLARIFICATION_RESPONSE,
    _FAREWELL_KEYWORDS,
    _is_farewell_message,
    _is_probably_russian_message,
    _strip_explain_more_tail,
    add_random_engagement_question,
)

# Форматирование
from .formatting import (
    _ensure_list_and_bold_breaks,
    _ensure_paragraph_breaks,
    _is_digit_only_line,
    _merge_definition_split_by_dash,
    _merge_digit_only_lines,
    _normalize_for_dedup,
    _strip_invisible_unicode,
    fix_glued_words,
    normalize_bold_spacing,
)

# Pipeline (главные точки входа)
from .pipeline import (
    clean_ai_response,
    finalize_ai_response,
)

__all__ = [
    # Pipeline
    "clean_ai_response",
    "finalize_ai_response",
    # Дедупликация
    "remove_duplicate_text",
    "_remove_duplicate_long_substrings",
    # Форматирование
    "normalize_bold_spacing",
    "_strip_invisible_unicode",
    "fix_glued_words",
    "_is_digit_only_line",
    "_merge_digit_only_lines",
    "_ensure_list_and_bold_breaks",
    "_merge_definition_split_by_dash",
    "_ensure_paragraph_breaks",
    "_normalize_for_dedup",
    # Вовлечение
    "add_random_engagement_question",
    "_strip_explain_more_tail",
    "_is_farewell_message",
    "_is_probably_russian_message",
    "_FAREWELL_KEYWORDS",
    "_CLARIFICATION_MAX_MESSAGE_LEN",
    "_CLARIFICATION_MIN_LAST_REPLY_LEN",
    "_CLARIFICATION_PHRASES",
    "_CLARIFICATION_RESPONSE",
]
