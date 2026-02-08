"""
Тесты для модуля переводчика (Yandex Translate интеграция).

Проверяет:
- Команду /translate
- Выбор языков
- Перевод текста
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Chat, InlineKeyboardMarkup, Message, User

from bot.handlers.translate import translate_command


@pytest.mark.asyncio
async def test_translate_command():
    """Тест команды /translate - должна показать выбор языков."""
    # Mock объектов
    message = MagicMock(spec=Message)
    message.answer = AsyncMock()
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 12345

    state = MagicMock()

    # Вызываем команду
    await translate_command(message, state)

    # Проверяем что ответ отправлен
    message.answer.assert_called_once()

    # Проверяем содержимое ответа
    call_args = message.answer.call_args
    response_text = call_args.args[0] if call_args.args else call_args.kwargs.get("text", "")
    assert "Переводчик PandaPal" in response_text

    # Проверяем что есть клавиатура с выбором языков
    assert "reply_markup" in call_args.kwargs
    keyboard = call_args.kwargs["reply_markup"]
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем что есть кнопки для разных языков
    buttons = keyboard.inline_keyboard
    assert len(buttons) >= 3  # Минимум 3 ряда кнопок

    # Проверяем наличие английского языка
    first_row = buttons[0]
    assert any("Английский" in btn.text for btn in first_row)


@pytest.mark.asyncio
async def test_translate_service_initialization():
    """Тест инициализации сервиса перевода."""
    from bot.services.translate_service import get_translate_service

    service = get_translate_service()

    assert service is not None
    assert service.api_key
    assert service.folder_id
    assert service.translate_url
    assert len(service.SUPPORTED_LANGUAGES) == 5  # ru, en, de, fr, es


@pytest.mark.asyncio
async def test_translate_supported_languages():
    """Тест списка поддерживаемых языков."""
    from bot.services.translate_service import get_translate_service

    service = get_translate_service()

    languages = service.get_supported_languages()

    assert "ru" in languages
    assert "en" in languages
    assert "de" in languages
    assert "fr" in languages
    assert "es" in languages


@pytest.mark.asyncio
async def test_translate_language_names():
    """Тест получения названий языков."""
    from bot.services.translate_service import get_translate_service

    service = get_translate_service()

    assert service.get_language_name("ru") == "Русский"
    assert service.get_language_name("en") == "Английский"
    assert service.get_language_name("de") == "Немецкий"
    assert service.get_language_name("fr") == "Французский"
    assert service.get_language_name("es") == "Испанский"
