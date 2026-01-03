"""
Тесты производительности системы геймификации
Проверка что система работает быстро даже при большой нагрузке
"""

import os
import tempfile
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.gamification_service import GamificationService


class TestGamificationPerformance:
    """Тесты производительности геймификации"""

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
        """Создаёт тестового пользователя в БД"""
        user = User(
            telegram_id=999888777,
            username="test_perf_user",
            first_name="Тестовый",
            last_name="Производительность",
            user_type="child",
            age=10,
            grade=5,
        )
        real_db_session.add(user)
        real_db_session.commit()
        return user

    @pytest.mark.performance
    def test_process_message_performance(self, real_db_session, test_user):
        """Тест: обработка сообщения должна быть быстрой (< 100ms)"""
        gamification_service = GamificationService(real_db_session)

        start_time = time.time()
        gamification_service.process_message(test_user.telegram_id, "Тестовое сообщение")
        real_db_session.commit()
        elapsed_time = (time.time() - start_time) * 1000  # в миллисекундах

        assert (
            elapsed_time < 100
        ), f"Обработка сообщения заняла {elapsed_time}ms, должно быть < 100ms"

    @pytest.mark.performance
    def test_batch_messages_performance(self, real_db_session, test_user):
        """Тест: обработка 100 сообщений должна быть быстрой (< 5 секунд)"""
        gamification_service = GamificationService(real_db_session)

        start_time = time.time()
        for i in range(100):
            gamification_service.process_message(test_user.telegram_id, f"Сообщение {i}")
            if i % 10 == 0:  # Коммитим каждые 10 сообщений
                real_db_session.commit()
        real_db_session.commit()
        elapsed_time = time.time() - start_time

        assert elapsed_time < 5, f"Обработка 100 сообщений заняла {elapsed_time}s, должно быть < 5s"

    @pytest.mark.performance
    def test_get_achievements_performance(self, real_db_session, test_user):
        """Тест: получение списка достижений должно быть быстрым (< 50ms)"""
        gamification_service = GamificationService(real_db_session)

        # Создаем некоторую историю
        for i in range(50):
            message = ChatHistory(
                user_telegram_id=test_user.telegram_id,
                message_text=f"Сообщение {i}",
                message_type="user",
            )
            real_db_session.add(message)
        real_db_session.commit()

        start_time = time.time()
        achievements = gamification_service.get_achievements_with_progress(test_user.telegram_id)
        elapsed_time = (time.time() - start_time) * 1000  # в миллисекундах

        assert (
            elapsed_time < 50
        ), f"Получение достижений заняло {elapsed_time}ms, должно быть < 50ms"
        assert len(achievements) > 0, "Должны быть достижения"

    @pytest.mark.performance
    def test_get_stats_performance(self, real_db_session, test_user):
        """Тест: получение статистики должно быть быстрым (< 100ms)"""
        gamification_service = GamificationService(real_db_session)

        # Создаем большую историю
        for i in range(200):
            message = ChatHistory(
                user_telegram_id=test_user.telegram_id,
                message_text=f"Сообщение {i}",
                message_type="user",
            )
            real_db_session.add(message)
        real_db_session.commit()

        start_time = time.time()
        stats = gamification_service.get_user_stats(test_user.telegram_id)
        elapsed_time = (time.time() - start_time) * 1000  # в миллисекундах

        assert (
            elapsed_time < 100
        ), f"Получение статистики заняло {elapsed_time}ms, должно быть < 100ms"
        assert "total_messages" in stats, "Статистика должна содержать total_messages"
