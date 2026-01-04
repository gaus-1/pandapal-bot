"""
Barrel export для сервисов
Удобный импорт всех сервисов из одного модуля

"""

# Импорт moderation_service из оригинального файла
from bot.services.ai_service_solid import YandexAIService, get_ai_service
from bot.services.analytics_service import AnalyticsService
from bot.services.bonus_lessons_service import BonusLessonsService  # noqa: E402
from bot.services.history_service import ChatHistoryService
from bot.services.moderation_service import ContentModerationService  # noqa: E402
from bot.services.payment_service import PaymentService  # noqa: E402
from bot.services.personal_tutor_service import PersonalTutorService  # noqa: E402
from bot.services.premium_features_service import PremiumFeaturesService  # noqa: E402
from bot.services.priority_support_service import PrioritySupportService  # noqa: E402
from bot.services.session_service import SessionService, get_session_service  # noqa: E402
from bot.services.simple_engagement import (  # noqa: E402
    SimpleEngagementService,
    get_simple_engagement,
)
from bot.services.simple_monitor import SimpleMonitor, get_simple_monitor  # noqa: E402
from bot.services.subscription_service import SubscriptionService  # noqa: E402
from bot.services.telegram_auth_service import TelegramAuthService  # noqa: E402
from bot.services.user_service import UserService  # noqa: E402

__all__ = [
    "YandexAIService",
    "get_ai_service",
    "AnalyticsService",
    "ChatHistoryService",
    "ContentModerationService",
    "UserService",
    "SubscriptionService",
    "PaymentService",
    "TelegramAuthService",
    "SessionService",
    "get_session_service",
    "PremiumFeaturesService",
    "PersonalTutorService",
    "PrioritySupportService",
    "BonusLessonsService",
    "SimpleMonitor",
    "get_simple_monitor",
    "SimpleEngagementService",
    "get_simple_engagement",
]
