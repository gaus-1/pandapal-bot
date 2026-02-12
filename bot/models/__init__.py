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

# Модель питомца-панды (тамагочи)
from .panda_pet import PandaPet

# Модели платежей
from .payments import Payment, Subscription

# Модели реферальной программы
from .referral import ReferralPayout, Referrer

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
    # Referral
    "Referrer",
    "ReferralPayout",
    # Games
    "GameSession",
    "GameStats",
    # Panda pet (tamagotchi)
    "PandaPet",
]
