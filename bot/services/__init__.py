"""
Barrel export для сервисов
Удобный импорт всех сервисов из одного модуля

"""

# Импорт moderation_service с fallback на оптимизированную версию
import os
from pathlib import Path

from bot.services.ai_service_solid import YandexAIService, get_ai_service
from bot.services.analytics_service import AnalyticsService
from bot.services.history_service import ChatHistoryService

_optimized_service_available = False
try:
    from bot.services._optimized.moderation_service import ContentModerationService

    _optimized_service_available = True
except ImportError:
    # Fallback на оригинальную версию только для локальной разработки
    # В продакшене оптимизированные файлы обязательны
    env = os.getenv("ENVIRONMENT", os.getenv("environment", "development")).lower()
    optimized_dir = Path(__file__).parent / "_optimized"
    runtime_dir = optimized_dir / "_runtime"

    # В продакшене обфусцированные файлы обязательны
    # Также проверяем: если директория существует, но нет runtime - значит неполная копия
    if env == "production" or (optimized_dir.exists() and not runtime_dir.exists()):
        raise ImportError(
            "Optimized service files are required. "
            "Please ensure bot/services/_optimized/ directory exists with required files and _runtime/ subdirectory."
        )

    # Для разработки используем оригинальные файлы
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
