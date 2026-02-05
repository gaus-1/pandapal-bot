"""
Unit-тесты для bot/services/referral_service.py.
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base
from bot.services.referral_service import (
    parse_referrer_from_ref,
    resolve_referrer_telegram_id,
    is_referrer,
)


@pytest.fixture(scope="function")
def real_db_session():
    """Сессия БД (sqlite) с таблицами из Base (включая referrers)."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


class TestParseReferrerFromRef:
    """Парсинг ref_<telegram_id>."""

    def test_valid_ref(self):
        assert parse_referrer_from_ref("ref_729414271") == 729414271
        assert parse_referrer_from_ref("ref_1") == 1
        assert parse_referrer_from_ref("ref_123456789") == 123456789

    def test_invalid_ref(self):
        assert parse_referrer_from_ref(None) is None
        assert parse_referrer_from_ref("") is None
        assert parse_referrer_from_ref("   ") is None
        assert parse_referrer_from_ref("ref_") is None
        assert parse_referrer_from_ref("ref_abc") is None
        assert parse_referrer_from_ref("ref_-1") is None
        assert parse_referrer_from_ref("games") is None
        assert parse_referrer_from_ref("ref_123_extra") is None

    def test_stripped(self):
        assert parse_referrer_from_ref("  ref_729414271  ") == 729414271


class TestIsReferrerAndResolve:
    """Проверка whitelist и resolve (требуют БД)."""

    @pytest.fixture
    def db_with_referrer(self, real_db_session):
        """Сессия с одним реферером 729414271."""
        from bot.models import Referrer

        r = Referrer(telegram_id=729414271, comment="Преподаватель")
        real_db_session.add(r)
        real_db_session.commit()
        return real_db_session

    def test_is_referrer_true(self, db_with_referrer):
        assert is_referrer(db_with_referrer, 729414271) is True

    def test_is_referrer_false(self, db_with_referrer):
        assert is_referrer(db_with_referrer, 999) is False

    def test_resolve_valid_ref(self, db_with_referrer):
        assert resolve_referrer_telegram_id(db_with_referrer, "ref_729414271") == 729414271

    def test_resolve_invalid_ref_not_in_whitelist(self, db_with_referrer):
        assert resolve_referrer_telegram_id(db_with_referrer, "ref_999") is None

    def test_resolve_none_ref(self, db_with_referrer):
        assert resolve_referrer_telegram_id(db_with_referrer, None) is None
