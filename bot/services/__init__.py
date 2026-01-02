"""
Barrel export для сервисов
Удобный импорт всех сервисов из одного модуля

"""

from bot.services.ai_service_solid import YandexAIService, get_ai_service
from bot.services.analytics_service import AnalyticsService
from bot.services.history_service import ChatHistoryService

# Импорт moderation_service с fallback на оптимизированную версию
try:
    from bot.services._optimized.moderation_service import ContentModerationService
except ImportError:
    # Fallback на оригинальную версию для разработки
    from bot.services.moderation_service import ContentModerationService

from bot.services.simple_engagement import SimpleEngagementService, get_simple_engagement
from bot.services.simple_monitor import SimpleMonitor, get_simple_monitor
from bot.services.subscription_service import SubscriptionService
from bot.services.user_service import UserService

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
