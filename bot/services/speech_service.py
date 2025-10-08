"""
Сервис распознавания речи через OpenAI Whisper
Конвертирует голосовые сообщения в текст
"""

import os
import tempfile
from typing import Optional

from loguru import logger

# Whisper временно отключен для быстрого деплоя на Render
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("⚠️ OpenAI Whisper не установлен - голосовые сообщения недоступны")


class SpeechRecognitionService:
    """
    Сервис для распознавания речи через Whisper
    Поддерживает русский и английский языки
    """
    
    def __init__(self, model_size: str = "tiny"):
        """
        Инициализация сервиса
        
        Args:
            model_size: Размер модели Whisper
                - tiny (39M, быстро, менее точно)
                - base (74M, баланс) ✅ РЕКОМЕНДУЕТСЯ для русского
                - small (244M, точнее, медленнее)
                - medium (769M, очень точно, очень медленно)
                - large (1550M, максимальная точность)
                - turbo (809M, быстро, только английский)
        
        Примечание: turbo НЕ поддерживает русский язык!
        Для русского используйте base или small.
        """
        logger.info(f"🎤 Инициализация распознавания речи: {model_size}")
        
        if not WHISPER_AVAILABLE:
            logger.warning("⚠️ Whisper недоступен - используется заглушка")
            self.model = None
            self.model_size = model_size
            return
        
        try:
            self.model = whisper.load_model(model_size)
            self.model_size = model_size
            logger.info(f"✅ Whisper модель {model_size} загружена успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки Whisper: {e}")
            raise
    
    async def transcribe_voice(
        self, 
        voice_file_bytes: bytes, 
        language: str = "ru",
        auto_detect_language: bool = True
    ) -> Optional[str]:
        """
        Распознать речь из голосового сообщения
        
        Args:
            voice_file_bytes: Байты аудио файла (.ogg)
            language: Предполагаемый язык (ru/en) - используется если auto_detect=False
            auto_detect_language: Автоопределение языка (рекомендуется)
        
        Returns:
            str: Распознанный текст или None при ошибке
        """
        # Проверка доступности Whisper
        if not WHISPER_AVAILABLE or self.model is None:
            logger.warning("⚠️ Whisper недоступен - возвращаем заглушку")
            return "Извини, распознавание речи временно недоступно. Пожалуйста, напиши текстом! 📝"
        
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
            
            # Параметры распознавания
            transcribe_options = {
                "fp16": False,  # CPU совместимость
                "verbose": False
            }
            
            # Автоопределение языка или использование указанного
            if not auto_detect_language:
                transcribe_options["language"] = language
            
            # Распознаем речь через Whisper
            result = self.model.transcribe(temp_file_path, **transcribe_options)
            
            # Логируем определенный язык
            detected_lang = result.get("language", "unknown")
            logger.info(f"🌍 Определен язык: {detected_lang}")
            
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

