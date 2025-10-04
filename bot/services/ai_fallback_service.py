"""
🤖 СИСТЕМА FALLBACK ДЛЯ AI
Автоматическое переключение на резервные AI при сбоях Gemini
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import random

from loguru import logger
import aiohttp
from google.generativeai import GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class AIProvider(Enum):
    """Провайдеры AI"""
    GEMINI = "gemini"
    OPENAI_FALLBACK = "openai_fallback"
    LOCAL_FALLBACK = "local_fallback"
    CACHED_RESPONSES = "cached_responses"


class AIFallbackService:
    """🤖 Сервис с автоматическим переключением AI провайдеров"""
    
    def __init__(self):
        self.current_provider = AIProvider.GEMINI
        self.fallback_responses = self._load_fallback_responses()
        self.provider_status = {
            AIProvider.GEMINI: True,
            AIProvider.OPENAI_FALLBACK: True,
            AIProvider.LOCAL_FALLBACK: True,
            AIProvider.CACHED_RESPONSES: True,
        }
        self.provider_errors = {provider: 0 for provider in AIProvider}
        self.max_errors = 3
        self.last_successful_provider = AIProvider.GEMINI
        
    def _load_fallback_responses(self) -> Dict[str, List[str]]:
        """Загрузка заготовленных ответов для fallback"""
        return {
            "greeting": [
                "Привет! Я PandaPalAI, твой помощник в учебе! 🐼",
                "Здравствуй! Готов помочь с уроками! 📚",
                "Привет! Чем могу помочь с учебой? ✨"
            ],
            "math": [
                "Давай разберем эту задачу пошагово! 📐",
                "Математика - это интересно! Покажи задачу 🧮",
                "Готов помочь с решением! 💡"
            ],
            "science": [
                "Наука - это увлекательно! Расскажи, что изучаешь 🔬",
                "Готов объяснить любые научные факты! 🌟",
                "Давай разберем этот вопрос вместе! 🧪"
            ],
            "language": [
                "Русский язык - основа всех знаний! Помогу с правилами 📝",
                "Готов помочь с грамматикой и правописанием! ✍️",
                "Давай разберем правила языка вместе! 📖"
            ],
            "history": [
                "История - это увлекательное путешествие в прошлое! 🏛️",
                "Готов рассказать интересные факты из истории! 📜",
                "Давай изучать историю вместе! 🗿"
            ],
            "error": [
                "Извини, сейчас у меня небольшие технические проблемы. Попробуй еще раз через минуту! 🔧",
                "Сейчас перезагружаюсь. Через секунду буду готов помочь! ⚡",
                "Временно недоступен, но скоро вернусь! 🚀"
            ],
            "image": [
                "Вижу изображение! Давай разберем его вместе! 👀",
                "Отличное фото! Что именно хочешь узнать? 📸",
                "Интересное изображение! Расскажу, что вижу! 🖼️"
            ],
            "voice": [
                "Слышу тебя! Расскажи, с чем нужна помощь! 🎤",
                "Понял твое сообщение! Готов помочь! 👂",
                "Отлично! Что изучаем сегодня? 🗣️"
            ]
        }
    
    async def generate_response(
        self, 
        message: str, 
        user_telegram_id: int,
        message_type: str = "text",
        image_data: Optional[bytes] = None
    ) -> str:
        """Генерация ответа с автоматическим fallback"""
        
        # Определяем категорию сообщения для fallback
        category = self._categorize_message(message, message_type)
        
        # Пробуем текущий провайдер
        try:
            response = await self._try_provider(
                self.current_provider, 
                message, 
                user_telegram_id, 
                message_type, 
                image_data
            )
            
            if response:
                # Сбрасываем счетчик ошибок при успехе
                self.provider_errors[self.current_provider] = 0
                self.last_successful_provider = self.current_provider
                return response
                
        except Exception as e:
            logger.error(f"❌ Ошибка провайдера {self.current_provider.value}: {e}")
            self.provider_errors[self.current_provider] += 1
            
            # Переключаемся на fallback если превышен лимит ошибок
            if self.provider_errors[self.current_provider] >= self.max_errors:
                await self._switch_to_fallback()
        
        # Пробуем fallback провайдеры
        return await self._try_fallback_providers(message, user_telegram_id, category)
    
    async def _try_provider(
        self, 
        provider: AIProvider, 
        message: str, 
        user_telegram_id: int,
        message_type: str,
        image_data: Optional[bytes] = None
    ) -> Optional[str]:
        """Попытка генерации ответа через конкретный провайдер"""
        
        if provider == AIProvider.GEMINI:
            return await self._try_gemini(message, user_telegram_id, message_type, image_data)
        elif provider == AIProvider.OPENAI_FALLBACK:
            return await self._try_openai_fallback(message, user_telegram_id)
        elif provider == AIProvider.LOCAL_FALLBACK:
            return await self._try_local_fallback(message, user_telegram_id)
        elif provider == AIProvider.CACHED_RESPONSES:
            return await self._try_cached_responses(message, user_telegram_id)
        
        return None
    
    async def _try_gemini(
        self, 
        message: str, 
        user_telegram_id: int,
        message_type: str,
        image_data: Optional[bytes] = None
    ) -> Optional[str]:
        """Попытка использования Gemini AI"""
        try:
            from bot.services.ai_service import GeminiAIService
            ai_service = GeminiAIService()
            
            if message_type == "image" and image_data:
                response = await ai_service.process_image_with_ai(image_data, message)
            elif message_type == "voice":
                response = await ai_service.generate_response(f"Голосовое сообщение: {message}")
            else:
                response = await ai_service.generate_response(message)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка Gemini AI: {e}")
            raise
    
    async def _try_openai_fallback(self, message: str, user_telegram_id: int) -> Optional[str]:
        """Fallback через OpenAI (если настроен)"""
        try:
            # Здесь можно добавить интеграцию с OpenAI
            # Пока возвращаем None для использования следующего fallback
            logger.info("🔄 OpenAI fallback не настроен, переключаемся дальше")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка OpenAI fallback: {e}")
            return None
    
    async def _try_local_fallback(self, message: str, user_telegram_id: int) -> Optional[str]:
        """Локальный fallback с простыми правилами"""
        try:
            # Простая логика на основе ключевых слов
            message_lower = message.lower()
            
            if any(word in message_lower for word in ["привет", "здравствуй", "hi", "hello"]):
                return random.choice(self.fallback_responses["greeting"])
            elif any(word in message_lower for word in ["математика", "матеша", "решить", "задача"]):
                return random.choice(self.fallback_responses["math"])
            elif any(word in message_lower for word in ["наука", "физика", "химия", "биология"]):
                return random.choice(self.fallback_responses["science"])
            elif any(word in message_lower for word in ["русский", "язык", "грамматика", "правописание"]):
                return random.choice(self.fallback_responses["language"])
            elif any(word in message_lower for word in ["история", "исторический", "прошлое"]):
                return random.choice(self.fallback_responses["history"])
            else:
                return "Понимаю твое сообщение! К сожалению, сейчас у меня ограниченные возможности, но я стараюсь помочь! 🤖"
                
        except Exception as e:
            logger.error(f"❌ Ошибка локального fallback: {e}")
            return None
    
    async def _try_cached_responses(self, message: str, user_telegram_id: int) -> Optional[str]:
        """Использование кэшированных ответов"""
        try:
            # Попытка найти похожий вопрос в кэше
            # Пока возвращаем стандартный ответ
            category = self._categorize_message(message, "text")
            return random.choice(self.fallback_responses.get(category, self.fallback_responses["error"]))
            
        except Exception as e:
            logger.error(f"❌ Ошибка кэшированных ответов: {e}")
            return None
    
    def _categorize_message(self, message: str, message_type: str) -> str:
        """Категоризация сообщения для выбора fallback ответа"""
        if message_type == "image":
            return "image"
        elif message_type == "voice":
            return "voice"
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["привет", "здравствуй", "hi", "hello"]):
            return "greeting"
        elif any(word in message_lower for word in ["математика", "матеша", "решить", "задача"]):
            return "math"
        elif any(word in message_lower for word in ["наука", "физика", "химия", "биология"]):
            return "science"
        elif any(word in message_lower for word in ["русский", "язык", "грамматика", "правописание"]):
            return "language"
        elif any(word in message_lower for word in ["история", "исторический", "прошлое"]):
            return "history"
        else:
            return "error"
    
    async def _try_fallback_providers(self, message: str, user_telegram_id: int, category: str) -> str:
        """Попытка использования всех fallback провайдеров по порядку"""
        
        # Список провайдеров в порядке приоритета для fallback
        fallback_order = [
            AIProvider.LOCAL_FALLBACK,
            AIProvider.CACHED_RESPONSES,
        ]
        
        for provider in fallback_order:
            try:
                if not self.provider_status[provider]:
                    continue
                    
                response = await self._try_provider(provider, message, user_telegram_id, "text", None)
                if response:
                    logger.info(f"✅ Fallback успешен через {provider.value}")
                    return response
                    
            except Exception as e:
                logger.error(f"❌ Ошибка fallback провайдера {provider.value}: {e}")
                self.provider_errors[provider] += 1
                
                if self.provider_errors[provider] >= self.max_errors:
                    self.provider_status[provider] = False
        
        # Если все fallback провайдеры не сработали
        return random.choice(self.fallback_responses["error"])
    
    async def _switch_to_fallback(self):
        """Переключение на fallback провайдер"""
        logger.warning(f"🔄 Переключение с {self.current_provider.value} на fallback")
        
        # Отключаем проблемный провайдер
        self.provider_status[self.current_provider] = False
        
        # Переключаемся на последний успешный провайдер или локальный fallback
        if self.provider_status[self.last_successful_provider]:
            self.current_provider = self.last_successful_provider
        else:
            self.current_provider = AIProvider.LOCAL_FALLBACK
        
        logger.info(f"✅ Переключились на провайдер {self.current_provider.value}")
    
    async def reset_provider(self, provider: AIProvider):
        """Сброс провайдера (включение обратно)"""
        self.provider_status[provider] = True
        self.provider_errors[provider] = 0
        logger.info(f"🔄 Провайдер {provider.value} сброшен и включен")
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Получение статуса всех провайдеров"""
        return {
            "current_provider": self.current_provider.value,
            "last_successful_provider": self.last_successful_provider.value,
            "providers": {
                provider.value: {
                    "status": "active" if self.provider_status[provider] else "inactive",
                    "errors": self.provider_errors[provider],
                    "max_errors": self.max_errors
                }
                for provider in AIProvider
            },
            "timestamp": datetime.now().isoformat()
        }


# Глобальный экземпляр fallback сервиса
ai_fallback_service = AIFallbackService()
