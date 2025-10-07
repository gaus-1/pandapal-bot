"""
Фасад для работы с Google Gemini AI
Координирует работу специализированных сервисов
Соблюдает принципы SOLID
"""

import hashlib
from typing import Dict, List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from typing import Type

from bot.config import settings
from bot.services.ai_response_generator import AIResponseGenerator
from bot.services.ai_context_manager import AIContextManager
from bot.services.cache_service import AIResponseCache, cache_service
from bot.services.moderation_service import ContentModerationService


# Глобальный экземпляр сервиса
ai_service = None


def get_ai_service() -> "GeminiAIService":
    """Получение глобального экземпляра AI сервиса"""
    global ai_service
    if ai_service is None:
        ai_service = GeminiAIService()
    return ai_service


class GeminiAIService:
    """
    Фасад для работы с Google Gemini AI
    Координирует работу специализированных сервисов
    """

    def __init__(self):
        """Инициализация AI сервиса"""
        # Инициализация специализированных сервисов
        self.response_generator = AIResponseGenerator()
        self.context_manager = AIContextManager()
        self.moderation = ContentModerationService()

        logger.info("✅ Gemini AI Service инициализирован")

    async def generate_response(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]] = None,
        user_age: Optional[int] = None,
        user_grade: Optional[int] = None,
        user_telegram_id: int = 0,
    ) -> str:
        """
        Генерация ответа AI с учётом контекста и возраста
        """
        try:
            # Модерация входящего сообщения
            is_safe, reason = self.moderation.is_safe_content(user_message)
            if not is_safe:
                logger.warning(f"🚫 Небезопасный контент: {reason}")
                return "Извините, я не могу ответить на это сообщение. Пожалуйста, задайте другой вопрос."

            # Проверка кэша
            cache_key = self._generate_cache_key(user_message, user_age, user_grade)
            cached_response = await cache_service.get(cache_key)
            if cached_response:
                logger.info("📦 Ответ найден в кэше")
                return cached_response

            # Подготовка контекста (используется в response_generator)
            self.context_manager.prepare_context(
                user_message, chat_history, user_age, user_grade
            )

            # Генерация ответа
            ai_response = await self.response_generator.generate_text_response(
                user_message, chat_history
            )

            # Модерация исходящего ответа
            is_safe_response, reason_response = self.moderation.is_safe_content(ai_response)
            if not is_safe_response:
                logger.warning(f"🚫 Небезопасный ответ AI: {reason_response}")
                ai_response = "Извините, я не могу дать полный ответ на этот вопрос. Попробуйте переформулировать."

            # Сохранение в кэш
            await cache_service.set(cache_key, ai_response, ttl=3600)

            logger.info(f"✅ AI ответ сгенерирован: {len(ai_response)} символов")
            return ai_response

        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI: {e}")
            return "Ой, что-то пошло не так. Попробуй переформулировать вопрос или напиши /start"

    async def analyze_image(self, image_data: bytes, prompt: str = "Опиши это изображение") -> str:
        """
        Анализ изображения через Gemini Vision API
        """
        try:
            # Модерация промпта
            is_safe, reason = self.moderation.is_safe_content(prompt)
            if not is_safe:
                logger.warning(f"🚫 Небезопасный промпт для изображения: {reason}")
                return "Извините, не могу проанализировать изображение с таким запросом."

            # Генерация ответа на изображение
            response = await self.response_generator.generate_image_response(image_data, prompt)

            # Модерация ответа
            is_safe_response, _ = self.moderation.is_safe_content(response)
            if not is_safe_response:
                return "Извините, не могу предоставить анализ этого изображения."

            logger.info("✅ Анализ изображения завершен")
            return response

        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения: {e}")
            return "Извините, не могу проанализировать изображение."

    def _generate_cache_key(
        self, user_message: str, user_age: Optional[int], user_grade: Optional[int]
    ) -> str:
        """Генерация ключа кэша"""
        key_data = f"{user_message}:{user_age}:{user_grade}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_model_info(self) -> Dict[str, str]:
        """Получение информации о модели"""
        return {
            "model": settings.gemini_model,
            "temperature": str(settings.ai_temperature),
            "max_tokens": str(settings.ai_max_tokens),
            "public_name": "PandaPalAI"
        }

    def get_service_status(self) -> Dict[str, any]:
        """Получение статуса сервиса"""
        return {
            "service": "GeminiAIService",
            "status": "healthy",
            "components": {
                "response_generator": "active",
                "context_manager": "active",
                "moderation": "active",
            },
        }
