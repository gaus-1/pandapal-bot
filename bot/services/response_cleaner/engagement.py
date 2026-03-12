"""
Вовлекающие вопросы и уточняющая логика для ответов AI.

Stateless-функции для: определения прощания, языка сообщения,
добавления вовлекающих вопросов, удаления запрещённых фраз
и обработки уточняющих запросов.
"""

import random
import re

_FAREWELL_KEYWORDS = frozenset(
    {
        "пока",
        "до свидания",
        "до свиданья",
        "прощай",
        "прощайте",
        "bye",
        "goodbye",
        "see you",
        "увидимся",
    }
)

# Уточняющий вопрос: только при явном коротком продолжении без конкретики (без вызова модели)
_CLARIFICATION_MAX_MESSAGE_LEN = 25
_CLARIFICATION_MIN_LAST_REPLY_LEN = 180
_CLARIFICATION_PHRASES = frozenset(
    {
        "а это?",
        "и что?",
        "а можно по-другому?",
        "а что с этим?",
        "а ещё?",
        "а почему?",
        "???",
        "не понял",
        "не поняла",
        "а дальше?",
        "и?",
        "ну и?",
        "а как?",
        "зачем?",
    }
)
_CLARIFICATION_RESPONSE = (
    "Напиши, пожалуйста, чуть подробнее — о чём именно хочешь узнать? Тогда отвечу точнее."
)


def _is_probably_russian_message(text: str) -> bool:
    """Определить, что сообщение в основном русскоязычное (для RU-вовлечения)."""
    if not text:
        return False
    has_cyrillic = bool(re.search(r"[а-яё]", text.lower()))
    has_latin = bool(re.search(r"[a-z]", text.lower()))
    if has_cyrillic:
        return True
    # Для нейтральных/коротких сообщений без явной латиницы оставляем поведение RU по умолчанию.
    return not has_latin


def _is_farewell_message(text: str) -> bool:
    """Проверка, что пользователь явно прощается (без вопроса)."""
    if not text:
        return False
    normalized = text.lower().strip()
    if "?" in normalized:
        return False
    return any(keyword in normalized for keyword in _FAREWELL_KEYWORDS)


# Фразы, которые промпт запрещает (модель иногда выдаёт их вопреки промпту)
_EXPLAIN_MORE_PATTERNS = (
    "объяснить подробнее",
    "рассказать подробнее",
    "хочешь, объясню подробнее",
    "разберём подробнее",
    "давай разберём подробнее",
    "хочешь узнать подробнее",
)


def _strip_explain_more_tail(text: str) -> str:
    """
    Удаляет фразы «объяснить подробнее?» и подобные из хвоста ответа.
    Промпт запрещает заканчивать ответ приглашением «давай разберём подробнее» —
    даём полный разбор сразу.
    """
    if not text:
        return text
    lines = text.rstrip().split("\n")
    # Проверяем последние 2 строки
    for _ in range(2):
        if not lines:
            break
        last = lines[-1].strip().lower()
        if any(pat in last for pat in _EXPLAIN_MORE_PATTERNS):
            lines.pop()
            # Убираем пустые строки-разделители после удаления
            while lines and not lines[-1].strip():
                lines.pop()
        else:
            break
    return "\n".join(lines)


# Минимальная длина ответа, при которой добавляется вопрос-вовлечение
_MIN_RESPONSE_LEN_FOR_ENGAGEMENT = 200


def add_random_engagement_question(response: str) -> str:
    """
    Добавляет случайный вопрос для вовлечения в конец ответа.
    Не добавляет вопрос к коротким ответам (<200 символов), чтобы не быть навязчивым.

    Args:
        response: Исходный ответ AI

    Returns:
        str: Ответ с добавленным случайным вопросом (отделенным пустой строкой)
    """
    if not response or not response.strip():
        return response

    # Шаг 1: удалить запрещённые «объяснить подробнее?» из хвоста
    response = _strip_explain_more_tail(response)
    if not response or not response.strip():
        return response

    # Не добавляем вопрос к коротким/простым ответам — это навязчиво
    if len(response.strip()) < _MIN_RESPONSE_LEN_FOR_ENGAGEMENT:
        return response

    # Варианты вопросов для вовлечения (тон в духе панды: дружеский, без давления)
    engagement_questions = [
        "Спроси меня ещё что-нибудь, мне нравится с тобой общаться!",
        "Есть вопросы посложнее?",
        "Что ещё разберём?",
        "Какой следующий вопрос?",
        "Хочешь задачку на закрепление?",
        "Попробуем разобрать пример?",
        "Продолжаем? Задавай следующий вопрос!",
        "Хочешь ещё что-нибудь узнать по этой теме?",
        "Интересно? Спрашивай дальше!",
        "Давай разберём ещё что-нибудь?",
        "Какую тему возьмём следующей?",
        "Ну как, понятно? Спрашивай, если что!",
    ]

    # Проверяем, нет ли уже вопроса в конце ответа
    response_lower = response.lower().strip()
    question_indicators = [
        "понятно?",
        "спроси меня",
        "есть вопросы",
        "что ещё разберём",
        "какой следующий",
        "задавай",
        "спрашивай",
    ]

    last_part = response_lower[-150:] if len(response_lower) > 150 else response_lower
    has_existing_question = any(indicator in last_part for indicator in question_indicators)

    if has_existing_question:
        # Если вопрос-вовлечение уже есть — отделяем его пустой строкой
        response_stripped = response.strip()
        if not response_stripped.endswith("\n\n") and "\n\n" not in response_stripped[-50:]:
            lines = response_stripped.split("\n")
            if len(lines) > 1 and lines[-1].strip():
                return "\n".join(lines[:-1]) + "\n\n" + lines[-1]
        return response

    # Добавляем случайный вопрос
    random_question = random.choice(engagement_questions)

    # ВСЕГДА отделяем вопрос пустой строкой от основного текста
    response_stripped = response.strip()
    while response_stripped.endswith("\n"):
        response_stripped = response_stripped.rstrip("\n")

    return f"{response_stripped}\n\n{random_question}"
