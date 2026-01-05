"""
Реальные интеграционные тесты для обработки иностранных языков в фото и аудио.

Проверяет:
- OCR текста на фото с иностранным языком + перевод + объяснение
- Распознавание речи на иностранном языке + перевод + объяснение
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
class TestForeignLanguageImageOCR:
    """Тесты OCR текста на фото с иностранным языком."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_image_with_english_text_ocr_and_translation(self):
        """Тест OCR английского текста на фото + перевод + объяснение."""
        from bot.services.translate_service import get_translate_service
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()
        translate_service = get_translate_service()

        # Создаем простое тестовое изображение с английским текстом через base64
        # Простое изображение 1x1 пиксель с текстом (в реальности будет фото с текстом)
        # Для реального теста нужна картинка - создадим минимальное изображение через PIL если доступен
        try:
            import io

            from PIL import Image, ImageDraw, ImageFont

            # Создаем изображение с английским текстом
            img = Image.new("RGB", (400, 100), color="white")
            draw = ImageDraw.Draw(img)

            try:
                # Пытаемся использовать системный шрифт
                font = ImageFont.truetype("arial.ttf", 30)
            except Exception:
                # Fallback на стандартный шрифт
                font = ImageFont.load_default()

            text = "Hello! What is the capital of France?"
            draw.text((10, 30), text, fill="black", font=font)

            # Конвертируем в байты
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            image_bytes = img_byte_arr.getvalue()

        except ImportError:
            pytest.skip("PIL/Pillow не установлен, пропускаем тест с изображением")

        # Анализируем изображение через Yandex Vision OCR
        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes, user_question="Что здесь написано?"
        )

        recognized_text = result.get("recognized_text", "")
        assert recognized_text, "OCR не распознал текст на изображении"

        print(f"\n[OK] OCR распознал текст: {recognized_text}")

        # Определяем язык
        detected_lang = await translate_service.detect_language(recognized_text)
        assert detected_lang == "en", f"Ожидался английский язык, получен: {detected_lang}"

        # Переводим
        translated_text = await translate_service.translate_text(
            recognized_text, target_language="ru", source_language="en"
        )
        assert translated_text is not None, "Перевод не выполнен"

        print(f"[OK] Перевод: {translated_text}")

        # Проверяем что в анализе есть информация о переводе
        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"

        print(f"[OK] AI анализ выполнен, длина: {len(analysis)} символов")


