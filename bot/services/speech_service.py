"""
Сервис распознавания речи через OpenAI Whisper
Конвертирует голосовые сообщения в текст
"""

import os
import tempfile
from typing import Optional

import whisper
from loguru import logger


class SpeechRecognitionService:
    """
    Сервис для распознавания речи через Whisper
    Поддерживает русский и английский языки
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Инициализация сервиса
        
        Args:
            model_size: Размер модели Whisper
                - tiny (39M, быстро, неточно)
                - base (74M, баланс) ✅ РЕКОМЕНДУЕТСЯ
                - small (244M, медленно, точно)
        """
        logger.info(f"🎤 Загрузка Whisper модели: {model_size}")
        
        try:
            self.model = whisper.load_model(model_size)
            logger.info("✅ Whisper модель загружена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки Whisper: {e}")
            raise
    
    async def transcribe_voice(
        self, 
        voice_file_bytes: bytes, 
        language: str = "ru"
    ) -> Optional[str]:
        """
        Распознать речь из голосового сообщения
        
        Args:
            voice_file_bytes: Байты аудио файла (.ogg)
            language: Язык речи (ru/en)
        
        Returns:
            str: Распознанный текст или None при ошибке
        """
        temp_file_path = None
        
        try:
            # Создаем временный файл для аудио
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=".ogg"
            ) as temp_file:
                temp_file.write(voice_file_bytes)
                temp_file_path = temp_file.name
            
            logger.info(f"🎤 Распознавание речи: {temp_file_path}")
            
            # Распознаем речь через Whisper
            result = self.model.transcribe(
                temp_file_path,
                language=language,
                fp16=False,
                verbose=False
            )
            
            # Получаем распознанный текст
            text = result["text"].strip()
            
            logger.info(f"✅ Речь распознана: {text[:100]}...")
            
            return text
            
        except Exception as e:
            logger.error(f"❌ Ошибка распознавания речи: {e}")
            return None
            
        finally:
            # Удаляем временный файл
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить временный файл: {e}")
    
    def get_service_status(self) -> dict:
        """Получить статус сервиса"""
        return {
            "service": "SpeechRecognitionService",
            "status": "active" if self.model else "inactive",
            "model": "whisper-base",
            "languages": ["ru", "en"]
        }


# Глобальный экземпляр сервиса (Singleton)
_speech_service: Optional[SpeechRecognitionService] = None


def get_speech_service() -> SpeechRecognitionService:
    """
    Получить глобальный экземпляр сервиса
    Создается один раз при первом вызове
    """
    global _speech_service
    
    if _speech_service is None:
        _speech_service = SpeechRecognitionService(model_size="base")
    
    return _speech_service

