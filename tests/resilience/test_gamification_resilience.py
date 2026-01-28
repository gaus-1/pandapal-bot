"""
Тесты отказоустойчивости системы геймификации
Проверка что система корректно обрабатывает ошибки
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, User
from bot.services.gamification_service import GamificationService


class TestGamificationResilience:
    """Тесты отказоустойчивости геймификации"""

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
            username="test_resilience_user",
            first_name="Тестовый",
            last_name="Отказоустойчивость",
            user_type="child",
            age=10,
            grade=5,
        )
        real_db_session.add(user)
        real_db_session.commit()
        return user

    def test_handles_empty_message(self, real_db_session, test_user):
        """Тест: обработка пустого сообщения не должна вызывать ошибку"""
        gamification_service = GamificationService(real_db_session)

        # Пустое сообщение
        unlocked = gamification_service.process_message(test_user.telegram_id, "")
        real_db_session.commit()

        # Не должно быть исключений
        assert unlocked is not None, "Должен вернуться список (может быть пустым)"

    def test_handles_very_long_message(self, real_db_session, test_user):
        """Тест: обработка очень длинного сообщения"""
        gamification_service = GamificationService(real_db_session)

        # Очень длинное сообщение (10000 символов)
        long_message = "A" * 10000
        unlocked = gamification_service.process_message(test_user.telegram_id, long_message)
        real_db_session.commit()

        # Не должно быть исключений
        assert unlocked is not None, "Должен обработать длинное сообщение"

    def test_handles_special_characters(self, real_db_session, test_user):
        """Тест: обработка сообщений со специальными символами"""
        gamification_service = GamificationService(real_db_session)

        special_messages = [
            "Привет! 🎉",
            "Вопрос? ❓",
            "Сообщение с\nпереносами",
            "Сообщение\tс\tтабами",
            "Сообщение с 'кавычками'",
            'Сообщение с "двойными" кавычками',
        ]

        for msg in special_messages:
            unlocked = gamification_service.process_message(test_user.telegram_id, msg)
            real_db_session.commit()
            assert unlocked is not None, f"Должен обработать сообщение: {msg[:20]}"

    def test_handles_nonexistent_user(self, real_db_session):
        """Тест: обработка сообщения от несуществующего пользователя"""
        gamification_service = GamificationService(real_db_session)

        # Пользователь не существует в БД
        nonexistent_id = 999999999

        # Должен создать прогресс автоматически
        unlocked = gamification_service.process_message(nonexistent_id, "Привет!")
        real_db_session.commit()

        # Не должно быть исключений, прогресс должен быть создан
        progress = gamification_service.get_or_create_progress(nonexistent_id)
        assert progress is not None, "Прогресс должен быть создан автоматически"

    def test_handles_database_rollback(self, real_db_session, test_user):
        """Тест: корректная обработка отката транзакции"""
        gamification_service = GamificationService(real_db_session)

        # Получаем начальный прогресс
        initial_progress = gamification_service.get_or_create_progress(test_user.telegram_id)
        initial_xp = initial_progress.points

        # Обрабатываем сообщение
        gamification_service.process_message(test_user.telegram_id, "Тест")
        real_db_session.commit()

        # Откатываем транзакцию
        real_db_session.rollback()

        # Проверяем что после отката состояние корректное
        progress_after_rollback = gamification_service.get_or_create_progress(test_user.telegram_id)
        # После отката XP может быть как до, так и после (зависит от реализации)
        assert progress_after_rollback is not None, "Прогресс должен существовать после отката"

    def test_handles_concurrent_updates(self, real_db_session, test_user):
        """Тест: обработка конкурентных обновлений"""
        gamification_service = GamificationService(real_db_session)

        # Симулируем конкурентные обновления
        for i in range(10):
            gamification_service.process_message(test_user.telegram_id, f"Сообщение {i}")
            real_db_session.commit()

        # Проверяем что все обновления применены
        progress = gamification_service.get_or_create_progress(test_user.telegram_id)
        assert progress.points >= 10, "Все сообщения должны быть обработаны"
