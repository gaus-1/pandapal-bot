"""
Massive coverage tests - Part 3: Database functions only

⚠️ ВНИМАНИЕ: Тесты моделей перенесены в test_models.py
Оставлены только тесты функций базы данных
"""

from unittest.mock import Mock, patch

import pytest

from bot.database import get_db, init_db


class TestDatabaseFunctions:
    """Тесты функций базы данных"""

    @pytest.mark.unit
    def test_database_context_manager(self):
        """Тест context manager для БД"""
        with patch("bot.database.SessionLocal") as mock_sl:
            mock_session = Mock()
            mock_sl.return_value = mock_session

            with get_db() as db:
                assert db == mock_session

            mock_session.close.assert_called()

    @pytest.mark.unit
    def test_init_db_function(self):
        """Тест функции инициализации БД"""
        with patch("bot.database.Base") as mock_base, patch("bot.database.engine"):
            init_db()
            mock_base.metadata.create_all.assert_called()
