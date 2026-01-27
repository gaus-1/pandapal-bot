"""
Unit тесты для модели News.
"""

import pytest
from datetime import datetime

from bot.models.news import News


def test_news_model_creation():
    """Тест создания модели News."""
    news = News(
        title="Тестовая новость",
        content="Содержание новости",
        source="test_source",
        category="игры",
        age_min=6,
        age_max=15,
        grade_min=1,
        grade_max=9,
    )

    assert news.title == "Тестовая новость"
    assert news.category == "игры"
    assert news.age_min == 6
    assert news.age_max == 15
    # is_active и is_moderated имеют значения по умолчанию из БД
    # При создании объекта без сохранения в БД они могут быть None


def test_news_model_to_dict():
    """Тест преобразования модели в словарь."""
    news = News(
        id=1,
        title="Тест",
        content="Содержание",
        source="test",
        category="игры",
    )

    data = news.to_dict()

    assert data["id"] == 1
    assert data["title"] == "Тест"
    assert data["category"] == "игры"
    assert "created_at" in data


def test_news_model_repr():
    """Тест строкового представления модели."""
    news = News(
        id=1,
        title="Тестовая новость",
        content="Содержание",
        source="test",
        category="игры",
    )

    repr_str = repr(news)
    assert "News" in repr_str
    assert "1" in repr_str
    assert "игры" in repr_str
