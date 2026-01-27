"""
Unit тесты для NewsRepository.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from bot.models.news import News
from bot.services.news.repository import NewsRepository


@pytest.fixture
def mock_db():
    """Фикстура для mock сессии БД."""
    db = MagicMock()
    return db


@pytest.fixture
def repository(mock_db):
    """Фикстура для NewsRepository."""
    return NewsRepository(mock_db)


def test_repository_save(repository, mock_db):
    """Тест сохранения новости."""
    news_data = {
        "title": "Тест",
        "content": "Содержание",
        "source": "test",
        "category": "игры",
        "age_min": 6,
        "age_max": 15,
    }

    # Mock flush для получения ID
    mock_news = News(id=1, **news_data)
    mock_db.add.return_value = None
    mock_db.flush.return_value = None

    # В реальном тесте нужно использовать реальную БД или более сложный mock
    # Здесь упрощенный вариант
    result = repository.save(news_data)

    assert mock_db.add.called


def test_repository_find_by_category(repository, mock_db):
    """Тест поиска по категории."""
    # Mock execute и scalars
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    result = repository.find_by_category("игры", age=10, grade=5, limit=10)

    assert isinstance(result, list)
    assert mock_db.execute.called


def test_repository_find_by_age(repository, mock_db):
    """Тест поиска по возрасту."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    result = repository.find_by_age(10, limit=10)

    assert isinstance(result, list)


def test_repository_find_by_grade(repository, mock_db):
    """Тест поиска по классу."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    result = repository.find_by_grade(5, limit=10)

    assert isinstance(result, list)


def test_repository_find_recent(repository, mock_db):
    """Тест поиска последних новостей."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    result = repository.find_recent(limit=10)

    assert isinstance(result, list)
