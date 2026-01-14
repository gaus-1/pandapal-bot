"""
Сервис для обработки аудио в Mini App.

Отвечает за:
- Распознавание речи через SpeechKit
- Определение языка
- Перевод на русский (если нужно)
- Валидацию размера аудио
"""

import base64

from aiohttp import web
from loguru import logger

from bot.services.speech_service import get_speech_service
from bot.services.translate_service import get_translate_service


class MiniappAudioService:
    """Сервис для обработки голосовых сообщений в Mini App."""

    MAX_AUDIO_BASE64_SIZE = 14 * 1024 * 1024  # 14MB
    MAX_AUDIO_BYTES_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        """Инициализация сервиса."""
        self.speech_service = get_speech_service()
        self.translate_service = get_translate_service()

    async def process_audio(
        self,
        audio_base64: str,
        telegram_id: int,
        response: web.StreamResponse,
    ) -> str | None:
        """
        Обрабатывает голосовое сообщение.

        Args:
            audio_base64: Base64 строка аудио (может содержать префикс data:audio/...;base64,)
            telegram_id: ID пользователя в Telegram
            response: SSE response для отправки событий

        Returns:
            str: Распознанный и переведенный текст, или None при ошибке
        """
        try:
            logger.info(f"🎤 Stream: Обработка голосового сообщения от {telegram_id}")

            # Отправляем событие обработки аудио
            await response.write(b'event: status\ndata: {"status": "transcribing"}\n\n')

            # Убираем data:audio/...;base64, префикс
            if "base64," in audio_base64:
                audio_base64 = audio_base64.split("base64,")[1]

            # Валидация размера
            if len(audio_base64) > self.MAX_AUDIO_BASE64_SIZE:
                error_msg = 'event: error\ndata: {"error": "Аудио слишком большое"}\n\n'
                await response.write(error_msg.encode("utf-8"))
                return None

            audio_bytes = base64.b64decode(audio_base64)

            if len(audio_bytes) > self.MAX_AUDIO_BYTES_SIZE:
                error_msg = 'event: error\ndata: {"error": "Аудио слишком большое"}\n\n'
                await response.write(error_msg.encode("utf-8"))
                return None

            # Распознавание речи
            transcribed_text = await self.speech_service.transcribe_voice(
                audio_bytes, language="ru"
            )

            if not transcribed_text or not transcribed_text.strip():
                error_msg = 'event: error\ndata: {"error": "Не удалось распознать речь"}\n\n'
                await response.write(error_msg.encode("utf-8"))
                return None

            # Определяем язык и переводим если нужно
            detected_lang = await self.translate_service.detect_language(transcribed_text)

            if (
                detected_lang
                and detected_lang != "ru"
                and detected_lang in self.translate_service.SUPPORTED_LANGUAGES
            ):
                lang_name = self.translate_service.get_language_name(detected_lang)
                translated_text = await self.translate_service.translate_text(
                    transcribed_text, target_language="ru", source_language=detected_lang
                )
                if translated_text:
                    user_message = (
                        f"🌍 Вижу, что ты сказал на {lang_name}!\n\n"
                        f"📝 Оригинал: {transcribed_text}\n"
                        f"🇷🇺 Перевод: {translated_text}\n\n"
                        f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                    )
                else:
                    user_message = transcribed_text
            else:
                user_message = transcribed_text

            logger.info(f"✅ Stream: Аудио распознано: {transcribed_text[:100]}")
            await response.write(b'event: status\ndata: {"status": "transcribed"}\n\n')

            return user_message

        except Exception as e:
            logger.error(f"❌ Stream: Ошибка обработки аудио: {e}", exc_info=True)
            await response.write(
                f'event: error\ndata: {{"error": "Ошибка обработки аудио: {str(e)}"}}\n\n'.encode()
            )
            return None
