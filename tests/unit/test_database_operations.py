"""
Complete database operations tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from bot.database import get_db, init_db, SessionLocal, engine, Base


class TestDatabaseOperations:

    @pytest.mark.unit
    def test_get_db_yields_session(self):
        with patch("bot.database.SessionLocal") as mock_session_class:
            mock_session = Mock(spec=Session)
            mock_session_class.return_value = mock_session

            with get_db() as db:
                assert db == mock_session

            mock_session.close.assert_called_once()

    @pytest.mark.unit
    def test_get_db_closes_on_exception(self):
        with patch("bot.database.SessionLocal") as mock_session_class:
            mock_session = Mock(spec=Session)
            mock_session_class.return_value = mock_session

            try:
                with get_db() as db:
                    raise ValueError("Test error")
            except ValueError:
                pass

            mock_session.close.assert_called_once()

    @pytest.mark.unit
    def test_init_db_creates_tables(self):
        with patch("bot.database.Base") as mock_base, patch("bot.database.engine") as mock_engine:
            init_db()
            mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)

    @pytest.mark.unit
    def test_session_local_exists(self):
        assert SessionLocal is not None

    @pytest.mark.unit
    def test_engine_exists(self):
        assert engine is not None

    @pytest.mark.unit
    def test_base_exists(self):
        assert Base is not None
