"""
Тесты для исправлений из аудита поведения панды и RAG пайплайна.

Покрывает:
- CoT триггер (точность — «задача» без чисел не триггерит)
- Clarification фразы (расширенный набор)
- Embedding truncation (граница слова)
- Query expansion (множественные синонимы)
- Reranker (биграммы)
- Forbidden content (FORBIDDEN_PATTERNS)
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.services.yandex_ai_response_generator import (
    IContextBuilder,
    IModerator,
    YandexAIResponseGenerator,
    _CLARIFICATION_PHRASES,
)


@pytest.fixture
def response_generator():
    """Генератор ответов с моками."""
    moderator = Mock(spec=IModerator)
    moderator.moderate = Mock(return_value=(True, None))
    builder = Mock(spec=IContextBuilder)
    gen = YandexAIResponseGenerator(moderator, builder)
    from bot.services.knowledge_service import KnowledgeService

    gen.knowledge_service = Mock(spec=KnowledgeService)
    gen.knowledge_service.get_helpful_content = AsyncMock(return_value=[])
    gen.knowledge_service.format_and_compress_knowledge_for_ai = Mock(return_value="")
    return gen


# ── CoT триггер ────────────────────────────────────────────────────
class TestCoTTriggerPrecision:
    """«задача» без чисел не триггерит CoT; с числами — триггерит."""

    def test_zadacha_without_number_no_cot(self, response_generator):
        assert response_generator._is_calculation_task("расскажи про задачу Монти Холла") is False

    def test_zadacha_with_number_triggers_cot(self, response_generator):
        assert response_generator._is_calculation_task("реши задачу: было 10 яблок") is True

    def test_arithmetic_expression(self, response_generator):
        assert response_generator._is_calculation_task("25 + 38") is True

    def test_narrative_no_cot(self, response_generator):
        assert response_generator._is_calculation_task("расскажи про фотосинтез") is False

    def test_skolko_vsego(self, response_generator):
        assert response_generator._is_calculation_task("сколько всего планет") is True

    def test_posthitay(self, response_generator):
        assert response_generator._is_calculation_task("посчитай сумму") is True


# ── Clarification фразы ────────────────────────────────────────────
class TestClarificationPhrases:
    """Расширенный набор фраз для уточняющих вопросов."""

    @pytest.mark.parametrize(
        "phrase",
        ["а ещё?", "???", "не понял", "не поняла", "а дальше?", "и?", "ну и?", "а как?", "зачем?"],
    )
    def test_phrase_in_set(self, phrase):
        assert phrase in _CLARIFICATION_PHRASES

    def test_expanded_set_size(self):
        assert len(_CLARIFICATION_PHRASES) >= 14


# ── Embedding truncation ──────────────────────────────────────────
class TestEmbeddingTruncation:
    """Обрезка по границе слова."""

    def test_truncate_word_boundary(self):
        from bot.services.embeddings_service import _truncate_on_word_boundary

        text = "один два три четыре пять"
        result = _truncate_on_word_boundary(text, 14)
        assert result == "один два три"
        assert not result.endswith("ч")

    def test_truncate_no_change_short(self):
        from bot.services.embeddings_service import _truncate_on_word_boundary

        text = "короткий текст"
        assert _truncate_on_word_boundary(text, 100) == text

    def test_truncate_single_word(self):
        from bot.services.embeddings_service import _truncate_on_word_boundary

        # Нет пробела — возвращаем обрезку
        result = _truncate_on_word_boundary("оченьдлинноеслово", 5)
        assert len(result) <= 5


# ── Query expansion ────────────────────────────────────────────────
class TestQueryExpansionMultipleSynonyms:
    """Используется >1 синоним на термин."""

    def test_multiple_synonyms_added(self):
        from bot.services.rag.query_expander import QueryExpander

        expander = QueryExpander()
        result = expander.expand("умножение", max_additions=4)
        # Должно быть хотя бы 2 добавленных слова, а не 1
        words = result.split()
        assert len(words) >= 3, f"Ожидалось >=3 слов, получили: {words}"


# ── Reranker биграммы ──────────────────────────────────────────────
class TestRerankerBigrams:
    """Биграммный бонус повышает релевантность фразы."""

    def test_bigram_boost(self):
        from bot.services.rag.reranker import ResultReranker

        reranker = ResultReranker()

        class FakeResult:
            def __init__(self, title, content):
                self.title = title
                self.content = content

        # Документ с точной биграммой
        exact = FakeResult("Теорема", "теорема пифагора для прямоугольного треугольника")
        # Документ со словами раздельно
        scattered = FakeResult("Пифагор", "пифагор изучал теоремы в Греции")

        exact_score = reranker._calculate_relevance("теорема пифагора", exact)
        scattered_score = reranker._calculate_relevance("теорема пифагора", scattered)

        assert exact_score > scattered_score, (
            f"Биграммный бонус: {exact_score:.2f} должен быть > {scattered_score:.2f}"
        )


# ── Forbidden content ─────────────────────────────────────────────
class TestForbiddenContent:
    """_contains_forbidden_content использует FORBIDDEN_PATTERNS."""

    def test_forbidden_patterns_catches_terrorism(self):
        from bot.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        assert service._contains_forbidden_content("статья про терроризм") is True

    def test_safe_content_passes(self):
        from bot.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        assert service._contains_forbidden_content("математика для школьников") is False

    def test_empty_passes(self):
        from bot.services.knowledge_service import KnowledgeService

        service = KnowledgeService()
        assert service._contains_forbidden_content("") is False
        assert service._contains_forbidden_content("   ") is False


# ── Image moderation ──────────────────────────────────────────────
class TestImageModeration:
    """moderate_image_content теперь проверяет OCR-текст через модератор."""

    @pytest.mark.asyncio
    async def test_blocks_forbidden_image_text(self, response_generator):
        # OCR возвращает запрещённый текст
        response_generator.yandex_service.recognize_text = AsyncMock(
            return_value="купи наркотики тут"
        )
        response_generator.moderator.moderate = Mock(return_value=(False, "наркотик"))

        is_safe, reason = await response_generator.moderate_image_content(b"fake_image_data")
        assert is_safe is False
        assert "наркотик" in reason

    @pytest.mark.asyncio
    async def test_passes_safe_image(self, response_generator):
        response_generator.yandex_service.recognize_text = AsyncMock(
            return_value="домашнее задание по математике"
        )
        response_generator.moderator.moderate = Mock(return_value=(True, None))

        is_safe, reason = await response_generator.moderate_image_content(b"safe_image")
        assert is_safe is True

    @pytest.mark.asyncio
    async def test_passes_when_ocr_fails(self, response_generator):
        # OCR бросает исключение — не блокируем
        response_generator.yandex_service.recognize_text = AsyncMock(side_effect=Exception("API error"))

        is_safe, reason = await response_generator.moderate_image_content(b"any_image")
        assert is_safe is True
        assert reason == "OK"


# ── Модерация ОТВЕТА AI ──────────────────────────────────────────
class TestResponseOutputModeration:
    """finalize_ai_response модерирует ответ через sanitize_ai_response."""

    def test_blocks_forbidden_output(self):
        from bot.services.yandex_ai_response_generator import finalize_ai_response

        # Ответ с запрещённым словом должен быть заменён
        result = finalize_ai_response("Вот как сделать наркотики дома", user_message="расскажи")
        assert "наркотик" not in result.lower()
        assert "учёб" in result.lower() or "📚" in result

    def test_passes_safe_output(self):
        from bot.services.yandex_ai_response_generator import finalize_ai_response

        result = finalize_ai_response("Фотосинтез — это процесс преобразования света.", user_message="что такое фотосинтез")
        assert "Фотосинтез" in result


# ── Engagement question guard ─────────────────────────────────────
class TestEngagementQuestionGuard:
    """Короткие ответы не получают вопрос-вовлечение."""

    def test_short_answer_no_engagement(self):
        from bot.services.yandex_ai_response_generator import add_random_engagement_question

        result = add_random_engagement_question("Ответ: 4.")
        assert result == "Ответ: 4."  # Без вопроса

    def test_long_answer_gets_engagement(self):
        from bot.services.yandex_ai_response_generator import add_random_engagement_question

        long_text = "Фотосинтез — процесс. " * 20  # >200 символов
        result = add_random_engagement_question(long_text.strip())
        assert len(result) > len(long_text.strip())


# ── Dedup threshold 75% ──────────────────────────────────────────
class TestDedupThreshold:
    """Порог 75% не удаляет формулы с повторяющимися словами."""

    def test_similar_formulas_preserved(self):
        from bot.services.yandex_ai_response_generator import clean_ai_response

        text = (
            "Площадь треугольника = (a·h)/2\n\n"
            "Площадь прямоугольника = a·b\n\n"
            "Площадь параллелограмма = a·h"
        )
        result = clean_ai_response(text)
        assert "треугольника" in result
        assert "прямоугольника" in result
        assert "параллелограмма" in result


# ── Educational bypass fix ────────────────────────────────────────
class TestEducationalBypassFix:
    """Глаголы-действия удалены из EDUCATIONAL_CONTEXTS."""

    def test_no_generic_verbs_in_contexts(self):
        from bot.services.moderation_service import ContentModerationService

        contexts_lower = [c.lower() for c in ContentModerationService.EDUCATIONAL_CONTEXTS]
        dangerous_verbs = ["расскажи", "покажи", "помоги", "создай", "напиши", "нарисуй", "составь", "построй"]
        for verb in dangerous_verbs:
            assert verb not in contexts_lower, f"'{verb}' не должен быть в EDUCATIONAL_CONTEXTS"


# ── Broken synonym fix ───────────────────────────────────────────
class TestBrokenSynonymsFix:
    """Общеупотребительные слова не заменяются на запрещённые."""

    def test_chemistry_not_replaced(self):
        from bot.services.advanced_moderation import AdvancedModerationService

        service = AdvancedModerationService()
        normalized = service._normalize_text("расскажи про химию")
        assert "наркотик" not in normalized

    def test_relations_not_replaced(self):
        from bot.services.advanced_moderation import AdvancedModerationService

        service = AdvancedModerationService()
        normalized = service._normalize_text("отношения между странами")
        assert "секс" not in normalized
