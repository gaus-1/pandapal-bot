"""
Сервис реакций панды в чате по тону сообщения пользователя.

Выбор одной из 4 картинок (happy, eating, offended, questioning)
только для фидбека — не смешивать с реакциями в играх.
"""

import random

from loguru import logger

from bot.config.panda_chat_reactions_data import (
    CONTINUE_AFTER_REACTION,
    NEGATIVE_PHRASES,
    POSITIVE_PHRASES,
    REACTIONS_NEGATIVE,
    REACTIONS_POSITIVE,
)


def _phrase_in_text(phrase: str, text: str) -> bool:
    """Проверка вхождения фразы как отдельного фрагмента (границы слов)."""
    idx = text.find(phrase)
    if idx == -1:
        return False
    before_ok = idx == 0 or not text[idx - 1].isalpha()
    after_ok = idx + len(phrase) == len(text) or not text[idx + len(phrase)].isalpha()
    return before_ok and after_ok


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

    has_positive = any(_phrase_in_text(phrase, text) for phrase in POSITIVE_PHRASES)
    has_negative = any(_phrase_in_text(phrase, text) for phrase in NEGATIVE_PHRASES)

    if has_positive and not has_negative:
        reaction = random.choice(REACTIONS_POSITIVE)
        logger.debug(f"Реакция чата: позитив -> {reaction}")
        return reaction
    if has_negative and not has_positive:
        reaction = random.choice(REACTIONS_NEGATIVE)
        logger.debug(f"Реакция чата: негатив -> {reaction}")
        return reaction
    return None


def add_continue_after_reaction(response: str) -> str:
    """
    После реакции панды добавить предложение продолжить (отдельно от основного текста).

    Добавляет одну из фраз CONTINUE_AFTER_REACTION, если в конце ответа ещё нет
    явного приглашения (вопрос, «спроси», «что ещё» и т.п.).
    """
    if not response or not response.strip():
        return response
    text = response.strip()
    lower = text.lower()
    # Уже есть приглашение в последних ~120 символах
    tail = lower[-120:] if len(lower) > 120 else lower
    if "?" in tail or "спроси" in tail or "что ещё" in tail or "следующ" in tail:
        return response
    suffix = random.choice(CONTINUE_AFTER_REACTION)
    if not text.endswith("\n\n"):
        text = text.rstrip()
        if text and not text.endswith("\n"):
            text += "\n\n"
    return text + suffix
