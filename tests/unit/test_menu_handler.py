"""
Unit тесты для bot/handlers/menu.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers.menu import (
    back_to_main_menu,
    help_type_selected,
    homework_help,
    show_progress,
    subject_selected,
)


class TestMenuHandler:
    """Тесты для обработчика меню"""

    @pytest.fixture
    def mock_message(self):
        """Мок сообщения"""
        message = MagicMock()
        message.from_user.id = 123456789
        message.from_user.username = "test_user"
        message.text = "📚 Помощь с уроками"
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_callback(self):
        """Мок callback query"""
        callback = MagicMock()
        callback.from_user.id = 123456789
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.message.answer = AsyncMock()
        callback.answer = AsyncMock()
        callback.data = "subject:math"
        return callback

    @pytest.fixture
    def fsm_context(self):
        """FSM контекст для тестов"""
        storage = MemoryStorage()
        return FSMContext(storage=storage, key=MagicMock())

    @pytest.mark.asyncio
    async def test_homework_help(self, mock_message, fsm_context):
        """Тест обработки кнопки помощи с уроками"""
        await homework_help(mock_message, fsm_context)

        # Проверяем что ответ отправлен
        mock_message.answer.assert_called_once()

        # Проверяем что в ответе есть текст про помощь с уроками
        call_args = mock_message.answer.call_args
        text = call_args.kwargs.get("text", "")
        assert "Помощь" in text or "помощь" in text.lower() or "уроками" in text.lower()

        # Проверяем что есть клавиатура
        assert "reply_markup" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_subject_selected(self, mock_callback, fsm_context):
        """Тест выбора предмета"""
        mock_callback.data = "subject:math"

        await subject_selected(mock_callback, fsm_context)

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что предмет сохранен в состояние
        data = await fsm_context.get_data()
        assert "subject" in data
        assert data["subject"] == "math"

        # Проверяем что callback ответил
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_type_selected(self, mock_callback, fsm_context):
        """Тест выбора типа помощи"""
        mock_callback.data = "help:solve"

        # Устанавливаем предмет в состояние
        await fsm_context.update_data(subject="math", subject_name="🔢 Математика")

        await help_type_selected(mock_callback, fsm_context)

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что режим помощи сохранен
        data = await fsm_context.get_data()
        assert "help_mode" in data
        assert data["help_mode"] == "solve"

        # Проверяем что callback ответил
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_progress(self, mock_message, fsm_context):
        """Тест показа прогресса"""
        mock_message.text = "📊 Мой прогресс"

        with patch("bot.handlers.menu.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.handlers.menu.UserService") as mock_user_service:
                mock_service = MagicMock()
                mock_user = MagicMock()
                mock_user.first_name = "Тест"
                mock_user.grade = 5
                mock_user.age = 10
                mock_service.get_user_by_telegram_id.return_value = mock_user
                mock_user_service.return_value = mock_service

                await show_progress(mock_message, fsm_context)

                # Проверяем что ответ отправлен
                mock_message.answer.assert_called_once()

                # Проверяем что в ответе есть информация о прогрессе
                call_args = mock_message.answer.call_args
                text = call_args.kwargs.get("text", "")
                assert "прогресс" in text.lower() or "Прогресс" in text

    @pytest.mark.asyncio
    async def test_back_to_main_menu(self, mock_callback, fsm_context):
        """Тест возврата в главное меню"""
        mock_callback.data = "menu:main"

        # Устанавливаем какое-то состояние
        await fsm_context.set_state("some_state")
        await fsm_context.update_data(subject="math")

        await back_to_main_menu(mock_callback, fsm_context)

        # Проверяем что состояние очищено
        state = await fsm_context.get_state()
        assert state is None

        data = await fsm_context.get_data()
        assert len(data) == 0

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что callback ответил
        mock_callback.answer.assert_called_once()
