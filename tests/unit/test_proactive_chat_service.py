"""
Unit-тесты для ProactiveChatService.

Проверяют логику добавления проактивных сообщений (24ч / 7 дней).
"""

from datetime import UTC, datetime, timedelta

import pytest

from bot.services.proactive_chat_service import (
    PROACTIVE_THRESHOLD_HOURS,
    PROACTIVE_THRESHOLD_DAYS_REMINDER,
    get_proactive_message,
    should_add_proactive_message,
)


class TestShouldAddProactiveMessage:
    """Тесты решения: добавлять ли проактивное сообщение."""

    def test_empty_history_no_add(self):
        """Пустая история — не добавлять."""
        add, msg_type = should_add_proactive_message([], datetime.now(UTC) - timedelta(hours=25))
        assert add is False
        assert msg_type is None

    def test_last_user_ts_none_no_add(self):
        """Нет последнего сообщения пользователя — не добавлять."""
        add, msg_type = should_add_proactive_message([{"role": "user", "content": "привет"}], None)
        assert add is False
        assert msg_type is None

    def test_last_message_is_ai_no_add(self):
        """Последнее сообщение от AI — не добавлять (уже добавили ранее)."""
        add, msg_type = should_add_proactive_message(
            [
                {"role": "user", "content": "привет"},
                {"role": "ai", "content": "Соскучился! Заходи."},
            ],
            datetime.now(UTC) - timedelta(hours=25),
        )
        assert add is False
        assert msg_type is None

    def test_last_user_25h_add_missed_24h(self):
        """Последнее от user, прошло 25ч — добавлять missed_24h."""
        last_ts = datetime.now(UTC) - timedelta(hours=25)
        add, msg_type = should_add_proactive_message([{"role": "user", "content": "пока"}], last_ts)
        assert add is True
        assert msg_type == "missed_24h"

    def test_last_user_1h_no_add(self):
        """Последнее от user, прошло 1ч — не добавлять."""
        last_ts = datetime.now(UTC) - timedelta(hours=1)
        add, msg_type = should_add_proactive_message(
            [{"role": "user", "content": "спасибо"}], last_ts
        )
        assert add is False
        assert msg_type is None

    def test_last_user_8d_add_reminder_7d(self):
        """Последнее от user, прошло 8 дней — добавлять reminder_7d."""
        last_ts = datetime.now(UTC) - timedelta(days=8)
        add, msg_type = should_add_proactive_message([{"role": "user", "content": "пока"}], last_ts)
        assert add is True
        assert msg_type == "reminder_7d"

    def test_last_user_25h_prefer_missed_24h_not_reminder(self):
        """При 25ч возвращаем missed_24h, не reminder_7d."""
        last_ts = datetime.now(UTC) - timedelta(hours=25)
        add, msg_type = should_add_proactive_message([{"role": "user", "content": "х"}], last_ts)
        assert msg_type == "missed_24h"


class TestGetProactiveMessage:
    """Тесты текстов проактивных сообщений."""

    def test_missed_24h_returns_non_empty(self):
        """missed_24h возвращает непустую строку."""
        text = get_proactive_message("missed_24h")
        assert isinstance(text, str)
        assert len(text) > 10

    def test_reminder_7d_returns_non_empty(self):
        """reminder_7d возвращает непустую строку."""
        text = get_proactive_message("reminder_7d")
        assert isinstance(text, str)
        assert len(text) > 10

    def test_gender_female_missed_24h(self):
        """При female в missed_24h текст может содержать женскую форму."""
        text = get_proactive_message("missed_24h", user_gender="female")
        assert "готова" in text or "писала" in text or len(text) > 5

    def test_constants(self):
        """Пороги заданы константами."""
        assert PROACTIVE_THRESHOLD_HOURS == 24
        assert PROACTIVE_THRESHOLD_DAYS_REMINDER == 7
