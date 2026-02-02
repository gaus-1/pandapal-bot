"""
Модели базы данных для PandaPal Bot.

Этот модуль реэкспортирует все модели из подмодулей для обратной совместимости.
Все импорты вида `from bot.models import User` продолжат работать.
"""

# Базовый класс
# Модели аналитики
from .analytics import AnalyticsMetric
from .base import Base

# Модели чата
from .chat import ChatHistory, DailyRequestCount

# Модели игр
from .games import GameSession, GameStats

# Модели обучения
from .learning import HomeworkSubmission, LearningSession, ProblemTopic

# Модели новостей
from .news import News

# Модели платежей
from .payments import Payment, Subscription

# Модели пользователей
from .user import User, UserProgress

# Экспорт всех моделей
__all__ = [
    # Base
    "Base",
    # User
    "User",
    "UserProgress",
    # Chat
    "ChatHistory",
    "DailyRequestCount",
    # Learning
    "LearningSession",
    "ProblemTopic",
    "HomeworkSubmission",
    # Analytics
    "AnalyticsMetric",
    # Payments
    "Subscription",
    "Payment",
    # Games
    "GameSession",
    "GameStats",
    # News
    "News",
]
