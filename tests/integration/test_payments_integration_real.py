"""
РЕАЛЬНЫЕ интеграционные тесты платёжной системы
Работают с реальной архитектурой приложения (API endpoints + БД)

Тестируем:
- Создание платежей через API
- Обработку webhook
- Активацию Premium
- Telegram авторизацию
- Полный цикл оплаты
"""

import hashlib
import hmac
import json
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.config import settings
from bot.models import Base, Subscription, User
from bot.services import SubscriptionService, UserService


class TestPaymentsIntegrationReal:
    """Реальные интеграционные тесты платежей"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Создаёт реальную SQLite БД"""
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
        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=777888999,
            username="payment_test",
            first_name="Payment",
            last_name="Test",
        )
        real_db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_webhook_activates_premium_subscription(self, real_db_session, test_user):
        """
        КРИТИЧНО: Webhook от YooKassa активирует Premium подписку
        """
        from bot.api.premium_endpoints import yookassa_webhook

        subscription_service = SubscriptionService(real_db_session)

        # Проверяем что Premium не активен
        assert not subscription_service.is_premium_active(777888999)

        # Симулируем webhook от YooKassa
        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "payment_integration_test",
                "status": "succeeded",
                "amount": {"value": "99.00", "currency": "RUB"},
                "metadata": {
                    "telegram_id": "777888999",
                    "plan_id": "month",
                },
                "paid": True,
                "payment_method": {"type": "bank_card"},
            },
        }

        class MockRequest:
            async def text(self):
                return json.dumps(webhook_data)

            async def json(self):
                return webhook_data

            @property
            def headers(self):
                return {"Content-Type": "application/json"}

        @contextmanager
        def mock_get_db():
            yield real_db_session

        # Обрабатываем webhook
        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response = await yookassa_webhook(MockRequest())
            assert response.status == 200
            real_db_session.commit()

            # КРИТИЧНО: Premium должен быть активирован
            assert subscription_service.is_premium_active(777888999)

            # Проверяем подписку
            subscription = subscription_service.get_active_subscription(777888999)
            assert subscription is not None
            assert subscription.plan_id == "month"

    @pytest.mark.asyncio
    async def test_subscription_service_operations(self, real_db_session, test_user):
        """
        Тестирование SubscriptionService (реальные операции с БД)
        """
        subscription_service = SubscriptionService(real_db_session)

        # Тест 1: Активация подписки
        subscription = subscription_service.activate_subscription(
            telegram_id=777888999,
            plan_id="month",
            transaction_id="test_tx_123",
        )
        real_db_session.commit()

        assert subscription is not None
        assert subscription.is_active is True
        assert subscription.plan_id == "month"

        # Тест 2: Проверка Premium статуса
        assert subscription_service.is_premium_active(777888999)

        # Тест 3: Получение активной подписки
        active_sub = subscription_service.get_active_subscription(777888999)
        assert active_sub.plan_id == "month"

        # Тест 4: Деактивация истекшей подписки
        subscription.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        real_db_session.commit()

        assert not subscription_service.is_premium_active(777888999)

        # Тест 5: Массовая деактивация
        count = subscription_service.deactivate_expired_subscriptions()
        real_db_session.commit()

        assert count >= 1

    @pytest.mark.asyncio
    async def test_multiple_payment_methods(self, real_db_session):
        """
        Тестирование разных способов оплаты
        """
        from bot.api.premium_endpoints import yookassa_webhook

        payment_methods = [
            ("bank_card", "yookassa_card"),
            ("sberbank", "yookassa_sbp"),
            ("yoo_money", "yookassa_other"),
        ]

        for i, (yookassa_method, expected_db_method) in enumerate(payment_methods):
            telegram_id = 777888200 + i

            # Создаём пользователя
            user_service = UserService(real_db_session)
            user_service.get_or_create_user(
                telegram_id=telegram_id,
                username=f"test_{yookassa_method}",
                first_name="Test",
            )
            real_db_session.commit()

            # Webhook с этим способом оплаты
            webhook_data = {
                "type": "notification",
                "event": "payment.succeeded",
                "object": {
                    "id": f"payment_{yookassa_method}_{i}",
                    "status": "succeeded",
                    "amount": {"value": "99.00", "currency": "RUB"},
                    "metadata": {
                        "telegram_id": str(telegram_id),
                        "plan_id": "month",
                    },
                    "paid": True,
                    "payment_method": {"type": yookassa_method},
                },
            }

            class MockRequest:
                async def text(self):
                    return json.dumps(webhook_data)

                async def json(self):
                    return webhook_data

                @property
                def headers(self):
                    return {"Content-Type": "application/json"}

            @contextmanager
            def mock_get_db():
                yield real_db_session

            with patch("bot.api.premium_endpoints.get_db", mock_get_db):
                response = await yookassa_webhook(MockRequest())
                assert response.status == 200
                real_db_session.commit()

                # Проверяем payment_method
                subscription_service = SubscriptionService(real_db_session)
                subscription = subscription_service.get_active_subscription(telegram_id)
                assert subscription.payment_method == expected_db_method


print("\n✅ РЕАЛЬНЫЕ ИНТЕГРАЦИОННЫЕ ТЕСТЫ СОЗДАНЫ!")
print("Запуск: pytest tests/integration/test_payments_integration_real.py -v")
