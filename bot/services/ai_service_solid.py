"""
AI сервис - Facade для Yandex Cloud (YandexGPT).

Миграция с Google Gemini на Yandex Cloud.
Соблюдение SOLID принципов.
"""

from typing import Dict, List, Optional

from loguru import logger

from bot.services.ai_context_builder import ContextBuilder
from bot.services.ai_moderator import ContentModerator
from bot.services.yandex_ai_response_generator import YandexAIResponseGenerator

# Безопасная интеграция метрик (опционально)
try:
    from bot.monitoring.metrics_integration import safe_track_ai_service

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

    # Создаем пустой декоратор если метрики недоступны
    def safe_track_ai_service(func):
        """Заглушка декоратора метрик."""
        return func


class YandexAIService:
    """
    Facade для Yandex Cloud AI сервисов.

    Соблюдает принципы SOLID:
    - SRP: только координация AI сервисов
    - OCP: можно расширять без изменения
    - LSP: можно заменить реализации
    - ISP: использует только нужные интерфейсы
    - DIP: зависит от абстракций
    """

    def __init__(self):
        """Dependency Injection - соблюдение DIP."""
        # Создаем зависимости
        moderator = ContentModerator()
        context_builder = ContextBuilder()

        # Инжектим зависимости в Yandex генератор
        self.response_generator = YandexAIResponseGenerator(moderator, context_builder)

        logger.info("✅ Yandex Cloud AI Service (SOLID) инициализирован")

    @safe_track_ai_service
    async def generate_response(
        self, user_message: str, chat_history: List[Dict] = None, user_age: Optional[int] = None
    ) -> str:
        """
        Генерация ответа через YandexGPT.

        Args:
            user_message: Сообщение пользователя
            chat_history: История чата
            user_age: Возраст пользователя для адаптации

        Returns:
            str: Ответ от AI
        """
        return await self.response_generator.generate_response(user_message, chat_history, user_age)

    def get_model_info(self) -> Dict[str, str]:
        """Информация о текущей модели."""
        return self.response_generator.get_model_info()


# Глобальный экземпляр (Singleton)
_ai_service: Optional[YandexAIService] = None


def get_ai_service() -> YandexAIService:
    """
    Получить глобальный экземпляр Yandex AI сервиса.

    Реализует паттерн Singleton для обеспечения единого экземпляра
    во всем приложении.

    Returns:
        YandexAIService: Глобальный экземпляр AI сервиса.
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = YandexAIService()
    return _ai_service
