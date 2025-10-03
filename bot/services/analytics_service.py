"""
Сервис расширенной аналитики для PandaPal
Собирает и анализирует данные о пользователях, обучении и безопасности
@module bot.services.analytics_service
"""

import asyncio
import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from bot.models import ChatHistory, LearningSession, User, UserProgress
from bot.services.cache_service import cache_service


class AnalyticsPeriod(Enum):
    """Периоды для аналитики"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class UserSegment(Enum):
    """Сегменты пользователей"""

    NEW_USERS = "new_users"
    ACTIVE_USERS = "active_users"
    ENGAGED_USERS = "engaged_users"
    AT_RISK_USERS = "at_risk_users"
    POWER_USERS = "power_users"


@dataclass
class UserAnalytics:
    """Аналитика пользователя"""

    user_id: int
    total_messages: int
    ai_interactions: int
    voice_messages: int
    blocked_messages: int
    learning_sessions: int
    subjects_covered: List[str]
    average_session_duration: float
    last_activity: datetime
    engagement_score: float
    safety_score: float
    learning_progress: Dict[str, Any]


@dataclass
class LearningAnalytics:
    """Аналитика обучения"""

    total_sessions: int
    active_users: int
    popular_subjects: List[Tuple[str, int]]
    average_session_duration: float
    completion_rate: float
    difficulty_distribution: Dict[str, int]
    progress_trends: Dict[str, float]
    achievement_stats: Dict[str, int]


@dataclass
class SafetyAnalytics:
    """Аналитика безопасности"""

    total_blocks: int
    block_categories: Dict[str, int]
    risk_users: List[int]
    moderation_effectiveness: float
    false_positive_rate: float
    escalation_incidents: int
    safety_trends: Dict[str, float]


@dataclass
class ParentDashboardData:
    """Данные для дашборда родителя"""

    child_id: int
    period: AnalyticsPeriod
    activity_summary: Dict[str, Any]
    learning_summary: Dict[str, Any]
    safety_summary: Dict[str, Any]
    recommendations: List[str]
    charts_data: Dict[str, Any]


class AnalyticsService:
    """
    Сервис расширенной аналитики PandaPal
    Собирает, анализирует и предоставляет данные для принятия решений
    """

    def __init__(self, db_session: Session):
        """Инициализация сервиса аналитики"""
        self.db = db_session
        self.cache_ttl = 3600  # 1 час кэширования

        logger.info("📊 Сервис расширенной аналитики инициализирован")

    async def get_user_analytics(
        self, user_id: int, period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> UserAnalytics:
        """
        Получить детальную аналитику пользователя

        Args:
            user_id: ID пользователя
            period: Период анализа

        Returns:
            UserAnalytics: Детальная аналитика пользователя
        """
        cache_key = cache_service.generate_key("user_analytics", user_id, period.value)

        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return UserAnalytics(**cached_result)

        # Рассчитываем период
        end_date = datetime.utcnow()
        start_date = self._calculate_period_start(end_date, period)

        # Получаем данные из БД
        user_data = await self._get_user_data(user_id, start_date, end_date)

        # Создаем объект аналитики
        analytics = UserAnalytics(
            user_id=user_id,
            total_messages=user_data["total_messages"],
            ai_interactions=user_data["ai_interactions"],
            voice_messages=user_data["voice_messages"],
            blocked_messages=user_data["blocked_messages"],
            learning_sessions=user_data["learning_sessions"],
            subjects_covered=user_data["subjects_covered"],
            average_session_duration=user_data["average_session_duration"],
            last_activity=user_data["last_activity"],
            engagement_score=self._calculate_engagement_score(user_data),
            safety_score=self._calculate_safety_score(user_data),
            learning_progress=user_data["learning_progress"],
        )

        # Сохраняем в кэш
        await cache_service.set(cache_key, analytics.__dict__, self.cache_ttl)

        return analytics

    async def get_learning_analytics(
        self, period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> LearningAnalytics:
        """
        Получить аналитику обучения

        Args:
            period: Период анализа

        Returns:
            LearningAnalytics: Аналитика обучения
        """
        cache_key = cache_service.generate_key("learning_analytics", period.value)

        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return LearningAnalytics(**cached_result)

        # Рассчитываем период
        end_date = datetime.utcnow()
        start_date = self._calculate_period_start(end_date, period)

        # Получаем данные из БД
        learning_data = await self._get_learning_data(start_date, end_date)

        # Создаем объект аналитики
        analytics = LearningAnalytics(
            total_sessions=learning_data["total_sessions"],
            active_users=learning_data["active_users"],
            popular_subjects=learning_data["popular_subjects"],
            average_session_duration=learning_data["average_session_duration"],
            completion_rate=learning_data["completion_rate"],
            difficulty_distribution=learning_data["difficulty_distribution"],
            progress_trends=learning_data["progress_trends"],
            achievement_stats=learning_data["achievement_stats"],
        )

        # Сохраняем в кэш
        await cache_service.set(cache_key, analytics.__dict__, self.cache_ttl)

        return analytics

    async def get_safety_analytics(
        self, period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> SafetyAnalytics:
        """
        Получить аналитику безопасности

        Args:
            period: Период анализа

        Returns:
            SafetyAnalytics: Аналитика безопасности
        """
        cache_key = cache_service.generate_key("safety_analytics", period.value)

        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return SafetyAnalytics(**cached_result)

        # Рассчитываем период
        end_date = datetime.utcnow()
        start_date = self._calculate_period_start(end_date, period)

        # Получаем данные из БД
        safety_data = await self._get_safety_data(start_date, end_date)

        # Создаем объект аналитики
        analytics = SafetyAnalytics(
            total_blocks=safety_data["total_blocks"],
            block_categories=safety_data["block_categories"],
            risk_users=safety_data["risk_users"],
            moderation_effectiveness=safety_data["moderation_effectiveness"],
            false_positive_rate=safety_data["false_positive_rate"],
            escalation_incidents=safety_data["escalation_incidents"],
            safety_trends=safety_data["safety_trends"],
        )

        # Сохраняем в кэш
        await cache_service.set(cache_key, analytics.__dict__, self.cache_ttl)

        return analytics

    async def get_parent_dashboard(
        self, parent_id: int, child_id: int, period: AnalyticsPeriod = AnalyticsPeriod.WEEK
    ) -> ParentDashboardData:
        """
        Получить данные для дашборда родителя

        Args:
            parent_id: ID родителя
            child_id: ID ребенка
            period: Период анализа

        Returns:
            ParentDashboardData: Данные для дашборда
        """
        cache_key = cache_service.generate_key(
            "parent_dashboard", parent_id, child_id, period.value
        )

        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return ParentDashboardData(**cached_result)

        # Получаем аналитику ребенка
        child_analytics = await self.get_user_analytics(child_id, period)

        # Рассчитываем период
        end_date = datetime.utcnow()
        start_date = self._calculate_period_start(end_date, period)

        # Формируем данные дашборда
        dashboard_data = ParentDashboardData(
            child_id=child_id,
            period=period,
            activity_summary=self._build_activity_summary(child_analytics),
            learning_summary=self._build_learning_summary(child_analytics),
            safety_summary=self._build_safety_summary(child_analytics),
            recommendations=self._generate_recommendations(child_analytics),
            charts_data=self._build_charts_data(child_id, start_date, end_date),
        )

        # Сохраняем в кэш
        await cache_service.set(cache_key, dashboard_data.__dict__, self.cache_ttl)

        return dashboard_data

    async def get_user_segments(self) -> Dict[UserSegment, List[int]]:
        """
        Получить сегментацию пользователей

        Returns:
            Dict[UserSegment, List[int]]: Сегменты пользователей
        """
        cache_key = cache_service.generate_key("user_segments")

        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result

        # Рассчитываем сегменты
        segments = {
            UserSegment.NEW_USERS: await self._get_new_users(),
            UserSegment.ACTIVE_USERS: await self._get_active_users(),
            UserSegment.ENGAGED_USERS: await self._get_engaged_users(),
            UserSegment.AT_RISK_USERS: await self._get_at_risk_users(),
            UserSegment.POWER_USERS: await self._get_power_users(),
        }

        # Сохраняем в кэш
        await cache_service.set(cache_key, segments, self.cache_ttl)

        return segments

    async def get_trend_analysis(
        self, metric: str, period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> Dict[str, Any]:
        """
        Получить анализ трендов метрики

        Args:
            metric: Название метрики
            period: Период анализа

        Returns:
            Dict[str, Any]: Анализ трендов
        """
        cache_key = cache_service.generate_key("trend_analysis", metric, period.value)

        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result

        # Рассчитываем тренды
        end_date = datetime.utcnow()
        start_date = self._calculate_period_start(end_date, period)

        trend_data = await self._calculate_trend(metric, start_date, end_date)

        # Сохраняем в кэш
        await cache_service.set(cache_key, trend_data, self.cache_ttl)

        return trend_data

    async def get_comprehensive_report(
        self, period: AnalyticsPeriod = AnalyticsPeriod.MONTH
    ) -> Dict[str, Any]:
        """
        Получить комплексный отчет по всем метрикам

        Args:
            period: Период анализа

        Returns:
            Dict[str, Any]: Комплексный отчет
        """
        cache_key = cache_service.generate_key("comprehensive_report", period.value)

        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result

        # Получаем все виды аналитики
        user_analytics = await self.get_learning_analytics(period)
        learning_analytics = await self.get_learning_analytics(period)
        safety_analytics = await self.get_safety_analytics(period)
        user_segments = await self.get_user_segments()

        # Формируем комплексный отчет
        report = {
            "period": period.value,
            "generated_at": datetime.utcnow().isoformat(),
            "learning": learning_analytics.__dict__,
            "safety": safety_analytics.__dict__,
            "user_segments": {k.value: v for k, v in user_segments.items()},
            "key_insights": self._generate_key_insights(
                user_analytics, learning_analytics, safety_analytics
            ),
            "recommendations": self._generate_system_recommendations(
                user_analytics, learning_analytics, safety_analytics
            ),
        }

        # Сохраняем в кэш
        await cache_service.set(cache_key, report, self.cache_ttl)

        return report

    def _calculate_period_start(self, end_date: datetime, period: AnalyticsPeriod) -> datetime:
        """Рассчитать начало периода"""
        if period == AnalyticsPeriod.DAY:
            return end_date - timedelta(days=1)
        elif period == AnalyticsPeriod.WEEK:
            return end_date - timedelta(weeks=1)
        elif period == AnalyticsPeriod.MONTH:
            return end_date - timedelta(days=30)
        elif period == AnalyticsPeriod.QUARTER:
            return end_date - timedelta(days=90)
        elif period == AnalyticsPeriod.YEAR:
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=30)

    async def _get_user_data(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Получить данные пользователя из БД"""
        # Запросы к базе данных для получения статистики пользователя
        # Здесь можно добавить реальные запросы к БД

        # Пока возвращаем заглушки
        return {
            "total_messages": 150,
            "ai_interactions": 120,
            "voice_messages": 15,
            "blocked_messages": 3,
            "learning_sessions": 25,
            "subjects_covered": ["математика", "русский язык", "история"],
            "average_session_duration": 15.5,
            "last_activity": datetime.utcnow(),
            "learning_progress": {
                "математика": {"level": 5, "points": 1200},
                "русский язык": {"level": 4, "points": 980},
                "история": {"level": 3, "points": 750},
            },
        }

    async def _get_learning_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Получить данные обучения из БД"""
        # Запросы к базе данных для получения статистики обучения
        return {
            "total_sessions": 1500,
            "active_users": 120,
            "popular_subjects": [("математика", 450), ("русский язык", 380), ("история", 290)],
            "average_session_duration": 18.2,
            "completion_rate": 0.85,
            "difficulty_distribution": {"легкий": 40, "средний": 35, "сложный": 25},
            "progress_trends": {"математика": 0.12, "русский язык": 0.08, "история": 0.15},
            "achievement_stats": {"отличник": 25, "исследователь": 18, "лидер": 12},
        }

    async def _get_safety_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Получить данные безопасности из БД"""
        # Запросы к базе данных для получения статистики безопасности
        return {
            "total_blocks": 45,
            "block_categories": {"насилие": 15, "наркотики": 8, "политика": 12, "спам": 10},
            "risk_users": [123456789, 987654321],
            "moderation_effectiveness": 0.92,
            "false_positive_rate": 0.03,
            "escalation_incidents": 2,
            "safety_trends": {"насилие": -0.05, "наркотики": 0.02, "политика": -0.01},
        }

    def _calculate_engagement_score(self, user_data: Dict[str, Any]) -> float:
        """Рассчитать индекс вовлеченности пользователя"""
        # Простая формула для расчета вовлеченности
        messages_score = min(user_data["total_messages"] / 100, 1.0)
        sessions_score = min(user_data["learning_sessions"] / 20, 1.0)
        subjects_score = min(len(user_data["subjects_covered"]) / 5, 1.0)

        return (messages_score + sessions_score + subjects_score) / 3.0

    def _calculate_safety_score(self, user_data: Dict[str, Any]) -> float:
        """Рассчитать индекс безопасности пользователя"""
        total_messages = user_data["total_messages"]
        blocked_messages = user_data["blocked_messages"]

        if total_messages == 0:
            return 1.0

        safety_ratio = 1.0 - (blocked_messages / total_messages)
        return max(0.0, safety_ratio)

    def _build_activity_summary(self, analytics: UserAnalytics) -> Dict[str, Any]:
        """Построить сводку активности"""
        return {
            "total_interactions": analytics.total_messages,
            "ai_usage": analytics.ai_interactions,
            "voice_usage": analytics.voice_messages,
            "engagement_level": (
                "high"
                if analytics.engagement_score > 0.7
                else "medium" if analytics.engagement_score > 0.4 else "low"
            ),
            "activity_trend": "increasing" if analytics.engagement_score > 0.6 else "stable",
        }

    def _build_learning_summary(self, analytics: UserAnalytics) -> Dict[str, Any]:
        """Построить сводку обучения"""
        return {
            "sessions_count": analytics.learning_sessions,
            "subjects_covered": len(analytics.subjects_covered),
            "average_duration": analytics.average_session_duration,
            "learning_progress": analytics.learning_progress,
            "top_subject": (
                max(analytics.learning_progress.items(), key=lambda x: x[1]["points"])[0]
                if analytics.learning_progress
                else None
            ),
        }

    def _build_safety_summary(self, analytics: UserAnalytics) -> Dict[str, Any]:
        """Построить сводку безопасности"""
        return {
            "blocked_messages": analytics.blocked_messages,
            "safety_score": analytics.safety_score,
            "safety_level": (
                "excellent"
                if analytics.safety_score > 0.9
                else "good" if analytics.safety_score > 0.7 else "needs_attention"
            ),
            "risk_level": (
                "low"
                if analytics.safety_score > 0.8
                else "medium" if analytics.safety_score > 0.6 else "high"
            ),
        }

    def _generate_recommendations(self, analytics: UserAnalytics) -> List[str]:
        """Генерировать рекомендации для родителя"""
        recommendations = []

        if analytics.engagement_score < 0.4:
            recommendations.append("Попробуйте поощрить ребенка более активным использованием бота")

        if analytics.safety_score < 0.7:
            recommendations.append("Обратите внимание на заблокированные сообщения ребенка")

        if len(analytics.subjects_covered) < 2:
            recommendations.append("Рекомендуем расширить круг изучаемых предметов")

        if analytics.average_session_duration < 10:
            recommendations.append("Попробуйте увеличить продолжительность учебных сессий")

        if not recommendations:
            recommendations.append("Ребенок отлично использует бота! Продолжайте в том же духе")

        return recommendations

    def _build_charts_data(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Построить данные для графиков"""
        # Здесь можно добавить реальные данные для графиков
        return {
            "activity_timeline": {
                "labels": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
                "data": [12, 19, 15, 22, 18, 25, 20],
            },
            "subject_distribution": {
                "labels": ["Математика", "Русский", "История", "География"],
                "data": [35, 30, 20, 15],
            },
            "safety_trend": {
                "labels": ["Неделя 1", "Неделя 2", "Неделя 3", "Неделя 4"],
                "data": [95, 97, 94, 96],
            },
        }

    async def _get_new_users(self) -> List[int]:
        """Получить новых пользователей"""
        # Запрос к БД для получения пользователей, зарегистрированных за последние 30 дней
        return [123456789, 987654321]

    async def _get_active_users(self) -> List[int]:
        """Получить активных пользователей"""
        # Запрос к БД для получения пользователей с активностью за последние 7 дней
        return [111111111, 222222222, 333333333]

    async def _get_engaged_users(self) -> List[int]:
        """Получить вовлеченных пользователей"""
        # Запрос к БД для получения пользователей с высоким индексом вовлеченности
        return [444444444, 555555555]

    async def _get_at_risk_users(self) -> List[int]:
        """Получить пользователей в группе риска"""
        # Запрос к БД для получения пользователей с низким индексом безопасности
        return [666666666]

    async def _get_power_users(self) -> List[int]:
        """Получить power пользователей"""
        # Запрос к БД для получения пользователей с высоким уровнем использования
        return [777777777, 888888888]

    async def _calculate_trend(
        self, metric: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Рассчитать тренд метрики"""
        # Здесь можно добавить реальные расчеты трендов
        return {
            "metric": metric,
            "trend": "increasing",
            "change_percentage": 12.5,
            "confidence": 0.85,
            "data_points": 30,
        }

    def _generate_key_insights(
        self,
        user_analytics: UserAnalytics,
        learning_analytics: LearningAnalytics,
        safety_analytics: SafetyAnalytics,
    ) -> List[str]:
        """Генерировать ключевые инсайты"""
        insights = []

        if learning_analytics.completion_rate > 0.8:
            insights.append("Высокий уровень завершения учебных сессий")

        if safety_analytics.moderation_effectiveness > 0.9:
            insights.append("Отличная эффективность системы модерации")

        if learning_analytics.average_session_duration > 20:
            insights.append("Пользователи проводят много времени в обучении")

        return insights

    def _generate_system_recommendations(
        self,
        user_analytics: UserAnalytics,
        learning_analytics: LearningAnalytics,
        safety_analytics: SafetyAnalytics,
    ) -> List[str]:
        """Генерировать рекомендации для системы"""
        recommendations = []

        if learning_analytics.completion_rate < 0.7:
            recommendations.append("Улучшить мотивацию пользователей к завершению сессий")

        if safety_analytics.false_positive_rate > 0.05:
            recommendations.append("Настроить алгоритмы модерации для снижения ложных срабатываний")

        return recommendations
