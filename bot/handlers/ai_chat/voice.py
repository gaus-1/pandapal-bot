"""
Обработка голосовых и аудио сообщений для AI чата.
"""

from aiogram import F, Router
from aiogram.types import Message
from loguru import logger

from bot.monitoring import log_user_activity

from .helpers import read_file_safely
from .text import handle_ai_message


def register_handlers(router: Router) -> None:
    """Регистрирует handlers для голосовых и аудио сообщений."""
    router.message.register(handle_voice, F.voice)
    router.message.register(handle_audio, F.audio)


async def handle_voice(message: Message):
    """
    Обработка голосовых сообщений

    ВАЖНО: Интеграция с Yandex SpeechKit для распознавания речи.
    Стабильная версия с проверенными параметрами.

    Параметры распознавания:
    - Формат: OGG Opus (Telegram стандарт)
    - Язык: ru-RU
    - API: Yandex Cloud SpeechKit STT

    Args:
        message: Голосовое сообщение от пользователя
    """
    telegram_id = message.from_user.id

    try:
        logger.info(f"🎤 Получено голосовое сообщение от {telegram_id}")

        # Показываем что обрабатываем
        processing_msg = await message.answer("🎤 Слушаю твоё сообщение... Пожалуйста, подожди! 🐼")

        # Скачиваем голосовое сообщение
        voice_file = await message.bot.get_file(message.voice.file_id)
        voice_bytes = await message.bot.download_file(voice_file.file_path)

        # Проверяем размер голосового сообщения (Telegram лимит обычно 1MB, но может быть больше)
        max_voice_size = 20 * 1024 * 1024  # 20MB для безопасности
        if voice_file.file_size and voice_file.file_size > max_voice_size:
            await processing_msg.edit_text(
                f"🎤 Голосовое сообщение слишком большое! "
                f"Максимум {max_voice_size / (1024 * 1024):.0f}MB. "
                f"Попробуй записать короче! 📏"
            )
            return

        # Читаем байты потоково с ограничением размера
        try:
            audio_data = read_file_safely(voice_bytes, max_size=max_voice_size)
        except ValueError as e:
            logger.warning(f"⚠️ Голосовое сообщение превышает лимит: {e}")
            await processing_msg.edit_text(
                "🎤 Голосовое сообщение слишком большое! " "Попробуй записать короче! 📏"
            )
            return

        # Получаем сервис распознавания речи
        from bot.services.speech_service import get_speech_service

        speech_service = get_speech_service()

        # Распознаем речь с автоопределением языка
        recognized_text = await speech_service.transcribe_voice(
            audio_data,
            language="ru",  # Русский язык
        )

        if not recognized_text:
            await processing_msg.edit_text(
                "🎤 Не удалось распознать речь.\n" "Попробуй говорить четче или напиши текстом! 📝"
            )
            log_user_activity(telegram_id, "voice_recognition_failed", False, "SpeechKit failed")
            return

        # Удаляем сообщение "Слушаю..."
        await processing_msg.delete()

        # Определяем язык текста и переводим если не русский
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        detected_lang = await translate_service.detect_language(recognized_text)

        # Если язык определен и это не русский, но поддерживаемый язык
        if (
            detected_lang
            and detected_lang != "ru"
            and detected_lang in translate_service.SUPPORTED_LANGUAGES
        ):
            lang_name = translate_service.get_language_name(detected_lang)
            logger.info(f"🌍 Аудио: Обнаружен иностранный язык: {detected_lang}")
            # Переводим текст
            translated_text = await translate_service.translate_text(
                recognized_text, target_language="ru", source_language=detected_lang
            )
            if translated_text:
                # Показываем что было распознано и переведено
                await message.answer(
                    f'🎤 <i>Я услышал на {lang_name}:</i> "{recognized_text}"\n'
                    f'🇷🇺 <i>Перевод:</i> "{translated_text}"\n\n'
                    f"Сейчас объясню перевод и подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
                # Формируем сообщение с переводом и объяснением
                recognized_text = (
                    f"🌍 Вижу, что ты сказал на {lang_name}!\n\n"
                    f"📝 Оригинал: {recognized_text}\n"
                    f"🇷🇺 Перевод: {translated_text}\n\n"
                    f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                )
                logger.info(f"✅ Аудио переведено: {detected_lang} → ru")
            else:
                await message.answer(
                    f'🎤 <i>Я услышал:</i> "{recognized_text}"\n\n'
                    f"Сейчас подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
        else:
            # Показываем что было распознано
            await message.answer(
                f'🎤 <i>Я услышал:</i> "{recognized_text}"\n\n' f"Сейчас подумаю над ответом... 🐼",
                parse_mode="HTML",
            )

        logger.info(f"✅ Речь распознана: {recognized_text[:100]}")

        # Логируем успешную активность
        log_user_activity(telegram_id, "voice_message_sent", True)

        # Обрабатываем как обычное текстовое сообщение (передаем оригинальный message с bot)
        # Временно сохраняем текст в message для обработки
        original_text = message.text
        try:
            # Используем __dict__ для обхода frozen instance
            object.__setattr__(message, "text", recognized_text)
            await handle_ai_message(message, None)
        finally:
            # Восстанавливаем оригинальный текст
            if original_text is not None:
                object.__setattr__(message, "text", original_text)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки голосового сообщения: {e}")
        await message.answer(
            "😔 Произошла ошибка при обработке голосового сообщения.\n"
            "Попробуй написать текстом! 📝"
        )
        log_user_activity(telegram_id, "voice_processing_error", False, str(e))


async def handle_audio(message: Message):
    """
    Обработка аудиофайлов (музыка, треки)

    ВАЖНО: Использует ту же логику распознавания что и голосовые сообщения.
    Yandex SpeechKit STT с параметрами (voice_file_bytes, language).

    Args:
        message: Аудиофайл от пользователя
    """
    telegram_id = message.from_user.id

    try:
        logger.info(f"🎵 Получен аудиофайл от {telegram_id}")

        # Показываем что обрабатываем
        processing_msg = await message.answer("🎵 Слушаю аудиофайл... Пожалуйста, подожди! 🐼")

        # Скачиваем аудиофайл
        audio_file = await message.bot.get_file(message.audio.file_id)
        audio_bytes = await message.bot.download_file(audio_file.file_path)

        # Проверяем размер аудиофайла
        max_audio_size = 20 * 1024 * 1024  # 20MB лимит
        if audio_file.file_size and audio_file.file_size > max_audio_size:
            await processing_msg.edit_text(
                f"🎵 Аудиофайл слишком большой! "
                f"Максимум {max_audio_size / (1024 * 1024):.0f}MB. "
                f"Попробуй другой файл! 📏"
            )
            return

        # Читаем байты потоково с ограничением размера
        try:
            audio_data = read_file_safely(audio_bytes, max_size=max_audio_size)
        except ValueError as e:
            logger.warning(f"⚠️ Аудиофайл превышает лимит: {e}")
            await processing_msg.edit_text(
                "🎵 Аудиофайл слишком большой! " "Попробуй другой файл! 📏"
            )
            return

        # Получаем сервис распознавания речи
        from bot.services.speech_service import get_speech_service

        speech_service = get_speech_service()

        # Распознаем речь
        recognized_text = await speech_service.transcribe_voice(
            audio_data,
            language="ru",
        )

        if not recognized_text:
            await processing_msg.edit_text(
                "🎵 Не удалось распознать речь из аудио.\n"
                "Попробуй голосовое сообщение или напиши текстом! 📝"
            )
            log_user_activity(telegram_id, "audio_recognition_failed", False, "SpeechKit failed")
            return

        # Удаляем сообщение "Слушаю..."
        await processing_msg.delete()

        # Определяем язык текста и переводим если не русский
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        detected_lang = await translate_service.detect_language(recognized_text)

        # Если язык определен и это не русский, но поддерживаемый язык
        if (
            detected_lang
            and detected_lang != "ru"
            and detected_lang in translate_service.SUPPORTED_LANGUAGES
        ):
            lang_name = translate_service.get_language_name(detected_lang)
            logger.info(f"🌍 Аудио: Обнаружен иностранный язык: {detected_lang}")
            # Переводим текст
            translated_text = await translate_service.translate_text(
                recognized_text, target_language="ru", source_language=detected_lang
            )
            if translated_text:
                # Показываем что было распознано и переведено
                await message.answer(
                    f'🎵 <i>Я услышал на {lang_name}:</i> "{recognized_text}"\n'
                    f'🇷🇺 <i>Перевод:</i> "{translated_text}"\n\n'
                    f"Сейчас объясню перевод и подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
                # Формируем сообщение с переводом и объяснением
                recognized_text = (
                    f"🌍 Вижу, что ты сказал на {lang_name}!\n\n"
                    f"📝 Оригинал: {recognized_text}\n"
                    f"🇷🇺 Перевод: {translated_text}\n\n"
                    f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                )
                logger.info(f"✅ Аудио переведено: {detected_lang} → ru")
            else:
                await message.answer(
                    f'🎵 <i>Я услышал:</i> "{recognized_text}"\n\n'
                    f"Сейчас подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
        else:
            # Показываем что было распознано
            await message.answer(
                f'🎵 <i>Я услышал:</i> "{recognized_text}"\n\n' f"Сейчас подумаю над ответом... 🐼",
                parse_mode="HTML",
            )

        logger.info(f"✅ Речь из аудио распознана: {recognized_text[:100]}")

        # Логируем успешную активность
        log_user_activity(telegram_id, "audio_message_sent", True)

        # Обрабатываем как обычное текстовое сообщение
        original_text = message.text
        try:
            object.__setattr__(message, "text", recognized_text)
            await handle_ai_message(message, None)
        finally:
            if original_text is not None:
                object.__setattr__(message, "text", original_text)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки аудиофайла: {e}")
        await message.answer(
            "😔 Произошла ошибка при обработке аудиофайла.\n" "Попробуй написать текстом! 📝"
        )
        log_user_activity(telegram_id, "audio_processing_error", False, str(e))
