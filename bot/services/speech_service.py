"""
Сервис распознавания речи через Yandex SpeechKit.

Поддерживает русский и английский языки.
"""

import subprocess
import tempfile
from pathlib import Path

from loguru import logger

from bot.services.yandex_cloud_service import get_yandex_cloud_service

# Коды языков Yandex SpeechKit (ru-RU, en-US)
YANDEX_SPEECH_LANGUAGE: dict[str, str] = {"ru": "ru-RU", "en": "en-US"}


def _normalize_speech_language(language: str | None) -> str:
    """Нормализация кода языка для SpeechKit: ru или en."""
    if not language or not language.strip():
        return "ru"
    lang = language.strip().lower()
    return "en" if lang.startswith("en") else "ru"


class SpeechRecognitionService:
    """Сервис для распознавания речи через Yandex SpeechKit STT."""

    def __init__(self):
        """Инициализация сервиса распознавания речи."""
        self.yandex_service = get_yandex_cloud_service()
        logger.info("✅ Yandex SpeechKit STT сервис инициализирован")

    async def transcribe_voice(self, voice_file_bytes: bytes, language: str = "ru") -> str | None:
        """Распознать речь из голосового сообщения через Yandex SpeechKit."""
        try:
            lang = _normalize_speech_language(language)
            yandex_language = YANDEX_SPEECH_LANGUAGE.get(lang, "ru-RU")
            logger.info(f"🎤 Распознавание речи через Yandex SpeechKit (язык: {yandex_language})")

            # Конвертируем webm в oggopus через ffmpeg (если нужно)
            audio_data = await self._convert_audio_if_needed(voice_file_bytes)

            # Определяем формат аудио
            audio_format = "oggopus"

            # Распознаём речь через Yandex SpeechKit (ru-RU или en-US)
            recognized_text = await self.yandex_service.recognize_speech(
                audio_data=audio_data, audio_format=audio_format, language=yandex_language
            )

            if not recognized_text:
                logger.warning("⚠️ Yandex SpeechKit не распознал речь")
                return None

            logger.info(f"✅ Речь распознана: '{recognized_text[:100]}...'")
            return recognized_text

        except Exception as e:
            logger.error(f"❌ Ошибка распознавания речи (Yandex SpeechKit): {e}", exc_info=True)
            # Пробрасываем исключение дальше для правильной обработки в endpoint
            raise

    async def _convert_audio_if_needed(self, audio_bytes: bytes) -> bytes:
        """Конвертирует webm в oggopus через ffmpeg, если нужно."""
        try:
            # Проверяем, является ли это webm (первые байты: 1a 45 df a3)
            if audio_bytes[:4] == b"\x1a\x45\xdf\xa3":  # WebM signature
                logger.info("🔄 Конвертация WebM -> OGG Opus через ffmpeg...")

                # Создаем временные файлы
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as input_file:
                    input_file.write(audio_bytes)
                    input_path = input_file.name

                with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as output_file:
                    output_path = output_file.name

                try:
                    # Конвертируем через ffmpeg
                    # -i input.webm -acodec libopus -ar 48000 -ac 1 output.ogg
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-i",
                            input_path,
                            "-acodec",
                            "libopus",
                            "-ar",
                            "48000",
                            "-ac",
                            "1",
                            "-y",  # Перезаписать выходной файл
                            output_path,
                        ],
                        capture_output=True,
                        timeout=10,
                        check=True,
                    )

                    # Читаем конвертированный файл потоково с ограничением размера
                    max_converted_size = 20 * 1024 * 1024  # 20MB лимит
                    converted_bytes = b""
                    total_read = 0
                    chunk_size = 64 * 1024  # 64KB chunks

                    with open(output_path, "rb") as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            converted_bytes += chunk
                            total_read += len(chunk)
                            if total_read > max_converted_size:
                                logger.error(
                                    f"❌ Конвертированный файл слишком большой: "
                                    f"{total_read} байт > {max_converted_size} байт"
                                )
                                # Возвращаем исходные байты в случае ошибки
                                return audio_bytes

                    logger.info(
                        f"✅ Конвертация успешна: {len(audio_bytes)} -> {len(converted_bytes)} байт"
                    )
                    return converted_bytes

                except subprocess.CalledProcessError as e:
                    logger.error(f"❌ Ошибка ffmpeg: {e.stderr.decode() if e.stderr else str(e)}")
                    # Возвращаем исходные байты, попробуем отправить как есть
                    return audio_bytes
                except subprocess.TimeoutExpired:
                    logger.error("❌ ffmpeg timeout - конвертация заняла слишком много времени")
                    return audio_bytes
                finally:
                    # Удаляем временные файлы
                    try:
                        Path(input_path).unlink(missing_ok=True)
                        Path(output_path).unlink(missing_ok=True)
                    except Exception:
                        pass

            # Проверяем, является ли это ogg (первые байты: OggS)
            if audio_bytes[:4] == b"OggS":
                logger.info("✅ Аудио уже в формате OGG Opus, конвертация не требуется")
                return audio_bytes

            # Если не webm и не ogg, логируем предупреждение
            logger.warning(
                f"⚠️ Неизвестный формат аудио (первые байты: {audio_bytes[:4].hex()}), "
                "попробуем отправить как есть"
            )
            return audio_bytes

        except Exception as e:
            logger.warning(f"⚠️ Ошибка при проверке формата аудио: {e}, отправляем как есть")
            return audio_bytes


# Alias for backward compatibility
SpeechService = SpeechRecognitionService

# Глобальный экземпляр (Singleton)
_speech_service: SpeechRecognitionService | None = None


def get_speech_service() -> SpeechRecognitionService:
    """Получить глобальный экземпляр Yandex SpeechKit сервиса."""
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechRecognitionService()
    return _speech_service
