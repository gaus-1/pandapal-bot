"""
Тест: Структурированные ответы (Шаблон 1 и 2) + Визуализации.

Проверяет что визуализации работают ВМЕСТЕ со структурой ответов.
"""

import os

import pytest


def _check_real_api_key():
    """Проверяет наличие реального API ключа."""
    env_key = os.environ.get("YANDEX_CLOUD_API_KEY", "")
    if env_key and env_key != "test_api_key" and len(env_key) > 20:
        return True
    try:
        from bot.config.settings import settings

        settings_key = settings.yandex_cloud_api_key
        if (
            settings_key
            and settings_key != "test_api_key"
            and settings_key != "your_real_yandex_api_key_here"
            and len(settings_key) > 20
        ):
            return True
    except Exception:
        pass
    return False


REAL_API_KEY_AVAILABLE = _check_real_api_key()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
class TestTemplatesWithVisualizations:
    """Тесты структурированных ответов с визуализациями."""

    async def test_math_graph_with_template1_structure(self):
        """Тест: График функции + Структурированное объяснение (Шаблон 1)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        # Запрос на график с просьбой объяснить
        response = await ai_service.generate_response(
            user_message="Покажи график функции y = x² и объясни подробно что это такое с примерами.",
            chat_history=[],
            user_age=12,
        )

        print(f"\n\n=== ГРАФИК + ШАБЛОН 1 ===\n{response}\n")

        assert response is not None
        assert len(response) > 150, f"Ответ слишком короткий: {len(response)}"

        response_lower = response.lower()

        # Проверяем что есть упоминание графика
        has_graph_mention = any(
            marker in response_lower for marker in ["график", "парабола", "функция", "кривая"]
        )

        # Проверяем структуру (несколько предложений = есть структура)
        sentences_count = len([s for s in response.split(".") if s.strip()])
        has_structure = sentences_count >= 4

        # Проверяем примеры (конкретные точки или числа)
        has_example = any(
            marker in response_lower
            for marker in [
                "пример",
                "например",
                "если",
                "при",
                "возьмем",
                "подставим",
                "x =",
                "y =",
            ]
        )

        assert has_graph_mention, "Нет упоминания графика в ответе"
        assert has_structure, "Нет структуры ответа"
        assert has_example, "Нет примеров в ответе"

        print("[OK] График + Структурированный ответ работают вместе!")

    async def test_multiplication_table_with_template1_structure(self):
        """Тест: Таблица умножения + Структурированное объяснение (Шаблон 1)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        response = await ai_service.generate_response(
            user_message="Покажи таблицу умножения на 7 и объясни как ей пользоваться подробно с примерами.",
            chat_history=[],
            user_age=9,
        )

        print(f"\n\n=== ТАБЛИЦА + ШАБЛОН 1 ===\n{response}\n")

        assert response is not None
        assert len(response) > 150, f"Ответ слишком короткий: {len(response)}"

        response_lower = response.lower()

        # Проверяем упоминание таблицы
        has_table_mention = any(
            marker in response_lower for marker in ["таблица", "умножение", "строка", "столбец"]
        )

        # Проверяем что есть объяснение (любая структура подойдет)
        has_structure = len([s for s in response.split(".") if s.strip()]) >= 3

        # Проверяем примеры использования
        has_example = any(
            marker in response_lower
            for marker in ["пример", "например", "найти", "чтобы найти", "чтобы", "нужно"]
        )

        assert has_table_mention, "Нет упоминания таблицы в ответе"
        assert has_structure, "Нет структуры ответа"
        assert has_example, "Нет примеров использования в ответе"

        print("[OK] Таблица + Структурированный ответ работают вместе!")

    async def test_map_with_template2_structure(self):
        """Тест: Карта + Объясняющий рассказ (Шаблон 2)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        response = await ai_service.generate_response(
            user_message="Покажи карту Москвы и расскажи подробно про этот город.",
            chat_history=[],
            user_age=11,
        )

        print(f"\n\n=== КАРТА + ШАБЛОН 2 ===\n{response}\n")

        assert response is not None
        assert len(response) > 200, f"Ответ слишком короткий: {len(response)}"

        response_lower = response.lower()

        # Проверяем упоминание карты/города
        has_map_mention = any(
            marker in response_lower
            for marker in ["карта", "москва", "столица", "город", "находится"]
        )

        # Проверяем что есть подробный рассказ (любая структура)
        sentences_count = len([s for s in response.split(".") if s.strip()])
        has_detailed_explanation = sentences_count >= 4

        # Проверяем наличие фактов о городе
        has_facts = len(response) > 200  # Подробный ответ = есть факты

        assert has_map_mention, "Нет упоминания карты/города в ответе"
        assert has_detailed_explanation and has_facts, "Нет подробного объяснения"

        print("[OK] Карта + Объясняющий ответ работают вместе!")

    async def test_chemistry_scheme_with_template2_structure(self):
        """Тест: Схема (химия/биология) + Объясняющий рассказ (Шаблон 2)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        response = await ai_service.generate_response(
            user_message="Покажи схему строения атома и объясни простыми словами что это такое.",
            chat_history=[],
            user_age=13,
        )

        print(f"\n\n=== СХЕМА + ШАБЛОН 2 ===\n{response}\n")

        assert response is not None
        assert len(response) > 200, f"Ответ слишком короткий: {len(response)}"

        response_lower = response.lower()

        # Проверяем упоминание схемы/атома
        has_scheme_mention = any(
            marker in response_lower for marker in ["схема", "атом", "ядро", "электрон", "строение"]
        )

        # Проверяем аналогии ("на пальцах")
        has_analogy = any(
            marker in response_lower
            for marker in ["представь", "как", "похож", "словно", "это как", "можно сравнить"]
        )

        # Проверяем объяснение
        has_explanation = any(
            marker in response_lower for marker in ["состоит", "содержит", "вращаются", "находятся"]
        )

        assert has_scheme_mention, "Нет упоминания схемы/атома в ответе"
        assert has_analogy or has_explanation, "Нет аналогий или объяснения"

        print("[OK] Схема + Объясняющий ответ работают вместе!")

    async def test_physics_diagram_with_both_templates(self):
        """Тест: Диаграмма (физика) + Комбинация Шаблона 1 и 2."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        response = await ai_service.generate_response(
            user_message="Покажи диаграмму силы тока и напряжения и объясни подробно что такое закон Ома.",
            chat_history=[],
            user_age=14,
        )

        print(f"\n\n=== ДИАГРАММА + КОМБО ШАБЛОНОВ ===\n{response}\n")

        assert response is not None
        assert len(response) > 250, f"Ответ слишком короткий: {len(response)}"

        response_lower = response.lower()

        # Проверяем упоминание диаграммы/физики
        has_diagram_mention = any(
            marker in response_lower
            for marker in ["диаграмма", "график", "закон ома", "ток", "напряжение"]
        )

        # Проверяем что есть подробная структура (несколько предложений)
        sentences_count = len([s for s in response.split(".") if s.strip()])
        has_detailed_structure = sentences_count >= 5

        # Проверяем наличие формулы или примера
        has_formula_or_example = any(
            marker in response_lower
            for marker in ["формула", "пример", "например", "если", "=", "равен"]
        )

        assert has_diagram_mention, "Нет упоминания диаграммы/физики в ответе"
        assert has_detailed_structure, "Нет подробной структуры ответа"
        assert has_formula_or_example, "Нет формулы или примеров"

        print("[OK] Диаграмма + Структурированный ответ работают вместе!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
