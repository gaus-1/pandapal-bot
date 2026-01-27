"""
Unit тесты для модератора новостей.
"""

import pytest
from unittest.mock import MagicMock

from bot.services.news.moderators.content_moderator import NewsContentModerator


def test_news_moderator_safe_content():
    """Тест модерации безопасного контента."""
    moderator = NewsContentModerator()

    # Mock ContentModerationService
    moderator.moderation_service.is_safe_content = MagicMock(return_value=(True, None))

    news_item = {
        "title": "Интересная новость",
        "content": "Детская новость про животных и природу",
    }

    is_safe, reason = moderator.moderate(news_item)

    assert is_safe is True
    assert reason == "OK"


def test_news_moderator_unsafe_content():
    """Тест модерации небезопасного контента."""
    moderator = NewsContentModerator()

    # Mock ContentModerationService
    moderator.moderation_service.is_safe_content = MagicMock(return_value=(False, "Запрещенная тема"))

    news_item = {
        "title": "Небезопасная новость",
        "content": "Контент с запрещенными темами",
    }

    is_safe, reason = moderator.moderate(news_item)

    assert is_safe is False
    assert "модерация" in reason.lower() or "запрещен" in reason.lower()


def test_news_moderator_short_content():
    """Тест модерации слишком короткого контента."""
    moderator = NewsContentModerator()
    moderator.moderation_service.is_safe_content = MagicMock(return_value=(True, None))

    news_item = {
        "title": "Короткий",
        "content": "Мало",  # Слишком короткий
    }

    is_safe, reason = moderator.moderate(news_item)

    assert is_safe is False
    assert "короткий" in reason.lower()
