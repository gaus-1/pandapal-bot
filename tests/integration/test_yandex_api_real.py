"""
КРИТИЧЕСКИЕ INTEGRATION ТЕСТЫ - РЕАЛЬНЫЕ YANDEX API
Проверяет что backend ДЕЙСТВИТЕЛЬНО работает с Yandex Cloud БЕЗ МОКОВ!

⚠️ ВАЖНО: Эти тесты используют РЕАЛЬНЫЕ API и тратят деньги!
   Запускать только перед production деплоем!

Запуск:
    pytest tests/integration/test_yandex_api_real.py -v --tb=short
"""

import asyncio
import base64
from pathlib import Path

import pytest

from bot.services.ai_service_solid import get_ai_service
from bot.services.speech_service import SpeechService
from bot.services.vision_service import VisionService


@pytest.mark.integration
@pytest.mark.asyncio
class TestYandexAPIReal:
    """Тесты реальной работы с Yandex API."""

    async def test_yandex_gpt_text_response_real(self):
        """
        CRITICAL: Проверка что YandexGPT РЕАЛЬНО отвечает на текстовые вопросы.
        НЕТ МОКОВ!
        """
        ai_service = get_ai_service()

        # Реальный вопрос для проверки AI
        test_question = "Реши простое уравнение: 2x + 5 = 13. Напиши только ответ в формате x = ?"
        user_age = 10

        # КРИТИЧНО: Реальный запрос к Yandex GPT
        response = await ai_service.generate_response(
            user_message=test_question, chat_history=[], user_age=user_age
        )

        # Проверяем что получили реальный ответ
        assert response is not None, "YandexGPT не вернул ответ!"
        assert len(response) > 0, "YandexGPT вернул пустой ответ!"

        # Проверяем что AI решил уравнение правильно
        # Ответ должен содержать "x = 4" или подобное
        assert "4" in response, f"AI не решил уравнение правильно! Ответ: {response}"

        print(f"\n✅ YandexGPT РЕАЛЬНО работает!")
        print(f"   Вопрос: {test_question}")
        print(f"   Ответ: {response[:200]}...")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_panda_response_quality_no_asterisks_no_glued_real(self):
        """
        Проверка качества ответа панды: нет звёздочек в тексте, нет склеек (PossPossessive, ПомоПомогает).
        Реальный API из env.
        """
        ai_service = get_ai_service()
        question = (
            "Расскажи коротко про личные местоимения в английском: I, you, he. "
            "Дай 3 примера с переводом."
        )
        response = await ai_service.generate_response(
            user_message=question, chat_history=[], user_age=12
        )
        assert response is not None and len(response) > 0
        assert "*" not in response, f"В ответе не должно быть звёздочек: {response[:300]}"
        assert "PossPossessive" not in response
        assert "ПомоПомогает" not in response
        assert "неодушевлённыхвлённых" not in response

    async def test_yandex_speechkit_audio_recognition_real(self):
        """
        CRITICAL: Проверка что SpeechKit РЕАЛЬНО распознаёт аудио.
        НЕТ МОКОВ!

        ⚠️ Требует реальный аудио файл для теста!
        """
        speech_service = SpeechService()

        # Для полноценного теста нужен реальный OGG файл с голосом
        # Создаём минимальный валидный OGG файл для теста
        # (в production используйте реальную запись)

        # Путь к тестовому аудио (если есть)
        test_audio_path = Path("tests/fixtures/test_audio.ogg")

        if not test_audio_path.exists():
            pytest.skip(
                "Нет тестового аудио файла. "
                "Создайте tests/fixtures/test_audio.ogg с записью 'два плюс два'"
            )

        # Читаем реальный аудио файл
        with open(test_audio_path, "rb") as f:
            audio_data = f.read()

        # КРИТИЧНО: Реальный запрос к Yandex SpeechKit
        recognized_text = await speech_service.transcribe_voice(
            voice_file_bytes=audio_data, language="ru"
        )

        # Проверяем что получили распознанный текст
        assert recognized_text is not None, "SpeechKit не распознал аудио!"
        assert len(recognized_text) > 0, "SpeechKit вернул пустой текст!"

        print(f"\n✅ Yandex SpeechKit РЕАЛЬНО работает!")
        print(f"   Распознанный текст: {recognized_text}")

    async def test_yandex_vision_image_analysis_real(self):
        """
        CRITICAL: Проверка что Yandex Vision РЕАЛЬНО анализирует изображения.
        НЕТ МОКОВ!
        """
        vision_service = VisionService()

        # Создаём простое тестовое изображение PNG с текстом
        # (минимальный валидный PNG 1x1 белый пиксель)
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        image_data = base64.b64decode(test_image_base64)

        # КРИТИЧНО: Реальный запрос к Yandex Vision
        result = await vision_service.analyze_image(
            image_data=image_data,
            user_message="Что на этой картинке?",
            user_age=10,
        )

        # Проверяем что получили результат
        assert result is not None, "Yandex Vision не вернул результат!"
        assert result.analysis is not None, "Yandex Vision не вернул анализ!"
        assert len(result.analysis) > 0, "Yandex Vision вернул пустой анализ!"

        print(f"\n✅ Yandex Vision РЕАЛЬНО работает!")
        print(f"   Анализ: {result.analysis[:200]}...")
        if result.has_text:
            print(f"   Распознанный текст: {result.recognized_text}")

    async def test_full_ai_chat_flow_with_history_real(self):
        """
        CRITICAL: Проверка полного flow AI чата с историей.
        НЕТ МОКОВ!
        """
        ai_service = get_ai_service()

        # Симулируем реальный диалог с историей
        chat_history = []

        # Первый вопрос
        question1 = "Привет! Я учусь в 5 классе."
        response1 = await ai_service.generate_response(
            user_message=question1, chat_history=chat_history, user_age=10
        )

        assert response1 is not None
        assert len(response1) > 0

        # Добавляем в историю
        chat_history.append({"role": "user", "text": question1})
        chat_history.append({"role": "assistant", "text": response1})

        # Второй вопрос (с контекстом)
        question2 = "Помоги мне решить задачу: найди площадь квадрата со стороной 5 см"
        response2 = await ai_service.generate_response(
            user_message=question2, chat_history=chat_history, user_age=10
        )

        assert response2 is not None
        assert len(response2) > 0
        # AI должен вспомнить что ребёнок в 5 классе и дать соответствующий ответ
        assert "25" in response2 or "5×5" in response2 or "5*5" in response2

        print(f"\n✅ AI чат с историей РЕАЛЬНО работает!")
        print(f"   Q1: {question1}")
        print(f"   A1: {response1[:100]}...")
        print(f"   Q2: {question2}")
        print(f"   A2: {response2[:100]}...")


