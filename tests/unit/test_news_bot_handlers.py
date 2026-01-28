"""
Unit тесты для handlers новостного бота.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, User as TelegramUser
from aiogram.fsm.context import FSMContext

from bot.handlers.news_bot import help, news_feed, start


@pytest.fixture
def mock_message():
    """Фикстура для mock сообщения."""
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=TelegramUser)
    message.from_user.id = 123456789
    message.from_user.username = "test_user"
    message.from_user.first_name = "Тест"
    message.from_user.last_name = "Пользователь"
    message.text = "/start"
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
async def test_start_handler(mock_message, mock_state):
    """Тест handler команды /start."""
    with patch("bot.database.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_get_db.return_value.__exit__.return_value = None

        with patch("bot.services.user_service.UserService.get_or_create_user") as mock_user_service:
            mock_user_service.return_value = MagicMock()

            with patch("bot.services.news.repository.NewsRepository.find_recent") as mock_find:
                from bot.models.news import News

                mock_news = MagicMock(spec=News)
                mock_news.id = 1
                mock_news.title = "Тестовая новость"
                mock_news.content = "Содержание"
                mock_news.image_url = None
                mock_find.return_value = [mock_news]

                with patch("bot.services.news_bot.user_preferences_service.UserPreferencesService.mark_news_read"):
                    with patch.object(mock_message, "answer", new_callable=AsyncMock) as mock_answer:
                        with patch.object(mock_message, "answer_photo", new_callable=AsyncMock):
                            await start.cmd_start(mock_message)

                            assert mock_answer.called


@pytest.mark.asyncio
async def test_news_handler(mock_message, mock_state):
    """Тест handler команды /news."""
    with patch("bot.database.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_get_db.return_value.__exit__.return_value = None

        with patch("bot.services.news.repository.NewsRepository.find_recent") as mock_find:
            from bot.models.news import News

            mock_news = MagicMock(spec=News)
            mock_news.id = 1
            mock_news.title = "Тестовая новость"
            mock_news.content = "Содержание"
            mock_news.image_url = None
            mock_find.return_value = [mock_news]

            with patch("bot.services.news_bot.user_preferences_service.UserPreferencesService.mark_news_read"):
                with patch.object(mock_message, "answer", new_callable=AsyncMock) as mock_answer:
                    with patch.object(mock_message, "answer_photo", new_callable=AsyncMock):
                        await news_feed.cmd_news(mock_message)

                        assert mock_answer.called


@pytest.mark.asyncio
async def test_help_handler(mock_message):
    """Тест handler команды /help."""
    with patch.object(mock_message, "answer", new_callable=AsyncMock) as mock_answer:
        await help.cmd_help(mock_message)

        assert mock_answer.called
        # Проверяем, что в ответе есть информация о командах (текст в args или kwargs)
        call_args = mock_answer.call_args
        text = (call_args[1].get("text") or (call_args[0][0] if call_args[0] else "")) or ""
        assert "PandaPal News" in text
