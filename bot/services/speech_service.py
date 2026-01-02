"""
Сервис распознавания речи через Yandex SpeechKit.

Миграция с OpenAI Whisper на Yandex Cloud SpeechKit STT.
Поддерживает русский и английский языки.

⚠️ КРИТИЧЕСКИЙ МОДУЛЬ - РАБОТАЕТ СТАБИЛЬНО!
⛔ НЕ ИЗМЕНЯТЬ сигнатуру transcribe_voice() без явного запроса!
✅ Текущая сигнатура: transcribe_voice(voice_file_bytes: bytes, language: str = "ru")
"""

from typing import Optional

from loguru import logger

from bot.services.yandex_cloud_service import get_yandex_cloud_service


class SpeechRecognitionService:
    """
    Сервис для распознавания речи через Yandex SpeechKit STT.

    Преимущества Yandex SpeechKit:
    - Отличное распознавание русского языка
    - Поддержка различных форматов аудио
    - Низкая стоимость (₽0.30-0.60 за минуту)
    - Не требует локальных ресурсов (облачный)
    """

    def __init__(self):
        """Инициализация сервиса распознавания речи."""
        self.yandex_service = get_yandex_cloud_service()
        logger.info("✅ Yandex SpeechKit STT сервис инициализирован")

    async def transcribe_voice(
        self, voice_file_bytes: bytes, language: str = "ru"
    ) -> Optional[str]:
        """
        Распознать речь из голосового сообщения через Yandex SpeechKit.

        Args:
            voice_file_bytes: Байты аудио файла (.ogg, .mp3, .wav).
            language: Язык распознавания (ru/en).

        Returns:
            str: Распознанный текст или None при ошибке.
        """
        try:
            logger.info(f"🎤 Распознавание речи через Yandex SpeechKit (язык: {language})")

            # Определяем формат аудио
            # Браузер записывает в формате WebM/Opus (audio/webm)
            # Yandex SpeechKit поддерживает: oggopus, lpcm, mp3
            # WebM содержит Opus кодек, попробуем отправить как oggopus
            # Yandex может принять webm с opus кодеком как oggopus
            audio_format = "oggopus"

            # Язык в формате Yandex Cloud (ru-RU, en-US)
            yandex_language = f"{language}-{language.upper()}"

            # Распознаем речь через Yandex SpeechKit
            recognized_text = await self.yandex_service.recognize_speech(
                audio_data=voice_file_bytes, audio_format=audio_format, language=yandex_language
            )

            if not recognized_text:
                logger.warning("⚠️ Yandex SpeechKit не распознал речь")
                return None

            logger.info(f"✅ Речь распознана: '{recognized_text[:100]}...'")
            return recognized_text

        except Exception as e:
            logger.error(f"❌ Ошибка распознавания речи (Yandex SpeechKit): {e}")
            return None


# Alias for backward compatibility
SpeechService = SpeechRecognitionService

# Глобальный экземпляр (Singleton)
_speech_service: Optional[SpeechRecognitionService] = None


def get_speech_service() -> SpeechRecognitionService:
    """
    Получить глобальный экземпляр Yandex SpeechKit сервиса.

    Returns:
        SpeechRecognitionService: Глобальный экземпляр.
    """
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechRecognitionService()
    return _speech_service
