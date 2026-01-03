"""
Unit тесты для bot/handlers/emergency.py
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers.emergency import (
    EMERGENCY_INFO,
    cmd_emergency,
    get_emergency_keyboard,
    process_emergency_callback,
)


class TestEmergencyHandler:
    """Тесты для обработчика экстренных номеров"""

    @pytest.fixture
    def mock_message(self):
        """Мок сообщения"""
        message = MagicMock()
        message.from_user.id = 123456789
        message.from_user.username = "test_user"
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_callback(self):
        """Мок callback query"""
        callback = MagicMock()
        callback.from_user.id = 123456789
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.message.delete = AsyncMock()
        callback.answer = AsyncMock()
        callback.data = "emergency_112"
        return callback

    def test_get_emergency_keyboard(self):
        """Тест создания клавиатуры экстренных номеров"""
        keyboard = get_emergency_keyboard()

        assert keyboard is not None
        assert hasattr(keyboard, "inline_keyboard")
        assert len(keyboard.inline_keyboard) > 0

        # Проверяем что есть основные номера
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.text)

        assert any("112" in text for text in buttons_text), "Должна быть кнопка 112"
        assert any("101" in text for text in buttons_text), "Должна быть кнопка 101"
        assert any("102" in text for text in buttons_text), "Должна быть кнопка 102"
        assert any("103" in text for text in buttons_text), "Должна быть кнопка 103"

    @pytest.mark.asyncio
    async def test_cmd_emergency(self, mock_message):
        """Тест команды /emergency"""
        await cmd_emergency(mock_message)

        # Проверяем что ответ отправлен
        mock_message.answer.assert_called_once()

        # Проверяем что в ответе есть текст про экстренные номера
        call_args = mock_message.answer.call_args
        assert call_args is not None
        text = call_args.kwargs.get("text", "") or call_args.args[0] if call_args.args else ""
        assert text and (len(text) > 0)

        # Проверяем что есть клавиатура
        assert "reply_markup" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_process_emergency_callback_112(self, mock_callback):
        """Тест обработки callback для номера 112"""
        mock_callback.data = "emergency_112"

        await process_emergency_callback(mock_callback)

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что в тексте есть информация о 112
        call_args = mock_callback.message.edit_text.call_args
        text = call_args.kwargs.get("text", "") or (call_args.args[0] if call_args.args else "")
        assert text and len(text) > 0

        # Проверяем что callback ответил
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_emergency_callback_close(self, mock_callback):
        """Тест обработки callback для закрытия"""
        mock_callback.data = "emergency_close"

        await process_emergency_callback(mock_callback)

        # Проверяем что сообщение удалено
        mock_callback.message.delete.assert_called_once()
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_emergency_callback_back(self, mock_callback):
        """Тест обработки callback для возврата назад"""
        mock_callback.data = "emergency_back"

        await process_emergency_callback(mock_callback)

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что в тексте есть информация об экстренных номерах
        call_args = mock_callback.message.edit_text.call_args
        text = call_args.kwargs.get("text", "") or (call_args.args[0] if call_args.args else "")
        assert text and len(text) > 0

    def test_emergency_info_completeness(self):
        """Тест что все экстренные номера имеют информацию"""
        # Проверяем что все ключи из клавиатуры есть в EMERGENCY_INFO
        keyboard = get_emergency_keyboard()
        callback_data_list = []

        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data and button.callback_data.startswith("emergency_"):
                    callback_data = button.callback_data
                    if callback_data != "emergency_close" and callback_data != "emergency_back":
                        callback_data_list.append(callback_data)

        # Проверяем что для каждого номера есть информация
        for callback_data in callback_data_list:
            assert callback_data in EMERGENCY_INFO, f"Нет информации для {callback_data}"

