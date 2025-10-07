"""
Massive coverage tests - Part 1: Handlers
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aiogram.types import Message, CallbackQuery, User as TgUser, Chat
from aiogram.fsm.context import FSMContext
from bot.handlers.ai_chat import start_ai_chat, handle_ai_message
from bot.handlers.settings import show_settings, settings_age, SettingsStates
from bot.handlers.admin_commands import router as admin_router
from bot.handlers.parent_dashboard import router as parent_router
from bot.handlers.parental_control import router as control_router
from bot.models import User


@pytest.fixture
def msg():
    m = Mock(spec=Message)
    m.from_user = Mock(spec=TgUser)
    m.from_user.id = 123
    m.from_user.username = "test"
    m.from_user.first_name = "Test"
    m.chat = Mock(spec=Chat)
    m.chat.id = 123
    m.answer = AsyncMock()
    m.bot = Mock()
    m.bot.send_chat_action = AsyncMock()
    return m


@pytest.fixture
def st():
    s = Mock(spec=FSMContext)
    s.clear = AsyncMock()
    s.set_state = AsyncMock()
    s.get_state = AsyncMock(return_value=None)
    return s


class TestAllHandlers:

    @pytest.mark.asyncio
    async def test_start_ai_chat_handler(self, msg, st):
        await start_ai_chat(msg, st)
        msg.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_settings_user_found(self, msg):
        with (
            patch("bot.handlers.settings.get_db") as mock_db,
            patch("bot.handlers.settings.UserService") as mock_service,
        ):

            mock_db_context = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_db_context

            user = User(telegram_id=123, first_name="Test", age=10, user_type="child")
            mock_service_inst = Mock()
            mock_service_inst.get_user_by_telegram_id.return_value = user
            mock_service.return_value = mock_service_inst

            await show_settings(msg)
            msg.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_settings_age_callback(self, st):
        cb = Mock(spec=CallbackQuery)
        cb.message = Mock()
        cb.message.edit_text = AsyncMock()
        cb.answer = AsyncMock()

        await settings_age(cb, st)
        cb.message.edit_text.assert_called_once()

    @pytest.mark.unit
    def test_all_routers_exist(self):
        assert admin_router is not None
        assert parent_router is not None
        assert control_router is not None

    @pytest.mark.unit
    def test_settings_states_exist(self):
        assert SettingsStates.waiting_for_age is not None
        assert SettingsStates.waiting_for_name is not None
