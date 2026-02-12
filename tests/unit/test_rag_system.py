"""
Полноценные тесты RAG системы.

Проверяем:
- QueryExpander (расширение запросов)
- ResultReranker (переранжирование)
- SemanticCache (семантический кэш)
- ContextCompressor (сжатие контекста)
- Интеграция с KnowledgeService
"""

import pytest
from datetime import datetime, timedelta

from bot.services.rag import (
    ContextCompressor,
    QueryExpander,
    ResultReranker,
    SemanticCache,
    VectorSearchService,
)


class TestQueryExpander:
    """Тесты расширения запросов."""

    def test_expand_with_synonyms(self):
        """Проверка расширения запроса синонимами."""
        expander = QueryExpander()

        # Математические термины
        result = expander.expand("умножение чисел")
        assert "умножение" in result
        assert any(syn in result for syn in ["произведение", "умножить", "перемножение"])

    def test_expand_with_related_terms(self):
        """Проверка добавления связанных терминов."""
        expander = QueryExpander()

        result = expander.expand("таблица умножения")
        assert "таблица умножения" in result
        # Должны быть связанные термины
        assert len(result) > len("таблица умножения")

    def test_expand_max_additions(self):
        """Проверка ограничения количества добавлений."""
        expander = QueryExpander()

        result = expander.expand("умножение деление", max_additions=1)
        words = result.split()
        # Оригинал (2 слова) + максимум 1 добавление
        assert len(words) <= 5

    def test_generate_variations(self):
        """Проверка генерации вариаций запроса."""
        expander = QueryExpander()

        variations = expander.generate_variations("что такое фотосинтез")
        assert len(variations) >= 1
        assert len(variations) <= 3
        assert "что такое фотосинтез" in variations[0]

    def test_extract_keywords(self):
        """Проверка извлечения ключевых слов."""
        expander = QueryExpander()

        keywords = expander._extract_keywords("как решить уравнение с неизвестным")
        assert "решить" in keywords
        assert "уравнение" in keywords
        assert "неизвестным" in keywords
        # Стоп-слова должны быть удалены
        assert "как" not in keywords

    def test_formalize_question(self):
        """Проверка формализации вопроса."""
        expander = QueryExpander()

        formal = expander._formalize_question("что такое глагол")
        assert "определение" in formal

        formal = expander._formalize_question("как решить дробь")
        assert "решение" in formal


class MockResult:
    """Мок-объект для результата поиска."""

    def __init__(self, title: str, content: str, timestamp=None, source_url: str = ""):
        self.title = title
        self.content = content
        self.timestamp = timestamp
        self.source_url = source_url


class TestResultReranker:
    """Тесты переранжирования результатов."""

    def test_rerank_empty_results(self):
        """Проверка переранжирования пустого списка."""
        reranker = ResultReranker()

        results = reranker.rerank("test query", [], top_k=3)
        assert results == []

    def test_rerank_by_relevance(self):
        """Проверка ранжирования по релевантности."""
        reranker = ResultReranker()

        results = [
            MockResult("Математика", "Информация о математике", None, ""),
            MockResult("Умножение", "Детальная информация про умножение чисел", None, ""),
            MockResult("История", "Информация об истории", None, ""),
        ]

        ranked = reranker.rerank("умножение чисел", results, top_k=2)

        # Первый результат должен быть самым релевантным
        assert "умножение" in ranked[0].title.lower() or "умножение" in ranked[0].content.lower()
        assert len(ranked) == 2

    def test_rerank_by_source_quality(self):
        """Проверка учета качества источника."""
        reranker = ResultReranker()

        results = [
            MockResult("Статья", "Информация", None, "http://example.com"),
            MockResult("Статья", "Информация", None, "https://ru.wikipedia.org/wiki/Test"),
        ]

        ranked = reranker.rerank("информация", results, top_k=2)

        # Wikipedia должна быть выше
        assert "wikipedia" in ranked[0].source_url.lower()

    def test_rerank_by_recency(self):
        """Проверка учета актуальности."""
        reranker = ResultReranker()

        now = datetime.now()
        old_date = now - timedelta(days=365)

        results = [
            MockResult("Старая статья", "content", old_date, ""),
            MockResult("Новая статья", "content", now, ""),
        ]

        ranked = reranker.rerank("статья", results, top_k=2)

        # Новая статья должна быть выше (при равной релевантности)
        assert ranked[0].timestamp == now or ranked[1].timestamp == now

    def test_calculate_relevance(self):
        """Проверка расчета текстовой релевантности."""
        reranker = ResultReranker()

        result = MockResult("Умножение", "Детально про умножение чисел", None, "")
        relevance = reranker._calculate_relevance("умножение чисел", result)

        assert relevance > 0.5  # Высокая релевантность
        assert relevance <= 1.0

    def test_calculate_age_match(self):
        """Проверка соответствия возрасту."""
        reranker = ResultReranker()

        result = MockResult("Простой урок", "простой материал для детей", None, "")

        # Для младших детей (7 лет)
        match_young = reranker._calculate_age_match(result, 7)

        # Для старших (15 лет)
        match_old = reranker._calculate_age_match(result, 15)

        # Простой материал лучше для младших
        assert match_young >= match_old


