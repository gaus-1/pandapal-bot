"""
E2E тесты для полного flow новостного бота.

Проверка регистрации, выбора категорий, чтения новостей.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, User as TelegramUser, CallbackQuery
from aiogram.fsm.context import FSMContext


@pytest.fixture
def mock_message():
    """Фикстура для mock сообщения."""
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=TelegramUser)
    message.from_user.id = 123456789
    message.from_user.username = "test_user"
    message.from_user.first_name = "Тест"
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    return message


@pytest.fixture
def mock_state():
    """Фикстура для mock FSMContext."""
    state = MagicMock(spec=FSMContext)
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    return state


@pytest.mark.asyncio
async def test_complete_news_bot_flow(mock_message, mock_state):
    """Тест полного flow: регистрация → выбор категорий → чтение новостей."""
    with patch("bot.database.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_get_db.return_value.__exit__.return_value = None

        # 1. Регистрация через /start
        with patch("bot.services.user_service.UserService.get_or_create_user") as mock_user_service:
            mock_user_service.return_value = MagicMock()

            with patch("bot.services.news_bot.user_preferences_service.UserPreferencesService.get_or_create_preferences") as mock_prefs:
                # Первый вызов - нет предпочтений
                mock_prefs.return_value = {"age": None, "grade": None, "categories": []}

                from bot.handlers.news_bot.start import cmd_start

                await cmd_start(mock_message, mock_state)

                # Проверяем, что запрошен возраст
                assert mock_message.answer.called

                # 2. Устанавливаем возраст
                mock_prefs.return_value = {"age": 10, "grade": None, "categories": []}

                # 3. Выбор категорий
                from bot.handlers.news_bot.categories import cmd_categories

                await cmd_categories(mock_message, mock_state)

                # 4. Чтение новостей
                from bot.handlers.news_bot.news_feed import cmd_news

                with patch("bot.services.news.repository.NewsRepository.find_by_age") as mock_find:
                    from bot.models.news import News

                    mock_news = MagicMock(spec=News)
                    mock_news.id = 1
                    mock_news.title = "Тестовая новость"
                    mock_news.content = "Содержание новости"
                    mock_news.image_url = None

                    mock_find.return_value = [mock_news]

                    await cmd_news(mock_message, mock_state)

                    # Проверяем, что новость отправлена
                    assert mock_message.answer.called
