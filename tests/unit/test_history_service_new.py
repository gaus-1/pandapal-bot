"""
Тесты для Chat History Service
Проверка сохранения и получения истории чата
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from bot.models import ChatHistory
from bot.services.history_service import ChatHistoryService


class TestChatHistoryService:
    """Тесты для сервиса истории чата"""

    @pytest.fixture
    def service(self):
        """Создание экземпляра сервиса"""
        return ChatHistoryService()

    @pytest.fixture
    def mock_session(self):
        """Мок сессии базы данных"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.query = Mock()
        return session

    @pytest.mark.unit
    def test_service_init(self, service):
        """Тест инициализации сервиса"""
        assert service is not None

    @pytest.mark.unit
    def test_add_message_user(self, service, mock_session):
        """Тест добавления сообщения пользователя"""
        with patch("bot.services.history_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            service.add_message(
                telegram_id=12345,
                role="user",
                message="Привет!",
                ai_response=None,
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_add_message_assistant(self, service, mock_session):
        """Тест добавления ответа ассистента"""
        with patch("bot.services.history_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            service.add_message(
                telegram_id=12345,
                role="assistant",
                message="",
                ai_response="Привет! Чем могу помочь?",
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_get_recent_history_empty(self, service, mock_session):
        """Тест получения пустой истории"""
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )
        mock_session.query.return_value = mock_query

        with patch("bot.services.history_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = service.get_recent_history(telegram_id=12345, limit=10)

            assert result == []

    @pytest.mark.unit
    def test_get_recent_history_with_messages(self, service, mock_session):
        """Тест получения истории с сообщениями"""
        fake_messages = [
            ChatHistory(
                telegram_id=12345,
                role="user",
                message="Привет",
                timestamp=datetime.now(),
            ),
            ChatHistory(
                telegram_id=12345,
                role="assistant",
                ai_response="Привет! Как дела?",
                timestamp=datetime.now(),
            ),
        ]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            fake_messages
        )
        mock_session.query.return_value = mock_query

        with patch("bot.services.history_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = service.get_recent_history(telegram_id=12345, limit=10)

            assert len(result) == 2
            assert result[0].role == "user"
            assert result[1].role == "assistant"

    @pytest.mark.unit
    def test_get_recent_history_limit(self, service, mock_session):
        """Тест лимита сообщений в истории"""
        fake_messages = [
            ChatHistory(
                telegram_id=12345,
                role="user",
                message=f"Сообщение {i}",
                timestamp=datetime.now(),
            )
            for i in range(5)
        ]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            fake_messages[:3]  # Вернем только 3
        )
        mock_session.query.return_value = mock_query

        with patch("bot.services.history_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            result = service.get_recent_history(telegram_id=12345, limit=3)

            assert len(result) == 3

    @pytest.mark.unit
    def test_clear_history(self, service, mock_session):
        """Тест очистки истории"""
        mock_query = Mock()
        mock_query.filter.return_value.delete.return_value = 5
        mock_session.query.return_value = mock_query

        with patch("bot.services.history_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            service.clear_history(telegram_id=12345)

            mock_query.filter.return_value.delete.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_get_conversation_count(self, service, mock_session):
        """Тест подсчета сообщений"""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 42
        mock_session.query.return_value = mock_query

        with patch("bot.services.history_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            count = service.get_conversation_count(telegram_id=12345)

            assert count == 42

    @pytest.mark.unit
    def test_add_message_with_metadata(self, service, mock_session):
        """Тест добавления сообщения с метаданными"""
        with patch("bot.services.history_service.get_db_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session

            service.add_message(
                telegram_id=12345,
                role="user",
                message="Помоги с математикой",
                ai_response=None,
                user_age=10,
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
