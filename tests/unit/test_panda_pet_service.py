"""
Unit-тесты для bot/services/panda_pet_service.py.
Проверка get_or_create, get_state, feed/play/sleep и кулдаунов без реального API.
"""

import os
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, PandaPet, User
from bot.services.panda_pet_service import PandaPetService


@contextmanager
def temp_db_session():
    """Временная SQLite БД и сессия с коммитом при выходе."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()
        try:
            os.close(db_fd)
            os.unlink(db_path)
        except (PermissionError, OSError):
            pass


class TestPandaPetService:
    """Unit-тесты PandaPetService."""

    def test_get_or_create_creates_with_defaults(self):
        """Без питомца создаётся запись с дефолтами (hunger=60, mood=70, energy=50)."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222333,
                first_name="Test",
                username="u",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            pet = svc.get_or_create(111222333)
            db.flush()

            assert pet.hunger == 60
            assert pet.mood == 70
            assert pet.energy == 50
            assert pet.consecutive_visit_days == 1

    def test_get_or_create_returns_same_pet_on_second_call(self):
        """Повторный вызов возвращает того же питомца."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222334,
                first_name="Test",
                username="u2",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            pet1 = svc.get_or_create(111222334)
            db.flush()
            pet2 = svc.get_or_create(111222334)
            assert pet1.id == pet2.id
            assert pet2.hunger == 60

    def test_get_or_create_increments_consecutive_visit_days_on_new_day(self):
        """При визите в новый день увеличивается consecutive_visit_days."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222335,
                first_name="Test",
                username="u3",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            pet = svc.get_or_create(111222335)
            db.flush()
            assert pet.consecutive_visit_days == 1

            pet.last_visit_date = datetime.now(UTC) - timedelta(days=1)
            db.flush()

            pet2 = svc.get_or_create(111222335)
            assert pet2.consecutive_visit_days == 2

    def test_get_or_create_user_not_found_raises(self):
        """Для несуществующего telegram_id (нет User в БД) — ValueError('User not found')."""
        with temp_db_session() as db:
            svc = PandaPetService(db)
            with pytest.raises(ValueError, match="User not found"):
                svc.get_or_create(999000999)

    def test_get_state_returns_full_shape(self):
        """get_state возвращает dict с hunger, mood, energy, can_*, consecutive_visit_days, achievements."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222336,
                first_name="Test",
                username="u4",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            state = svc.get_state(111222336)

            assert state["hunger"] == 60
            assert state["mood"] == 70
            assert state["energy"] == 50
            assert state["can_feed"] is True
            assert state["can_play"] is True
            assert state["can_sleep"] is True
            assert "consecutive_visit_days" in state
            assert "achievements" in state
            assert isinstance(state["achievements"], dict)

    def test_feed_increases_hunger_and_sets_cooldown(self):
        """feed увеличивает hunger (не более 100), обновляет last_fed_at; can_feed False до кулдауна."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222337,
                first_name="Test",
                username="u5",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            state = svc.feed(111222337)
            assert state["hunger"] == 85
            assert state["can_feed"] is False
            assert state["last_fed_at"] is not None

    def test_feed_second_call_before_cooldown_raises(self):
        """Повторный feed до истечения FEED_COOLDOWN — ValueError."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222338,
                first_name="Test",
                username="u6",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            svc.feed(111222338)
            with pytest.raises(ValueError, match="30 минут"):
                svc.feed(111222338)

    def test_play_updates_mood_energy_and_cooldown(self):
        """play увеличивает mood, снижает energy; повторный до кулдауна — ValueError."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222339,
                first_name="Test",
                username="u7",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            state = svc.play(111222339)
            assert state["mood"] == 90
            assert state["energy"] == 40
            assert state["can_play"] is False

            with pytest.raises(ValueError, match="раз в час"):
                svc.play(111222339)

    def test_sleep_increases_energy_and_cooldown(self):
        """sleep увеличивает energy; повторный до кулдауна — ValueError."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222340,
                first_name="Test",
                username="u8",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            state = svc.sleep(111222340)
            assert state["energy"] == 80
            assert state["can_sleep"] is False

            with pytest.raises(ValueError, match="2 часа"):
                svc.sleep(111222340)

    def test_feed_hunger_capped_at_100(self):
        """Кормление не поднимает hunger выше 100."""
        with temp_db_session() as db:
            u = User(
                telegram_id=111222341,
                first_name="Test",
                username="u9",
                user_type="child",
                age=10,
                grade=5,
            )
            db.add(u)
            db.commit()

            svc = PandaPetService(db)
            pet = svc.get_or_create(111222341)
            pet.hunger = 90
            db.flush()

            state = svc.feed(111222341)
            assert state["hunger"] == 100
