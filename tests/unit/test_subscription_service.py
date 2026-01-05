"""
Unit тесты для bot/services/subscription_service.py
"""

import os
import tempfile
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, Subscription, User
from bot.services.subscription_service import SubscriptionService


class TestSubscriptionService:
    """Тесты для SubscriptionService"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Реальная БД для тестов"""
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
        """Создаёт тестового пользователя"""
        user = User(telegram_id=123456, username="test", first_name="Test")
        real_db_session.add(user)
        real_db_session.commit()
        return user

    def test_activate_subscription(self, real_db_session, test_user):
        """Тест активации подписки"""
        service = SubscriptionService(real_db_session)

        subscription = service.activate_subscription(
            telegram_id=123456,
            plan_id="month",
            transaction_id="test_tx_123",
            invoice_payload="premium_month_123456",
        )

        real_db_session.commit()

        assert subscription is not None
        assert subscription.user_telegram_id == 123456
        assert subscription.plan_id == "month"
        assert subscription.is_active is True

    def test_get_active_subscription(self, real_db_session, test_user):
        """Тест получения активной подписки"""
        service = SubscriptionService(real_db_session)

        # Активируем подписку
        service.activate_subscription(
            telegram_id=123456,
            plan_id="month",
            transaction_id="test_tx_123",
            invoice_payload="premium_month_123456",
        )
        real_db_session.commit()

        # Получаем активную подписку
        subscription = service.get_active_subscription(123456)
        assert subscription is not None
        assert subscription.is_active is True

    def test_get_active_subscription_not_found(self, real_db_session, test_user):
        """Тест получения несуществующей подписки"""
        service = SubscriptionService(real_db_session)

        subscription = service.get_active_subscription(123456)
        assert subscription is None

    def test_deactivate_expired_subscriptions(self, real_db_session, test_user):
        """Тест деактивации истекших подписок"""
        service = SubscriptionService(real_db_session)

        # Создаём истекшую подписку
        expired_subscription = Subscription(
            user_telegram_id=123456,
            plan_id="month",
            transaction_id="test_tx_expired",
            invoice_payload="premium_month_123456",
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        real_db_session.add(expired_subscription)
        real_db_session.commit()

        # Деактивируем истекшие
        deactivated = service.deactivate_expired_subscriptions()
        real_db_session.commit()

        assert deactivated >= 1

        # Проверяем что подписка деактивирована
        subscription = service.get_active_subscription(123456)
        assert subscription is None or subscription.is_active is False