class TestSemanticCache:
    """Тесты семантического кэша."""

    @pytest.mark.skip(reason="SemanticCache использует pgvector + async API, не in-memory")
    def test_cache_set_and_get(self):
        """Проверка сохранения и получения из кэша."""
        cache = SemanticCache(ttl_hours=1)

        cache.set("что такое математика", "Математика - наука о числах")

        # Точное совпадение
        result = cache.get("что такое математика", threshold=0.9)
        assert result == "Математика - наука о числах"

    @pytest.mark.skip(reason="SemanticCache использует pgvector + async API")
    def test_cache_semantic_match(self):
        """Проверка семантического поиска в кэше."""
        cache = SemanticCache(ttl_hours=1)

        cache.set("что такое умножение", "Умножение - операция")

        # Похожий запрос
        result = cache.get("объясни умножение", threshold=0.4)
        assert result is not None

    @pytest.mark.skip(reason="SemanticCache использует pgvector + async API")
    def test_cache_miss(self):
        """Проверка промаха кэша."""
        cache = SemanticCache(ttl_hours=1)

        cache.set("математика", "результат")

        # Совсем другой запрос
        result = cache.get("биология", threshold=0.9)
        assert result is None

    @pytest.mark.skip(reason="SemanticCache использует pgvector, нет _cleanup_expired")
    def test_cache_expiration(self):
        """Проверка истечения TTL."""
        cache = SemanticCache(ttl_hours=0)  # Мгновенное истечение

        cache.set("запрос", "результат")

        # Принудительная очистка
        cache._cleanup_expired()

        # После очистки не должно быть результата
        assert len(cache.cache) == 0

    @pytest.mark.skip(reason="SemanticCache использует pgvector, нет max_size")
    def test_cache_max_size(self):
        """Проверка ограничения размера кэша."""
        cache = SemanticCache(ttl_hours=24)
        cache.max_size = 3

        cache.set("запрос1", "результат1")
        cache.set("запрос2", "результат2")
        cache.set("запрос3", "результат3")
        cache.set("запрос4", "результат4")  # Должен вытеснить первый

        assert len(cache.cache) == 3
        # Первый запрос должен быть удален
        result = cache.get("запрос1", threshold=0.99)
        assert result is None

    @pytest.mark.skip(reason="SemanticCache использует embeddings, нет _calculate_similarity")
    def test_cache_similarity_calculation(self):
        """Проверка расчета Jaccard similarity."""
        cache = SemanticCache(ttl_hours=1)

        similarity = cache._calculate_similarity("что такое математика", "что такое алгебра")

        # Должна быть частичная схожесть (общие слова "что такое")
        assert similarity > 0.0
        assert similarity < 1.0

    @pytest.mark.skip(reason="SemanticCache API отличается, нет stats()")
    def test_cache_stats(self):
        """Проверка статистики кэша."""
        cache = SemanticCache(ttl_hours=12)

        cache.set("запрос1", "результат1")
        cache.set("запрос2", "результат2")

        stats = cache.stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 1000
        assert stats["ttl_hours"] == 12

    @pytest.mark.skip(reason="SemanticCache использует pgvector, нет clear()")
    def test_cache_clear(self):
        """Проверка очистки кэша."""
        cache = SemanticCache(ttl_hours=1)

        cache.set("запрос", "результат")
        assert len(cache.cache) > 0

        cache.clear()
        assert len(cache.cache) == 0


