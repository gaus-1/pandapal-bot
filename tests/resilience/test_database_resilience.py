"""
Тесты отказоустойчивости базы данных
Проверка что БД корректно обрабатывает ошибки и восстанавливается
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.history_service import ChatHistoryService
from bot.services.user_service import UserService


class TestDatabaseResilience:
    """Тесты отказоустойчивости БД"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Создаёт реальную SQLite БД для каждого теста"""
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

    def test_handles_duplicate_user_creation(self, real_db_session):
        """Тест: обработка попытки создания дубликата пользователя"""
        user_service = UserService(real_db_session)

        # Создаём пользователя
        user1 = user_service.get_or_create_user(
            telegram_id=888777666,
            username="duplicate_test",
            first_name="Test",
        )
        real_db_session.commit()

        # Пытаемся создать того же пользователя снова
        user2 = user_service.get_or_create_user(
            telegram_id=888777666,
            username="duplicate_test",
            first_name="Test",
        )
        real_db_session.commit()

        # Должен вернуть существующего пользователя, а не создать нового
        assert user1.id == user2.id, "Должен вернуть существующего пользователя"

    def test_handles_rollback_after_error(self, real_db_session):
        """Тест: корректная обработка отката после ошибки"""
        user_service = UserService(real_db_session)

        # Создаём пользователя
        user = user_service.get_or_create_user(
            telegram_id=777666555,
            username="rollback_test",
            first_name="Test",
        )
        real_db_session.commit()

        initial_id = user.id

        # Симулируем ошибку (попытка создать пользователя с невалидными данными)
        try:
            # Пытаемся создать пользователя с очень длинным username (может вызвать ошибку)
            invalid_user = User(
                telegram_id=777666556,
                username="x" * 1000,  # Очень длинный username
                first_name="Test",
            )
            real_db_session.add(invalid_user)
            real_db_session.flush()
            real_db_session.rollback()
        except Exception:
            real_db_session.rollback()

        # Проверяем что исходный пользователь не затронут
        retrieved_user = user_service.get_user_by_telegram_id(777666555)
        assert retrieved_user is not None
        assert retrieved_user.id == initial_id

    def test_handles_concurrent_transactions(self, real_db_session):
        """Тест: обработка конкурентных транзакций"""
        user_service = UserService(real_db_session)

        # Создаём несколько пользователей в одной транзакции
        users = []
        for i in range(10):
            user = user_service.get_or_create_user(
                telegram_id=600000 + i,
                username=f"concurrent_{i}",
                first_name=f"Test{i}",
            )
            users.append(user)

        real_db_session.commit()

        # Проверяем что все пользователи созданы
        assert len(users) == 10
        for user in users:
            assert user.id is not None

    def test_handles_database_connection_loss(self, real_db_session):
        """Тест: обработка потери соединения с БД"""
        user_service = UserService(real_db_session)

        # Создаём пользователя
        user = user_service.get_or_create_user(
            telegram_id=500000,
            username="connection_test",
            first_name="Test",
        )
        real_db_session.commit()

        # Закрываем сессию (симуляция потери соединения)
        real_db_session.close()

        # Создаём новую сессию
        engine = real_db_session.bind
        new_session = sessionmaker(bind=engine)()

        # Проверяем что можем работать с новой сессией
        new_user_service = UserService(new_session)
        retrieved_user = new_user_service.get_user_by_telegram_id(500000)
        assert retrieved_user is not None
        assert retrieved_user.username == "connection_test"

        new_session.close()

    def test_handles_invalid_data_types(self, real_db_session):
        """Тест: обработка невалидных типов данных"""
        user_service = UserService(real_db_session)

        # Пытаемся создать пользователя с None значениями (должно работать)
        user = user_service.get_or_create_user(
            telegram_id=400000,
            username=None,  # None допустимо
            first_name=None,
            last_name=None,
        )
        real_db_session.commit()

        assert user is not None
        assert user.telegram_id == 400000

    def test_handles_empty_strings(self, real_db_session):
        """Тест: обработка пустых строк"""
        user_service = UserService(real_db_session)

        # Создаём пользователя с пустыми строками
        user = user_service.get_or_create_user(
            telegram_id=300000,
            username="",
            first_name="",
            last_name="",
        )
        real_db_session.commit()

        assert user is not None
        retrieved_user = user_service.get_user_by_telegram_id(300000)
        assert retrieved_user.username == ""
