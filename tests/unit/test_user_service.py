"""
Unit тесты для bot/services/user_service.py
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, User
from bot.services.user_service import UserService


class TestUserService:
    """Тесты для UserService"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Реальная БД для тестов"""
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

    def test_get_or_create_user_new(self, real_db_session):
        """Тест создания нового пользователя"""
        service = UserService(real_db_session)

        user = service.get_or_create_user(
            telegram_id=123456, username="test", first_name="Test", last_name="User"
        )

        assert user is not None
        assert user.telegram_id == 123456
        assert user.username == "test"
        assert user.first_name == "Test"
        assert user.last_name == "User"

    def test_get_or_create_user_existing(self, real_db_session):
        """Тест получения существующего пользователя"""
        service = UserService(real_db_session)

        # Создаём пользователя
        user1 = service.get_or_create_user(telegram_id=123456, username="test", first_name="Test")
        real_db_session.commit()

        # Получаем того же пользователя
        user2 = service.get_or_create_user(telegram_id=123456, username="test2", first_name="Test2")

        assert user1.id == user2.id
        assert user2.telegram_id == 123456

    def test_get_user_by_telegram_id(self, real_db_session):
        """Тест получения пользователя по telegram_id"""
        service = UserService(real_db_session)

        # Создаём пользователя
        service.get_or_create_user(telegram_id=123456, username="test", first_name="Test")
        real_db_session.commit()

        # Получаем пользователя
        user = service.get_user_by_telegram_id(123456)
        assert user is not None
        assert user.telegram_id == 123456

    def test_get_user_by_telegram_id_not_found(self, real_db_session):
        """Тест получения несуществующего пользователя"""
        service = UserService(real_db_session)

        user = service.get_user_by_telegram_id(999999)
        assert user is None

    def test_update_user_profile(self, real_db_session):
        """Тест обновления профиля пользователя"""
        service = UserService(real_db_session)

        # Создаём пользователя
        service.get_or_create_user(telegram_id=123456, username="test", first_name="Test")
        real_db_session.commit()

        # Обновляем профиль
        service.update_user_profile(telegram_id=123456, age=12, grade=6, user_type="child")
        real_db_session.commit()

        # Проверяем обновление
        user = service.get_user_by_telegram_id(123456)
        assert user.age == 12
        assert user.grade == 6
        assert user.user_type == "child"

    def test_get_or_create_user_with_referrer_new(self, real_db_session):
        """Новый пользователь с ref получает referrer_telegram_id."""
        service = UserService(real_db_session)
        user = service.get_or_create_user(
            telegram_id=123456,
            username="test",
            first_name="Test",
            last_name="User",
            referrer_telegram_id=729414271,
        )
        real_db_session.commit()
        assert user.referrer_telegram_id == 729414271

    def test_get_or_create_user_with_referrer_existing_no_ref(self, real_db_session):
        """Существующий пользователь без реферера получает ref при следующем заходе."""
        service = UserService(real_db_session)
        service.get_or_create_user(telegram_id=123456, username="a", first_name="A")
        real_db_session.commit()
        user2 = service.get_or_create_user(
            telegram_id=123456,
            username="b",
            first_name="B",
            referrer_telegram_id=729414271,
        )
        real_db_session.commit()
        assert user2.referrer_telegram_id == 729414271

    def test_get_or_create_user_referrer_not_overwritten(self, real_db_session):
        """У существующего пользователя с реферером ref не перезаписывается."""
        service = UserService(real_db_session)
        service.get_or_create_user(
            telegram_id=123456,
            username="a",
            first_name="A",
            referrer_telegram_id=729414271,
        )
        real_db_session.commit()
        user2 = service.get_or_create_user(
            telegram_id=123456,
            username="b",
            first_name="B",
            referrer_telegram_id=999,
        )
        real_db_session.commit()
        assert user2.referrer_telegram_id == 729414271
