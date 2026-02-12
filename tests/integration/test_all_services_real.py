"""
РЕАЛЬНЫЕ интеграционные тесты для ВСЕХ сервисов проекта
БЕЗ МОКОВ - только реальные операции с БД и сервисами

Тестируем:
- PremiumFeaturesService
- PersonalTutorService
- PrioritySupportService
- BonusLessonsService
- AnalyticsService (расширенные методы)
- GamificationService (premium achievements)
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, Subscription, User
from bot.services import (
    AnalyticsService,
    BonusLessonsService,
    PersonalTutorService,
    PremiumFeaturesService,
    PrioritySupportService,
    SubscriptionService,
    UserService,
)
from bot.services.gamification_service import GamificationService


class TestAllServicesReal:
    """Реальные интеграционные тесты всех сервисов"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Создаёт реальную SQLite БД для каждого теста"""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        yield session

        session.close()
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    @pytest.fixture
    def test_user(self, real_db_session):
        """Создаёт тестового пользователя в БД"""
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=111222333,
            username="test_all_services",
            first_name="Тестовый",
            last_name="Пользователь",
        )
        real_db_session.commit()
        return user

    @pytest.fixture
    def premium_user(self, real_db_session, test_user):
        """Создаёт пользователя с активной Premium подпиской"""
        subscription_service = SubscriptionService(real_db_session)
        subscription_service.activate_subscription(
            telegram_id=111222333,
            plan_id="month",
            transaction_id="test_premium_tx",
            payment_method="stars",
        )
        real_db_session.commit()
        return test_user

    @pytest.fixture
    def vip_user(self, real_db_session, test_user):
        """Создаёт пользователя с Premium подпиской"""
        subscription_service = SubscriptionService(real_db_session)
        subscription_service.activate_subscription(
            telegram_id=111222333,
            plan_id="month",
            transaction_id="test_vip_tx",
            payment_method="stars",
        )
        real_db_session.commit()
        return test_user

    # PremiumFeaturesService

    @pytest.mark.asyncio
    async def test_premium_features_service_free_user(self, real_db_session, test_user):
        """Тест PremiumFeaturesService для бесплатного пользователя"""
        service = PremiumFeaturesService(real_db_session)

        assert not service.is_premium_active(111222333)
        assert not service.has_unlimited_ai(111222333)
        # all_subjects_access: True для всех (лимит в can_make_ai_request)
        assert service.has_all_subjects_access(111222333)
        assert not service.has_personal_tutor(111222333)
        assert not service.has_detailed_analytics(111222333)
        assert not service.has_exclusive_achievements(111222333)
        assert not service.has_priority_support(111222333)
        assert not service.has_bonus_lessons(111222333)
        assert not service.has_vip_status(111222333)

    @pytest.mark.asyncio
    async def test_premium_features_service_premium_user(self, real_db_session, premium_user):
        """Тест PremiumFeaturesService для Premium пользователя"""
        _ = premium_user  # Фикстура используется для настройки БД
        service = PremiumFeaturesService(real_db_session)

        assert service.is_premium_active(111222333)
        assert service.has_unlimited_ai(111222333)
        assert service.has_all_subjects_access(111222333)
        assert service.has_personal_tutor(111222333)
        assert service.has_detailed_analytics(111222333)
        assert service.has_exclusive_achievements(111222333)
        assert service.has_priority_support(111222333)
        # bonus_lessons: любой Premium (plan not None)
        assert service.has_bonus_lessons(111222333)
        assert service.has_vip_status(111222333)

    @pytest.mark.asyncio
    async def test_premium_features_service_vip_user(self, real_db_session, vip_user):
        """Тест PremiumFeaturesService для VIP пользователя"""
        _ = vip_user  # Фикстура используется для настройки БД
        service = PremiumFeaturesService(real_db_session)

        assert service.is_premium_active(111222333)
        assert service.has_bonus_lessons(111222333)  # VIP имеет доступ
        assert service.has_vip_status(111222333)  # VIP статус

    # PersonalTutorService

    @pytest.mark.asyncio
    async def test_personal_tutor_service_free_user(self, real_db_session, test_user):
        """Тест PersonalTutorService для бесплатного пользователя"""
        service = PersonalTutorService(real_db_session)

        with pytest.raises(PermissionError):
            service.get_learning_plan(111222333)  # Не async метод

    @pytest.mark.asyncio
    async def test_personal_tutor_service_premium_user(self, real_db_session, premium_user):
        """Тест PersonalTutorService для Premium пользователя"""
        _ = premium_user  # Фикстура используется для настройки БД
        service = PersonalTutorService(real_db_session)

        plan = await service.get_learning_plan(111222333)
        assert plan is not None
        assert "plan" in plan
        assert isinstance(plan["plan"], str)
        assert len(plan["plan"]) > 0

    # PrioritySupportService

    @pytest.mark.asyncio
    async def test_priority_support_service_free_user(self, real_db_session, test_user):
        """Тест PrioritySupportService для бесплатного пользователя"""
        service = PrioritySupportService(real_db_session)

        priority = service.get_support_priority(111222333)
        assert priority == "Free"

        wait_time = service.estimate_wait_time(111222333)
        assert "24 часов" in wait_time or "24 часа" in wait_time

    @pytest.mark.asyncio
    async def test_priority_support_service_premium_user(self, real_db_session, premium_user):
        """Тест PrioritySupportService для Premium пользователя"""
        _ = premium_user  # Фикстура используется для настройки БД
        service = PrioritySupportService(real_db_session)

        priority = service.get_support_priority(111222333)
        assert priority == "Premium"

        wait_time = service.estimate_wait_time(111222333)
        assert "30 минут" in wait_time or "менее" in wait_time

    @pytest.mark.asyncio
    async def test_priority_support_service_vip_user(self, real_db_session, vip_user):
        """Тест PrioritySupportService для VIP пользователя"""
        _ = vip_user  # Фикстура используется для настройки БД
        service = PrioritySupportService(real_db_session)

        priority = service.get_support_priority(111222333)
        assert priority == "VIP"

        wait_time = service.estimate_wait_time(111222333)
        assert "5 минут" in wait_time or "менее" in wait_time

    # BonusLessonsService

    @pytest.mark.asyncio
    async def test_bonus_lessons_service_free_user(self, real_db_session, test_user):
        """Тест BonusLessonsService для бесплатного пользователя"""
        service = BonusLessonsService(real_db_session)

        with pytest.raises(PermissionError):
            service.get_bonus_lessons(111222333)

    @pytest.mark.asyncio
    async def test_bonus_lessons_service_premium_user(self, real_db_session, premium_user):
        """Тест BonusLessonsService для Premium пользователя (не VIP)"""
        _ = premium_user  # Фикстура используется для настройки БД
        service = BonusLessonsService(real_db_session)

        with pytest.raises(PermissionError):
            service.get_bonus_lessons(111222333)

    @pytest.mark.asyncio
    async def test_bonus_lessons_service_vip_user(self, real_db_session, vip_user):
        """Тест BonusLessonsService для VIP пользователя"""
        _ = vip_user  # Фикстура используется для настройки БД
        service = BonusLessonsService(real_db_session)

        lessons = service.get_bonus_lessons(111222333)
        assert lessons is not None
        assert isinstance(lessons, list)
        assert len(lessons) > 0

        # Проверяем структуру урока
        lesson = lessons[0]
        assert "id" in lesson
        assert "title" in lesson
        assert "content" in lesson
        assert "icon" in lesson

    # AnalyticsService (расширенные методы)

    @pytest.mark.asyncio
    async def test_analytics_service_messages_per_day(self, real_db_session, premium_user):
        """Тест AnalyticsService.get_messages_per_day для Premium"""
        _ = premium_user  # Фикстура используется для настройки БД
        from bot.services.chat_history_service import ChatHistoryService

        # Создаём историю сообщений
        history_service = ChatHistoryService(real_db_session)
        for i in range(5):
            history_service.add_message(
                telegram_id=111222333,
                user_message=f"Вопрос {i}",
                ai_response=f"Ответ {i}",
                subject="математика",
            )
        real_db_session.commit()

        analytics_service = AnalyticsService(real_db_session)
        messages_per_day = analytics_service.get_messages_per_day(111222333, days=30)

        assert messages_per_day is not None
        assert isinstance(messages_per_day, list)
        assert len(messages_per_day) > 0

        # Проверяем структуру
        day_data = messages_per_day[0]
        assert "date" in day_data
        assert "count" in day_data

    @pytest.mark.asyncio
    async def test_analytics_service_most_active_subjects(self, real_db_session, premium_user):
        """Тест AnalyticsService.get_most_active_subjects для Premium"""
        _ = premium_user  # Фикстура используется для настройки БД
        from bot.services.chat_history_service import ChatHistoryService

        # Создаём историю с разными предметами
        history_service = ChatHistoryService(real_db_session)
        subjects = ["математика", "русский", "математика", "физика", "математика"]
        for subject in subjects:
            history_service.add_message(
                telegram_id=111222333,
                user_message="Вопрос",
                ai_response="Ответ",
                subject=subject,
            )
        real_db_session.commit()

        analytics_service = AnalyticsService(real_db_session)
        active_subjects = analytics_service.get_most_active_subjects(111222333, limit=5)

        assert active_subjects is not None
        assert isinstance(active_subjects, list)
        assert len(active_subjects) > 0

        # Математика должна быть на первом месте
        assert active_subjects[0]["subject"] == "математика"
        assert active_subjects[0]["count"] >= 3

    @pytest.mark.asyncio
    async def test_analytics_service_learning_trends(self, real_db_session, premium_user):
        """Тест AnalyticsService.get_learning_trends для Premium"""
        _ = premium_user  # Фикстура используется для настройки БД
        from bot.services.chat_history_service import ChatHistoryService

        # Создаём историю за несколько дней
        history_service = ChatHistoryService(real_db_session)
        for i in range(10):
            history_service.add_message(
                telegram_id=111222333,
                user_message=f"Вопрос {i}",
                ai_response=f"Ответ {i}",
                subject="математика",
            )
        real_db_session.commit()

        analytics_service = AnalyticsService(real_db_session)
        trends = analytics_service.get_learning_trends(111222333, days=90)

        assert trends is not None
        assert isinstance(trends, dict)
        assert "total_messages" in trends
        assert "average_per_day" in trends
        assert "trend" in trends  # "increasing", "decreasing", "stable"

    # GamificationService (premium achievements)

    @pytest.mark.asyncio
    async def test_gamification_service_premium_achievements(self, real_db_session, premium_user):
        """Тест GamificationService для premium achievements"""
        _ = premium_user  # Фикстура используется для настройки БД
        service = GamificationService(real_db_session)

        # Получаем все достижения
        achievements = service.get_user_achievements(111222333)

        # Проверяем что есть premium achievements
        premium_achievements = [a for a in achievements if a.get("is_premium_only", False)]
        assert len(premium_achievements) > 0

        # Проверяем структуру
        for achievement in premium_achievements:
            assert "id" in achievement
            assert "name" in achievement
            assert "is_premium_only" in achievement
            assert achievement["is_premium_only"] is True
