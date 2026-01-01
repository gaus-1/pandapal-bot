"""
Unit тесты для WebScraperService
Проверяем парсинг образовательных сайтов
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.web_scraper import (
    EducationalContent,
    NewsItem,
    WebScraperService,
)


class TestEducationalContent:
    """Тесты для dataclass EducationalContent"""

    def test_educational_content_creation(self):
        """Создание EducationalContent"""
        content = EducationalContent(
            title="Тест",
            content="Контент",
            subject="математика",
            difficulty="средний",
            source_url="https://example.com",
            extracted_at=datetime.now(),
            tags=["тест", "математика"],
        )

        assert content.title == "Тест"
        assert content.subject == "математика"
        assert content.difficulty == "средний"
        assert len(content.tags) == 2


class TestNewsItem:
    """Тесты для dataclass NewsItem"""

    def test_news_item_creation(self):
        """Создание NewsItem"""
        news = NewsItem(
            title="Новость",
            content="Текст новости",
            url="https://example.com/news",
            published_date=datetime.now(),
            source="test_source",
        )

        assert news.title == "Новость"
        assert news.source == "test_source"
        assert news.published_date is not None


class TestWebScraperService:
    """Тесты для WebScraperService"""

    def test_service_initialization(self):
        """Инициализация сервиса"""
        scraper = WebScraperService()

        assert scraper.session is None
        assert scraper.user_agent is not None
        assert "nsportal_config" in scraper.__dict__
        assert "school203_config" in scraper.__dict__

    def test_nsportal_config_has_required_fields(self):
        """Конфигурация nsportal содержит необходимые поля"""
        scraper = WebScraperService()

        assert "base_url" in scraper.nsportal_config
        assert "library_url" in scraper.nsportal_config
        assert "subjects" in scraper.nsportal_config
        assert len(scraper.nsportal_config["subjects"]) > 0

    def test_school203_config_has_required_fields(self):
        """Конфигурация school203 содержит необходимые поля"""
        scraper = WebScraperService()

        assert "base_url" in scraper.school203_config
        assert "sections" in scraper.school203_config

    @pytest.mark.asyncio
    async def test_session_context_manager(self):
        """Тест контекстного менеджера сессии"""
        scraper = WebScraperService()

        async with scraper:
            assert scraper.session is not None

        # После выхода из контекста сессия должна быть закрыта
        assert scraper.session is None or scraper.session.closed

    def test_user_agent_is_valid(self):
        """User-Agent валиден"""
        scraper = WebScraperService()

        assert "Mozilla" in scraper.user_agent
        assert "Chrome" in scraper.user_agent

    def test_subjects_list_contains_main_subjects(self):
        """Список предметов содержит основные предметы"""
        scraper = WebScraperService()
        subjects = scraper.nsportal_config["subjects"]

        main_subjects = ["matematika", "russkiy-yazyk", "fizika"]
        for subject in main_subjects:
            assert subject in subjects
