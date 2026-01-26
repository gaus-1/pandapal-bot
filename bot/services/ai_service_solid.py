"""
AI сервис для генерации ответов через Yandex Cloud.

Предоставляет единый интерфейс для работы с YandexGPT, SpeechKit и Vision API.
"""

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
    """Facade для Yandex Cloud AI сервисов."""

    def __init__(self):
        """Инициализация сервиса."""
        # Создаем зависимости
        moderator = ContentModerator()
        context_builder = ContextBuilder()

        # Инжектим зависимости в Yandex генератор
        self.response_generator = YandexAIResponseGenerator(moderator, context_builder)

        logger.info("✅ Yandex Cloud AI Service (SOLID) инициализирован")

    @safe_track_ai_service
    async def generate_response(
        self,
        user_message: str,
        chat_history: list[dict] = None,
        user_age: int | None = None,
        user_name: str | None = None,
        user_grade: int | None = None,
        is_history_cleared: bool = False,
        message_count_since_name: int = 0,
        skip_name_asking: bool = False,
        non_educational_questions_count: int = 0,
        is_premium: bool = False,
        is_auto_greeting_sent: bool = False,
    ) -> str:
        """Генерация ответа через YandexGPT."""
        return await self.response_generator.generate_response(
            user_message,
            chat_history,
            user_age,
            user_name,
            user_grade,
            is_history_cleared,
            message_count_since_name,
            skip_name_asking,
            non_educational_questions_count,
            is_premium,
            is_auto_greeting_sent,
        )

    def get_model_info(self) -> dict[str, str]:
        """Получить информацию о текущей AI модели."""
        return self.response_generator.get_model_info()

    async def analyze_image(
        self, image_data: bytes, user_message: str | None = None, user_age: int | None = None
    ) -> str:
        """Анализировать изображение через Yandex Vision API."""
        return await self.response_generator.analyze_image(image_data, user_message, user_age)

    async def moderate_image_content(self, image_data: bytes) -> tuple[bool, str]:
        """Проверить изображение на безопасность через модерацию."""
        return await self.response_generator.moderate_image_content(image_data)


# Глобальный экземпляр (Singleton)
_ai_service: YandexAIService | None = None


def get_ai_service() -> YandexAIService:
    """Получить глобальный экземпляр Yandex AI сервиса."""
    global _ai_service
    if _ai_service is None:
        _ai_service = YandexAIService()
    return _ai_service
