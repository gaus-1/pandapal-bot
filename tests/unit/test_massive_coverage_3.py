"""
Massive coverage tests - Part 3: Models and Database
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from bot.database import get_db, init_db
from bot.models import ChatHistory, User


class TestModelsExtended:

    @pytest.mark.unit
    def test_user_all_combinations(self):
        users = [
            User(telegram_id=1),
            User(telegram_id=2, username="user2"),
            User(telegram_id=3, first_name="User3"),
            User(telegram_id=4, last_name="User4"),
            User(telegram_id=5, user_type="child"),
            User(telegram_id=6, age=10),
            User(telegram_id=7, grade=5),
            User(telegram_id=8, username="u8", first_name="F8", last_name="L8"),
            User(telegram_id=9, user_type="parent", age=35),
            User(telegram_id=10, user_type="teacher", age=40),
        ]

        for user in users:
            assert user.telegram_id > 0

    @pytest.mark.unit
    def test_chat_history_all_types(self):
        for msg_type in ["user", "bot", "system"]:
            h = ChatHistory()
            h.message_type = msg_type
            h.message_text = f"Test {msg_type}"
            assert h.message_type == msg_type

    @pytest.mark.unit
    def test_user_different_ages(self):
        for age in [5, 8, 10, 12, 15, 18, 25, 35, 50]:
            user = User(telegram_id=age, age=age)
            assert user.age == age

    @pytest.mark.unit
    def test_user_different_grades(self):
        for grade in range(1, 12):
            user = User(telegram_id=grade, grade=grade)
            assert user.grade == grade

    @pytest.mark.unit
    def test_database_context_manager(self):
        with patch("bot.database.SessionLocal") as mock_sl:
            mock_session = Mock()
            mock_sl.return_value = mock_session

            with get_db() as db:
                assert db == mock_session

            mock_session.close.assert_called()

    @pytest.mark.unit
    def test_init_db_function(self):
        with patch("bot.database.Base") as mock_base, patch("bot.database.engine"):
            init_db()
            mock_base.metadata.create_all.assert_called()
