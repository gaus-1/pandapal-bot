"""
AI сервис для генерации ответов через Yandex Cloud (YandexGPT).

Предоставляет единый интерфейс для работы с AI сервисами Yandex Cloud,
включая генерацию текстовых ответов, анализ изображений и модерацию контента.
Реализует паттерн Facade и следует принципам SOLID.
"""

from typing import Dict, List, Optional, Tuple

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

    Координирует работу с YandexGPT, SpeechKit и Vision API,
    обеспечивая единый интерфейс для генерации ответов и анализа контента.

    Принципы проектирования:
    - SRP: только координация AI сервисов
    - OCP: можно расширять без изменения существующего кода
    - LSP: можно заменить реализации без нарушения функциональности
    - ISP: использует только необходимые интерфейсы
    - DIP: зависит от абстракций, а не от конкретных реализаций
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
        self,
        user_message: str,
        chat_history: List[Dict] = None,
        user_age: Optional[int] = None,
        user_name: Optional[str] = None,
        is_history_cleared: bool = False,
        message_count_since_name: int = 0,
        skip_name_asking: bool = False,
        non_educational_questions_count: int = 0,
    ) -> str:
        """
        Генерация ответа через YandexGPT.

        Args:
            user_message: Сообщение пользователя
            chat_history: История чата
            user_age: Возраст пользователя для адаптации
            user_name: Имя пользователя для обращения
            is_history_cleared: Флаг очистки истории
            message_count_since_name: Количество сообщений с последнего обращения по имени

        Returns:
            str: Ответ от AI
        """
        return await self.response_generator.generate_response(
            user_message,
            chat_history,
            user_age,
            user_name,
            is_history_cleared,
            message_count_since_name,
            skip_name_asking,
            non_educational_questions_count,
        )

    def get_model_info(self) -> Dict[str, str]:
        """
        Получить информацию о текущей AI модели.

        Returns:
            Dict[str, str]: Словарь с информацией о модели (name, version и т.д.)
        """
        return self.response_generator.get_model_info()

    async def analyze_image(
        self, image_data: bytes, user_message: Optional[str] = None, user_age: Optional[int] = None
    ) -> str:
        """
        Анализировать изображение через Yandex Vision API.

        Args:
            image_data: Байты изображения для анализа
            user_message: Опциональное текстовое сообщение пользователя
            user_age: Возраст пользователя для адаптации ответа

        Returns:
            str: Текстовое описание содержимого изображения
        """
        return await self.response_generator.analyze_image(image_data, user_message, user_age)

    async def moderate_image_content(self, image_data: bytes) -> Tuple[bool, str]:
        """
        Проверить изображение на безопасность через модерацию.

        Args:
            image_data: Байты изображения для проверки

        Returns:
            tuple[bool, str]: (is_safe, reason)
                - is_safe: True если изображение безопасно, False если нет
                - reason: Причина блокировки (если is_safe=False)
        """
        return await self.response_generator.moderate_image_content(image_data)


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
