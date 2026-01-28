"""
Тесты высоконагруженности системы
Проверка что система выдерживает большую нагрузку
"""

import asyncio
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.gamification_service import GamificationService


class TestLoadHandling:
    """Тесты высоконагруженности"""

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
    def test_users(self, real_db_session):
        """Создаёт несколько тестовых пользователей"""
        users = []
        for i in range(10):
            user = User(
                telegram_id=999888777 + i,
                username=f"test_load_user_{i}",
                first_name=f"Тестовый{i}",
                last_name="Нагрузка",
                user_type="child",
                age=10,
                grade=5,
            )
            real_db_session.add(user)
            users.append(user)
        real_db_session.commit()
        return users

    @pytest.mark.performance
    def test_concurrent_messages(self, real_db_session, test_users):
        """Тест: обработка сообщений от нескольких пользователей одновременно"""
        gamification_service = GamificationService(real_db_session)

        def process_user_messages(user):
            """Обработка сообщений для одного пользователя"""
            for i in range(10):
                gamification_service.process_message(user.telegram_id, f"Сообщение {i}")
                real_db_session.commit()

        # Обрабатываем сообщения от всех пользователей параллельно
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_user_messages, user) for user in test_users]
            # Ждем завершения всех задач
            for future in futures:
                future.result()  # Проверяем что нет исключений

        # Проверяем что все сообщения обработаны
        for user in test_users:
            progress = gamification_service.get_or_create_progress(user.telegram_id)
            assert (
                progress.points >= 10
            ), f"Пользователь {user.telegram_id} должен иметь минимум 10 XP"

    @pytest.mark.performance
    def test_many_achievements_check(self, real_db_session, test_users):
        """Тест: проверка достижений для многих пользователей"""
        gamification_service = GamificationService(real_db_session)

        # Создаем историю для всех пользователей
        for user in test_users:
            for i in range(50):
                message = ChatHistory(
                    user_telegram_id=user.telegram_id,
                    message_text=f"Сообщение {i}",
                    message_type="user",
                )
                real_db_session.add(message)
        real_db_session.commit()

        # Проверяем достижения для всех пользователей
        def check_achievements(user):
            """Проверка достижений для одного пользователя"""
            achievements = gamification_service.get_achievements_with_progress(user.telegram_id)
            return len(achievements)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_achievements, user) for user in test_users]
            results = [future.result() for future in futures]

        # Проверяем что все получили достижения
        assert all(count > 0 for count in results), "Все пользователи должны иметь достижения"
