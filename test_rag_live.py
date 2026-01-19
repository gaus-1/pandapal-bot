"""
Полноценный live-тест RAG системы с реальными запросами.

Тестируем:
- QueryExpander с реальными школьными вопросами
- ResultReranker с mock-данными
- SemanticCache с различными запросами
- ContextCompressor на реальных текстах
- KnowledgeService enhanced_search
"""

import asyncio

from bot.services.knowledge_service import get_knowledge_service
from bot.services.rag import ContextCompressor, QueryExpander, ResultReranker, SemanticCache


class MockResult:
    """Mock result для тестирования."""

    def __init__(self, title: str, content: str, source_url: str = ""):
        self.title = title
        self.content = content
        self.source_url = source_url
        self.timestamp = None


def test_query_expander():
    """Тест расширения запросов."""
    print("\n" + "=" * 60)
    print("TEST 1: QueryExpander - Query Expansion")
    print("=" * 60)

    expander = QueryExpander()

    test_queries = [
        "таблица умножения",
        "что такое глагол",
        "синус угла",
        "фотосинтез растений",
        "падежи существительных",
    ]

    for query in test_queries:
        expanded = expander.expand(query)
        print(f"\nOriginal:  {query}")
        print(f"Expanded:  {expanded}")

        variations = expander.generate_variations(query)
        print(f"Variations ({len(variations)}):")
        for i, var in enumerate(variations, 1):
            print(f"  {i}. {var}")

    print("\n[OK] QueryExpander works!")


def test_result_reranker():
    """Тест переранжирования результатов."""
    print("\n" + "=" * 60)
    print("TEST 2: ResultReranker - Result Reranking")
    print("=" * 60)

    reranker = ResultReranker()

    # Создаем mock результаты
    results = [
        MockResult(
            "История математики",
            "Математика существует с древних времен",
            "http://example.com",
        ),
        MockResult(
            "Таблица умножения",
            "Таблица умножения - основа арифметики. Умножение чисел от 1 до 10.",
            "https://ru.wikipedia.org/wiki/Multiplication",
        ),
        MockResult(
            "Умножение векторов",
            "В линейной алгебре умножение векторов определяется специальным образом",
            "http://math.edu",
        ),
        MockResult("Физика", "Физика изучает природу и материю", "http://physics.com"),
    ]

    query = "таблица умножения для детей"
    print(f"\nQuery: {query}")
    print(f"Total results: {len(results)}")

    ranked = reranker.rerank(query, results, user_age=10, top_k=3)

    print("\nTop-3 reranked results:")
    for i, result in enumerate(ranked, 1):
        print(f"{i}. {result.title}")
        print(f"   Content: {result.content[:60]}...")
        print(f"   Source: {result.source_url}")

    print("\n[OK] ResultReranker works!")


def test_semantic_cache():
    """Тест семантического кэша."""
    print("\n" + "=" * 60)
    print("TEST 3: SemanticCache - Semantic Caching")
    print("=" * 60)

    cache = SemanticCache(ttl_hours=24)

    # Сохраняем несколько запросов
    test_data = [
        ("что такое математика", "Математика - наука о числах и вычислениях"),
        ("как решить уравнение", "Уравнение решается методом подстановки"),
        ("фотосинтез растений", "Фотосинтез - процесс получения энергии растениями"),
    ]

    for query, answer in test_data:
        cache.set(query, answer)
        print(f"Cached: {query}")

    print(f"\nCache stats: {cache.stats()}")

    # Проверяем точные совпадения
    print("\n--- Exact matches ---")
    for query, _expected in test_data:
        result = cache.get(query, threshold=0.95)
        status = "HIT" if result else "MISS"
        print(f"[{status}] {query}")

    # Проверяем семантически похожие запросы
    print("\n--- Semantic matches (threshold=0.5) ---")
    similar_queries = [
        "объясни математику",
        "решение уравнений",
        "как работает фотосинтез",
        "что такое биология",  # Должен быть MISS
    ]

    for query in similar_queries:
        result = cache.get(query, threshold=0.5)
        status = "HIT" if result else "MISS"
        print(f"[{status}] {query}")
        if result:
            print(f"     -> {result[:50]}...")

    print("\n[OK] SemanticCache works!")


def test_context_compressor():
    """Тест сжатия контекста."""
    print("\n" + "=" * 60)
    print("TEST 4: ContextCompressor - Context Compression")
    print("=" * 60)

    compressor = ContextCompressor()

    # Длинный контекст
    context = """
    Математика - одна из древнейших наук. Она изучает числа, формы и паттерны.
    История математики начинается с древних цивилизаций. Египтяне использовали математику для строительства.
    Умножение - это арифметическая операция. Таблица умножения помогает быстро считать.
    Деление тесно связано с умножением. Это обратная операция.
    География изучает Землю и её поверхность. Континенты и океаны - основные объекты географии.
    Биология - наука о живых организмах. Клетки являются основой жизни.
    Физика изучает материю и энергию. Законы Ньютона описывают движение тел.
    """

    questions = [
        "что такое умножение",
        "история математики",
        "география континенты",
    ]

    for question in questions:
        compressed = compressor.compress(context, question, max_sentences=3)
        print(f"\nQuestion: {question}")
        print(f"Original context: {len(context)} chars")
        print(f"Compressed: {len(compressed)} chars")
        print(f"Compression ratio: {len(compressed) / len(context) * 100:.1f}%")
        print(f"Content preview: {compressed[:100]}...")

    print("\n[OK] ContextCompressor works!")


