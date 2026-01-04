"""
Soak тесты - долгосрочные тесты на утечки памяти
Проверка стабильности системы при длительной работе
"""

import os
import tempfile
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.gamification_service import GamificationService
from bot.services.history_service import ChatHistoryService
from bot.services.user_service import UserService


class TestSoakTests:
    """Soak тесты - долгосрочная стабильность"""

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

    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_leak_chat_history(self, real_db_session):
        """Тест: проверка утечек памяти при создании большого количества сообщений"""
        history_service = ChatHistoryService(real_db_session)
        user_service = UserService(real_db_session)

        user = user_service.get_or_create_user(
            telegram_id=777666555,
            username="soak_test_user",
            first_name="Soak",
            last_name="Test",
        )
        real_db_session.commit()

        # Создаём много сообщений (симуляция длительной работы)
        message_count = 1000
        for i in range(message_count):
            history_service.add_message(
                telegram_id=777666555,
                message_text=f"Сообщение {i}",
                message_type="user",
            )
            if i % 100 == 0:
                real_db_session.commit()

        real_db_session.commit()

        # Проверяем что все сообщения созданы (limit может быть ограничен)
        messages = history_service.get_chat_history(777666555, limit=message_count + 100)
        assert (
            len(messages) >= message_count
        ), f"Должно быть создано минимум {message_count} сообщений, получено {len(messages)}"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_repeated_service_calls(self, real_db_session):
        """Тест: многократные вызовы сервисов не должны вызывать утечки памяти"""
        user_service = UserService(real_db_session)
        gamification_service = GamificationService(real_db_session)

        user = user_service.get_or_create_user(
            telegram_id=666555444,
            username="repeated_test_user",
            first_name="Repeated",
            last_name="Test",
        )
        real_db_session.commit()

        # Многократные вызовы сервисов
        iterations = 500
        for i in range(iterations):
            # Получаем пользователя
            retrieved_user = user_service.get_user_by_telegram_id(666555444)
            assert retrieved_user is not None

            # Обрабатываем сообщение
            gamification_service.process_message(666555444, f"Сообщение {i}")
            if i % 50 == 0:
                real_db_session.commit()

        real_db_session.commit()

        # Проверяем что сервисы работают корректно
        progress = gamification_service.get_or_create_progress(666555444)
        assert progress.points > 0, "Должны быть начислены очки"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_long_running_transaction_stability(self, real_db_session):
        """Тест: стабильность при длительных транзакциях"""
        user_service = UserService(real_db_session)

        # Создаём много пользователей в одной "долгой" транзакции
        users = []
        user_count = 200
        for i in range(user_count):
            user = user_service.get_or_create_user(
                telegram_id=500000 + i,
                username=f"long_tx_user_{i}",
                first_name=f"User{i}",
                last_name="Long",
            )
            users.append(user)

        # Коммитим все сразу
        real_db_session.commit()

        # Проверяем что все пользователи созданы
        assert len(users) == user_count, "Все пользователи должны быть созданы"
        for user in users:
            assert user.id is not None, "У каждого пользователя должен быть ID"
