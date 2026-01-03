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
    # Fallback на оригинальную версию ТОЛЬКО в development
    # В production обфусцированные файлы ОБЯЗАТЕЛЬНЫ для защиты от копирования
    import os

    # Определяем окружение
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY"))
    environment = os.getenv("ENVIRONMENT", "production" if is_railway else "development")

    # В production БЕЗ обфусцированных файлов - ПАДАЕМ
    # Это защита от копирования репозитория
    if environment == "production" or is_railway:
        raise ImportError(
            "❌ КРИТИЧЕСКАЯ ОШИБКА: Optimized service files are required in production. "
            "Обфусцированные файлы не найдены. Это может означать:\n"
            "1. Проект скопирован без обфусцированных файлов (они в .gitignore)\n"
            "2. Build скрипт не выполнился (проверьте railway_build.sh или nixpacks.toml)\n"
            "3. PyArmor не установлен или не работает\n\n"
            "Для локальной разработки установите ENVIRONMENT=development"
        )

    # В development используем оригинальный файл (fallback)
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
