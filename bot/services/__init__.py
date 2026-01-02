"""
Barrel export для сервисов
Удобный импорт всех сервисов из одного модуля

"""

# Импорт moderation_service с fallback на оптимизированную версию
from bot.services.ai_service_solid import YandexAIService, get_ai_service
from bot.services.analytics_service import AnalyticsService
from bot.services.history_service import ChatHistoryService

_optimized_service_available = False
try:
    from bot.services._optimized.moderation_service import ContentModerationService

    _optimized_service_available = True
except ImportError:
    # Fallback на оригинальную версию только для development
    # В production обфусцированные файлы обязательны (создаются через railway_build.sh)
    import os

    # Проверяем, находимся ли мы в production (Railway)
    # Railway автоматически устанавливает переменную RAILWAY_ENVIRONMENT
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY"))
    env = os.getenv("ENVIRONMENT", "production" if is_railway else "development").lower()

    # В production (Railway) обфусцированные файлы обязательны
    # Они создаются через railway_build.sh перед запуском
    if env == "production" or is_railway:
        raise ImportError(
            "Optimized service files are required in production. "
            "Please ensure railway_build.sh was executed during build. "
            "If running locally, set ENVIRONMENT=development to use original files."
        )

    # Для development используем оригинальный файл
    from bot.services.moderation_service import ContentModerationService  # noqa: E402

from bot.services.simple_engagement import (  # noqa: E402
    SimpleEngagementService,
    get_simple_engagement,
)
from bot.services.simple_monitor import SimpleMonitor, get_simple_monitor  # noqa: E402
from bot.services.subscription_service import SubscriptionService  # noqa: E402
from bot.services.user_service import UserService  # noqa: E402

__all__ = [
    "YandexAIService",
    "get_ai_service",
    "AnalyticsService",
    "ChatHistoryService",
    "ContentModerationService",
    "UserService",
    "SubscriptionService",
    "SimpleMonitor",
    "get_simple_monitor",
    "SimpleEngagementService",
    "get_simple_engagement",
]
