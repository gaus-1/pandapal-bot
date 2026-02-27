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

    def test_format_and_compress_knowledge_for_ai(self):
        """format_and_compress_knowledge_for_ai: пустой список — '', с материалом — непустая строка."""
        service = KnowledgeService()

        assert service.format_and_compress_knowledge_for_ai([], "вопрос", max_sentences=5) == ""

        from datetime import datetime

        from bot.services.web_scraper import EducationalContent

        materials = [
            EducationalContent(
                title="Фотосинтез",
                content="Фотосинтез — процесс образования органических веществ. Растения используют свет.",
                subject="биология",
                difficulty="средний",
                source_url="https://example.com",
                extracted_at=datetime.now(),
                tags=["биология"],
            )
        ]
        result = service.format_and_compress_knowledge_for_ai(
            materials, "что такое фотосинтез", max_sentences=10
        )
        assert result != ""
        assert "Фотосинтез" in result
        assert "фотосинтез" in result.lower() or "Фотосинтез" in result

    def test_build_rag_query_no_history_returns_message(self):
        """build_rag_query: без истории возвращает исходное сообщение."""
        out = KnowledgeService.build_rag_query("Что такое фотосинтез?", None)
        assert out == "Что такое фотосинтез?"
        out_empty = KnowledgeService.build_rag_query("  Вопрос  ", [])
        assert out_empty == "Вопрос"

    def test_build_rag_query_no_assistant_returns_message(self):
        """build_rag_query: если в истории нет ответов assistant — возвращает сообщение."""
        history = [{"role": "user", "text": "Привет"}]
        out = KnowledgeService.build_rag_query("а ещё?", history)
        assert out == "а ещё?"

    def test_build_rag_query_continuation_prepends_topic(self):
        """build_rag_query: «а ещё?» + длинный ответ assistant — в запросе есть фрагмент темы."""
        long_reply = (
            "Фотосинтез — это процесс, при котором растения превращают свет в энергию. "
            "Он происходит в хлоропластах. Без фотосинтеза не было бы жизни на Земле."
        )
        history = [
            {"role": "user", "text": "Что такое фотосинтез?"},
            {"role": "assistant", "text": long_reply},
        ]
        out = KnowledgeService.build_rag_query("а ещё примеры?", history)
        assert "Фотосинтез" in out or "фотосинтез" in out.lower()
        assert "а ещё примеры?" in out or "ещё примеры" in out

    def test_build_rag_query_long_message_unchanged(self):
        """build_rag_query: длинное сообщение возвращается без дополнения темы."""
        history = [
            {"role": "user", "text": "Что такое фотосинтез?"},
            {"role": "assistant", "text": "Фотосинтез — процесс в растениях."},
        ]
        long_msg = "Расскажи подробнее про этапы фотосинтеза и где он происходит"
        out = KnowledgeService.build_rag_query(long_msg, history)
        assert out == long_msg

    def test_get_knowledge_service_singleton(self):
        """Тест получения singleton экземпляра"""
        service1 = get_knowledge_service()
        service2 = get_knowledge_service()

        assert service1 is service2
        assert isinstance(service1, KnowledgeService)
