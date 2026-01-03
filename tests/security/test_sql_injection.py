"""
РЕАЛЬНЫЕ тесты защиты от SQL инъекций
Проверка что все входные данные валидируются и экранируются
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from bot.models import Base, User
from bot.services.user_service import UserService


class TestSQLInjectionProtection:
    """Тесты защиты от SQL инъекций"""

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

    def test_sql_injection_in_username(self, real_db_session):
        """Тест: SQL инъекция в username должна быть безопасной"""
        user_service = UserService(real_db_session)

        # Попытка SQL инъекции в username
        malicious_username = "'; DROP TABLE users; --"
        telegram_id = 999888111

        # Создаём пользователя с опасным username
        user = user_service.get_or_create_user(
            telegram_id=telegram_id,
            username=malicious_username,
            first_name="Test",
            last_name="User",
        )
        real_db_session.commit()

        # Проверяем что таблица users всё ещё существует
        result = real_db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        )
        table_exists = result.fetchone() is not None
        assert table_exists, "Таблица users должна существовать после SQL инъекции"

        # Проверяем что username сохранён как строка, а не выполнен как SQL
        retrieved_user = user_service.get_user_by_telegram_id(telegram_id)
        assert retrieved_user is not None
        assert (
            retrieved_user.username == malicious_username
        ), "Username должен быть сохранён как строка"

    def test_sql_injection_in_first_name(self, real_db_session):
        """Тест: SQL инъекция в first_name должна быть безопасной"""
        user_service = UserService(real_db_session)

        # Попытка SQL инъекции
        malicious_name = "Robert'); DROP TABLE users; --"
        telegram_id = 999888222

        user = user_service.get_or_create_user(
            telegram_id=telegram_id,
            username="test_user",
            first_name=malicious_name,
            last_name="User",
        )
        real_db_session.commit()

        # Проверяем что таблица существует
        result = real_db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        )
        assert result.fetchone() is not None, "Таблица должна существовать"

        # Проверяем что имя сохранено корректно
        retrieved_user = user_service.get_user_by_telegram_id(telegram_id)
        assert retrieved_user.first_name == malicious_name

    def test_sql_injection_in_message_text(self, real_db_session):
        """Тест: SQL инъекция в message_text должна быть безопасной"""
        from bot.models import ChatHistory

        # Попытка SQL инъекции в сообщении
        malicious_message = "'; DELETE FROM users WHERE '1'='1'; --"

        message = ChatHistory(
            user_telegram_id=999888333,
            message_text=malicious_message,
            message_type="user",
        )
        real_db_session.add(message)
        real_db_session.commit()

        # Проверяем что таблица users существует
        result = real_db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        )
        assert result.fetchone() is not None, "Таблица users должна существовать"

        # Проверяем что сообщение сохранено как строка
        stmt = select(ChatHistory).where(ChatHistory.user_telegram_id == 999888333)
        retrieved_message = real_db_session.scalar(stmt)
        assert retrieved_message is not None
        assert retrieved_message.message_text == malicious_message

    def test_union_based_sql_injection(self, real_db_session):
        """Тест: защита от UNION-based SQL инъекций"""
        user_service = UserService(real_db_session)

        # Создаём нормального пользователя
        user1 = user_service.get_or_create_user(
            telegram_id=111111,
            username="normal_user",
            first_name="Normal",
            last_name="User",
        )
        real_db_session.commit()

        # Попытка UNION инъекции через username
        malicious_username = "admin' UNION SELECT * FROM users WHERE '1'='1"

        user2 = user_service.get_or_create_user(
            telegram_id=222222,
            username=malicious_username,
            first_name="Hacker",
            last_name="User",
        )
        real_db_session.commit()

        # Проверяем что оба пользователя созданы независимо
        user1_retrieved = user_service.get_user_by_telegram_id(111111)
        user2_retrieved = user_service.get_user_by_telegram_id(222222)

        assert user1_retrieved is not None
        assert user2_retrieved is not None
        assert user1_retrieved.username == "normal_user"
        assert user2_retrieved.username == malicious_username

    def test_boolean_based_sql_injection(self, real_db_session):
        """Тест: защита от boolean-based SQL инъекций"""
        user_service = UserService(real_db_session)

        # Попытка boolean инъекции
        malicious_input = "admin' OR '1'='1"

        user = user_service.get_or_create_user(
            telegram_id=333333,
            username=malicious_input,
            first_name="Test",
            last_name="User",
        )
        real_db_session.commit()

        # Проверяем что пользователь создан с корректным username
        retrieved_user = user_service.get_user_by_telegram_id(333333)
        assert retrieved_user.username == malicious_input
        # Проверяем что не создались лишние пользователи
        stmt = select(func.count(User.id))
        total_users = real_db_session.scalar(stmt)
        assert total_users == 1, "Должен быть только один пользователь"

    def test_time_based_sql_injection(self, real_db_session):
        """Тест: защита от time-based SQL инъекций"""
        user_service = UserService(real_db_session)

        # Попытка time-based инъекции
        malicious_input = "admin'; WAITFOR DELAY '00:00:05'; --"

        start_time = time.time()
        user = user_service.get_or_create_user(
            telegram_id=444444,
            username=malicious_input,
            first_name="Test",
            last_name="User",
        )
        real_db_session.commit()
        elapsed_time = time.time() - start_time

        # Запрос должен выполниться быстро (без задержки)
        assert elapsed_time < 1.0, "Запрос не должен содержать задержку из SQL инъекции"

        # Проверяем что username сохранён как строка
        retrieved_user = user_service.get_user_by_telegram_id(444444)
        assert retrieved_user.username == malicious_input
