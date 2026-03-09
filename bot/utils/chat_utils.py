"""
Утилиты для анализа сообщений и работы с чатом.
Вынесены из обработчиков для устранения дублирования кода.
"""

import re


def extract_user_name_from_message(user_message: str) -> tuple[str | None, bool]:
    """
    Извлечение имени пользователя из сообщения.

    Args:
        user_message: Сообщение пользователя

    Returns:
        tuple: (имя или None, является ли отказом)
    """
    cleaned_message = user_message.strip().lower()
    cleaned_message = re.sub(r"[.,!?;:]+$", "", cleaned_message)

    refusal_patterns = [
        r"не\s+хочу",
        r"не\s+скажу",
        r"не\s+буду",
        r"не\s+назову",
        r"не\s+хочу\s+называть",
        r"не\s+буду\s+называть",
        r"не\s+хочу\s+говорить",
        r"не\s+скажу\s+имя",
        r"не\s+хочу\s+сказать",
    ]
    is_refusal = any(re.search(pattern, cleaned_message) for pattern in refusal_patterns)
    if is_refusal:
        return None, True

    common_words = [
        "да",
        "нет",
        "ок",
        "окей",
        "хорошо",
        "спасибо",
        "привет",
        "пока",
        "здравствуй",
        "здравствуйте",
        "как дела",
        "что",
        "как",
        "почему",
        "где",
        "когда",
        "кто",
    ]

    cleaned_for_check = cleaned_message.split()[0] if cleaned_message.split() else cleaned_message

    is_like_name = (
        2 <= len(cleaned_for_check) <= 15
        and re.match(r"^[а-яёА-ЯЁa-zA-Z-]+$", cleaned_for_check)
        and cleaned_for_check not in common_words
        and len(cleaned_message.split()) <= 2
    )

    if is_like_name:
        return cleaned_message.split()[0].capitalize(), False

    return None, False


def count_user_messages_since_name_mention(history: list[dict], user_first_name: str | None) -> int:
    """
    Подсчет количества сообщений пользователя с момента последнего упоминания его имени ИИ.

    Args:
        history: История чата в формате [{"role": "...", "text": "..."}, ...]
        user_first_name: Имя пользователя

    Returns:
        int: Количество сообщений от пользователя (роль "user")
    """
    user_message_count = 0
    if user_first_name:
        # Ищем последнее упоминание имени AI (в любом виде)
        last_name_mention_index = -1
        for i, msg in enumerate(history):
            if (
                msg.get("role") == "assistant"
                and user_first_name.lower() in msg.get("text", "").lower()
            ):
                last_name_mention_index = i
                break

        # Если упоминание найдено
        if last_name_mention_index >= 0:
            # Считаем только user-сообщения
            user_message_count = sum(
                1 for msg in history[last_name_mention_index + 1 :] if msg.get("role") == "user"
            )
        else:
            # Если имени нет в ответах ИИ - считаем все
            user_message_count = sum(1 for msg in history if msg.get("role") == "user")
    else:
        # Если имени у юзера вообще нет - считаем все
        user_message_count = sum(1 for msg in history if msg.get("role") == "user")

    return user_message_count
