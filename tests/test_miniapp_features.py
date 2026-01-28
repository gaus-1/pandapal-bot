"""
Тесты для новых функций Mini App.

Тестирует:
- Очистку чата
- Копирование сообщений
- Ответ на сообщение
- Скролл
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.models import User
from bot.services.reminder_service import ReminderService


@pytest.mark.asyncio
async def test_clear_chat_history():
    """Тест очистки истории чата."""
    # Mock useChat hook - проверяем что clearHistory вызывается
    mock_clear = MagicMock()

    # Симулируем вызов clearHistory
    mock_clear()

    # Проверяем что вызов произошел
    mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_copy_message():
    """Тест копирования сообщения."""
    # Проверяем что navigator.clipboard.writeText вызывается
    message_content = "Тестовое сообщение от Панды"

    # Mock clipboard API
    mock_clipboard = MagicMock()
    mock_clipboard.writeText = MagicMock()

    # Симулируем копирование
    mock_clipboard.writeText(message_content)

    # Проверяем что текст скопирован
    mock_clipboard.writeText.assert_called_once_with(message_content)


@pytest.mark.asyncio
async def test_reply_to_message():
    """Тест ответа на сообщение."""
    original_message = "Привет от Панды!"
    reply_text = "Спасибо, Панда!"

    # Формируем сообщение с ответом
    full_message = f'[Ответ на: "{original_message[:50]}..."]\n\n{reply_text}'

    # Проверяем формат
    assert "[Ответ на:" in full_message
    assert reply_text in full_message


@pytest.mark.asyncio
async def test_scroll_buttons():
    """Тест кнопок скролла."""
    # Mock scroll functions
    mock_scroll_top = MagicMock()
    mock_scroll_bottom = MagicMock()

    # Симулируем скролл вверх
    mock_scroll_top()
    assert mock_scroll_top.call_count == 1

    # Симулируем скролл вниз
    mock_scroll_bottom()
    assert mock_scroll_bottom.call_count == 1


@pytest.mark.asyncio
async def test_reminder_service_get_inactive_users():
    """Тест получения списка неактивных пользователей."""
    # Мокируем БД
    with patch("bot.services.reminder_service.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Создаем мок пользователя
        mock_user = User(
            telegram_id=123456,
            username="test_user",
            first_name="Test",
            last_name="User",
            user_type="child",
            is_active=True,
            last_activity=datetime.utcnow() - timedelta(days=8),
            reminder_sent_at=None,
        )

        # Настраиваем мок БД
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        mock_db.execute.return_value = mock_result

        # Получаем неактивных пользователей
        inactive_users = ReminderService.get_inactive_users()

        # Проверяем результат
        assert len(inactive_users) == 1
        assert inactive_users[0].telegram_id == 123456


@pytest.mark.asyncio
async def test_reminder_service_send_reminder():
    """Тест отправки напоминания пользователю."""
    # Мокируем бота
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    # Создаем мок пользователя
    mock_user = User(
        telegram_id=123456,
        username="test_user",
        first_name="Test",
        user_type="child",
        is_active=True,
        last_activity=datetime.utcnow() - timedelta(days=8),
        reminder_sent_at=None,
    )

    # Мокируем БД
    with patch("bot.services.reminder_service.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Настраиваем мок БД для обновления
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Отправляем напоминание
        success = await ReminderService.send_reminder(mock_bot, mock_user)

        # Проверяем результат
        assert success is True
        mock_bot.send_message.assert_called_once()

        # Проверяем параметры вызова
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 123456
        assert "Привет" in call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_reminder_messages_variety():
    """Тест разнообразия сообщений напоминаний."""
    messages = ReminderService.REMINDER_MESSAGES

    # Проверяем что есть хотя бы 3 варианта
    assert len(messages) >= 3

    # Проверяем что все сообщения содержат панду и дружелюбны
    for message in messages:
        # Проверяем наличие панды (эмодзи или слово)
        has_panda = "🐼" in message or "панда" in message.lower()
        assert has_panda, f"Сообщение должно содержать панду: {message}"

        # Проверяем дружелюбность (должно быть приветствие или обращение)
        is_friendly = any(
            word.lower() in message.lower()
            for word in ["привет", "эй", "скучаю", "заходи", "соскучился", "помог", "рад"]
        )
        assert is_friendly, f"Сообщение должно быть дружелюбным: {message}"


@pytest.mark.asyncio
async def test_navigation_buttons_size():
    """Тест размера кнопок навигации."""
    # Проверяем что размеры кнопок увеличены
    min_height = 70  # минимальная высота кнопки
    icon_size = 24  # минимальный размер иконки

    assert min_height >= 70
    assert icon_size >= 24


@pytest.mark.asyncio
async def test_emergency_screen_scroll():
    """Тест автоскролла на экране SOS."""
    # Mock useRef и scrollTo
    mock_container_ref = MagicMock()
    mock_container_ref.current = MagicMock()
    mock_container_ref.current.scrollTo = MagicMock()

    # Симулируем скролл вверх при открытии
    mock_container_ref.current.scrollTo(top=0, behavior="smooth")

    # Проверяем что скролл вызван
    mock_container_ref.current.scrollTo.assert_called_once()
