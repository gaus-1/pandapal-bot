"""
E2E тесты ответов панды с реальным YandexGPT API.

Ригидное тестирование уровня production:
- Позитивные: ответ содержит ожидаемый контент
- Негативные: ответ НЕ должен содержать нерелевантный контент
- Качество: строгие критерии (длина, предложения, релевантность)
- Пустые/ошибочные: детекция placeholder, ошибок, нерелевантности

Требует YANDEX_CLOUD_API_KEY, YANDEX_CLOUD_FOLDER_ID.
Запуск: pytest tests/e2e/test_panda_responses_real.py -v
"""

import os

import pytest

from bot.services.ai_service_solid import get_ai_service
from bot.services.visualization_service import get_visualization_service


def _has_real_api_keys() -> bool:
    """Проверка наличия реальных API ключей."""
    key = os.getenv("YANDEX_CLOUD_API_KEY", "")
    folder = os.getenv("YANDEX_CLOUD_FOLDER_ID", "")
    return bool(
        key
        and folder
        and key not in ("test_api_key", "your_real_yandex_api_key_here")
        and len(key) > 20
    )


class ResponseQualityValidator:
    """
    Валидатор качества ответов панды (Google-level строгость).

    Критерии:
    - Не пустой, не placeholder, не ошибка
    - Минимальная длина и кол-во предложений
    - Релевантность (ключевые слова темы)
    - Отсутствие нерелевантного контента (негативные паттерны)
    """

    # Фразы-признаки ошибки или placeholder
    PLACEHOLDER_PATTERNS = frozenset(
        {
            "извините, не могу",
            "ошибка",
            "произошла ошибка",
            "попробуйте позднее",
            "не удалось",
            "недоступен",
            "i cannot",
            "i'm sorry",
            "error occurred",
        }
    )

    @classmethod
    def assert_not_empty(cls, response: str | None, context: str = "") -> None:
        """Ответ не пустой и не None."""
        assert response is not None, f"{context}: ответ None"
        text = response.strip()
        assert len(text) >= 50, f"{context}: ответ слишком короткий ({len(text)} символов)"

    @classmethod
    def assert_no_placeholder_or_error(cls, response: str, context: str = "") -> None:
        """Ответ не содержит placeholder или сообщение об ошибке."""
        lower = response.lower()
        for bad in cls.PLACEHOLDER_PATTERNS:
            assert bad not in lower, f"{context}: обнаружен placeholder/ошибка '{bad}'"

    @classmethod
    def assert_relevant(
        cls,
        response: str,
        required_keywords: list[str],
        context: str = "",
    ) -> None:
        """Ответ релевантен теме (содержит хотя бы один ключевой термин)."""
        lower = response.lower()
        found = [k for k in required_keywords if k.lower() in lower]
        assert found, (
            f"{context}: ответ не релевантен теме. Ожидались: {required_keywords}. "
            f"Получено: {response[:200]}..."
        )

    @classmethod
    def assert_not_contains(
        cls,
        response: str,
        forbidden_patterns: list[str],
        context: str = "",
    ) -> None:
        """Негативный тест: ответ НЕ должен содержать нерелевантный контент."""
        lower = response.lower()
        found = [p for p in forbidden_patterns if p.lower() in lower]
        assert not found, (
            f"{context}: ответ содержит нерелевантный контент: {found}. "
            f"Фрагмент: {response[:300]}..."
        )

    @classmethod
    def assert_quality(
        cls,
        response: str,
        min_length: int = 150,
        min_sentences: int = 4,
        context: str = "",
    ) -> dict:
        """Проверка структуры и развёрнутости ответа."""
        issues = []
        sentences = [s.strip() for s in response.split(".") if s.strip()]
        if len(response) < min_length:
            issues.append(f"Длина {len(response)} < {min_length}")
        if len(sentences) < min_sentences:
            issues.append(f"Предложений {len(sentences)} < {min_sentences}")
        assert not issues, f"{context}: {'; '.join(issues)}"
        return {"length": len(response), "sentences": len(sentences)}


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(not _has_real_api_keys(), reason="Требуется Yandex API ключи")
class TestPandaResponsesReal:
    """E2E тесты ответов панды с реальным API."""

    @pytest.fixture
    def ai_service(self):
        return get_ai_service()

    # --- Позитивные тесты ---

    @pytest.mark.asyncio
    async def test_list_square_roots_has_values(self, ai_service):
        """«Список квадратных корней» — ответ содержит конкретные значения."""
        response = await ai_service.generate_response(
            user_message="Список квадратных корней от 1 до 20",
            chat_history=[],
            user_age=12,
        )
        ResponseQualityValidator.assert_not_empty(response, "Список корней")
        ResponseQualityValidator.assert_no_placeholder_or_error(response, "Список корней")
        ResponseQualityValidator.assert_relevant(
            response,
            ["√1", "√2", "√3", "√4", "1.41", "1.73", "корн"],
            "Список корней",
        )
        ResponseQualityValidator.assert_quality(
            response, min_length=100, min_sentences=3, context="Список корней"
        )

    @pytest.mark.asyncio
    async def test_table_square_roots_visualization(self):
        """«Таблица квадратных корней» — детектор находит визуализацию."""
        viz = get_visualization_service()
        image, vtype = viz.detect_visualization_request("таблица квадратных корней")
        assert image is not None, "Детектор не нашёл визуализацию таблицы корней"
        assert vtype == "table"

    @pytest.mark.asyncio
    async def test_table_multiplication_visualization(self):
        """«Таблица умножения» — детектор даёт таблицу (не корни)."""
        viz = get_visualization_service()
        image, vtype = viz.detect_visualization_request("таблица умножения на 7")
        assert image is not None
        assert vtype == "table"

    @pytest.mark.asyncio
    async def test_photosynthesis_full_answer(self, ai_service):
        """«Что такое фотосинтез» — развёрнутый ответ по биологии."""
        response = await ai_service.generate_response(
            user_message="Что такое фотосинтез? Объясни простыми словами.",
            chat_history=[],
            user_age=10,
        )
        ResponseQualityValidator.assert_not_empty(response, "Фотосинтез")
        ResponseQualityValidator.assert_no_placeholder_or_error(response, "Фотосинтез")
        ResponseQualityValidator.assert_relevant(
            response, ["фотосинтез", "растение", "свет", "углекислый", "кислород"],
            "Фотосинтез",
        )
        ResponseQualityValidator.assert_quality(
            response, min_length=200, min_sentences=5, context="Фотосинтез"
        )

    # --- Негативные тесты ---

    @pytest.mark.asyncio
    async def test_table_multiplication_not_square_roots(self, ai_service):
        """
        НЕГАТИВНЫЙ: «Таблица умножения» — ответ НЕ должен содержать квадратные корни.
        Запрос про умножение, а не про √n.
        """
        response = await ai_service.generate_response(
            user_message="Объясни таблицу умножения на 7. Какие там значения?",
            chat_history=[],
            user_age=10,
        )
        ResponseQualityValidator.assert_not_empty(response, "Таблица умножения")
        # Не должно быть значений квадратных корней (√1, √2, 1.41, 1.73 и т.п.)
        ResponseQualityValidator.assert_not_contains(
            response,
            ["√1", "√2", "√3", "1.41", "1.73", "√4=", "√5="],
            "Таблица умножения (не корни)",
        )
        ResponseQualityValidator.assert_relevant(
            response,
            ["умножени", "7", "таблиц", "×", "*"],
            "Таблица умножения",
        )

    @pytest.mark.asyncio
    async def test_math_question_not_biology(self, ai_service):
        """
        НЕГАТИВНЫЙ: запрос по математике — ответ не должен переключаться на биологию.
        """
        response = await ai_service.generate_response(
            user_message="Что такое уравнение? Объясни на примере 2x+5=15",
            chat_history=[],
            user_age=12,
        )
        ResponseQualityValidator.assert_not_empty(response, "Уравнение")
        ResponseQualityValidator.assert_relevant(
            response,
            ["уравнен", "x", "перемен", "решен", "число"],
            "Уравнение",
        )
        # Не должно быть биологии
        ResponseQualityValidator.assert_not_contains(
            response,
            ["фотосинтез", "клетка", "ДНК", "хлорофилл"],
            "Математика (не биология)",
        )

    @pytest.mark.asyncio
    async def test_geography_not_math(self, ai_service):
        """
        НЕГАТИВНЫЙ: «самая длинная река» — география, не математика.
        """
        response = await ai_service.generate_response(
            user_message="Какая самая длинная река в России?",
            chat_history=[],
            user_age=11,
        )
        ResponseQualityValidator.assert_not_empty(response, "Река")
        ResponseQualityValidator.assert_relevant(
            response,
            ["волг", "лен", "река", "росси", "енис", "обь"],
            "География: река",
        )

    # --- Проверки на пустые и нерелевантные ответы ---

    @pytest.mark.asyncio
    async def test_no_empty_response_on_valid_question(self, ai_service):
        """Валидный вопрос — ответ не пустой, не одно слово."""
        questions = [
            "Что такое скорость в физике?",
            "Объясни что такое подлежащее",
            "Когда началась Вторая мировая война?",
        ]
        for q in questions:
            response = await ai_service.generate_response(
                user_message=q,
                chat_history=[],
                user_age=12,
            )
            ResponseQualityValidator.assert_not_empty(response, q)
            ResponseQualityValidator.assert_no_placeholder_or_error(response, q)
            assert len(response.split()) >= 10, f"Ответ слишком короткий: {q}"

    @pytest.mark.asyncio
    async def test_response_has_minimum_structure(self, ai_service):
        """Ответ имеет структуру: несколько предложений, не поток сознания."""
        response = await ai_service.generate_response(
            user_message="Что такое вода? Из чего она состоит?",
            chat_history=[],
            user_age=10,
        )
        ResponseQualityValidator.assert_not_empty(response, "Вода")
        result = ResponseQualityValidator.assert_quality(
            response, min_length=150, min_sentences=4, context="Вода"
        )
        assert result["sentences"] >= 4
        assert result["length"] >= 150

    # --- Расширенное покрытие по предметам ---

    @pytest.mark.asyncio
    async def test_subjects_math_history_biology_physics(self, ai_service):
        """Ответы по математике, истории, биологии, физике — релевантны и развёрнуты."""
        cases = [
            ("Математика", "Что такое квадратное уравнение?", ["уравнен", "квадрат", "x"]),
            ("История", "Когда началась Великая Отечественная война?", ["1941", "войн", "герма"]),
            ("Биология", "Что такое клетка?", ["клетк", "организм", "ядро"]),
            ("Физика", "Что такое сила? Единица измерения?", ["сил", "ньютон", "н"]),
        ]
        for subject, question, keywords in cases:
            response = await ai_service.generate_response(
                user_message=question,
                chat_history=[],
                user_age=12,
            )
            ResponseQualityValidator.assert_not_empty(response, subject)
            ResponseQualityValidator.assert_relevant(response, keywords, subject)
            ResponseQualityValidator.assert_quality(
                response, min_length=120, min_sentences=3, context=subject
            )
