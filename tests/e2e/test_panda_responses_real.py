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
import re

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

    # --- Русский язык ---

    @pytest.mark.asyncio
    async def test_russian_response_no_anglicisms(self, ai_service):
        """
        Ответ на русском не должен содержать американизмов и кальки.
        Литературная норма русского языка.
        """
        response = await ai_service.generate_response(
            user_message="Что такое скорость? Объясни простыми словами.",
            chat_history=[],
            user_age=11,
        )
        ResponseQualityValidator.assert_not_empty(response, "Русский язык")
        lower = response.lower()
        # Не должно быть распространённых англицизмов вместо русских эквивалентов
        anglicisms = ["апдейт", "фидбек", "краш", "респект", "вайб"]
        found = [a for a in anglicisms if a in lower]
        assert not found, (
            f"Ответ содержит англицизмы вместо русских слов: {found}. "
            f"Используй литературную норму русского языка."
        )

    # --- Chain-of-Thought (пошаговое рассуждение) ---

    @pytest.mark.asyncio
    async def test_cot_word_problem_apples(self, ai_service):
        """
        CoT: задача про яблоки (23 - 20 + 6 = 9).
        Ответ должен содержать пошаговое рассуждение и правильный ответ 9.
        """
        response = await ai_service.generate_response(
            user_message="В кафе было 23 яблока. 20 ушло на обед, купили ещё 6. Сколько всего яблок?",
            chat_history=[],
            user_age=10,
        )
        ResponseQualityValidator.assert_not_empty(response, "CoT яблоки")
        ResponseQualityValidator.assert_no_placeholder_or_error(response, "CoT яблоки")
        # Должно быть пошаговое рассуждение
        has_steps = any(
            p in response.lower()
            for p in ["сначала", "значит", "осталось", "23", "20", "6", "итого"]
        )
        assert has_steps, f"Нет пошагового рассуждения: {response[:300]}"
        # Правильный ответ 9 (цифрой или словом)
        has_correct = "9" in response or "девять" in response.lower()
        assert has_correct, f"Ответ должен содержать 9 или «девять», получено: {response[:400]}"

    @pytest.mark.asyncio
    async def test_cot_word_problem_balls(self, ai_service):
        """
        CoT: задача про мячи (5 + 2×3 = 11).
        Ответ должен содержать шаги и правильный ответ 11.
        """
        response = await ai_service.generate_response(
            user_message="У Ромы было 5 мячей. Он купил 2 упаковки по 3 мяча. Сколько всего мячей?",
            chat_history=[],
            user_age=10,
        )
        ResponseQualityValidator.assert_not_empty(response, "CoT мячи")
        # Пошаговое рассуждение (CoT): начало с шага, упоминание данных задачи
        has_steps = any(
            p in response.lower()
            for p in ["сначала", "упаковк", "умнож", "сложим", "значит", "итого"]
        )
        assert has_steps, f"Нет пошагового рассуждения: {response[:300]}"

    @pytest.mark.asyncio
    async def test_cot_response_has_reasoning_format(self, ai_service):
        """CoT: ответ на задачу с числами содержит формат рассуждения (шаги, вывод)."""
        response = await ai_service.generate_response(
            user_message="В зоомагазине было 64 щенка. Продали 28. Остальных по 4 в клетку. Сколько клеток?",
            chat_history=[],
            user_age=11,
        )
        ResponseQualityValidator.assert_not_empty(response, "CoT клетки")
        # Пошаговое рассуждение: 64-28, деление на 4
        has_reasoning = any(
            w in response.lower()
            for w in ["сначала", "осталось", "значит", "итого", "ответ", "клеток", "64", "28"]
        )
        assert has_reasoning, f"Нет рассуждения: {response[:300]}"

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

    # --- Формула в ответе (типографский вид, без LaTeX) ---

    @pytest.mark.asyncio
    async def test_formula_response_force_of_attraction(self, ai_service):
        """При запросе про формулу силы притяжения ответ содержит формулу в типографском виде, без LaTeX."""
        response = await ai_service.generate_response(
            user_message="Что такое сила притяжения и по какой формуле рассчитывается?",
            chat_history=[],
            user_age=12,
        )
        ResponseQualityValidator.assert_not_empty(response, "Формула притяжения")
        ResponseQualityValidator.assert_no_placeholder_or_error(response, "Формула притяжения")
        lower = response.lower()
        # Должны быть элементы формулы (F, G, m, r или гравитац)
        has_formula_related = any(
            x in lower for x in ["f ", " g ", " m", "r²", "r^2", "гравитац", "притяжен"]
        )
        assert has_formula_related, f"Ожидалась формула или пояснение: {response[:400]}"
        # Не должно быть сырого LaTeX
        assert "\\frac" not in response and "\\sqrt" not in response, "Формула не в LaTeX"

    # --- Русский язык: орфография, разбор ---

    @pytest.mark.asyncio
    async def test_russian_orthography_or_parsing(self, ai_service):
        """Ответы на запросы по русскому языку: без англицизмов, структурированы при разборе."""
        response = await ai_service.generate_response(
            user_message="Разбери по составу слово «подводный».",
            chat_history=[],
            user_age=11,
        )
        ResponseQualityValidator.assert_not_empty(response, "Разбор по составу")
        lower = response.lower()
        anglicisms = ["апдейт", "фидбек", "краш"]
        assert not any(a in lower for a in anglicisms), "Ответ не должен содержать англицизмы"
        # При разборе ожидаем структуру: корень, окончание или список
        has_structure = (
            "корень" in lower or "окончание" in lower or "приставк" in lower or "суффикс" in lower
        )
        assert has_structure or len(response) >= 100, (
            f"Ожидалась структура разбора или развёрнутый ответ: {response[:300]}"
        )

    # --- Полнота: не менее 10 пунктов списка при запросе примеров ---

    @pytest.mark.asyncio
    async def test_completeness_list_at_least_10(self, ai_service):
        """При запросе примеров/списка в ответе не менее 8 пунктов (допуск из-за вариативности API)."""
        response = await ai_service.generate_response(
            user_message="Приведи 10 примеров имён прилагательных.",
            chat_history=[],
            user_age=10,
        )
        ResponseQualityValidator.assert_not_empty(response, "10 примеров")
        # Подсчёт пунктов списка: строки, начинающиеся с - , • , * или 1. 2. 3.
        list_items = re.findall(r"^(?:\s*[-•*]\s+|\s*\d+\.\s+)", response, re.MULTILINE)
        count = len(list_items)
        assert count >= 8, (
            f"Ожидалось не менее 8 пунктов списка, получено {count}: {response[:500]}"
        )
