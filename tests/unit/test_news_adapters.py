"""
Unit тесты для адаптеров новостей.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.news.adapters.age_adapter import AgeNewsAdapter
from bot.services.news.adapters.category_classifier import NewsCategoryClassifier
from bot.services.news.adapters.content_filter import NewsContentFilter


@pytest.mark.asyncio
async def test_age_adapter():
    """Тест AgeNewsAdapter."""
    adapter = AgeNewsAdapter()

    content = "Сложная новость с техническими терминами"

    # Mock YandexGPT ответ
    with patch.object(adapter.yandex_service, "generate_text_response") as mock_generate:
        mock_generate.return_value = "Упрощенная новость для детей"

        adapted = await adapter.adapt_content(content, age=10, grade=5)

        assert adapted == "Упрощенная новость для детей"
        assert mock_generate.called


@pytest.mark.asyncio
async def test_category_classifier():
    """Тест NewsCategoryClassifier."""
    classifier = NewsCategoryClassifier()

    # Mock YandexGPT ответ
    with patch.object(classifier.yandex_service, "generate_text_response") as mock_generate:
        mock_generate.return_value = "игры|ДА"

        category, is_relevant = await classifier.classify("Новость про игру", "Текст новости")

        assert category == "игры"
        assert is_relevant is True


def test_content_filter_keywords():
    """Тест фильтрации по ключевым словам."""
    filter_service = NewsContentFilter()

    # Тест на детский контент
    news_item = {
        "title": "Новость про детей",
        "content": "Интересная новость для школьников",
    }

    is_safe, reason = filter_service._check_keywords(f"{news_item['title']} {news_item['content']}")
    assert is_safe is True

    # Тест на взрослый контент
    news_item_adult = {
        "title": "Политическая новость",
        "content": "Важные политические события",
    }

    is_safe, reason = filter_service._check_keywords(
        f"{news_item_adult['title']} {news_item_adult['content']}"
    )
    assert is_safe is False
    assert "политика" in reason.lower()


def test_content_filter_quality():
    """Тест проверки качества."""
    filter_service = NewsContentFilter()

    # Хорошая новость
    is_good, reason = filter_service._check_quality("Длинный заголовок", "Достаточно длинный текст новости" * 10)
    assert is_good is True

    # Слишком короткая
    is_good, reason = filter_service._check_quality("Короткий", "Мало")
    assert is_good is False