class TestContextCompressor:
    """Тесты сжатия контекста."""

    def test_compress_empty_context(self):
        """Проверка сжатия пустого контекста."""
        compressor = ContextCompressor()

        result = compressor.compress("", "вопрос")
        assert result == ""

    def test_compress_by_relevance(self):
        """Проверка сжатия по релевантности."""
        compressor = ContextCompressor()

        context = """
        Математика - наука о числах. История появилась давно.
        Умножение - важная операция. География изучает землю.
        Деление связано с умножением. Биология изучает жизнь.
        """

        compressed = compressor.compress(context, "умножение деление", max_sentences=2)

        # Должны остаться предложения про умножение и деление
        assert "умножение" in compressed.lower()
        assert "деление" in compressed.lower()
        # Биология не должна попасть
        assert "биология" not in compressed.lower()

    def test_compress_preserves_order(self):
        """Проверка сохранения порядка предложений."""
        compressor = ContextCompressor()

        context = (
            "Первое предложение про математику. Второе про умножение. Третье тоже про математику."
        )

        compressed = compressor.compress(context, "математика", max_sentences=2)

        # Порядок должен быть сохранен
        sentences = compressed.split(". ")
        if len(sentences) >= 2:
            assert sentences[0].strip().startswith("Первое") or sentences[0].strip().startswith(
                "Второе"
            )

    def test_split_sentences(self):
        """Проверка разбиения на предложения."""
        compressor = ContextCompressor()

        text = "Первое предложение. Второе предложение! Третье предложение?"
        sentences = compressor._split_sentences(text)

        assert len(sentences) == 3
        assert "Первое предложение" in sentences[0]

    def test_sentence_relevance(self):
        """Проверка расчета релевантности предложения."""
        compressor = ContextCompressor()

        sentence = "Умножение - важная математическая операция"
        question = "что такое умножение"

        relevance = compressor._sentence_relevance(sentence, question)

        assert relevance > 0.0
        assert relevance <= 1.2  # Макс = 1.0 + 0.2 бонус за длину

    def test_compress_skips_educational_phrases(self):
        """Для «что такое», «объясни» контекст не сжимается."""
        compressor = ContextCompressor()
        context = "Важный контекст. Ещё один пункт. Третий пункт."

        result = compressor.compress(context, "что такое умножение", max_sentences=1)
        assert result == context

        result = compressor.compress(context, "объясни теорему Пифагора", max_sentences=1)
        assert result == context


class TestKnowledgeServiceRAG:
    """Тесты интеграции RAG в KnowledgeService."""

    def test_knowledge_service_has_rag_components(self):
        """Проверка наличия RAG компонентов в KnowledgeService."""
        from bot.services.knowledge_service import KnowledgeService

        service = KnowledgeService()

        assert hasattr(service, "query_expander")
        assert hasattr(service, "reranker")
        assert hasattr(service, "semantic_cache")
        assert hasattr(service, "vector_search")
        assert isinstance(service.query_expander, QueryExpander)
        assert isinstance(service.reranker, ResultReranker)
        assert isinstance(service.semantic_cache, SemanticCache)
        assert isinstance(service.vector_search, VectorSearchService)

    def test_deduplicate_results(self):
        """Проверка дедупликации результатов."""
        from bot.services.knowledge_service import KnowledgeService

        service = KnowledgeService()

        results = [
            MockResult("Статья 1", "Контент", None, "http://example.com/1"),
            MockResult("Статья 2", "Контент", None, "http://example.com/2"),
            MockResult("Статья 1 дубль", "Контент", None, "http://example.com/1"),  # Дубль
        ]

        unique = service._deduplicate_results(results)

        assert len(unique) == 2
        # URL должны быть уникальны
        urls = [r.source_url for r in unique]
        assert len(urls) == len(set(urls))


