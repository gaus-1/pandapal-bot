"""
Unit-тесты проверки лимита 30 запросов (Premium).

Критично: после 30 запросов пользователь не получает ответы (текст, аудио, фото),
даже после очистки чата и перезапуска бота. Счётчик в daily_request_counts.
"""

import os
import tempfile
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, DailyRequestCount, User
from bot.services.premium_features_service import PremiumFeaturesService


class TestPremiumLimitEnforcement:
    """Проверка блокировки после 30 запросов."""

    @pytest.fixture(scope="function")
    def db_session(self):
        """Сессия БД (SQLite)."""
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

    @pytest.fixture
    def free_user(self, db_session):
        """Бесплатный пользователь без подписки."""
        user = User(telegram_id=900001, username="free_user", first_name="Free")
        db_session.add(user)
        db_session.commit()
        return user

    def test_can_make_ai_request_under_limit(self, db_session, free_user):
        """До 30 запросов can_make_ai_request возвращает True."""
        _ = free_user
        service = PremiumFeaturesService(db_session)
        can_request, reason = service.can_make_ai_request(900001)
        assert can_request is True
        assert reason is None

    def test_can_make_ai_request_after_30_blocks(self, db_session, free_user):
        """После 30 запросов can_make_ai_request возвращает False."""
        _ = free_user
        now = datetime.now(UTC)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        rec = DailyRequestCount(
            user_telegram_id=900001,
            date=today,
            request_count=30,
            last_request_at=now,
        )
        db_session.add(rec)
        db_session.commit()

        service = PremiumFeaturesService(db_session)
        can_request, reason = service.can_make_ai_request(900001)
        assert can_request is False
        assert reason is not None
        assert "30" in reason

    def test_increment_request_count_reaches_limit(self, db_session, free_user):
        """increment_request_count возвращает limit_reached=True при 30 запросах."""
        _ = free_user
        service = PremiumFeaturesService(db_session)
        for i in range(30):
            limit_reached, total = service.increment_request_count(900001)
            db_session.commit()
            if i < 29:
                assert limit_reached is False
            else:
                assert limit_reached is True
                assert total >= 30

    def test_get_limit_reached_message_text(self, db_session, free_user):
        """Текст сообщения о лимите не пустой."""
        _ = free_user
        service = PremiumFeaturesService(db_session)
        text = service.get_limit_reached_message_text()
        assert isinstance(text, str)
        assert len(text) > 0
        assert "30" in text
        assert "Premium" in text or "premium" in text
