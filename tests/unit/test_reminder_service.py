"""
Unit тесты для ReminderService.
Проверяем отправку напоминаний неактивным пользователям.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.models import User
from bot.services.reminder_service import ReminderService


class TestReminderService:
    """Тесты для ReminderService"""

    @pytest.fixture
    def mock_user(self):
        """Мок пользователя"""
        user = Mock(spec=User)
        user.telegram_id = 123456789
        user.id = 1
        user.is_active = True
        user.last_activity = datetime.utcnow() - timedelta(days=8)
        user.reminder_sent_at = None
        return user

    @pytest.fixture
    def mock_bot(self):
        """Мок Telegram бота"""
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        return bot

    def test_get_inactive_users_no_users(self):
        """Тест когда нет неактивных пользователей"""
        with patch("bot.services.reminder_service.get_db") as mock_get_db:
            mock_db = Mock()
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value.__enter__.return_value = mock_db

            users = ReminderService.get_inactive_users()

        assert len(users) == 0

    def test_get_inactive_users_found_users(self, mock_user):
        """Тест поиска неактивных пользователей"""
        with patch("bot.services.reminder_service.get_db") as mock_get_db:
            mock_db = Mock()
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [mock_user]
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value.__enter__.return_value = mock_db

            users = ReminderService.get_inactive_users()

        assert len(users) == 1
        assert users[0].telegram_id == mock_user.telegram_id

    @pytest.mark.asyncio
    async def test_send_reminder_success(self, mock_bot, mock_user):
        """Тест успешной отправки напоминания"""
        with patch("bot.services.reminder_service.get_db") as mock_get_db:
            mock_db = Mock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result
            mock_get_db.return_value.__enter__.return_value = mock_db

            result = await ReminderService.send_reminder(mock_bot, mock_user)

        assert result is True
        mock_bot.send_message.assert_called_once()
        assert mock_user.reminder_sent_at is not None

    @pytest.mark.asyncio
    async def test_send_reminder_error(self, mock_bot, mock_user):
        """Тест обработки ошибки при отправке"""
        mock_bot.send_message.side_effect = Exception("Telegram API error")

        with patch("bot.services.reminder_service.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db

            result = await ReminderService.send_reminder(mock_bot, mock_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_process_reminders_success(self, mock_bot, mock_user):
        """Тест обработки всех напоминаний"""
        with patch.object(ReminderService, "get_inactive_users", return_value=[mock_user]):
            with patch.object(ReminderService, "send_reminder", return_value=True) as mock_send:
                stats = await ReminderService.process_reminders(mock_bot)

        assert stats["total"] == 1
        assert stats["sent"] == 1
        assert stats["failed"] == 0
        mock_send.assert_called_once_with(mock_bot, mock_user)

    @pytest.mark.asyncio
    async def test_process_reminders_partial_failure(self, mock_bot, mock_user):
        """Тест когда часть напоминаний не отправлена"""
        mock_user2 = Mock(spec=User)
        mock_user2.telegram_id = 987654321

        with patch.object(
            ReminderService, "get_inactive_users", return_value=[mock_user, mock_user2]
        ):
            with patch.object(
                ReminderService, "send_reminder", side_effect=[True, False]
            ) as mock_send:
                stats = await ReminderService.process_reminders(mock_bot)

        assert stats["total"] == 2
        assert stats["sent"] == 1
        assert stats["failed"] == 1

    def test_reminder_messages_not_empty(self):
        """Тест что есть сообщения для напоминаний"""
        assert len(ReminderService.REMINDER_MESSAGES) > 0
        assert all(isinstance(msg, str) for msg in ReminderService.REMINDER_MESSAGES)
        assert all(len(msg) > 0 for msg in ReminderService.REMINDER_MESSAGES)
