"""
Обработка голосовых и аудио сообщений для AI чата.
"""

from aiogram import F, Router
from aiogram.types import Message
from loguru import logger

from bot.monitoring import log_user_activity

from .helpers import check_premium_limit, read_file_safely
from .text import handle_ai_message

MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB


def register_handlers(router: Router) -> None:
    """Регистрирует handlers для голосовых и аудио сообщений."""
    router.message.register(handle_voice, F.voice)
    router.message.register(handle_audio, F.audio)


async def _process_audio_input(message: Message, file_id: str, media_type: str) -> None:
    """
    Общая логика обработки голосовых/аудио сообщений.

    Args:
        message: Сообщение от пользователя
        file_id: ID файла в Telegram
        media_type: "voice" или "audio" (для логов и UI)
    """
    telegram_id = message.from_user.id
    emoji = "🎤" if media_type == "voice" else "🎵"
    label = "Голосовое сообщение" if media_type == "voice" else "Аудиофайл"
    activity_prefix = "voice" if media_type == "voice" else "audio"

    try:
        logger.info(f"{emoji} Получен {media_type} от {telegram_id}")

        # Проверка Premium-лимитов ДО скачивания
        if not await check_premium_limit(telegram_id, message.from_user.username, message):
            return

        processing_msg = await message.answer(
            f"{emoji} Слушаю {label.lower()}... Пожалуйста, подожди! 🐼"
        )

        # Скачиваем файл
        tg_file = await message.bot.get_file(file_id)
        file_stream = await message.bot.download_file(tg_file.file_path)

        # Проверяем размер
        if tg_file.file_size and tg_file.file_size > MAX_AUDIO_SIZE:
            await processing_msg.edit_text(
                f"{emoji} {label} слишком большой! "
                f"Максимум {MAX_AUDIO_SIZE / (1024 * 1024):.0f}MB. "
                f"Попробуй записать короче! 📏"
            )
            return

        # Читаем байты потоково
        try:
            audio_data = read_file_safely(file_stream, max_size=MAX_AUDIO_SIZE)
        except ValueError as e:
            logger.warning(f"⚠️ {label} превышает лимит: {e}")
            await processing_msg.edit_text(
                f"{emoji} {label} слишком большой! Попробуй записать короче! 📏"
            )
            return

        # Распознавание речи
        from bot.services.speech_service import get_speech_service

        speech_service = get_speech_service()
        lang_code = (message.from_user.language_code or "ru").strip().lower()
        speech_lang = "en" if lang_code.startswith("en") else "ru"
        recognized_text = await speech_service.transcribe_voice(audio_data, language=speech_lang)

        if not recognized_text:
            await processing_msg.edit_text(
                f"{emoji} Не удалось распознать речь.\n"
                "Попробуй говорить четче или напиши текстом! 📝"
            )
            log_user_activity(
                telegram_id, f"{activity_prefix}_recognition_failed", False, "SpeechKit failed"
            )
            return

        await processing_msg.delete()

        # Перевод иностранного языка
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        detected_lang = await translate_service.detect_language(recognized_text)

        if (
            detected_lang
            and detected_lang != "ru"
            and detected_lang in translate_service.SUPPORTED_LANGUAGES
        ):
            lang_name = translate_service.get_language_name(detected_lang)
            logger.info(f"🌍 {media_type}: Обнаружен иностранный язык: {detected_lang}")

            translated_text = await translate_service.translate_text(
                recognized_text, target_language="ru", source_language=detected_lang
            )
            if translated_text:
                await message.answer(
                    f'{emoji} <i>Я услышал на {lang_name}:</i> "{recognized_text}"\n'
                    f'🇷🇺 <i>Перевод:</i> "{translated_text}"\n\n'
                    f"Сейчас объясню перевод и подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
                recognized_text = (
                    f"🌍 Вижу, что ты сказал на {lang_name}!\n\n"
                    f"📝 Оригинал: {recognized_text}\n"
                    f"🇷🇺 Перевод: {translated_text}\n\n"
                    f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                )
                logger.info(f"✅ {media_type} переведено: {detected_lang} → ru")
            else:
                await message.answer(
                    f'{emoji} <i>Я услышал:</i> "{recognized_text}"\n\nСейчас подумаю над ответом... 🐼',
                    parse_mode="HTML",
                )
        else:
            await message.answer(
                f'{emoji} <i>Я услышал:</i> "{recognized_text}"\n\nСейчас подумаю над ответом... 🐼',
                parse_mode="HTML",
            )

        logger.info(f"✅ Речь распознана: {recognized_text[:100]}")
        log_user_activity(telegram_id, f"{activity_prefix}_message_sent", True)

        # Обрабатываем как текстовое сообщение
        original_text = message.text
        try:
            object.__setattr__(message, "text", recognized_text)
            await handle_ai_message(message, None)
        finally:
            if original_text is not None:
                object.__setattr__(message, "text", original_text)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки {media_type}: {e}")
        await message.answer(
            f"😔 Произошла ошибка при обработке {label.lower()}.\nПопробуй написать текстом! 📝"
        )
        log_user_activity(telegram_id, f"{activity_prefix}_processing_error", False, str(e))


async def handle_voice(message: Message):
    """Обработка голосовых сообщений."""
    await _process_audio_input(message, message.voice.file_id, "voice")


async def handle_audio(message: Message):
    """Обработка аудиофайлов."""
    await _process_audio_input(message, message.audio.file_id, "audio")
