"""
Ultra coverage tests - handlers deep dive
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aiogram.types import Message, User as TgUser, Chat
from aiogram.fsm.context import FSMContext
from bot.handlers.start import cmd_start
from bot.handlers.ai_chat import handle_ai_message, start_ai_chat
from bot.handlers.settings import show_settings
from bot.models import User


@pytest.fixture
def full_mock_message():
    m = Mock(spec=Message)
    m.message_id = 1
    m.from_user = Mock(spec=TgUser)
    m.from_user.id = 123456789
    m.from_user.username = "testuser"
    m.from_user.first_name = "Test"
    m.from_user.last_name = "User"
    m.from_user.language_code = "ru"
    m.chat = Mock(spec=Chat)
    m.chat.id = 123456789
    m.chat.type = "private"
    m.text = "Test"
    m.answer = AsyncMock()
    m.bot = Mock()
    m.bot.send_chat_action = AsyncMock()
    return m


class TestHandlersDeep:

    @pytest.mark.asyncio
    async def test_start_command_100_users(self, full_mock_message):
        if hasattr(cmd_start, "_last_message_times"):
            cmd_start._last_message_times.clear()

        for user_id in range(100, 200):
            full_mock_message.from_user.id = user_id

            with (
                patch("bot.handlers.start.get_db") as mock_db,
                patch("bot.handlers.start.UserService") as mock_service,
                patch("bot.handlers.start.datetime") as mock_datetime,
            ):

                from datetime import datetime, timedelta

                mock_datetime.now.return_value = datetime.now() + timedelta(seconds=user_id)

                mock_db_context = MagicMock()
                mock_db.return_value.__enter__.return_value = mock_db_context

                user = User(telegram_id=user_id, first_name=f"User{user_id}")
                mock_service_inst = Mock()
                mock_service_inst.get_or_create_user.return_value = user
                mock_service.return_value = mock_service_inst

                state = Mock(spec=FSMContext)
                state.clear = AsyncMock()

                await cmd_start(full_mock_message, state)

    @pytest.mark.asyncio
    async def test_ai_chat_various_messages(self, full_mock_message):
        messages = [
            "Hello",
            "How are you?",
            "Help with math",
            "Explain science",
            "Tell me about history",
            "What is 2+2?",
            "Who are you?",
            "Thanks!",
            "Goodbye",
            "See you later",
        ]

        for msg in messages:
            full_mock_message.text = msg
            await start_ai_chat(full_mock_message, Mock(spec=FSMContext))

    @pytest.mark.asyncio
    async def test_settings_various_users(self, full_mock_message):
        for user_id in range(100):
            full_mock_message.from_user.id = user_id

            with (
                patch("bot.handlers.settings.get_db") as mock_db,
                patch("bot.handlers.settings.UserService") as mock_service,
            ):

                mock_db_context = MagicMock()
                mock_db.return_value.__enter__.return_value = mock_db_context

                user = User(telegram_id=user_id, first_name=f"U{user_id}", age=10)
                mock_service_inst = Mock()
                mock_service_inst.get_user_by_telegram_id.return_value = user
                mock_service.return_value = mock_service_inst

                await show_settings(full_mock_message)
