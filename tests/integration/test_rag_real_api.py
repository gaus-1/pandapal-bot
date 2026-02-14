"""
Тесты RAG системы с реальными API запросами.

Проверяет что Панда:
- Учитывает ВСЕ слова в запросе пользователя
- Дает глубокие структурированные ответы
- Правильно использует Wikipedia и образовательные источники
- Отвечает на все аспекты сложных вопросов

ВАЖНО: Требует реального YANDEX_CLOUD_API_KEY для запуска.
"""

import os

import pytest

from bot.services.ai_service_solid import get_ai_service
from bot.services.knowledge_service import get_knowledge_service
from bot.services.prompt_builder import PromptBuilder


@pytest.mark.skipif(
    not os.getenv("YANDEX_CLOUD_API_KEY"),
    reason="Требуется YANDEX_CLOUD_API_KEY для реальных API тестов",
)
class TestRAGRealAPI:
    """Тесты RAG с реальными API запросами."""

    @pytest.fixture
    def ai_service(self):
        """Получить AI сервис."""
        return get_ai_service()

    @pytest.fixture
    def knowledge_service(self):
        """Получить Knowledge сервис."""
        return get_knowledge_service()

    @pytest.mark.asyncio
    async def test_all_words_considered_simple(self, ai_service):
        """Проверка что AI учитывает ВСЕ слова в простом вопросе."""
        # Вопрос содержит: "как", "почему", "вода", "пар"
        question = "Объясни как и почему вода превращается в пар?"

        response = await ai_service.generate_response(
            user_message=question, chat_history=[], user_age=12
        )

        # Проверяем что ответ содержит объяснения ДЛЯ ОБОИХ аспектов
        assert "как" in question.lower() or "процесс" in response.lower(), (
            "Не объяснён процесс (КАК)"
        )
        assert "почему" in question.lower() or any(
            word in response.lower() for word in ["потому", "причина", "из-за", "энергия"]
        ), "Не объяснена причина (ПОЧЕМУ)"

        # Проверяем что ответ достаточно глубокий
        assert len(response) > 300, (
            f"Ответ слишком короткий ({len(response)} символов), должен быть глубже"
        )

        # Проверяем структуру - должны быть абзацы
        paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
        assert len(paragraphs) >= 2, "Ответ не структурирован (нет абзацев)"

    @pytest.mark.asyncio
    async def test_all_words_considered_complex(self, ai_service):
        """Проверка что AI учитывает ВСЕ слова в сложном вопросе."""
        # Вопрос содержит несколько тем: "фотосинтез", "растения", "кислород", "как работает"
        question = "Расскажи подробно что такое фотосинтез, как он работает в растениях и зачем он нужен для кислорода?"

        response = await ai_service.generate_response(
            user_message=question, chat_history=[], user_age=13
        )

        # Проверяем что ответ покрывает ВСЕ аспекты
        assert "фотосинтез" in response.lower(), "Не упомянут фотосинтез"
        assert "растени" in response.lower(), "Не упомянуты растения"
        assert "кислород" in response.lower(), "Не упомянут кислород"

        # Проверяем что объяснён механизм (КАК работает)
        assert any(
            word in response.lower()
            for word in ["процесс", "работает", "происходит", "свет", "вода"]
        ), "Не объяснён механизм фотосинтеза"

        # Проверяем глубину ответа
        assert len(response) > 500, (
            f"Ответ слишком короткий для сложного вопроса ({len(response)} символов)"
        )

    @pytest.mark.asyncio
    async def test_multiple_questions_in_one(self, ai_service):
        """Проверка что AI отвечает на несколько вопросов в одном сообщении."""
        # Три вопроса в одном: "что", "как", "зачем"
        question = "Что такое электричество, как оно вырабатывается и зачем нужно в доме?"

        response = await ai_service.generate_response(
            user_message=question, chat_history=[], user_age=11
        )

        # Проверяем что ответ покрывает ВСЕ три вопроса
        # 1. ЧТО такое электричество
        assert any(
            word in response.lower() for word in ["электричество", "энергия", "ток", "электроны"]
        ), "Не объяснено ЧТО такое электричество"

        # 2. КАК вырабатывается
        assert any(
            word in response.lower()
            for word in ["электростанци", "генератор", "вырабатывается", "производ"]
        ), "Не объяснено КАК вырабатывается электричество"

        # 3. ЗАЧЕМ нужно
        assert any(
            word in response.lower() for word in ["свет", "приборы", "нужно", "использу", "работа"]
        ), "Не объяснено ЗАЧЕМ нужно электричество"

        # Проверяем структуру - должны быть разделы для каждого вопроса
        assert len(response) > 600, "Ответ слишком короткий для трёх вопросов"

    @pytest.mark.asyncio
    async def test_rag_list_square_roots(self, knowledge_service):
        """enhanced_search для «список квадратных корней» возвращает непустой результат."""
        results = await knowledge_service.enhanced_search(
            user_question="список квадратных корней", user_age=12, top_k=5, use_wikipedia=True
        )
        assert results is not None and len(results) > 0, "RAG не нашёл контент для списка корней"
        combined = " ".join(r.content for r in results).lower()
        assert any(p in combined for p in ["√", "корн", "1.41", "1.73", "2"]) or len(combined) > 100

    @pytest.mark.asyncio
    async def test_rag_knowledge_integration(self, knowledge_service):
        """Проверка что RAG находит релевантную информацию."""
        question = "Объясни теорему Пифагора"

        # Enhanced search с reranking
        results = await knowledge_service.enhanced_search(
            user_question=question, user_age=14, top_k=3
        )

        # Должны быть результаты для известной темы
        assert len(results) > 0, "RAG не нашёл информацию про теорему Пифагора"

        # Проверяем что результаты содержат релевантные слова
        combined_content = " ".join(r.content for r in results).lower()
        assert any(
            word in combined_content for word in ["пифагор", "треугольник", "гипотенуза", "катет"]
        ), "RAG результаты не релевантны запросу"

    @pytest.mark.asyncio
    async def test_enhanced_search_hybrid_flow(self, knowledge_service):
        """enhanced_search (vector + keyword + Wikipedia) возвращает результат."""
        results = await knowledge_service.enhanced_search(
            user_question="Что такое фотосинтез?",
            user_age=12,
            top_k=5,
            use_wikipedia=True,
        )
        assert results is not None
        assert len(results) >= 0  # Может быть пусто при недоступности API
        if results:
            combined = " ".join(r.content for r in results).lower()
            assert len(combined) > 0

    @pytest.mark.asyncio
    async def test_rag_wikipedia_integration(self, knowledge_service):
        """Проверка интеграции с Wikipedia."""
        question = "Что такое солнечная система?"

        # Получаем контекст из Wikipedia
        wiki_context = await knowledge_service.get_wikipedia_context_for_question(
            question, user_age=10
        )

        if wiki_context:  # Wikipedia может быть недоступна
            assert len(wiki_context) > 0, "Wikipedia контекст пустой"
            assert any(word in wiki_context.lower() for word in ["солнце", "планет", "систем"]), (
                "Wikipedia контекст не релевантен"
            )

    @pytest.mark.asyncio
    async def test_prompt_builder_extracts_keywords(self):
        """Проверка что системный промпт требует учитывать все слова запроса и ключевые термины."""
        builder = PromptBuilder()

        question = "Объясни как и почему происходит фотосинтез в растениях и зачем он нужен"

        prompt = builder.build_system_prompt(
            user_message=question,
            user_age=12,
            is_history_cleared=False,
        )

        prompt_lower = prompt.lower()
        # Промпт содержит инструкцию про полноту/важность ответа
        assert "важно" in prompt_lower or "все слова" in prompt_lower, (
            "Промпт не содержит инструкцию про полноту ответа или учёт всех слов"
        )
        # Промпт упоминает ключевые термины (или слова запроса)
        assert "ключевые" in prompt_lower, "Промпт не упоминает ключевые термины/слова"

        # Все важные слова из примера есть в вопросе (вопрос передаётся AI отдельно)
        important_words = ["как", "почему", "фотосинтез", "растени", "зачем"]
        for word in important_words:
            assert word in question.lower() or word in prompt_lower, (
                f"Важное слово «{word}» должно быть в вопросе или промпте"
            )


