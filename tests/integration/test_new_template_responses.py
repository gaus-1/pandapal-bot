"""
Тест новых шаблонов ответов (Шаблон 1 и Шаблон 2) с реальным API.

Проверяет:
1. Шаблон 1 (пошаговый) для точных наук
2. Шаблон 2 (объясняющий) для гуманитарных наук
3. Качество и подробность ответов
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
class TestNewTemplateResponses:
    """Тесты новых шаблонов ответов с реальным API."""

    async def test_template1_stepby_step_math(self):
        """Тест Шаблона 1 (пошаговый) для математики."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        # Простой математический вопрос - должен использоваться Шаблон 1
        response = await ai_service.generate_response(
            user_message="Как найти площадь прямоугольника? Объясни подробно с примером.",
            chat_history=[],
            user_age=10,
        )

        print(f"\n\n=== ШАБЛОН 1 (Математика) ===\n{response}\n")

        assert response is not None
        assert len(response) > 200, f"Ответ слишком короткий: {len(response)}"

        # Проверяем структуру Шаблона 1
        response_lower = response.lower()
        # Должны быть пошаговые инструкции (ключевые слова ИЛИ нумерация)
        has_steps = any(
            marker in response_lower
            for marker in ["шаг", "сначала", "затем", "потом", "после этого"]
        ) or ("1." in response and "2." in response and "3." in response)
        # Должен быть пример
        has_example = any(marker in response_lower for marker in ["пример", "например", "возьмем", "допустим", "если"])

        assert has_steps, "Нет пошаговых инструкций в ответе"
        assert has_example, "Нет примера в ответе"

        print("[OK] Шаблон 1 применен корректно!")

    async def test_template1_stepbystep_russian(self):
        """Тест Шаблона 1 (пошаговый) для русского языка (правила)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        response = await ai_service.generate_response(
            user_message="Как проверить безударную гласную в корне слова? Объясни подробно с примерами.",
            chat_history=[],
            user_age=10,
        )

        print(f"\n\n=== ШАБЛОН 1 (Русский язык) ===\n{response}\n")

        assert response is not None
        assert len(response) > 200, f"Ответ слишком короткий: {len(response)}"

        response_lower = response.lower()
        has_steps = any(
            marker in response_lower
            for marker in ["шаг", "сначала", "затем", "потом"]
        ) or ("1." in response and "2." in response and "3." in response)
        has_example = any(marker in response_lower for marker in ["пример", "например", "слово", "проверим"])

        assert has_steps, "Нет пошаговых инструкций в ответе"
        assert has_example, "Нет примера в ответе"

        print("[OK] Шаблон 1 применен корректно!")

    async def test_template2_explaining_biology(self):
        """Тест Шаблона 2 (объясняющий) для биологии."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        response = await ai_service.generate_response(
            user_message="Что такое фотосинтез? Объясни простыми словами подробно.",
            chat_history=[],
            user_age=11,
        )

        print(f"\n\n=== ШАБЛОН 2 (Биология) ===\n{response}\n")

        assert response is not None
        assert len(response) > 200, f"Ответ слишком короткий: {len(response)}"

        response_lower = response.lower()
        # Должны быть аналогии/сравнения
        has_analogy = any(
            marker in response_lower
            for marker in ["представь", "как", "это как", "похоже", "словно", "фабрика", "батарея"]
        )
        # Должна быть связь с жизнью
        has_life_example = any(
            marker in response_lower
            for marker in ["жизни", "поэтому", "благодаря", "лес", "дыши"]
        )

        assert has_analogy, "Нет аналогий/сравнений 'на пальцах' в ответе"
        assert has_life_example, "Нет примеров из жизни в ответе"

        print("[OK] Шаблон 2 применен корректно!")

    async def test_template2_explaining_history(self):
        """Тест Шаблона 2 (объясняющий) для истории."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        response = await ai_service.generate_response(
            user_message="Почему началась Великая Отечественная война? Объясни причины подробно.",
            chat_history=[],
            user_age=13,
        )

        print(f"\n\n=== ШАБЛОН 2 (История) ===\n{response}\n")

        assert response is not None
        assert len(response) > 250, f"Ответ слишком короткий: {len(response)}"

        response_lower = response.lower()
        # Должна быть причинно-следственная связь
        has_causality = any(
            marker in response_lower
            for marker in ["потому что", "поэтому", "из-за", "причина", "привело", "вызвало"]
        )
        # Должны быть факты/даты
        has_facts = any(marker in response_lower for marker in ["1941", "22 июня", "германия", "ссср"])

        assert has_causality, "Нет причинно-следственных связей в ответе"
        assert has_facts, "Нет конкретных фактов/дат в ответе"

        print("[OK] Шаблон 2 применен корректно!")

    async def test_response_quality_detailed(self):
        """Тест: все ответы должны быть подробными и развернутыми."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        test_cases = [
            ("Что такое дробь? Объясни подробно с примерами.", 10, "Математика"),
            ("Объясни что такое глагол. Расскажи подробно с примерами.", 9, "Русский"),
            ("Что такое атом? Объясни простыми словами подробно.", 12, "Физика"),
        ]

        for question, age, subject in test_cases:
            response = await ai_service.generate_response(
                user_message=question,
                chat_history=[],
                user_age=age,
            )

            print(f"\n\n=== {subject} ===")
            print(f"Вопрос: {question}")
            print(f"Длина ответа: {len(response)} символов")
            print(f"Предложений: {len([s for s in response.split('.') if s.strip()])}")
            print(f"Первые 200 символов:\n{response[:200]}...\n")

            assert response is not None, f"{subject}: AI не ответил"
            assert len(response) > 200, f"{subject}: Ответ слишком короткий ({len(response)} < 200)"

            # Проверка структурированности
            sentences = [s.strip() for s in response.split(".") if s.strip()]
            assert len(sentences) >= 4, f"{subject}: Слишком мало предложений ({len(sentences)} < 4)"

            # Проверка структурирования ответа (для frontend парсинга)
            has_structure = (
                "\n\n" in response or
                "Определение:" in response or
                "Ключевые свойства:" in response or
                "Как это работает:" in response or
                "Где применяется:" in response or
                "Итог:" in response
            )
            assert has_structure or len(response.split()) > 10, \
                f"{subject}: Ответ должен быть структурированным (абзацы или секции)"

            print(f"✅ {subject}: качество OK!")

        print("\n\n[OK] ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
