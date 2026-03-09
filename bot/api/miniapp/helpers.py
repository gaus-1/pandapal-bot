"""
Вспомогательные функции для Mini App endpoints.
"""

import base64
import re

import httpx
from aiohttp import web
from loguru import logger

from bot.database import get_db
from bot.services import UserService
from bot.services.speech_service import get_speech_service
from bot.services.translate_service import get_translate_service
from bot.services.vision_service import VisionService


async def process_audio_message(
    audio_base64: str,
    telegram_id: int,
    message: str,
    language_code: str | None = None,
) -> tuple[str | None, web.Response | None]:
    """
    Обработка голосового сообщения.

    Returns:
        tuple: (user_message, error_response) - если error_response не None, вернуть его
    """
    try:
        logger.info(f"🎤 Mini App: Обработка голосового сообщения от {telegram_id}")
        logger.info(f"🎤 Mini App: audio_base64 length: {len(audio_base64)}")

        if "base64," in audio_base64:
            audio_base64 = audio_base64.split("base64,")[1]
            logger.info(f"🎤 Mini App: После удаления префикса, length: {len(audio_base64)}")

        MAX_AUDIO_BASE64_SIZE = 14 * 1024 * 1024  # 14MB
        if len(audio_base64) > MAX_AUDIO_BASE64_SIZE:
            logger.warning(f"⚠️ Аудио слишком большое: {len(audio_base64)} байт")
            return None, web.json_response(
                {"error": "Аудио слишком большое. Максимум 10MB. Попробуй записать короче!"},
                status=413,
            )

        try:
            audio_bytes = base64.b64decode(audio_base64)
            logger.info(f"🎤 Mini App: Декодировано {len(audio_bytes)} байт аудио")
        except Exception as decode_error:
            logger.error(f"❌ Ошибка декодирования base64 аудио: {decode_error}")
            return None, web.json_response(
                {"error": "Неверный формат аудио. Попробуй записать заново!"},
                status=400,
            )

        MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
        if len(audio_bytes) > MAX_AUDIO_SIZE:
            logger.warning(f"⚠️ Декодированное аудио слишком большое: {len(audio_bytes)} байт")
            return None, web.json_response(
                {"error": "Аудио слишком большое. Максимум 10MB. Попробуй записать короче!"},
                status=413,
            )

        speech_lang = "en" if (language_code or "").strip().lower().startswith("en") else "ru"
        speech_service = get_speech_service()
        transcribed_text = await speech_service.transcribe_voice(audio_bytes, language=speech_lang)

        if not transcribed_text or not transcribed_text.strip():
            logger.warning("⚠️ Аудио не распознано или пустое")
            return None, web.json_response(
                {
                    "error": "Не удалось распознать речь. Попробуй говорить четче или напиши текстом!"
                },
                status=400,
            )

        translate_service = get_translate_service()
        detected_lang = await translate_service.detect_language(transcribed_text)

        if (
            detected_lang
            and detected_lang != "ru"
            and detected_lang in translate_service.SUPPORTED_LANGUAGES
        ):
            lang_name = translate_service.get_language_name(detected_lang)
            logger.info(f"🌍 Mini App: Обнаружен иностранный язык: {detected_lang}")
            translated_text = await translate_service.translate_text(
                transcribed_text, target_language="ru", source_language=detected_lang
            )
            if translated_text:
                user_message = (
                    f"🌍 Вижу, что ты сказал на {lang_name}!\n\n"
                    f"📝 Оригинал: {transcribed_text}\n"
                    f"🇷🇺 Перевод: {translated_text}\n\n"
                    f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                )
                logger.info(f"✅ Mini App: Аудио переведено: {detected_lang} → ru")
            else:
                user_message = transcribed_text
        else:
            user_message = transcribed_text

        logger.info(f"✅ Mini App: Аудио распознано: {transcribed_text[:100]}")
        if not user_message or not user_message.strip():
            logger.warning("⚠️ user_message не установлен после распознавания аудио")
            user_message = transcribed_text if transcribed_text else message

        return user_message, None

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Ошибка SpeechKit API (HTTP {e.response.status_code}): {e}", exc_info=True)
        error_message = "Ошибка распознавания речи. Попробуй записать заново или напиши текстом!"
        if e.response.status_code == 401:
            error_message = (
                "Ошибка авторизации в сервисе распознавания речи. Обратитесь в поддержку."
            )
        elif e.response.status_code == 413:
            error_message = "Аудио слишком большое. Попробуй записать короче!"
        elif e.response.status_code == 400:
            error_message = "Неверный формат аудио. Попробуй записать заново!"
        return None, web.json_response({"error": error_message}, status=500)
    except httpx.TimeoutException as e:
        logger.error(f"❌ Таймаут распознавания речи: {e}", exc_info=True)
        return None, web.json_response(
            {"error": "Аудио слишком длинное или сервис недоступен. Попробуй записать короче!"},
            status=504,
        )
    except Exception as e:
        logger.error(f"❌ Ошибка обработки аудио: {e}", exc_info=True)
        error_message = "Ошибка обработки аудио. Попробуй записать заново или напиши текстом!"
        if "timeout" in str(e).lower() or "time" in str(e).lower():
            error_message = "Аудио слишком длинное. Попробуй записать короче!"
        elif "format" in str(e).lower() or "decode" in str(e).lower():
            error_message = "Неверный формат аудио. Попробуй записать заново!"
        elif "401" in str(e) or "unauthorized" in str(e).lower():
            error_message = (
                "Ошибка авторизации в сервисе распознавания речи. Обратитесь в поддержку."
            )
        return None, web.json_response({"error": error_message}, status=500)


