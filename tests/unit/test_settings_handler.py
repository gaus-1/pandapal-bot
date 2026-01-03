"""
Unit тесты для bot/handlers/settings.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers.settings import (
    SettingsStates,
    cancel_action,
    clear_chat_history,
    confirm_clear_history,
    process_age,
    set_grade,
    settings_age,
    show_main_menu,
    show_settings,
)


class TestSettingsHandler:
    """Тесты для обработчика настроек"""

    @pytest.fixture
    def mock_message(self):
        """Мок сообщения"""
        message = MagicMock()
        message.from_user.id = 123456789
        message.from_user.username = "test_user"
        message.text = "⚙️ Настройки"
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
        callback.data = "settings:age"
        return callback

    @pytest.fixture
    def fsm_context(self):
        """FSM контекст для тестов"""
        storage = MemoryStorage()
        return FSMContext(storage=storage, key=MagicMock())

    @pytest.mark.asyncio
    async def test_show_settings(self, mock_message):
        """Тест показа настроек"""
        with patch("bot.handlers.settings.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.handlers.settings.UserService") as mock_user_service:
                mock_service = MagicMock()
                mock_user = MagicMock()
                mock_user.first_name = "Тест"
                mock_user.age = 10
                mock_user.grade = 5
                mock_user.user_type = "child"
                mock_service.get_user_by_telegram_id.return_value = mock_user
                mock_user_service.return_value = mock_service

                await show_settings(mock_message)

                # Проверяем что ответ отправлен
                mock_message.answer.assert_called_once()

                # Проверяем что в ответе есть информация о настройках
                call_args = mock_message.answer.call_args
                text = call_args.kwargs.get("text", "")
                assert "Настройки" in text or "настройки" in text.lower()

    @pytest.mark.asyncio
    async def test_settings_age(self, mock_callback, fsm_context):
        """Тест начала изменения возраста"""
        await settings_age(mock_callback, fsm_context)

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что состояние установлено
        state = await fsm_context.get_state()
        assert state == SettingsStates.waiting_for_age

        # Проверяем что callback ответил
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_age_valid(self, fsm_context):
        """Тест обработки валидного возраста"""
        message = MagicMock()
        message.from_user.id = 123456789
        message.text = "10"
        message.answer = AsyncMock()

        await fsm_context.set_state(SettingsStates.waiting_for_age)

        with patch("bot.handlers.settings.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.handlers.settings.UserService") as mock_user_service:
                mock_service = MagicMock()
                mock_service.update_user_profile = MagicMock()
                mock_user_service.return_value = mock_service

                await process_age(message, fsm_context)

                # Проверяем что ответ отправлен
                message.answer.assert_called()

                # Проверяем что состояние очищено
                state = await fsm_context.get_state()
                assert state is None

    @pytest.mark.asyncio
    async def test_process_age_invalid(self, fsm_context):
        """Тест обработки невалидного возраста"""
        message = MagicMock()
        message.from_user.id = 123456789
        message.text = "25"  # Слишком большой возраст
        message.answer = AsyncMock()

        await fsm_context.set_state(SettingsStates.waiting_for_age)

        await process_age(message, fsm_context)

        # Проверяем что отправлено сообщение об ошибке
        message.answer.assert_called_once()
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text", "") or (call_args.args[0] if call_args.args else "")
        assert text and len(text) > 0

    @pytest.mark.asyncio
    async def test_set_grade(self, mock_callback):
        """Тест установки класса"""
        mock_callback.data = "grade:5"

        with patch("bot.handlers.settings.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.handlers.settings.UserService") as mock_user_service:
                mock_service = MagicMock()
                mock_service.update_user_profile = MagicMock()
                mock_user_service.return_value = mock_service

                await set_grade(mock_callback)

                # Проверяем что сообщение отредактировано
                mock_callback.message.edit_text.assert_called_once()

                # Проверяем что профиль обновлен
                mock_service.update_user_profile.assert_called_once_with(
                    telegram_id=123456789, grade=5
                )

                # Проверяем что callback ответил
                mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_clear_history(self, mock_callback):
        """Тест подтверждения очистки истории"""
        mock_callback.data = "settings:clear_history"

        await confirm_clear_history(mock_callback)

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что в тексте есть предупреждение
        call_args = mock_callback.message.edit_text.call_args
        text = call_args.kwargs.get("text", "")
        assert "Очистить" in text or "очистить" in text.lower()

        # Проверяем что callback ответил
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_chat_history(self, mock_callback):
        """Тест очистки истории чата"""
        mock_callback.data = "confirm:clear_history"

        with patch("bot.handlers.settings.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_get_db.return_value.__exit__.return_value = None

            with patch("bot.handlers.settings.ChatHistoryService") as mock_history_service:
                mock_service = MagicMock()
                mock_service.clear_history.return_value = 10
                mock_history_service.return_value = mock_service

                await clear_chat_history(mock_callback)

                # Проверяем что история очищена
                mock_service.clear_history.assert_called_once_with(123456789)

                # Проверяем что сообщение отредактировано
                mock_callback.message.edit_text.assert_called_once()

                # Проверяем что callback ответил
                mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_action(self, mock_callback):
        """Тест отмены действия"""
        mock_callback.data = "cancel:clear_history"

        await cancel_action(mock_callback)

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что callback ответил
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_main_menu(self, mock_callback):
        """Тест возврата в главное меню"""
        mock_callback.data = "menu:main"

        await show_main_menu(mock_callback)

        # Проверяем что сообщение отредактировано
        mock_callback.message.edit_text.assert_called_once()

        # Проверяем что callback ответил
        mock_callback.answer.assert_called_once()