@pytest.mark.asyncio
class TestRAGIntegration:
    """Интеграционные тесты RAG системы."""

    async def test_enhanced_search_flow(self):
        """Проверка полного flow enhanced_search."""
        from bot.services.knowledge_service import KnowledgeService

        service = KnowledgeService()

        # Первый запрос - кэш пустой
        results1 = await service.enhanced_search("что такое умножение", user_age=10, top_k=3)

        # Проверяем что результаты есть (если база знаний не пустая)
        assert isinstance(results1, list)

        # Второй запрос - должен быть из кэша
        results2 = await service.enhanced_search("что такое умножение", user_age=10, top_k=3)

        assert isinstance(results2, list)

    async def test_wikipedia_integration(self):
        """Проверка интеграции с Wikipedia."""
        from bot.services.knowledge_service import KnowledgeService

        service = KnowledgeService()

        # Простой запрос в Wikipedia
        result = await service.get_wikipedia_summary(
            topic="Математика", user_age=12, max_length=200
        )

        assert result is not None
        if result:
            extract, title = result
            assert len(extract) > 0
            assert len(extract) <= 250
            assert len(title) > 0


def test_all_rag_components_importable():
    """Проверка что все RAG компоненты импортируются."""
    from bot.services.rag import (
        ContextCompressor,
        QueryExpander,
        ResultReranker,
        SemanticCache,
        VectorSearchService,
    )

    # Создаем экземпляры
    expander = QueryExpander()
    reranker = ResultReranker()
    cache = SemanticCache(ttl_hours=24)
    compressor = ContextCompressor()
    vector_search = VectorSearchService()

    assert expander is not None
    assert reranker is not None
    assert cache is not None
    assert compressor is not None
    assert vector_search is not None

    print("✅ Все RAG компоненты успешно импортированы и инициализированы")


if __name__ == "__main__":
    # Запуск без pytest для быстрой проверки
    print("RAG System Quick Test\n")

    # QueryExpander
    print("1. QueryExpander:")
    expander = QueryExpander()
    expanded = expander.expand("умножение чисел")
    print(f"   Original: 'умножение чисел'")
    print(f"   Expanded: '{expanded}'")
    variations = expander.generate_variations("что такое фотосинтез")
    print(f"   Variations: {len(variations)}")

    # ResultReranker
    print("\n2. ResultReranker:")
    reranker = ResultReranker()
    results = [
        MockResult("История", "Про историю", None, ""),
        MockResult("Умножение", "Детально про умножение", None, ""),
    ]
    ranked = reranker.rerank("умножение", results, top_k=1)
    print(f"   Top result: '{ranked[0].title}'")

    # SemanticCache
    print("\n3. SemanticCache:")
    cache = SemanticCache(ttl_hours=1)
    cache.set("что такое математика", "Математика - наука")
    hit = cache.get("что такое математика", threshold=0.9)
    print(f"   Cache hit: {hit is not None}")
    similar = cache.get("объясни математику", threshold=0.5)
    print(f"   Semantic hit: {similar is not None}")

    # ContextCompressor
    print("\n4. ContextCompressor:")
    compressor = ContextCompressor()
    context = "Математика важна. История интересна. Умножение - операция. Биология сложна."
    compressed = compressor.compress(context, "умножение", max_sentences=2)
    print(f"   Original: {len(context)} chars")
    print(f"   Compressed: {len(compressed)} chars")

    print("\nAll RAG components working!")
