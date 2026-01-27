"""
Фикстуры для тестов новостей.
"""

from datetime import datetime

import pytest


@pytest.fixture
def sample_news_item():
    """Фикстура для примера новости."""
    return {
        "title": "Интересная новость про животных",
        "content": "Сегодня ученые обнаружили новый вид панд в лесах Китая. Эти панды очень дружелюбные и любят играть.",
        "url": "https://example.com/news/1",
        "source": "test_source",
        "published_date": datetime.now(),
        "image_url": None,
    }


@pytest.fixture
def sample_news_items():
    """Фикстура для списка новостей."""
    return [
        {
            "title": "Новость про игры",
            "content": "Вышла новая интересная игра для детей",
            "source": "test",
            "category": "игры",
        },
        {
            "title": "Новость про спорт",
            "content": "Юные спортсмены победили на соревнованиях",
            "source": "test",
            "category": "спорт",
        },
        {
            "title": "Новость про животных",
            "content": "В зоопарке родился детеныш панды",
            "source": "test",
            "category": "животные",
        },
    ]


@pytest.fixture
def mock_news_api_response():
    """Фикстура для mock ответа API."""
    return {
        "news": [
            {
                "title": "Тестовая новость",
                "text": "Содержание новости",
                "url": "https://test.com",
                "publish_date": "2026-01-27T12:00:00Z",
            }
        ]
    }
