"""
Unit тесты для panda_service.
Проверяет логику тамагочи: decay, состояние, feed/play/sleep.
"""

import os
import tempfile
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, PandaPet, User
from bot.services import panda_service


@pytest.fixture(scope="function")
def db_session():
    """Фикстура для реальной БД."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except (PermissionError, OSError):
        pass


@pytest.fixture
def test_user(db_session):
    """Тестовый пользователь."""
    user = User(
        telegram_id=123456789,
        first_name="Test",
        username="testuser",
        user_type="child",
        age=10,
        grade=5,
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestPandaServiceGetOrCreate:
    """Тесты get_or_create_pet."""

    def test_create_pet_first_time(self, db_session, test_user):
        pet = panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        assert pet is not None
        assert pet.user_telegram_id == test_user.telegram_id
        assert pet.hunger == 60
        assert pet.mood == 70
        assert pet.energy == 50

    def test_get_existing_pet(self, db_session, test_user):
        panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        db_session.commit()
        pet2 = panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        assert pet2.id is not None
        assert pet2.user_telegram_id == test_user.telegram_id


class TestPandaServiceGetState:
    """Тесты get_state."""

    def test_get_state_returns_all_fields(self, db_session, test_user):
        state = panda_service.get_state(db_session, test_user.telegram_id)
        assert "hunger" in state
        assert "mood" in state
        assert "energy" in state
        assert "display_state" in state
        assert "achievements" in state
        assert "can_feed" in state
        assert "can_play" in state
        assert "sleep_need_feed_first" in state
        assert state["hunger"] == 60
        assert state["mood"] == 70
        assert state["display_state"] in (
            "neutral",
            "happy",
            "hungry",
            "wants_bamboo",
            "questioning",
            "excited",
        )

    def test_display_state_hungry_when_low(self, db_session, test_user):
        pet = panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        pet.hunger = 20
        pet.mood = 80
        pet.energy = 60
        db_session.flush()
        state = panda_service.get_state(db_session, test_user.telegram_id)
        assert state["display_state"] == "hungry"


class TestPandaServiceFeed:
    """Тесты feed."""

    def test_feed_increases_hunger(self, db_session, test_user):
        panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        db_session.commit()
        result = panda_service.feed(db_session, test_user.telegram_id)
        assert result["success"] is True
        assert result["state"]["hunger"] >= 60
        assert result["state"]["total_fed_count"] == 1

    def test_feed_twice_in_hour_ok(self, db_session, test_user):
        panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        db_session.commit()
        r1 = panda_service.feed(db_session, test_user.telegram_id)
        assert r1["success"] is True
        r2 = panda_service.feed(db_session, test_user.telegram_id)
        assert r2["success"] is True
        assert r2["state"]["total_fed_count"] == 2

    def test_feed_third_time_in_hour_rejected(self, db_session, test_user):
        panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        db_session.commit()
        panda_service.feed(db_session, test_user.telegram_id)
        panda_service.feed(db_session, test_user.telegram_id)
        r3 = panda_service.feed(db_session, test_user.telegram_id)
        assert r3["success"] is False
        assert r3["message"] == "no_bamboo"


class TestPandaServicePlay:
    """Тесты play."""

    def test_play_increases_mood(self, db_session, test_user):
        panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        db_session.commit()
        result = panda_service.play(db_session, test_user.telegram_id)
        assert result["success"] is True
        assert result["state"]["mood"] >= 70
        assert result["state"]["total_played_count"] == 1


class TestPandaServiceSleep:
    """Тесты put_to_sleep."""

    def test_sleep_need_feed_first_without_feed(self, db_session, test_user):
        panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        db_session.commit()
        result = panda_service.put_to_sleep(db_session, test_user.telegram_id)
        assert result["success"] is False
        assert result.get("need_feed_first") is True

    def test_sleep_after_feed_succeeds(self, db_session, test_user):
        panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        db_session.commit()
        panda_service.feed(db_session, test_user.telegram_id)
        result = panda_service.put_to_sleep(db_session, test_user.telegram_id)
        assert result["success"] is True
        assert result["state"]["energy"] == 100


class TestPandaServiceDecay:
    """Тесты decay (через get_state после обновления updated_at)."""

    def test_decay_applied_on_next_get_state(self, db_session, test_user):
        pet = panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        pet.hunger = 80
        pet.mood = 80
        pet.updated_at = datetime.now(UTC) - timedelta(hours=2)
        db_session.commit()
        state = panda_service.get_state(db_session, test_user.telegram_id)
        assert state["hunger"] < 80
        assert state["mood"] < 80


class TestGetUsersWithSadOrHungryPanda:
    """Тесты get_users_with_sad_or_hungry_panda."""

    def test_returns_user_when_hungry(self, db_session, test_user):
        pet = panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        pet.hunger = 30
        pet.mood = 80
        db_session.commit()
        users = panda_service.get_users_with_sad_or_hungry_panda(db_session)
        assert test_user.telegram_id in users

    def test_returns_empty_when_ok(self, db_session, test_user):
        pet = panda_service.get_or_create_pet(db_session, test_user.telegram_id)
        pet.hunger = 80
        pet.mood = 80
        db_session.commit()
        users = panda_service.get_users_with_sad_or_hungry_panda(db_session)
        assert test_user.telegram_id not in users
