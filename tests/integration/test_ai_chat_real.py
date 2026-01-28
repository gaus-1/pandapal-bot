"""
РЕАЛЬНЫЕ интеграционные тесты для AI чата с реальной БД
БЕЗ МОКОВ внутренних компонентов - только реальные сервисы

Мокаем только:
- Внешние API (Yandex AI) - если бы вызывался реально
- Telegram Bot API (message) - внешний сервис
"""

import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, ChatHistory, User
from bot.services.history_service import ChatHistoryService
from bot.services.moderation_service import ContentModerationService
from bot.services.user_service import UserService


class TestAIChatReal:
    """Реальные интеграционные тесты AI чата с реальной БД"""

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
    def mock_message(self):
        """Мок только внешнего Telegram API"""
        message = MagicMock()
        message.from_user.id = 123456789
        message.from_user.username = "test_user"
        message.from_user.first_name = "Тест"
        message.from_user.last_name = "Пользователь"
        message.text = "Помоги с математикой"
        message.chat.id = 123456789
        message.answer = AsyncMock()
        message.bot.send_chat_action = AsyncMock()
        return message

    def test_moderation_service_real_blocks_unsafe_content(self, real_db_session):
        """КРИТИЧНО: Реальная модерация блокирует небезопасный контент"""
        # Используем РЕАЛЬНЫЙ сервис модерации, не мок
        moderation = ContentModerationService()

        unsafe_messages = [
            "наркотики",
            "купить оружие",
            "как убить",
            "порно",
        ]

        for msg in unsafe_messages:
            is_safe, reason = moderation.is_safe_content(msg)
            assert is_safe is False, f"ОПАСНО! Контент не заблокирован: {msg}"
            assert reason is not None

    def test_moderation_service_real_allows_safe_content(self, real_db_session):
        """Реальная модерация разрешает безопасный образовательный контент"""
        moderation = ContentModerationService()

        safe_messages = [
            "помоги с математикой",
            "что такое фотосинтез",
            "объясни про дроби",
            "расскажи про планеты",
        ]

        for msg in safe_messages:
            is_safe, reason = moderation.is_safe_content(msg)
            assert is_safe is True, f"Безопасный контент заблокирован: {msg}, причина: {reason}"

    def test_user_service_real_creates_user(self, real_db_session):
        """Реальный UserService создает пользователя в БД"""
        user_service = UserService(real_db_session)

        user = user_service.get_or_create_user(
            telegram_id=111111111,
            username="test_child",
            first_name="Тест",
            last_name="Ребенок",
        )
        user_service.update_user_profile(telegram_id=111111111, age=10, grade=5, user_type="child")
        real_db_session.commit()

        # Проверяем что пользователь реально в БД
        found_user = user_service.get_user_by_telegram_id(111111111)
        assert found_user is not None
        assert found_user.age == 10
        assert found_user.grade == 5
        assert found_user.user_type == "child"

    def test_history_service_real_saves_messages(self, real_db_session):
        """Реальный ChatHistoryService сохраняет сообщения в БД"""
        user_service = UserService(real_db_session)
        history_service = ChatHistoryService(real_db_session)

        # Создаем пользователя
        user = user_service.get_or_create_user(
            telegram_id=222222222, username="test_user2", first_name="Тест2"
        )
        user_service.update_user_profile(telegram_id=222222222, age=12, user_type="child")
        real_db_session.commit()

        # Сохраняем сообщения через реальный сервис
        history_service.add_message(
            telegram_id=222222222, message_text="Привет", message_type="user"
        )
        history_service.add_message(
            telegram_id=222222222, message_text="Ответ AI", message_type="ai"
        )
        real_db_session.commit()

        # Проверяем что сообщения реально в БД
        history = history_service.get_formatted_history_for_ai(222222222)
        assert len(history) >= 2

        # Проверяем через прямой запрос к БД
        messages = (
            real_db_session.query(ChatHistory)
            .filter(ChatHistory.user_telegram_id == 222222222)
            .all()
        )
        assert len(messages) == 2
        assert messages[0].message_text == "Привет"
        assert messages[1].message_text == "Ответ AI"

    def test_moderation_integration_with_real_services(self, real_db_session):
        """Интеграция реальной модерации с реальными сервисами"""
        moderation = ContentModerationService()
        user_service = UserService(real_db_session)

        # Создаем пользователя
        user = user_service.get_or_create_user(
            telegram_id=333333333, username="test_user3", first_name="Тест3"
        )
        user_service.update_user_profile(telegram_id=333333333, age=10, user_type="child")
        real_db_session.commit()

        # Тестируем реальную модерацию
        safe_msg = "помоги с домашним заданием"
        unsafe_msg = "наркотики"

        is_safe1, _ = moderation.is_safe_content(safe_msg)
        is_safe2, reason2 = moderation.is_safe_content(unsafe_msg)

        assert is_safe1 is True
        assert is_safe2 is False
        assert reason2 is not None

        # Проверяем что альтернативный ответ безопасен
        safe_response = moderation.get_safe_response_alternative("blocked_content")
        is_safe_response, _ = moderation.is_safe_content(safe_response)
        assert is_safe_response is True
