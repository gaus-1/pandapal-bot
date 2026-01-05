"""
Тесты для модуля обратной связи (Yandex Forms интеграция).

Проверяет:
- Команду /feedback
- Структуру формы и ссылки
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Chat, InlineKeyboardMarkup, Message, User

from bot.handlers.feedback import FEEDBACK_FORM_URL, feedback_command


@pytest.mark.asyncio
async def test_feedback_command():
    """Тест команды /feedback - должна отправить форму обратной связи."""
    # Mock объектов
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.from_user.username = "test_user"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 12345

    # Вызываем команду
    await feedback_command(message)

    # Проверяем что ответ отправлен
    message.answer.assert_called_once()

    # Проверяем содержимое ответа
    call_args = message.answer.call_args
    response_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
    assert "Помоги улучшить PandaPal" in response_text

    # Проверяем что есть клавиатура с кнопкой
    assert "reply_markup" in call_args.kwargs
    keyboard = call_args.kwargs["reply_markup"]
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем URL формы
    button = keyboard.inline_keyboard[0][0]
    assert button.text == "📝 Оставить отзыв"
    assert "forms.yandex.ru" in button.url
    assert button.url == FEEDBACK_FORM_URL


@pytest.mark.asyncio
async def test_feedback_url_format():
    """Тест что URL формы имеет правильный формат."""
    assert FEEDBACK_FORM_URL.startswith("https://")
    assert "forms.yandex.ru" in FEEDBACK_FORM_URL
    assert "/cloud/" in FEEDBACK_FORM_URL
