"""
Unit тесты для bot/services/knowledge_service.py
"""

import pytest

from bot.services.knowledge_service import KnowledgeService, get_knowledge_service


class TestKnowledgeService:
    """Тесты для KnowledgeService"""

    def test_knowledge_service_init(self):
        """Тест инициализации сервиса"""
        service = KnowledgeService()
        assert service is not None
        assert hasattr(service, "knowledge_base")
        assert hasattr(service, "last_update")

    @pytest.mark.asyncio
    async def test_get_knowledge_for_subject(self):
        """Тест получения знаний по предмету"""
        service = KnowledgeService()

        materials = await service.get_knowledge_for_subject("matematika", "задача")
        assert isinstance(materials, list)

    @pytest.mark.asyncio
    async def test_get_helpful_content(self):
        """Тест получения полезного контента"""
        service = KnowledgeService()

        materials = await service.get_helpful_content("Как решить уравнение?", user_age=10)
        assert isinstance(materials, list)

    def test_get_knowledge_stats(self):
        """Тест получения статистики базы знаний"""
        service = KnowledgeService()

        stats = service.get_knowledge_stats()
        assert isinstance(stats, dict)

    def test_format_knowledge_for_ai(self):
        """Тест форматирования знаний для AI"""
        service = KnowledgeService()

        # Пустой список
        formatted = service.format_knowledge_for_ai([])
        assert formatted == ""

        # С моковыми данными
        from datetime import datetime

        from bot.services.web_scraper import EducationalContent

        materials = [
            EducationalContent(
                title="Тест",
                content="Содержание",
                subject="matematika",
                difficulty="средний",
                source_url="https://test.com",
                extracted_at=datetime.now(),
                tags=["тест", "математика"],
            )
        ]

        formatted = service.format_knowledge_for_ai(materials)
        assert "Тест" in formatted
        assert "matematika" in formatted

    def test_get_knowledge_service_singleton(self):
        """Тест получения singleton экземпляра"""
        service1 = get_knowledge_service()
        service2 = get_knowledge_service()

        assert service1 is service2
        assert isinstance(service1, KnowledgeService)
