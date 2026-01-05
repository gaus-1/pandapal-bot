"""
Реальные интеграционные тесты для ответов AI по всем школьным предметам.

Проверяет:
- Ответы AI по текстовым вопросам по ВСЕМ предметам
- Ответы AI по фото с заданиями по ВСЕМ предметам
- Использует реальные Yandex API (GPT, Vision, Translate)
"""

import os
import sys

import pytest


# Проверка наличия реального API ключа
def _check_real_api_key():
    """Проверяет наличие реального API ключа в env или settings."""
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
@pytest.mark.slow
class TestSubjectsTextRealAPI:
    """Тесты ответов AI по текстовым вопросам по всем предметам."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_math_text_question(self):
        """Тест ответа AI на вопрос по математике."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Реши уравнение: 2x + 5 = 15. Объясни решение пошагово."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=12,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"
        assert (
            "5" in response or "x = 5" in response or "пять" in response.lower()
        ), f"Ответ должен содержать решение: {response[:200]}"

        print(f"\n[OK] Math (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_russian_text_question(self):
        """Тест ответа AI на вопрос по русскому языку."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое подлежащее и сказуемое? Объясни простыми словами."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Russian (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_literature_text_question(self):
        """Тест ответа AI на вопрос по литературе."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Кто написал 'Капитанскую дочку'? О чем это произведение?"

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=14,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"
        assert (
            "пушкин" in response.lower() or "Пушкин" in response
        ), f"Ответ должен содержать автора: {response[:200]}"

        print(f"\n[OK] Literature (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_english_text_question(self):
        """Тест ответа AI на вопрос по английскому языку."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое Present Simple? Объясни простыми словами и приведи примеры."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=11,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] English (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_physics_text_question(self):
        """Тест ответа AI на вопрос по физике."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое скорость? Объясни простыми словами для ребенка."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=11,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Physics (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_chemistry_text_question(self):
        """Тест ответа AI на вопрос по химии."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое вода? Из каких элементов она состоит?"

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=12,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Chemistry (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_biology_text_question(self):
        """Тест ответа AI на вопрос по биологии."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое фотосинтез? Объясни простыми словами."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=11,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Biology (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_geography_text_question(self):
        """Тест ответа AI на вопрос по географии."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Какая столица Франции? Расскажи про этот город."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"
        assert (
            "париж" in response.lower() or "Париж" in response
        ), f"Ответ должен содержать столицу: {response[:200]}"

        print(f"\n[OK] Geography (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_history_text_question(self):
        """Тест ответа AI на вопрос по истории."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Когда началась Великая Отечественная война? Расскажи кратко."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=13,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"
        assert (
            "1941" in response or "тысяча девятьсот сорок первый" in response.lower()
        ), f"Ответ должен содержать год: {response[:200]}"

        print(f"\n[OK] History (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_informatics_text_question(self):
        """Тест ответа AI на вопрос по информатике."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое алгоритм? Объясни простыми словами и приведи пример."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=12,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Informatics (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_social_studies_text_question(self):
        """Тест ответа AI на вопрос по обществознанию."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое государство? Объясни простыми словами для ребенка."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=13,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Social Studies (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_german_text_question(self):
        """Тест ответа AI на вопрос по немецкому языку."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое артикль в немецком языке? Объясни der, die, das."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=12,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] German (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_french_text_question(self):
        """Тест ответа AI на вопрос по французскому языку."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое артикли le и la во французском языке? Объясни простыми словами."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=11,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] French (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_spanish_text_question(self):
        """Тест ответа AI на вопрос по испанскому языку."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Как сказать 'привет' по-испански? Объясни произношение."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Spanish (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_art_text_question(self):
        """Тест ответа AI на вопрос по ИЗО."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое композиция в рисунке? Объясни простыми словами."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=9,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Art (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_music_text_question(self):
        """Тест ответа AI на вопрос по музыке."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое нота? Объясни простыми словами для ребенка."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=8,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Music (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_technology_text_question(self):
        """Тест ответа AI на вопрос по труду (технологии)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Как сделать простую поделку из бумаги? Объясни пошагово."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Technology (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_pe_text_question(self):
        """Тест ответа AI на вопрос по физкультуре."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Какие упражнения полезны для здоровья? Объясни простыми словами."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=11,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] PE (text): {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_safety_text_question(self):
        """Тест ответа AI на вопрос по ОБЖ."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что делать при пожаре? Объясни правила безопасности простыми словами."

        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=12,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, "Ответ слишком короткий"

        print(f"\n[OK] Safety (text): {response[:150]}...")


@pytest.mark.integration
@pytest.mark.slow
class TestSubjectsPhotoRealAPI:
    """Тесты ответов AI по фото с заданиями по всем предметам."""

    def _create_test_image_with_text(self, text: str) -> bytes:
        """Создает тестовое изображение с текстом."""
        try:
            import io

            from PIL import Image, ImageDraw, ImageFont

            img = Image.new("RGB", (600, 200), color="white")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except Exception:
                font = ImageFont.load_default()

            draw.text((20, 80), text, fill="black", font=font)

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()
        except ImportError:
            pytest.skip("PIL/Pillow не установлен")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_math_photo_question(self):
        """Тест ответа AI на фото с математической задачей."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Реши: 15 + 27 = ?")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Реши эту задачу и объясни решение",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Math (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_russian_photo_question(self):
        """Тест ответа AI на фото с заданием по русскому языку."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text(
            "Подчеркни подлежащее и сказуемое: Мама готовит обед."
        )

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни что такое подлежащее и сказуемое",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Russian (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_literature_photo_question(self):
        """Тест ответа AI на фото с вопросом по литературе."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("А.С. Пушкин - Капитанская дочка")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="О чем это произведение?",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Literature (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_physics_photo_question(self):
        """Тест ответа AI на фото с задачей по физике."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Что такое сила? F = m * a")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни эту формулу простыми словами",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Physics (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_chemistry_photo_question(self):
        """Тест ответа AI на фото с вопросом по химии."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("H2O - формула воды")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни эту формулу",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Chemistry (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_biology_photo_question(self):
        """Тест ответа AI на фото с вопросом по биологии."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text(
            "Фотосинтез - процесс создания пищи растениями"
        )

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни что это такое",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Biology (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_geography_photo_question(self):
        """Тест ответа AI на фото с вопросом по географии."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Столица Франции - Париж")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Расскажи про этот город",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Geography (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_history_photo_question(self):
        """Тест ответа AI на фото с вопросом по истории."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Великая Отечественная война 1941-1945")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Расскажи про это событие",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] History (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_informatics_photo_question(self):
        """Тест ответа AI на фото с заданием по информатике."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text(
            "Алгоритм: 1. Начать 2. Выполнить действие 3. Завершить"
        )

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни что такое алгоритм",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Informatics (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_social_studies_photo_question(self):
        """Тест ответа AI на фото с вопросом по обществознанию."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Государство - организация власти в стране")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни что такое государство простыми словами",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Social Studies (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_german_photo_question(self):
        """Тест ответа AI на фото с заданием по немецкому языку."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text(
            "der Tisch, die Tür, das Buch - артикли в немецком"
        )

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни артикли der, die, das",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] German (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_french_photo_question(self):
        """Тест ответа AI на фото с заданием по французскому языку."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text(
            "le garçon, la fille - артикли во французском"
        )

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни артикли le и la",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] French (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_spanish_photo_question(self):
        """Тест ответа AI на фото с заданием по испанскому языку."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Hola - привет по-испански")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни как читается это слово",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Spanish (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_art_photo_question(self):
        """Тест ответа AI на фото с заданием по ИЗО."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text(
            "Композиция - расположение элементов в рисунке"
        )

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни что такое композиция",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Art (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_music_photo_question(self):
        """Тест ответа AI на фото с заданием по музыке."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("До, Ре, Ми, Фа, Соль, Ля, Си - ноты")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни что такое ноты",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Music (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_technology_photo_question(self):
        """Тест ответа AI на фото с заданием по труду (технологии)."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Поделка из бумаги - оригами")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни как сделать поделку",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Technology (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_pe_photo_question(self):
        """Тест ответа AI на фото с заданием по физкультуре."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Упражнения для здоровья - зарядка")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни какие упражнения полезны",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] PE (photo): {analysis[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_safety_photo_question(self):
        """Тест ответа AI на фото с заданием по ОБЖ."""
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()

        image_bytes = self._create_test_image_with_text("Правила безопасности при пожаре")

        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes,
            user_question="Объясни что делать при пожаре",
        )

        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "Анализ слишком короткий"

        print(f"\n[OK] Safety (photo): {analysis[:150]}...")