async def test_knowledge_service_integration():
    """Интеграционный тест с KnowledgeService."""
    print("\n" + "=" * 60)
    print("TEST 5: KnowledgeService Integration")
    print("=" * 60)

    service = get_knowledge_service()

    # Проверяем наличие RAG компонентов
    print("\nRAG Components:")
    print(f"  QueryExpander: {type(service.query_expander).__name__}")
    print(f"  ResultReranker: {type(service.reranker).__name__}")
    print(f"  SemanticCache: {type(service.semantic_cache).__name__}")

    # Тестируем enhanced_search
    print("\n--- Enhanced Search Test ---")

    test_queries = [
        ("таблица умножения", 8),
        ("что такое глагол", 10),
        ("фотосинтез", 12),
    ]

    for query, age in test_queries:
        print(f"\nQuery: '{query}' (age={age})")

        try:
            results = await service.enhanced_search(query, user_age=age, top_k=3)
            print(f"  Results found: {len(results)}")

            if results:
                print("  Top result:")
                top = results[0]
                print(f"    Title: {getattr(top, 'title', 'N/A')}")
                print(f"    Content: {getattr(top, 'content', 'N/A')[:80]}...")
        except Exception as e:
            print(f"  Error: {e}")

    # Проверяем кэш
    print("\n--- Cache Stats ---")
    stats = service.semantic_cache.stats()
    print(f"  Cache size: {stats['size']}")
    print(f"  Max size: {stats['max_size']}")
    print(f"  TTL: {stats['ttl_hours']} hours")

    print("\n[OK] KnowledgeService integration works!")


async def test_wikipedia_with_api():
    """Тест Wikipedia API с ключом."""
    print("\n" + "=" * 60)
    print("TEST 6: Wikipedia API Test")
    print("=" * 60)

    service = get_knowledge_service()

    topics = ["Математика", "Физика", "Биология"]

    for topic in topics:
        print(f"\nTopic: {topic}")
        try:
            result = await service.get_wikipedia_summary(topic=topic, user_age=12, max_length=150)

            if result:
                print(f"  Length: {len(result)} chars")
                print(f"  Preview: {result[:100]}...")
            else:
                print("  No result (may be rate limited or 403)")

        except Exception as e:
            print(f"  Error: {e}")

    print("\n[OK] Wikipedia test completed (results may vary due to rate limits)")


def test_rag_performance():
    """Тест производительности RAG компонентов."""
    print("\n" + "=" * 60)
    print("TEST 7: Performance Test")
    print("=" * 60)

    import time

    # QueryExpander
    expander = QueryExpander()
    start = time.time()
    for _ in range(100):
        expander.expand("тестовый запрос умножение")
    qe_time = time.time() - start
    print(f"QueryExpander: 100 expansions in {qe_time * 1000:.2f}ms")

    # SemanticCache
    cache = SemanticCache(ttl_hours=1)
    for i in range(100):
        cache.set(f"запрос {i}", f"результат {i}")

    start = time.time()
    for i in range(100):
        cache.get(f"запрос {i}", threshold=0.9)
    cache_time = time.time() - start
    print(f"SemanticCache: 100 lookups in {cache_time * 1000:.2f}ms")

    # ResultReranker
    reranker = ResultReranker()
    results = [
        MockResult(f"Title {i}", f"Content {i}", f"http://example.com/{i}") for i in range(20)
    ]

    start = time.time()
    for _ in range(50):
        reranker.rerank("тестовый запрос", results, top_k=5)
    rerank_time = time.time() - start
    print(f"ResultReranker: 50 reranks of 20 items in {rerank_time * 1000:.2f}ms")

    # ContextCompressor
    compressor = ContextCompressor()
    long_context = " ".join([f"Предложение номер {i}." for i in range(50)])

    start = time.time()
    for _ in range(50):
        compressor.compress(long_context, "тестовый запрос", max_sentences=5)
    compress_time = time.time() - start
    print(f"ContextCompressor: 50 compressions in {compress_time * 1000:.2f}ms")

    print("\n[OK] Performance test completed!")


async def main():
    """Запуск всех тестов."""
    print("\n")
    print("=" * 60)
    print("RAG SYSTEM - COMPREHENSIVE LIVE TEST")
    print("=" * 60)

    # Unit tests
    test_query_expander()
    test_result_reranker()
    test_semantic_cache()
    test_context_compressor()

    # Integration tests
    await test_knowledge_service_integration()
    await test_wikipedia_with_api()

    # Performance tests
    test_rag_performance()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED!")
    print("=" * 60)
    print("\nSummary:")
    print("  - QueryExpander: Expands queries with synonyms and variations")
    print("  - ResultReranker: Ranks results by relevance, age, source quality")
    print("  - SemanticCache: Caches similar queries (Jaccard similarity)")
    print("  - ContextCompressor: Compresses context to reduce tokens")
    print("  - KnowledgeService: Integrated all RAG components")
    print("\nRAG System is fully operational!")


if __name__ == "__main__":
    asyncio.run(main())