@pytest.mark.integration
@pytest.mark.asyncio
class TestYandexAPIErrorHandling:
    """Тесты обработки ошибок реальных API."""

    async def test_yandex_gpt_handles_invalid_input(self):
        """Проверка что YandexGPT корректно обрабатывает некорректный ввод."""
        ai_service = get_ai_service()

        # Пустое сообщение
        with pytest.raises(Exception):
            await ai_service.generate_response(user_message="", chat_history=[], user_age=10)

    async def test_yandex_speechkit_handles_invalid_audio(self):
        """Проверка что SpeechKit корректно обрабатывает некорректное аудио."""
        speech_service = SpeechService()

        # Некорректные данные (не аудио)
        invalid_audio = b"not an audio file"

        result = await speech_service.transcribe_voice(
            voice_file_bytes=invalid_audio, language="ru"
        )

        # Должен вернуть None, а не упасть
        assert result is None

    async def test_yandex_vision_handles_invalid_image(self):
        """Проверка что Vision корректно обрабатывает некорректное изображение."""
        vision_service = VisionService()

        # Некорректные данные (не изображение)
        invalid_image = b"not an image"

        result = await vision_service.analyze_image(
            image_data=invalid_image, user_message="Что это?", user_age=10
        )

        # Должен вернуть результат с ошибкой, а не упасть
        assert result is not None
        assert "ошибка" in result.analysis.lower() or len(result.analysis) == 0


if __name__ == "__main__":
    # Для быстрого локального запуска
    asyncio.run(TestYandexAPIReal().test_yandex_gpt_text_response_real())
