"""
Сервис проактивных сообщений панды в Mini App.

Добавляет в чат сообщения «соскучилась» (24ч без запросов) и напоминания (7 дней).
Тексты учитывают пол пользователя при наличии.
"""

import random
from datetime import UTC, datetime, timedelta
from typing import Literal

# Пороги: 24 часа для «соскучилась», 7 дней для напоминания
PROACTIVE_THRESHOLD_HOURS = 24
PROACTIVE_THRESHOLD_DAYS_REMINDER = 7


def should_add_proactive_message(
    history: list[dict],
    last_user_ts: datetime | None,
) -> tuple[bool, Literal["missed_24h", "reminder_7d"] | None]:
    """
    Нужно ли добавить проактивное сообщение в чат.

    Условия: история не пуста, последнее сообщение в истории — от пользователя,
    и с момента последнего user-сообщения прошло >= 24h (missed_24h) или >= 7d (reminder_7d).

    Args:
        history: Список сообщений [{"role": "user"|"ai", "content": str, ...}, ...].
        last_user_ts: Время последнего сообщения пользователя (из ChatHistory).

    Returns:
        (True, "missed_24h" | "reminder_7d") если нужно добавить, иначе (False, None).
    """
    if not history or last_user_ts is None:
        return False, None

    last_msg = history[-1]
    if last_msg.get("role") != "user":
        return False, None

    now = datetime.now(UTC)
    if last_user_ts.tzinfo is None:
        last_user_ts = last_user_ts.replace(tzinfo=UTC)
    delta = now - last_user_ts

    if delta >= timedelta(days=PROACTIVE_THRESHOLD_DAYS_REMINDER):
        return True, "reminder_7d"
    if delta >= timedelta(hours=PROACTIVE_THRESHOLD_HOURS):
        return True, "missed_24h"
    return False, None


def get_proactive_message(
    message_type: Literal["missed_24h", "reminder_7d"],
    user_gender: str | None = None,
) -> str:
    """
    Текст проактивного сообщения от панды.

    Учитывает пол пользователя для грамматики (обращение/подбадривание).
    """
    if message_type == "missed_24h":
        variants = [
            "От тебя давно вопросов не было — скучно. Напиши, когда будешь готов — разберём что угодно.",
            "Ты давно не писал — я соскучился. Есть вопросы по учёбе?",
            "Давно не общались. Заходи, разберём любую тему.",
        ]
        if user_gender and user_gender.lower() == "female":
            variants = [
                "От тебя давно вопросов не было — скучно. Напиши, когда будешь готова — разберём что угодно.",
                "Ты давно не писала — я соскучился. Есть вопросы по учёбе?",
                "Давно не общались. Заходи, разберём любую тему.",
            ]
    else:
        variants = [
            "Привет! Я скучаю по нашим беседам. Может, нужна помощь с домашкой? Заходи!",
            "Давно не заходил — у меня много интересного. Давай позанимаемся?",
            "Соскучился по нашим разборам. Есть вопросы по учёбе? Заглядывай!",
        ]
        if user_gender and user_gender.lower() == "female":
            variants = [
                "Привет! Я скучаю по нашим беседам. Может, нужна помощь с домашкой? Заходи!",
                "Давно не заходила — у меня много интересного. Давай позанимаемся?",
                "Соскучился по нашим разборам. Есть вопросы по учёбе? Заглядывай!",
            ]
    return random.choice(variants)
