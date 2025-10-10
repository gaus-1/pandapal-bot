"""
AI сервис - Facade pattern + Dependency Injection
Соблюдение SOLID принципов
"""

from typing import Dict, List, Optional

from loguru import logger

from bot.services.ai_context_builder import ContextBuilder
from bot.services.ai_moderator import ContentModerator
from bot.services.ai_response_generator_solid import AIResponseGenerator


class GeminiAIService:
    """
    Facade для AI сервисов
    Соблюдает принципы SOLID:
    - SRP: только координация
    - OCP: можно расширять без изменения
    - LSP: можно заменить реализации
    - ISP: использует только нужные интерфейсы
    - DIP: зависит от абстракций
    """

    def __init__(self):
        """Dependency Injection - соблюдение DIP"""
        # Создаем зависимости (в реальном проекте можно через DI контейнер)
        moderator = ContentModerator()
        context_builder = ContextBuilder()

        # Инжектим зависимости
        self.response_generator = AIResponseGenerator(moderator, context_builder)

        logger.info("✅ Gemini AI Service (SOLID) инициализирован")

    async def generate_response(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """Генерация ответа - делегирование ответственности"""
        return await self.response_generator.generate_response(user_message, chat_history, user_age)

    def get_model_info(self) -> Dict[str, str]:
        """Информация о модели - делегирование"""
        return self.response_generator.get_model_info()


# Глобальный экземпляр
_ai_service = None


def get_ai_service() -> GeminiAIService:
    """
    Получить глобальный экземпляр AI сервиса.

    Реализует паттерн Singleton для обеспечения единого экземпляра
    AI сервиса во всем приложении.

    Returns:
        GeminiAIService: Глобальный экземпляр AI сервиса.
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = GeminiAIService()
    return _ai_service
