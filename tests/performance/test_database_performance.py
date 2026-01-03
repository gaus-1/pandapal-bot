"""
Тесты производительности базы данных
Проверка что БД работает быстро даже при большой нагрузке
"""

import os
import tempfile
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.history_service import ChatHistoryService
from bot.services.user_service import UserService


class TestDatabasePerformance:
    """Тесты производительности БД"""

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

    @pytest.fixture
    def test_user(self, real_db_session):
        """Создаёт тестового пользователя"""
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=999888777,
            username="test_perf_user",
            first_name="Тестовый",
            last_name="Производительность",
        )
        real_db_session.commit()
        return user

    @pytest.mark.performance
    def test_user_creation_performance(self, real_db_session):
        """Тест: создание пользователя должно быть быстрым (< 50ms)"""
        user_service = UserService(real_db_session)

        start_time = time.time()
        user = user_service.get_or_create_user(
            telegram_id=123456789,
            username="perf_test",
            first_name="Test",
        )
        real_db_session.commit()
        elapsed_time = (time.time() - start_time) * 1000  # в миллисекундах

        assert (
            elapsed_time < 50
        ), f"Создание пользователя заняло {elapsed_time}ms, должно быть < 50ms"
        assert user is not None

    @pytest.mark.performance
    def test_message_insertion_performance(self, real_db_session, test_user):
        """Тест: вставка сообщения должна быть быстрой (< 30ms)"""
        history_service = ChatHistoryService(real_db_session)

        start_time = time.time()
        message = history_service.add_message(test_user.telegram_id, "Тестовое сообщение", "user")
        real_db_session.commit()
        elapsed_time = (time.time() - start_time) * 1000

        assert elapsed_time < 30, f"Вставка сообщения заняла {elapsed_time}ms, должно быть < 30ms"

    @pytest.mark.performance
    def test_batch_message_insertion(self, real_db_session, test_user):
        """Тест: вставка 100 сообщений должна быть быстрой (< 2 секунды)"""
        history_service = ChatHistoryService(real_db_session)

        start_time = time.time()
        for i in range(100):
            history_service.add_message(test_user.telegram_id, f"Сообщение {i}", "user")
            if i % 10 == 0:  # Коммитим каждые 10 сообщений
                real_db_session.commit()
        real_db_session.commit()
        elapsed_time = time.time() - start_time

        assert elapsed_time < 2, f"Вставка 100 сообщений заняла {elapsed_time}s, должно быть < 2s"

    @pytest.mark.performance
    def test_message_retrieval_performance(self, real_db_session, test_user):
        """Тест: получение истории должна быть быстрой (< 100ms)"""
        history_service = ChatHistoryService(real_db_session)

        # Создаём 50 сообщений
        for i in range(50):
            history_service.add_message(test_user.telegram_id, f"Сообщение {i}", "user")
        real_db_session.commit()

        # Получаем историю
        start_time = time.time()
        history = history_service.get_recent_history(test_user.telegram_id, limit=50)
        elapsed_time = (time.time() - start_time) * 1000

        assert elapsed_time < 100, f"Получение истории заняло {elapsed_time}ms, должно быть < 100ms"
        assert len(history) == 50

    @pytest.mark.performance
    def test_user_lookup_performance(self, real_db_session):
        """Тест: поиск пользователя должен быть быстрым (< 20ms)"""
        user_service = UserService(real_db_session)

        # Создаём пользователя
        user = user_service.get_or_create_user(
            telegram_id=555666777,
            username="lookup_test",
            first_name="Test",
        )
        real_db_session.commit()

        # Ищем пользователя
        start_time = time.time()
        found_user = user_service.get_user_by_telegram_id(555666777)
        elapsed_time = (time.time() - start_time) * 1000

        assert elapsed_time < 20, f"Поиск пользователя занял {elapsed_time}ms, должно быть < 20ms"
        assert found_user is not None
        assert found_user.telegram_id == 555666777
