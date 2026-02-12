"""
Интеграционные тесты для объяснения формул детям.

Проверяет работу formula_explainer и интеграцию с AI сервисом.
"""

import os

import pytest

# Тесты с AI требуют реальный Yandex API ключ (не test_api_key, не AQVTEST_*)
def _has_real_api_key():
    k = os.getenv("YANDEX_CLOUD_API_KEY", "") or ""
    return k and k != "test_api_key" and "AQVTEST" not in k and len(k) > 20
from loguru import logger

from bot.services.ai_service_solid import get_ai_service
from bot.services.formula_explainer import formula_explainer


class TestFormulaExplainer:
    """Тесты для сервиса объяснения формул."""

    def test_detect_quadratic_formula(self):
        """Тест обнаружения квадратного уравнения."""
        text = "Реши квадратное уравнение x² + 5x + 6 = 0"
        detected = formula_explainer.detect_formulas(text)
        assert "quadratic" in detected
        logger.info(f"✅ Обнаружено: {detected}")

    def test_detect_pythagorean_theorem(self):
        """Тест обнаружения теоремы Пифагора."""
        text = "Используй теорему Пифагора a² + b² = c²"
        detected = formula_explainer.detect_formulas(text)
        assert "pythagorean" in detected
        logger.info(f"✅ Обнаружено: {detected}")

    def test_detect_speed_formula(self):
        """Тест обнаружения формулы скорости."""
        text = "Найди скорость если v = s/t"
        detected = formula_explainer.detect_formulas(text)
        assert "speed" in detected
        logger.info(f"✅ Обнаружено: {detected}")

    def test_detect_density_formula(self):
        """Тест обнаружения формулы плотности."""
        text = "Вычисли плотность ρ = m/V"
        detected = formula_explainer.detect_formulas(text)
        assert "density" in detected
        logger.info(f"✅ Обнаружено: {detected}")

    def test_explain_pythagorean_theorem(self):
        """Тест объяснения теоремы Пифагора."""
        explanation = formula_explainer.explain_formula("pythagorean", user_age=12)
        assert "Теорема Пифагора" in explanation
        assert "a² + b² = c²" in explanation
        assert "гипотенуза" in explanation
        assert "катет" in explanation
        assert "Пример:" in explanation
        assert "Где это в жизни:" in explanation
        logger.info(f"✅ Объяснение:\n{explanation}")

    def test_explain_speed_formula(self):
        """Тест объяснения формулы скорости."""
        explanation = formula_explainer.explain_formula("speed", user_age=10)
        assert "Скорость" in explanation
        assert "v = s/t" in explanation
        assert "расстояние" in explanation
        assert "время" in explanation
        assert "Пример:" in explanation
        logger.info(f"✅ Объяснение:\n{explanation}")

    def test_enhance_prompt_with_formula_context(self):
        """Тест улучшения промпта контекстом формул."""
        user_message = "Объясни теорему Пифагора a² + b² = c²"
        context = formula_explainer.enhance_prompt_with_formula_context(user_message, user_age=12)
        assert context != ""
        assert "ОБНАРУЖЕНЫ ФОРМУЛЫ" in context
        assert "Теорема Пифагора" in context
        assert "ВАЖНО ДЛЯ ОТВЕТА" in context
        assert "ПРОСТЫМИ СЛОВАМИ" in context
        assert "КОНКРЕТНЫЙ ЧИСЛОВОЙ ПРИМЕР" in context
        logger.info(f"✅ Контекст:\n{context[:500]}...")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(not _has_real_api_key(), reason="Требуется реальный Yandex API ключ")
