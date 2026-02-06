"""
Реальные интеграционные тесты для обработки иностранных языков.

Проверяет:
- Определение языка текста
- Перевод текста с объяснением
- Обработку иностранного текста в AI чате
- Фильтрацию мата на иностранных языках
- Модерацию иностранного контента
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.moderation_service import ContentModerationService
from bot.services.translate_service import TranslateService, get_translate_service


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
class TestForeignLanguagesTranslation:
    """Тесты перевода и обработки иностранных языков."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_detect_english_language(self):
        """Тест определения английского языка."""
        translate_service = get_translate_service()

        test_texts = [
            "Hello, how are you?",
            "What is the capital of France?",
            "I love learning languages",
            "Can you help me with homework?",
        ]

        for text in test_texts:
            detected = await translate_service.detect_language(text)
            assert detected == "en", f"Ожидался английский язык для текста: {text}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_detect_german_language(self):
        """Тест определения немецкого языка."""
        translate_service = get_translate_service()

        test_texts = [
            "Hallo, wie geht es dir?",
            "Was ist die Hauptstadt von Deutschland?",
            "Ich liebe Sprachen lernen",
            "Kannst du mir bei den Hausaufgaben helfen?",
        ]

        for text in test_texts:
            detected = await translate_service.detect_language(text)
            assert detected == "de", f"Ожидался немецкий язык для текста: {text}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_detect_french_language(self):
        """Тест определения французского языка."""
        translate_service = get_translate_service()

        test_texts = [
            "Bonjour, comment allez-vous?",
            "Quelle est la capitale de la France?",
            "J'aime apprendre les langues",
            "Pouvez-vous m'aider avec les devoirs?",
        ]

        for text in test_texts:
            detected = await translate_service.detect_language(text)
            assert detected == "fr", f"Ожидался французский язык для текста: {text}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_detect_spanish_language(self):
        """Тест определения испанского языка."""
        translate_service = get_translate_service()

        test_texts = [
            "Hola, ¿cómo estás?",
            "¿Cuál es la capital de España?",
            "Me encanta aprender idiomas",
            "¿Puedes ayudarme con la tarea?",
        ]

        for text in test_texts:
            detected = await translate_service.detect_language(text)
            assert detected == "es", f"Ожидался испанский язык для текста: {text}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_translate_english_to_russian(self):
        """Тест перевода с английского на русский."""
        translate_service = get_translate_service()

        test_cases = [
            ("Hello", "Привет"),
            ("What is your name?", "Как тебя зовут?"),
            ("I love math", "Я люблю математику"),
            ("Can you help me?", "Можешь мне помочь?"),
        ]

        for english_text, expected_ru in test_cases:
            translated = await translate_service.translate_text(
                english_text, target_language="ru", source_language="en"
            )
            assert translated is not None, f"Перевод не выполнен для: {english_text}"
            assert len(translated) > 0, f"Перевод пустой для: {english_text}"
            print(f"[OK] {english_text} -> {translated}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_translate_german_to_russian(self):
        """Тест перевода с немецкого на русский."""
        translate_service = get_translate_service()

        test_cases = [
            ("Hallo", "Привет"),
            ("Wie geht es dir?", "Как дела?"),
            ("Ich mag Mathematik", "Мне нравится математика"),
        ]

        for german_text, expected_ru in test_cases:
            translated = await translate_service.translate_text(
                german_text, target_language="ru", source_language="de"
            )
            assert translated is not None, f"Перевод не выполнен для: {german_text}"
            assert len(translated) > 0, f"Перевод пустой для: {german_text}"
            print(f"[OK] {german_text} -> {translated}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_translate_french_to_russian(self):
        """Тест перевода с французского на русский."""
        translate_service = get_translate_service()

        test_cases = [
            ("Bonjour", "Добрый день"),
            ("Comment allez-vous?", "Как дела?"),
            ("J'aime les mathématiques", "Мне нравится математика"),
        ]

        for french_text, expected_ru in test_cases:
            translated = await translate_service.translate_text(
                french_text, target_language="ru", source_language="fr"
            )
            assert translated is not None, f"Перевод не выполнен для: {french_text}"
            assert len(translated) > 0, f"Перевод пустой для: {french_text}"
            print(f"[OK] {french_text} -> {translated}")


@pytest.mark.integration
@pytest.mark.slow
class TestForeignLanguageProfanityFilter:
    """Тесты фильтрации мата на иностранных языках."""

    def test_english_profanity_detection(self):
        """Тест обнаружения мата на английском."""
        moderation_service = ContentModerationService()

        profanity_texts = [
            "What the fuck is this?",
            "This is shit",
            "You are a bitch",
            "Damn it",
            "Go to hell",
        ]

        for text in profanity_texts:
            is_safe, reason = moderation_service.is_safe_content(text)
            assert not is_safe, f"Ожидалась блокировка для: {text}"
            assert reason is not None, f"Причина блокировки не указана для: {text}"
            print(f"[OK] Заблокирован: {text[:30]}...")

    def test_german_profanity_detection(self):
        """Тест обнаружения мата на немецком."""
        moderation_service = ContentModerationService()

        profanity_texts = [
            "Das ist Scheiße",
            "Verdammt noch mal",
            "Du bist eine Hure",
        ]

        for text in profanity_texts:
            is_safe, reason = moderation_service.is_safe_content(text)
            assert not is_safe, f"Ожидалась блокировка для: {text}"
            assert reason is not None, f"Причина блокировки не указана для: {text}"
            print(f"[OK] Заблокирован: {text[:30]}...")

    def test_french_profanity_detection(self):
        """Тест обнаружения мата на французском."""
        moderation_service = ContentModerationService()

        profanity_texts = [
            "Merde!",
            "Putain",
            "C'est de la merde",
        ]

        for text in profanity_texts:
            is_safe, reason = moderation_service.is_safe_content(text)
            assert not is_safe, f"Ожидалась блокировка для: {text}"
            assert reason is not None, f"Причина блокировки не указана для: {text}"
            print(f"[OK] Заблокирован: {text[:30]}...")

    def test_spanish_profanity_detection(self):
        """Тест обнаружения мата на испанском."""
        moderation_service = ContentModerationService()

        profanity_texts = [
            "Joder",
            "Mierda",
            "Eres un cabrón",
        ]

        for text in profanity_texts:
            is_safe, reason = moderation_service.is_safe_content(text)
            assert not is_safe, f"Ожидалась блокировка для: {text}"
            assert reason is not None, f"Причина блокировки не указана для: {text}"
            print(f"[OK] Заблокирован: {text[:30]}...")

    def test_educational_foreign_text_allowed(self):
        """Тест разрешения образовательного контента на иностранных языках."""
        moderation_service = ContentModerationService()

        safe_texts = [
            "Hello, can you help me with math?",
            "What is the capital of France?",
            "Hallo, ich lerne Deutsch",
            "Bonjour, je voudrais apprendre le français",
            "Hola, me gusta estudiar",
        ]

        for text in safe_texts:
            is_safe, reason = moderation_service.is_safe_content(text)
            assert is_safe, f"Образовательный текст заблокирован: {text}, причина: {reason}"
            print(f"[OK] Разрешен: {text[:50]}...")


@pytest.mark.integration
@pytest.mark.slow
class TestForeignLanguageAIChat:
    """Тесты обработки иностранных языков в AI чате."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_english_text_with_translation_and_explanation(self):
        """Тест обработки английского текста с переводом и объяснением."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        ai_service = get_ai_service()

        english_text = "Hello, what is the capital of France?"

        # Определяем язык
        detected_lang = await translate_service.detect_language(english_text)
        assert detected_lang == "en", "Должен быть определен английский язык"

        # Переводим
        translated_text = await translate_service.translate_text(
            english_text, target_language="ru", source_language="en"
        )
        assert translated_text is not None, "Перевод не выполнен"

        # Формируем запрос для AI
        user_message = (
            f"🌍 Вижу, что ты написал на Английский!\n\n"
            f"📝 Оригинал: {english_text}\n"
            f"🇷🇺 Перевод: {translated_text}\n\n"
            f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
        )

        # Генерируем ответ через AI
        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не вернул ответ"
        assert len(response) > 0, "Ответ AI пустой"
        assert (
            "перевод" in response.lower()
            or "столица" in response.lower()
            or "франция" in response.lower()
        ), (
            f"Ответ должен содержать объяснение перевода или информацию о столице Франции: {response[:200]}"
        )

        print(f"\n[OK] Английский текст обработан:")
        print(f"   Оригинал: {english_text}")
        print(f"   Перевод: {translated_text}")
        print(f"   Ответ AI: {response[:200]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_german_text_with_translation_and_explanation(self):
        """Тест обработки немецкого текста с переводом и объяснением."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        ai_service = get_ai_service()

        german_text = "Hallo, wie geht es dir? Was ist die Hauptstadt von Deutschland?"

        # Определяем язык
        detected_lang = await translate_service.detect_language(german_text)
        assert detected_lang == "de", "Должен быть определен немецкий язык"

        # Переводим
        translated_text = await translate_service.translate_text(
            german_text, target_language="ru", source_language="de"
        )
        assert translated_text is not None, "Перевод не выполнен"

        # Формируем запрос для AI
        user_message = (
            f"🌍 Вижу, что ты написал на Немецкий!\n\n"
            f"📝 Оригинал: {german_text}\n"
            f"🇷🇺 Перевод: {translated_text}\n\n"
            f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
        )

        # Генерируем ответ через AI
        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не вернул ответ"
        assert len(response) > 0, "Ответ AI пустой"

        print(f"\n[OK] Немецкий текст обработан:")
        print(f"   Оригинал: {german_text}")
        print(f"   Перевод: {translated_text}")
        print(f"   Ответ AI: {response[:200]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_french_text_with_translation_and_explanation(self):
        """Тест обработки французского текста с переводом и объяснением."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        ai_service = get_ai_service()

        french_text = "Bonjour, comment allez-vous? Quelle est la capitale de la France?"

        # Определяем язык
        detected_lang = await translate_service.detect_language(french_text)
        assert detected_lang == "fr", "Должен быть определен французский язык"

        # Переводим
        translated_text = await translate_service.translate_text(
            french_text, target_language="ru", source_language="fr"
        )
        assert translated_text is not None, "Перевод не выполнен"

        # Формируем запрос для AI
        user_message = (
            f"🌍 Вижу, что ты написал на Французский!\n\n"
            f"📝 Оригинал: {french_text}\n"
            f"🇷🇺 Перевод: {translated_text}\n\n"
            f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
        )

        # Генерируем ответ через AI
        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не вернул ответ"
        assert len(response) > 0, "Ответ AI пустой"

        print(f"\n[OK] Французский текст обработан:")
        print(f"   Оригинал: {french_text}")
        print(f"   Перевод: {translated_text}")
        print(f"   Ответ AI: {response[:200]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_spanish_text_with_translation_and_explanation(self):
        """Тест обработки испанского текста с переводом и объяснением."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        ai_service = get_ai_service()

        spanish_text = "Hola, ¿cómo estás? ¿Cuál es la capital de España?"

        # Определяем язык
        detected_lang = await translate_service.detect_language(spanish_text)
        assert detected_lang == "es", "Должен быть определен испанский язык"

        # Переводим
        translated_text = await translate_service.translate_text(
            spanish_text, target_language="ru", source_language="es"
        )
        assert translated_text is not None, "Перевод не выполнен"

        # Формируем запрос для AI
        user_message = (
            f"🌍 Вижу, что ты написал на Испанский!\n\n"
            f"📝 Оригинал: {spanish_text}\n"
            f"🇷🇺 Перевод: {translated_text}\n\n"
            f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
        )

        # Генерируем ответ через AI
        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не вернул ответ"
        assert len(response) > 0, "Ответ AI пустой"

        print(f"\n[OK] Испанский текст обработан:")
        print(f"   Оригинал: {spanish_text}")
        print(f"   Перевод: {translated_text}")
        print(f"   Ответ AI: {response[:200]}...")


@pytest.mark.integration
@pytest.mark.slow
class TestForeignLanguageEndToEnd:
    """End-to-end тесты для полной обработки иностранных языков."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_full_english_to_ai_response_flow(self):
        """Полный поток обработки английского текста от ввода до ответа AI."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.moderation_service import ContentModerationService
        from bot.services.translate_service import get_translate_service

        # Инициализация сервисов
        translate_service = get_translate_service()
        ai_service = get_ai_service()
        moderation_service = ContentModerationService()

        # Исходный английский текст
        english_text = "Hello! Can you help me with math homework?"

        # Шаг 1: Модерация исходного текста
        is_safe, reason = moderation_service.is_safe_content(english_text)
        assert is_safe, f"Образовательный текст заблокирован: {reason}"

        # Шаг 2: Определение языка
        detected_lang = await translate_service.detect_language(english_text)
        assert detected_lang == "en"

        # Шаг 3: Перевод
        translated_text = await translate_service.translate_text(
            english_text, target_language="ru", source_language="en"
        )
        assert translated_text is not None

        # Шаг 4: Формирование запроса для AI
        user_message = (
            f"🌍 Вижу, что ты написал на Английский!\n\n"
            f"📝 Оригинал: {english_text}\n"
            f"🇷🇺 Перевод: {translated_text}\n\n"
            f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
        )

        # Шаг 5: Модерация переведенного текста
        is_safe_translated, _ = moderation_service.is_safe_content(translated_text)
        assert is_safe_translated, "Переведенный текст должен быть безопасным"

        # Шаг 6: Генерация ответа AI
        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=10,
        )

        assert response is not None
        assert len(response) > 50, "Ответ AI слишком короткий"

        # Шаг 7: Модерация ответа AI
        sanitized_response = moderation_service.sanitize_ai_response(response)
        assert sanitized_response is not None

        print(f"\n[OK] Полный поток обработки:")
        print(f"   1. Входной текст: {english_text}")
        print(f"   2. Язык: {detected_lang}")
        print(f"   3. Перевод: {translated_text}")
        print(f"   4. Ответ AI: {response[:150]}...")
        print(f"   5. Очищенный ответ: {sanitized_response[:150]}...")
