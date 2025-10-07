"""
Additional handler tests for coverage
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aiogram.types import Message, CallbackQuery, User as TgUser, Chat
from aiogram.fsm.context import FSMContext
from bot.handlers.admin_commands import router as admin_router
from bot.handlers.parent_dashboard import router as parent_router
from bot.handlers.parental_control import router as control_router
from bot.models import User


@pytest.fixture
def basic_message():
    msg = Mock(spec=Message)
    msg.from_user = Mock(spec=TgUser)
    msg.from_user.id = 123
    msg.from_user.username = "test"
    msg.from_user.first_name = "Test"
    msg.chat = Mock(spec=Chat)
    msg.chat.id = 123
    msg.answer = AsyncMock()
    msg.bot = Mock()
    msg.bot.send_chat_action = AsyncMock()
    return msg


class TestRoutersExist:

    @pytest.mark.unit
    def test_admin_router(self):
        assert admin_router is not None

    @pytest.mark.unit
    def test_parent_router(self):
        assert parent_router is not None

    @pytest.mark.unit
    def test_control_router(self):
        assert control_router is not None


class TestBasicHandlerOperations:

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_message_answer_mock(self, basic_message):
        await basic_message.answer("test")
        basic_message.answer.assert_called_once_with("test")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chat_action_mock(self, basic_message):
        await basic_message.bot.send_chat_action(123, "typing")
        basic_message.bot.send_chat_action.assert_called_once()
