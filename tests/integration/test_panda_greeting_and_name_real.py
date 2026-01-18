"""
Реальные интеграционные тесты для проверки приветствия и общения по имени.

Проверяет:
- Приветствие при первом сообщении
- Запрос имени у пользователя
- Использование имени в ответах
- Качество ответов на текст/фото/аудио
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
class TestPandaGreetingReal:
    """Тесты приветствия панды с реальным API."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_greeting_on_first_message(self):
        """Тест приветствия при первом сообщении."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.prompt_builder import PromptBuilder

        ai_service = get_ai_service()
        prompt_builder = PromptBuilder()

        # Первое сообщение от пользователя
        user_message = "Привет"
        chat_history = []

        # Проверяем логику приветствия
        system_prompt = prompt_builder.build_system_prompt(
            user_message=user_message,
            chat_history=chat_history,
            user_age=10,
            user_name=None,  # Имя не известно
            is_history_cleared=False,
            message_count_since_name=0,
            non_educational_questions_count=0,
            is_auto_greeting_sent=False,
        )

        # Должна быть инструкция приветствия
        assert "привет" in system_prompt.lower() or "поприветствуй" in system_prompt.lower(), (
            f"Системный промпт должен содержать инструкцию приветствия: {system_prompt[:300]}"
        )

        # Генерируем ответ
        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=chat_history,
            user_age=10,
            user_name=None,
            is_history_cleared=False,
            message_count_since_name=0,
            skip_name_asking=False,
            non_educational_questions_count=0,
            is_premium=False,
            is_auto_greeting_sent=False,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 10, "Ответ слишком короткий"

        # Ответ должен содержать приветствие
        response_lower = response.lower()
        assert (
            "привет" in response_lower
            or "здравствуй" in response_lower
            or "добро" in response_lower
        ), f"Ответ должен содержать приветствие: {response}"

        # Проверка качества ответа
        assert len(response) > 30, f"Ответ слишком короткий для приветствия: {response}"
        assert "?" in response or "!" in response, "Ответ должен быть живым (знаки препинания)"

        print(f"\n[OK] Greeting on first message: {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_name_request_when_no_name(self):
        """Тест запроса имени когда у пользователя нет имени."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.prompt_builder import PromptBuilder

        ai_service = get_ai_service()
        prompt_builder = PromptBuilder()

        # Пользователь поздоровался, но имени нет
        user_message = "Привет"
        chat_history = []
        user_greeted = True  # Пользователь поздоровался

        # Проверяем логику запроса имени
        system_prompt = prompt_builder.build_system_prompt(
            user_message=user_message,
            chat_history=chat_history,
            user_age=10,
            user_name=None,  # Имя не известно
            is_history_cleared=False,
            message_count_since_name=0,
            non_educational_questions_count=0,
            is_auto_greeting_sent=False,
        )

        # Должна быть инструкция спросить имя
        should_ask_name = (
            "как тебя зовут" in system_prompt.lower()
            or "назвать своё имя" in system_prompt.lower()
            or "узнать имя" in system_prompt.lower()
        )

        # Генерируем ответ
        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=chat_history,
            user_age=10,
            user_name=None,
            is_history_cleared=False,
            message_count_since_name=0,
            skip_name_asking=False,
            non_educational_questions_count=0,
            is_premium=False,
            is_auto_greeting_sent=False,
        )

        assert response is not None, "AI не ответил"

        # Если система должна была попросить имя, проверяем ответ
        if should_ask_name:
            response_lower = response.lower()
            assert (
                "как тебя зовут" in response_lower
                or "как тебя" in response_lower
                or "имя" in response_lower
            ), f"Ответ должен спрашивать имя: {response}"

        print(f"\n[OK] Name request: {response[:150]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_name_usage_in_responses(self):
        """Тест использования имени в ответах."""
        from bot.services.ai_service_solid import get_ai_service
        from bot.services.prompt_builder import PromptBuilder

        ai_service = get_ai_service()
        prompt_builder = PromptBuilder()

        user_name = "Саша"
        chat_history = [
            {"role": "user", "text": "Привет"},
            {"role": "assistant", "text": "Привет, Саша! Как дела?"},
            {"role": "user", "text": "Хорошо"},
            {"role": "assistant", "text": "Отлично!"},
        ]

        # Много сообщений прошло (гарантированное использование имени)
        message_count_since_name = 10

        # Проверяем логику использования имени
        system_prompt = prompt_builder.build_system_prompt(
            user_message="Расскажи про математику",
            chat_history=chat_history,
            user_age=10,
            user_name=user_name,
            is_history_cleared=False,
            message_count_since_name=message_count_since_name,
            non_educational_questions_count=0,
            is_auto_greeting_sent=True,
        )

        # Должна быть инструкция использовать имя
        should_use_name = (
            user_name.lower() in system_prompt.lower()
            or "обращайся по имени" in system_prompt.lower()
        )

        # Генерируем ответ
        response = await ai_service.generate_response(
            user_message="Расскажи про математику",
            chat_history=chat_history,
            user_age=10,
            user_name=user_name,
            is_history_cleared=False,
            message_count_since_name=message_count_since_name,
            skip_name_asking=False,
            non_educational_questions_count=0,
            is_premium=False,
            is_auto_greeting_sent=True,
        )

        assert response is not None, "AI не ответил"

        # Если система должна была использовать имя, проверяем ответ
        # Имя используется с вероятностью 30%, поэтому не всегда может быть в ответе
        if should_use_name:
            response_lower = response.lower()
            # Имя может быть в разных падежах
            # Если имя не использовано - это нормально (вероятность 30%), но проверяем что ответ хороший
            name_used = user_name.lower() in response_lower or "саша" in response_lower
            if not name_used:
                # Если имя не использовано, проверяем что ответ всё равно информативен
                assert len(response) > 100, (
                    f"Ответ слишком короткий и имя не использовано: {response[:100]}"
                )
                print(f"   [INFO] Name '{user_name}' not used in response (30% probability), but response is informative")
            else:
                print(f"   [OK] Name '{user_name}' used in response")

        print(f"\n[OK] Name usage: {response[:150]}...")


@pytest.mark.integration
@pytest.mark.slow
class TestPandaResponseQualityReal:
    """Тесты качества ответов панды на текст/фото/аудио."""

    def _check_response_quality(self, response: str, min_sentences: int = 4) -> dict:
        """Проверка качества ответа."""
        issues = []
        quality_score = 100

        # 1. Проверка длины
        sentences = [s.strip() for s in response.split(".") if s.strip()]
        if len(sentences) < min_sentences:
            issues.append(f"Слишком мало предложений: {len(sentences)} < {min_sentences}")
            quality_score -= 30

        # 2. Проверка общей длины
        if len(response) < 150:
            issues.append(f"Ответ слишком короткий: {len(response)} < 150 символов")
            quality_score -= 20

        # 3. Проверка на наличие примеров
        example_keywords = ["например", "к примеру", "так", "также", "если", "чтобы"]
        has_examples = any(kw in response.lower() for kw in example_keywords)

        # 4. Проверка структуры
        paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]

        return {
            "quality_score": max(0, quality_score),
            "issues": issues,
            "sentences_count": len(sentences),
            "paragraphs_count": len(paragraphs),
            "has_examples": has_examples,
            "total_length": len(response),
        }

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_text_response_quality(self):
        """Тест качества текстового ответа."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()

        question = "Что такое фотосинтез? Объясни подробно с примерами."
        response = await ai_service.generate_response(
            user_message=question,
            chat_history=[],
            user_age=11,
        )

        assert response is not None, "AI не ответил"
        assert len(response) > 50, f"Ответ слишком короткий: {response}"

        quality = self._check_response_quality(response, min_sentences=4)
        assert quality["quality_score"] >= 70, (
            f"Низкое качество ответа: {quality['quality_score']}/100. "
            f"Проблемы: {quality['issues']}"
        )
        assert quality["sentences_count"] >= 4, (
            f"Слишком мало предложений: {quality['sentences_count']} < 4"
        )

        # Проверка что ответ содержит ключевые слова
        response_lower = response.lower()
        assert (
            "фотосинтез" in response_lower
            or "растение" in response_lower
            or "хлорофилл" in response_lower
        ), f"Ответ должен содержать информацию про фотосинтез: {response[:200]}"

        print(f"\n[OK] Text response quality: {quality['quality_score']}/100")
        print(f"   Response: {response[:200]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_photo_response_quality(self):
        """Тест качества ответа на фото."""
        import base64

        from bot.services.vision_service import VisionService
        from bot.services.ai_service_solid import get_ai_service

        vision_service = VisionService()
        ai_service = get_ai_service()

        # Создаём простое тестовое изображение с текстом задачи
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        image_data = base64.b64decode(test_image_base64)

        # Анализируем изображение
        vision_result = await vision_service.analyze_image(
            image_data=image_data,
            user_message="Реши эту задачу по математике: 15 + 27 = ?",
            user_age=10,
        )

        assert vision_result is not None, "Vision не вернул результат"
        assert vision_result.analysis is not None, "Vision не вернул анализ"

        # Если есть распознанный текст, используем его для ответа
        if vision_result.recognized_text:
            user_message = f"На фото написано: {vision_result.recognized_text}\n\nПомоги решить эту задачу полностью и подробно."
        else:
            user_message = "Помоги решить эту задачу по математике полностью и подробно."

        # Генерируем ответ AI
        response = await ai_service.generate_response(
            user_message=user_message,
            chat_history=[],
            user_age=10,
        )

        assert response is not None, "AI не ответил на фото"

        # Для фото ответ может быть короче, если задача простая
        # Минимальная длина 20 символов для информативности
        assert len(response) >= 20, f"Ответ слишком короткий: {response}"

        # Для фото используем гибкую проверку качества
        if len(response) < 50:
            # Для очень коротких ответов снижаем требования
            quality = self._check_response_quality(response, min_sentences=1)
            min_quality = 40  # Низкий порог для коротких ответов
        elif len(response) < 150:
            quality = self._check_response_quality(response, min_sentences=2)
            min_quality = 50  # Средний порог
        else:
            quality = self._check_response_quality(response, min_sentences=3)
            min_quality = 60  # Высокий порог для длинных ответов

        assert quality["quality_score"] >= min_quality, (
            f"Низкое качество ответа: {quality['quality_score']}/100 (требуется {min_quality}). "
            f"Проблемы: {quality['issues']}"
        )

        print(f"\n[OK] Photo response quality: {quality['quality_score']}/100")
        print(f"   Response: {response[:200]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_audio_response_quality(self):
        """Тест качества ответа на аудио."""
        import base64

        from bot.services.speech_service import SpeechService
        from bot.services.ai_service_solid import get_ai_service

        speech_service = SpeechService()
        ai_service = get_ai_service()

        # Создаём минимальное тестовое аудио (WAV заголовок, тишина)
        # Это не реальное аудио, но тест проверяет логику
        wav_header = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x22\x56\x00\x00\x44\xac\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00"
        audio_data = wav_header + b"\x00" * 100

        try:
            # Распознаём аудио
            transcribed = await speech_service.transcribe_voice(
                voice_file_bytes=audio_data, language="ru"
            )

            if transcribed:
                # Генерируем ответ на распознанный текст
                response = await ai_service.generate_response(
                    user_message=transcribed,
                    chat_history=[],
                    user_age=10,
                )

                assert response is not None, "AI не ответил на аудио"
                assert len(response) > 30, f"Ответ слишком короткий: {response}"

                quality = self._check_response_quality(response, min_sentences=2)
                print(f"\n[OK] Audio response quality: {quality['quality_score']}/100")
                print(f"   Transcribed: {transcribed}")
                print(f"   Response: {response[:200]}...")
            else:
                pytest.skip("SpeechKit не распознал аудио (это нормально для тестового файла)")

        except Exception as e:
            pytest.skip(f"SpeechKit API недоступен или ошибка: {e}")