@pytest.mark.integration
@pytest.mark.slow
class TestForeignLanguageAudioSpeech:
    """Тесты распознавания речи на иностранном языке."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_audio_english_speech_recognition_and_translation(self):
        """Тест распознавания английской речи + перевод + объяснение."""
        from pathlib import Path

        from bot.services.ai_service_solid import get_ai_service
        from bot.services.speech_service import get_speech_service
        from bot.services.translate_service import get_translate_service

        speech_service = get_speech_service()
        translate_service = get_translate_service()
        ai_service = get_ai_service()

        # Проверяем наличие тестового аудиофайла
        test_audio_path = Path("tests/fixtures/test_audio_english.ogg")

        if not test_audio_path.exists():
            # Пропускаем тест если файла нет, но объясняем что нужно для полного тестирования
            pytest.skip(
                f"Тест требует реального OGG аудиофайла: {test_audio_path}\n"
                "В реальном использовании:\n"
                "1. SpeechKit распознает речь с аудио\n"
                "2. Определяется язык распознанного текста\n"
                "3. Если язык иностранный - переводится на русский\n"
                "4. AI объясняет перевод ребенку\n"
                "\n"
                "Для создания тестового файла:\n"
                "- Запишите фразу на английском (например: 'Hello, can you help me with math?') в OGG формат\n"
                "- Сохраните как tests/fixtures/test_audio_english.ogg"
            )

        # Читаем аудиофайл
        with open(test_audio_path, "rb") as f:
            audio_data = f.read()

        # Шаг 1: Распознавание речи (пробуем английский язык)
        recognized_text = await speech_service.transcribe_voice(
            voice_file_bytes=audio_data, language="en"
        )

        assert recognized_text is not None, "SpeechKit не распознал аудио"
        assert len(recognized_text) > 0, "SpeechKit вернул пустой текст"

        print(f"\n[OK] Шаг 1 - SpeechKit распознал: {recognized_text}")

        # Шаг 2: Определение языка
        detected_lang = await translate_service.detect_language(recognized_text)
        print(f"[OK] Шаг 2 - Язык: {detected_lang}")

        # Шаг 3: Перевод если не русский
        if detected_lang and detected_lang != "ru":
            translated_text = await translate_service.translate_text(
                recognized_text, target_language="ru", source_language=detected_lang
            )
            assert translated_text is not None, "Перевод не выполнен"
            print(f"[OK] Шаг 3 - Перевод: {translated_text}")

            # Шаг 4: Формируем запрос для AI
            user_message = (
                f"Пользователь отправил голосовое сообщение на {translate_service.get_language_name(detected_lang)}:\n"
                f"Оригинал: '{recognized_text}'\n"
                f"Перевод на русский: '{translated_text}'\n\n"
                "Объясни этот текст ребенку, переведи его, дай транскрипцию (если применимо) и объясни важные грамматические моменты простыми словами."
            )

            # Шаг 5: Генерация ответа AI
            response = await ai_service.generate_response(
                user_message=user_message,
                chat_history=[],
                user_age=10,
            )

            assert response is not None
            assert len(response) > 50, "Ответ AI слишком короткий"
            print(f"[OK] Шаг 4-5 - AI ответ: {response[:200]}...")


@pytest.mark.integration
@pytest.mark.slow
class TestForeignLanguageFullFlow:
    """Полные end-to-end тесты для фото и аудио."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_image_ocr_translation_ai_explanation_flow(self):
        """Полный поток: фото с английским текстом → OCR → перевод → объяснение AI."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.translate_service import get_translate_service
        from bot.services.yandex_cloud_service import get_yandex_cloud_service

        yandex_service = get_yandex_cloud_service()
        translate_service = get_translate_service()
        ai_service = get_ai_service()

        try:
            import io

            from PIL import Image, ImageDraw, ImageFont

            # Создаем изображение с английским текстом
            img = Image.new("RGB", (500, 150), color="white")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", 32)
            except Exception:
                font = ImageFont.load_default()

            english_text = "Hello! Can you help me with math homework?"
            draw.text((20, 50), english_text, fill="black", font=font)

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            image_bytes = img_byte_arr.getvalue()

        except ImportError:
            pytest.skip("PIL/Pillow не установлен")

        # Шаг 1: OCR через Yandex Vision
        result = await yandex_service.analyze_image_with_text(
            image_data=image_bytes, user_question="Что здесь написано? Переведи и объясни."
        )

        recognized_text = result.get("recognized_text", "")
        assert recognized_text, "OCR не распознал текст"

        print(f"\n[OK] Шаг 1 - OCR: {recognized_text}")

        # Шаг 2: Определение языка (должен быть английский)
        detected_lang = await translate_service.detect_language(recognized_text)
        assert detected_lang == "en", f"Язык должен быть английский, получен: {detected_lang}"

        # Шаг 3: Перевод
        translated_text = await translate_service.translate_text(
            recognized_text, target_language="ru", source_language="en"
        )
        assert translated_text is not None

        print(f"[OK] Шаг 2-3 - Язык: {detected_lang}, Перевод: {translated_text}")

        # Шаг 4: Проверяем что AI анализ содержит информацию о переводе
        analysis = result.get("analysis", "")
        assert analysis, "AI анализ не выполнен"
        assert len(analysis) > 50, "AI анализ слишком короткий"

        print(f"[OK] Шаг 4 - AI анализ: {analysis[:200]}...")

        # Проверяем что в анализе есть упоминание перевода или английского текста
        analysis_lower = analysis.lower()
        assert (
            "перевод" in analysis_lower
            or "английск" in analysis_lower
            or "hello" in analysis_lower.lower()
            or translated_text.lower()[:20] in analysis_lower
        ), f"AI анализ должен содержать информацию о переводе: {analysis[:300]}"

        print(f"\n[OK] Полный поток выполнен успешно!")