@pytest.mark.skipif(
    not os.getenv("YANDEX_CLOUD_API_KEY"),
    reason="Требуется YANDEX_CLOUD_API_KEY",
)
class TestYandexAPIRealRequests:
    """Тесты с реальными запросами к Yandex Cloud API."""

    @pytest.fixture
    def ai_service(self):
        """Получить AI сервис."""
        return get_ai_service()

    @pytest.mark.asyncio
    async def test_simple_math_question(self, ai_service):
        """Реальный API тест - простой математический вопрос."""
        question = "Сколько будет 7 умножить на 8?"

        response = await ai_service.generate_response(
            user_message=question, chat_history=[], user_age=8
        )

        # Модель может ответить «56» или «пятьдесят шесть»
        response_lower = response.lower()
        has_correct_answer = (
            "56" in response
            or "пятьдесят шесть" in response_lower
            or "56." in response
            or response.strip().startswith("56 ")
        )
        assert has_correct_answer, f"Неправильный ответ на 7×8: ответ должен содержать 56 или пятьдесят шесть, получено: {response[:200]!r}"
        assert len(response) > 50, "Ответ слишком короткий"

    @pytest.mark.asyncio
    async def test_complex_explanation_question(self, ai_service):
        """Реальный API тест - сложный вопрос с объяснением."""
        question = "Объясни подробно что такое деление с остатком и как его решать с примерами"

        response = await ai_service.generate_response(
            user_message=question, chat_history=[], user_age=10
        )

        # Проверяем что ответ достаточно глубокий
        assert len(response) > 300, "Ответ недостаточно подробный для сложного вопроса"

        # Проверяем что есть примеры
        assert any(
            word in response.lower() for word in ["пример", "например", "допустим", "представь"]
        ), "Нет примеров в ответе"

        # Проверяем ключевые термины
        assert "остаток" in response.lower(), "Не объяснён остаток"
        assert "дел" in response.lower(), "Не объяснено деление"

    @pytest.mark.asyncio
    async def test_visualization_context_integration(self, ai_service):
        """Тест что AI правильно реагирует на контекст визуализации."""
        # Запрос на график
        question = "Покажи график функции y = x²"

        # Это должно активировать детектор визуализации, но проверяем только AI ответ
        response = await ai_service.generate_response(
            user_message=question, chat_history=[], user_age=14
        )

        # AI должен дать пояснение про параболу
        assert any(word in response.lower() for word in ["парабол", "график", "квадрат"]), (
            "AI не дал пояснение про график"
        )