async def process_photo_message(
    photo_base64: str, telegram_id: int, message: str
) -> tuple[str | None, web.Response | None]:
    """
    Обработка фото сообщения.

    Returns:
        tuple: (user_message, error_response) - если error_response не None, вернуть его
    """
    try:
        logger.info(f"📷 Mini App: Обработка фото от {telegram_id}")
        logger.info(f"📷 Mini App: photo_base64 length: {len(photo_base64)}")

        if "base64," in photo_base64:
            photo_base64 = photo_base64.split("base64,")[1]
            logger.info(f"📷 Mini App: После удаления префикса, length: {len(photo_base64)}")

        photo_bytes = base64.b64decode(photo_base64)
        logger.info(f"📷 Mini App: Декодировано {len(photo_bytes)} байт изображения")

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return None, web.json_response({"error": "User not found"}, status=404)

            vision_service = VisionService()
            logger.info(f"📷 Mini App: Вызываю analyze_image для пользователя {user.age} лет")
            # Формируем запрос с требованием полного ответа с примерами
            vision_prompt = (
                message or "Проанализируй это фото с заданием и реши задачу полностью и подробно"
            )
            if "полностью" not in vision_prompt.lower() and "подробно" not in vision_prompt.lower():
                vision_prompt += (
                    ". Реши задачу полностью и подробно: разбери задачу пошагово, "
                    "объясни каждый шаг, приведи примеры, дай исчерпывающее объяснение с пояснениями. "
                    "Ответ должен быть глубоким и развернутым с примерами."
                )
            vision_result = await vision_service.analyze_image(
                image_data=photo_bytes,
                user_message=vision_prompt,
                user_age=user.age,
            )

            # КРИТИЧЕСКИ ВАЖНО: Если Vision API дал готовый ответ - возвращаем его как готовый
            if vision_result.analysis and vision_result.analysis.strip():
                # Vision API уже решил задачу - возвращаем готовый ответ с маркером
                logger.info(
                    f"✅ Фото проанализировано, готовый ответ получен: {len(vision_result.analysis)} символов"
                )
                # Возвращаем специальный маркер в начале строки
                return f"__READY_ANSWER__{vision_result.analysis}", None

            # Если Vision API не дал готовый ответ - используем распознанный текст
            if vision_result.recognized_text:
                user_message = (
                    f"На фото написано: {vision_result.recognized_text}\n\n"
                    f"Помоги решить эту задачу полностью и подробно: "
                    f"разбери задачу пошагово, объясни каждый шаг, приведи примеры, "
                    f"дай исчерпывающее объяснение с пояснениями. "
                    f"Ответ должен быть глубоким и развернутым с примерами."
                )
            else:
                user_message = (message or "Помоги мне разобраться с этой задачей") + (
                    "\n\nДай исчерпывающее объяснение с примерами: "
                    "разбери задачу пошагово, объясни каждый шаг, приведи примеры. "
                    "Ответ должен быть глубоким и развернутым."
                )

            logger.info(f"✅ Фото проанализировано, текст распознан: {len(user_message)} символов")
            return user_message, None

    except Exception as e:
        logger.error(f"❌ Ошибка обработки фото: {e}", exc_info=True)
        return None, web.json_response({"error": f"Ошибка обработки фото: {str(e)}"}, status=500)


def format_achievements(unlocked_achievements: list) -> list:
    """Форматирование списка достижений для ответа."""
    try:
        from bot.services.gamification_service import ALL_ACHIEVEMENTS

        achievement_info = []
        for achievement_id in unlocked_achievements:
            achievement = next((a for a in ALL_ACHIEVEMENTS if a.id == achievement_id), None)
            if achievement:
                achievement_info.append(
                    {
                        "id": achievement.id,
                        "title": achievement.title,
                        "description": achievement.description,
                        "icon": achievement.icon,
                        "xp_reward": achievement.xp_reward,
                    }
                )
        return achievement_info
    except Exception as e:
        logger.error(f"❌ Ошибка формирования достижений: {e}")
        return []


async def send_achievements_event(response, unlocked_achievements: list) -> None:
    """Отправка события о достижениях через SSE."""
    try:
        import json as json_lib

        achievement_info = format_achievements(unlocked_achievements)
        if achievement_info:
            chunk_data = json_lib.dumps({"achievements": achievement_info}, ensure_ascii=False)
            await response.write(f"event: achievements\ndata: {chunk_data}\n\n".encode())
    except Exception as e:
        logger.error(f"❌ Stream: Ошибка формирования достижений: {e}")


def extract_user_name_from_message(user_message: str) -> tuple[str | None, bool]:
    """
    Извлечение имени пользователя из сообщения.

    Returns:
        tuple: (имя или None, является ли отказом)
    """
    from bot.utils.chat_utils import extract_user_name_from_message as _extract

    return _extract(user_message)


def extract_user_grade_from_message(user_message: str) -> int | None:
    """
    Извлечение класса пользователя из сообщения.

    Returns:
        int | None: Класс (1-11) или None если не найден
    """
    cleaned_message = user_message.strip().lower()

    # Паттерны для извлечения класса
    grade_patterns = [
        r"(\d+)\s*класс",  # "5 класс", "7 класс"
        r"в\s*(\d+)\s*классе",  # "в 5 классе"
        r"учусь\s*в\s*(\d+)",  # "учусь в 5"
        r"класс\s*(\d+)",  # "класс 5"
        r"^(\d+)$",  # Просто число "5" (если сообщение короткое)
    ]

    for pattern in grade_patterns:
        match = re.search(pattern, cleaned_message)
        if match:
            grade = int(match.group(1))
            # Валидация: класс должен быть от 1 до 11
            if 1 <= grade <= 11:
                return grade

    return None
