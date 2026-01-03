"""
Unit тесты для bot/services/history_service.py
"""

import os
import tempfile
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.history_service import ChatHistoryService


class TestHistoryService:
    """Тесты для ChatHistoryService"""

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

    @pytest.fixture
    def test_user(self, real_db_session):
        """Создаёт тестового пользователя"""
        user = User(telegram_id=123456, username="test", first_name="Test")
        real_db_session.add(user)
        real_db_session.commit()
        return user

    def test_add_message(self, real_db_session, test_user):
        """Тест добавления сообщения"""
        service = ChatHistoryService(real_db_session)

        message = service.add_message(
            telegram_id=123456, message_text="Привет!", message_type="user"
        )

        real_db_session.commit()

        assert message is not None
        assert message.message_text == "Привет!"
        assert message.message_type == "user"

        history = service.get_recent_history(123456, limit=10)
        assert len(history) == 1

    def test_get_recent_history(self, real_db_session, test_user):
        """Тест получения истории"""
        service = ChatHistoryService(real_db_session)

        # Добавляем несколько сообщений
        for i in range(5):
            service.add_message(
                telegram_id=123456,
                message_text=f"Сообщение {i}",
                message_type="user" if i % 2 == 0 else "ai",
            )

        real_db_session.commit()

        history = service.get_recent_history(123456, limit=10)
        assert len(history) == 5

    def test_get_recent_history_limit(self, real_db_session, test_user):
        """Тест лимита истории"""
        service = ChatHistoryService(real_db_session)

        # Добавляем 10 сообщений
        for i in range(10):
            service.add_message(
                telegram_id=123456, message_text=f"Сообщение {i}", message_type="user"
            )

        real_db_session.commit()

        # Запрашиваем с лимитом 5
        history = service.get_recent_history(123456, limit=5)
        assert len(history) == 5

    def test_clear_history(self, real_db_session, test_user):
        """Тест очистки истории"""
        service = ChatHistoryService(real_db_session)

        # Добавляем сообщения
        for i in range(5):
            service.add_message(
                telegram_id=123456, message_text=f"Сообщение {i}", message_type="user"
            )

        real_db_session.commit()

        # Очищаем
        deleted = service.clear_history(123456)
        real_db_session.commit()

        assert deleted == 5

        # Проверяем что история пуста
        history = service.get_recent_history(123456, limit=10)
        assert len(history) == 0

    def test_get_conversation_context(self, real_db_session, test_user):
        """Тест получения контекста разговора"""
        service = ChatHistoryService(real_db_session)

        service.add_message(telegram_id=123456, message_text="Привет!", message_type="user")
        service.add_message(telegram_id=123456, message_text="Привет! Как дела?", message_type="ai")
        real_db_session.commit()

        context = service.get_conversation_context(123456)
        assert "Привет!" in context
        assert "User:" in context
        assert "AI:" in context

    def test_get_formatted_history_for_ai(self, real_db_session, test_user):
        """Тест получения истории в формате для AI"""
        service = ChatHistoryService(real_db_session)

        service.add_message(telegram_id=123456, message_text="Вопрос", message_type="user")
        service.add_message(telegram_id=123456, message_text="Ответ", message_type="ai")
        real_db_session.commit()

        formatted = service.get_formatted_history_for_ai(123456)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[1]["role"] == "assistant"

    def test_get_recent_history_empty(self, real_db_session, test_user):
        """Тест получения пустой истории"""
        service = ChatHistoryService(real_db_session)

        history = service.get_recent_history(123456, limit=10)
        assert len(history) == 0

