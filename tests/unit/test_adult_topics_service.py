"""
Тесты для AdultTopicsService - объяснение взрослых тем детям.

Проверяет:
- Детекцию тем по ключевым словам
- Качество объяснений
- Покрытие всех категорий тем
- Интеграцию с модерацией
"""

import pytest

from bot.services.adult_topics_service import AdultTopicExplanation, get_adult_topics_service


class TestAdultTopicsService:
    """Тесты для сервиса взрослых тем."""

    @pytest.fixture
    def service(self):
        """Получить экземпляр сервиса."""
        return get_adult_topics_service()

    def test_service_initialization(self, service):
        """Проверка инициализации сервиса."""
        assert service is not None
        assert len(service.topics) > 0
        assert "what_are_money" in service.topics
        assert "utilities" in service.topics
        assert "bank" in service.topics

    def test_detect_money_topic(self, service):
        """Проверка детекции темы про деньги."""
        queries = [
            "Что такое деньги?",
            "Откуда берутся деньги?",
            "Расскажи про деньги",
            "Как появились деньги в мире?",
        ]

        for query in queries:
            topic = service.detect_topic(query)
            assert topic is not None, f"Не обнаружена тема в запросе: {query}"
            assert topic.topic_id == "what_are_money"

    def test_detect_utilities_topic(self, service):
        """Проверка детекции темы про ЖКУ."""
        queries = [
            "Что такое ЖКУ?",
            "За что платим коммунальные услуги?",
            "Что такое коммуналка?",
            "Почему нужно платить за квартиру?",
        ]

        for query in queries:
            topic = service.detect_topic(query)
            assert topic is not None, f"Не обнаружена тема в запросе: {query}"
            assert topic.topic_id == "utilities"

    def test_detect_credit_topic(self, service):
        """Проверка детекции темы про кредит и ипотеку."""
        queries = [
            "Что такое кредит?",
            "Что такое ипотека?",
            "Почему кредит нужно отдавать больше?",
            "Как взять кредит в банке?",
        ]

        for query in queries:
            topic = service.detect_topic(query)
            assert topic is not None, f"Не обнаружена тема в запросе: {query}"
            assert topic.topic_id == "credit"

    def test_detect_passport_topic(self, service):
        """Проверка детекции темы про документы."""
        queries = [
            "Что такое паспорт?",
            "Зачем нужно свидетельство о рождении?",
            "Какие документы нужны человеку?",
        ]

        for query in queries:
            topic = service.detect_topic(query)
            assert topic is not None, f"Не обнаружена тема в запросе: {query}"
            assert topic.topic_id == "passport"

    def test_get_explanation(self, service):
        """Проверка получения объяснения темы."""
        explanation = service.get_explanation("what_are_money")
        assert explanation is not None
        assert "деньги" in explanation.lower()
        assert "📚" in explanation  # Заголовок
        assert len(explanation) > 200  # Достаточно подробное объяснение

    def test_explanation_has_examples(self, service):
        """Проверка наличия примеров в объяснениях."""
        explanation = service.get_explanation("credit")
        assert "🔍 Примеры:" in explanation or "Например" in explanation

    def test_search_topics(self, service):
        """Проверка поиска тем."""
        results = service.search_topics("деньги")
        assert len(results) > 0
        assert any(t.topic_id == "what_are_money" for t in results)

    def test_all_topics_have_required_fields(self, service):
        """Проверка что все темы имеют обязательные поля."""
        for topic_id, topic in service.topics.items():
            assert topic.topic_id == topic_id
            assert len(topic.keywords) > 0, f"Тема {topic_id} не имеет ключевых слов"
            assert len(topic.title) > 0, f"Тема {topic_id} не имеет заголовка"
            assert len(topic.explanation) > 100, f"Тема {topic_id} имеет слишком короткое объяснение"

    def test_no_forbidden_topics(self, service):
        """Проверка что запрещенные темы не объясняются."""
        forbidden_queries = [
            "Что такое наркотики?",
            "Как купить алкоголь?",
            "Расскажи про секс",
            "Что такое порно?",
        ]

        for query in forbidden_queries:
            topic = service.detect_topic(query)
            # Запрещённые темы НЕ должны детектироваться
            assert topic is None, f"Запрещённая тема обнаружена: {query}"

    def test_educational_money_questions_not_blocked(self, service):
        """Проверка что образовательные вопросы про деньги НЕ блокируются."""
        educational_queries = [
            "Что такое деньги и зачем они нужны?",
            "Что такое кредит?",
            "Что такое налоги?",
            "Что такое зарплата?",
            "Что такое банк?",
        ]

        for query in educational_queries:
            topic = service.detect_topic(query)
            assert topic is not None, f"Образовательный запрос НЕ обнаружен: {query}"

    def test_topic_coverage(self, service):
        """Проверка покрытия категорий тем."""
        categories = {
            "money": ["what_are_money", "salary", "bank", "credit", "taxes"],
            "home": ["utilities", "house_maintenance", "insurance"],
            "tech": ["internet", "mobile_connection", "subscriptions"],
            "docs": ["passport", "contract"],
            "work": ["work_life", "vacation", "career"],
            "health": ["health_insurance", "medicine_safety"],
            "emotions": ["adult_emotions", "obligations", "time_management"],
        }

        for category, expected_topics in categories.items():
            for topic_id in expected_topics:
                assert (
                    topic_id in service.topics
                ), f"Тема {topic_id} отсутствует в категории {category}"

    def test_explanation_quality(self, service):
        """Проверка качества объяснений - должны быть понятны детям."""
        topic = service.topics["what_are_money"]

        # Проверяем что объяснение написано простым языком
        explanation = topic.explanation

        # Должны быть простые объяснения (как для детей)
        child_friendly_words = ["как", "представь", "например", "проще", "понятно"]
        assert any(
            word in explanation.lower() for word in child_friendly_words
        ), "Объяснение не адаптировано для детей"

        # НЕ должно быть сложных терминов без объяснений
        complex_terms = ["фидуциарный", "монетарный", "эмиссия"]
        assert not any(
            term in explanation.lower() for term in complex_terms
        ), "Объяснение содержит сложные термины без расшифровки"

    def test_singleton_pattern(self):
        """Проверка паттерна Singleton."""
        service1 = get_adult_topics_service()
        service2 = get_adult_topics_service()
        assert service1 is service2, "AdultTopicsService должен быть singleton"
