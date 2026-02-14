"""
Сервис реакций панды в чате по тону сообщения пользователя.

Выбор одной из 4 картинок (happy, eating, offended, questioning)
только для фидбека — не смешивать с реакциями в играх.
"""

import random

from loguru import logger

from bot.config.panda_chat_reactions_data import (
    NEGATIVE_PHRASES,
    POSITIVE_PHRASES,
    REACTIONS_NEGATIVE,
    REACTIONS_POSITIVE,
)


def get_chat_reaction(message: str) -> str | None:
    """
    Определить реакцию панды по тексту сообщения пользователя.

    Позитивный фидбек -> "happy" или "eating" (случайно).
    Негативный фидбек -> "offended" или "questioning" (случайно).
    Иначе -> None (нейтральное/учебное сообщение).

    Args:
        message: Текст сообщения (уже после модерации и нормализации).

    Returns:
        Одно из "happy", "eating", "offended", "questioning" или None.
    """
    if not message or not isinstance(message, str):
        return None
    text = message.strip().lower()
    if not text:
        return None

    has_positive = any(phrase in text for phrase in POSITIVE_PHRASES)
    has_negative = any(phrase in text for phrase in NEGATIVE_PHRASES)

    if has_positive and not has_negative:
        reaction = random.choice(REACTIONS_POSITIVE)
        logger.debug(f"Реакция чата: позитив -> {reaction}")
        return reaction
    if has_negative and not has_positive:
        reaction = random.choice(REACTIONS_NEGATIVE)
        logger.debug(f"Реакция чата: негатив -> {reaction}")
        return reaction
    return None