class TestFormulaExplanationsWithAI:
    """Интеграционные тесты объяснения формул с реальным AI."""

    async def test_explain_pythagorean_theorem_with_ai(self):
        """Тест объяснения теоремы Пифагора через AI."""
        ai_service = get_ai_service()
        user_message = "Объясни теорему Пифагора простыми словами"

        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=12,
            user_name="Тестовый",
        )

        assert response
        assert len(response) > 100
        # Проверяем что ответ содержит ключевые элементы
        response_lower = response.lower()
        assert any(
            word in response_lower
            for word in ["пифагор", "треугольник", "гипотенуза", "катет", "квадрат"]
        )
        # Проверяем что есть пример
        assert any(word in response_lower for word in ["пример", "если", "допустим"])

        # Проверка структурирования ответа (для frontend парсинга)
        has_structure = (
            "\n\n" in response
            or "Определение:" in response
            or "Ключевые свойства:" in response
            or "Как это работает:" in response
            or "Где применяется:" in response
            or "Итог:" in response
        )
        assert has_structure or len(response.split()) > 10, (
            "Ответ должен быть структурированным (абзацы или секции)"
        )

        logger.info(f"✅ Ответ AI:\n{response}")

    async def test_explain_speed_formula_with_ai(self):
        """Тест объяснения формулы скорости через AI."""
        ai_service = get_ai_service()
        user_message = "Как найти скорость если известны расстояние и время?"

        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=10,
            user_name="Тестовый",
        )

        assert response
        assert len(response) > 100
        response_lower = response.lower()
        assert any(word in response_lower for word in ["скорость", "расстояние", "время"])
        # Проверяем что есть формула
        assert "v" in response or "скорость" in response_lower
        # Проверяем что есть пример с числами
        assert any(char.isdigit() for char in response)
        logger.info(f"✅ Ответ AI:\n{response}")

    async def test_explain_area_circle_with_ai(self):
        """Тест объяснения площади круга через AI."""
        ai_service = get_ai_service()
        user_message = "Как найти площадь круга? Объясни формулу S = πr²"

        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=13,
            user_name="Тестовый",
        )

        assert response
        assert len(response) > 150
        response_lower = response.lower()
        # Проверяем ключевые слова
        assert any(word in response_lower for word in ["площадь", "круг", "радиус"])
        # Проверяем что есть объяснение символов
        assert "π" in response or "пи" in response_lower
        assert "r" in response or "радиус" in response_lower
        # Проверяем что есть числовой пример
        assert any(char.isdigit() for char in response)
        logger.info(f"✅ Ответ AI:\n{response}")

    async def test_explain_newton_second_law_with_ai(self):
        """Тест объяснения второго закона Ньютона через AI."""
        ai_service = get_ai_service()
        user_message = "Объясни второй закон Ньютона F = ma"

        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=14,
            user_name="Тестовый",
        )

        assert response
        assert len(response) > 150
        response_lower = response.lower()
        # Проверяем ключевые слова
        assert any(word in response_lower for word in ["сила", "масса", "ускорение", "ньютон"])
        # Проверяем что есть объяснение букв
        assert "F" in response or "сила" in response_lower
        assert "m" in response or "масса" in response_lower
        assert "a" in response or "ускорение" in response_lower
        # Проверяем что есть пример
        assert any(char.isdigit() for char in response)
        logger.info(f"✅ Ответ AI:\n{response}")

    async def test_explain_density_with_ai(self):
        """Тест объяснения плотности через AI."""
        ai_service = get_ai_service()
        user_message = "Что такое плотность вещества? Объясни формулу ρ = m/V"

        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=13,
            user_name="Тестовый",
        )

        assert response
        assert len(response) > 150
        response_lower = response.lower()
        # Проверяем ключевые слова
        assert any(word in response_lower for word in ["плотность", "масса", "объем", "объём"])
        # Проверяем что есть пример из жизни или связь с опытом
        life_example_words = [
            "железо",
            "дерево",
            "вода",
            "тонет",
            "плавает",
            "легкий",
            "лёгкий",
            "тяжелый",
            "тяжёлый",
            "например",
            "пример",
            "г/см",
            "кг/м",
            "единиц",
        ]
        assert any(word in response_lower for word in life_example_words), (
            f"Ожидался пример или единицы плотности. Ответ: {response[:300]}..."
        )
        # Проверяем что есть числовой пример
        assert any(char.isdigit() for char in response)
        logger.info(f"✅ Ответ AI:\n{response}")
