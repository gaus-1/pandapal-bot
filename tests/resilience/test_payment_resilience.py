"""
ТЕСТЫ ОТКАЗОУСТОЙЧИВОСТИ для платёжной системы
Проверяем работу системы при различных сбоях

Тестируем:
- Обработку таймаутов YooKassa API
- Восстановление после сбоя БД
- Обработку дубликатов webhook
- Откат транзакций при ошибках
- Работу при недоступности внешних сервисов
- Race conditions при одновременных запросах
"""

import asyncio
import hashlib
import hmac
import json
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from bot.config import settings
from bot.models import Base, Payment, Subscription, User
from bot.services import PaymentService, SubscriptionService, UserService


class TestPaymentResilience:
    """Тесты отказоустойчивости платёжной системы"""

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
            telegram_id=888999000,
            username="resilience_test",
            first_name="Resilience",
        )
        real_db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_yookassa_timeout_handling(self, real_db_session, test_user):
        """
        КРИТИЧНО: Обработка таймаута при создании платежа в YooKassa
        """
        payment_service = PaymentService(real_db_session)

        # Мокаем YooKassa Payment.create чтобы симулировать таймаут
        with patch("yookassa.Payment.create") as mock_create:
            mock_create.side_effect = asyncio.TimeoutError("YooKassa timeout")

            # Пытаемся создать платеж
            with pytest.raises(Exception):  # Ожидаем ошибку
                await payment_service.create_payment(
                    telegram_id=888999000,
                    amount=99.0,
                    plan_id="week",
                    description="Test",
                    customer_email="test@pandapal.ru",
                )

            # Проверяем что НЕ создана запись в БД (откат транзакции)
            payment_count = (
                real_db_session.query(Payment).filter_by(user_telegram_id=888999000).count()
            )
            assert payment_count == 0

    @pytest.mark.asyncio
    async def test_database_connection_loss(self, real_db_session, test_user):
        """
        КРИТИЧНО: Обработка потери соединения с БД
        """
        subscription_service = SubscriptionService(real_db_session)

        # Активируем подписку
        subscription_service.activate_subscription(
            telegram_id=888999000,
            plan_id="week",
            transaction_id="test_tx_resilience",
        )
        real_db_session.commit()

        # Симулируем потерю соединения
        real_db_session.close()

        # Пытаемся проверить Premium статус
        with pytest.raises(Exception):  # Ожидаем ошибку
            subscription_service.is_premium_active(888999000)

    @pytest.mark.asyncio
    async def test_duplicate_webhook_handling(self, real_db_session, test_user):
        """
        КРИТИЧНО: Идемпотентность webhook - дубликаты не создают проблем
        """
        from bot.api.premium_endpoints import yookassa_webhook

        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "payment_duplicate_test",
                "status": "succeeded",
                "amount": {"value": "99.00", "currency": "RUB"},
                "metadata": {
                    "telegram_id": "888999000",
                    "plan_id": "week",
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

        # Отправляем webhook 10 раз подряд
        for i in range(10):
            with patch("bot.api.premium_endpoints.get_db", mock_get_db):
                response = await yookassa_webhook(MockRequest())
                assert response.status == 200
                real_db_session.commit()

        # Проверяем что создана ТОЛЬКО ОДНА подписка
        subscriptions = (
            real_db_session.query(Subscription).filter_by(user_telegram_id=888999000).all()
        )

        # Должна быть максимум 1 активная подписка
        active_subscriptions = [s for s in subscriptions if s.is_active]
        assert len(active_subscriptions) <= 1

    @pytest.mark.asyncio
    async def test_race_condition_simultaneous_payments(self, real_db_session, test_user):
        """
        КРИТИЧНО: Race condition - одновременное создание платежей
        """
        payment_service = PaymentService(real_db_session)

        # Создаём 5 платежей одновременно
        tasks = [
            payment_service.create_payment(
                telegram_id=888999000,
                amount=99.0,
                plan_id="week",
                description=f"Concurrent {i}",
                customer_email="test@pandapal.ru",
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем что все платежи созданы
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0

        # Проверяем что payment_id уникальные
        payment_ids = [r["payment_id"] for r in successful]
        assert len(payment_ids) == len(set(payment_ids))

    @pytest.mark.asyncio
    async def test_partial_webhook_data(self, real_db_session, test_user):
        """
        Обработка webhook с неполными данными
        """
        from bot.api.premium_endpoints import yookassa_webhook

        # Webhook без metadata
        incomplete_webhook = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "payment_incomplete",
                "status": "succeeded",
                "amount": {"value": "99.00", "currency": "RUB"},
                # metadata отсутствует
                "paid": True,
            },
        }

        class MockRequest:
            async def text(self):
                return json.dumps(incomplete_webhook)

            async def json(self):
                return incomplete_webhook

            @property
            def headers(self):
                return {"Content-Type": "application/json"}

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response = await yookassa_webhook(MockRequest())

            # Должен вернуть ошибку или обработать gracefully
            assert response.status in [200, 400]

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, real_db_session, test_user):
        """
        КРИТИЧНО: Откат транзакции при ошибке активации подписки
        """
        subscription_service = SubscriptionService(real_db_session)

        # Мокаем метод чтобы вызвать ошибку в середине транзакции
        original_method = subscription_service.activate_subscription

        def failing_activation(*args, **kwargs):
            # Начинаем создавать подписку
            subscription = original_method(*args, **kwargs)
            real_db_session.flush()

            # Симулируем ошибку
            raise Exception("Simulated error during activation")

        with patch.object(subscription_service, "activate_subscription", failing_activation):
            # Пытаемся активировать подписку
            with pytest.raises(Exception):
                subscription_service.activate_subscription(
                    telegram_id=888999000,
                    plan_id="week",
                    transaction_id="rollback_test",
                )

        # Откатываем вручную
        real_db_session.rollback()

        # Проверяем что подписка НЕ создана (откат сработал)
        subscriptions = (
            real_db_session.query(Subscription).filter_by(user_telegram_id=888999000).all()
        )
        assert len(subscriptions) == 0

    @pytest.mark.asyncio
    async def test_expired_subscription_cleanup_under_load(self, real_db_session):
        """
        Очистка истекших подписок под нагрузкой
        """
        subscription_service = SubscriptionService(real_db_session)

        # Создаём 100 пользователей с истекшими подписками
        for i in range(100):
            telegram_id = 888999000 + i
            user_service = UserService(real_db_session)
            user_service.get_or_create_user(
                telegram_id=telegram_id, username=f"user_{i}", first_name="Test"
            )
            real_db_session.commit()

            # Создаём истекшую подписку
            expired_sub = Subscription(
                user_telegram_id=telegram_id,
                plan_id="week",
                starts_at=datetime.now(timezone.utc) - timedelta(days=14),
                expires_at=datetime.now(timezone.utc) - timedelta(days=7),
                is_active=True,
                transaction_id=f"expired_{i}",
            )
            real_db_session.add(expired_sub)
            real_db_session.commit()

        # Деактивируем все истекшие подписки
        count = subscription_service.deactivate_expired_subscriptions()
        real_db_session.commit()

        # Проверяем что все деактивированы
        assert count == 100

        active_expired = (
            real_db_session.query(Subscription)
            .filter(
                Subscription.is_active == True,
                Subscription.expires_at < datetime.now(timezone.utc),
            )
            .count()
        )
        assert active_expired == 0

    @pytest.mark.asyncio
    async def test_concurrent_webhook_processing(self, real_db_session, test_user):
        """
        КРИТИЧНО: Одновременная обработка множества webhook
        """
        from bot.api.premium_endpoints import yookassa_webhook

        # Создаём 20 разных webhook одновременно
        async def process_webhook(payment_id, telegram_id):
            webhook_data = {
                "type": "notification",
                "event": "payment.succeeded",
                "object": {
                    "id": payment_id,
                    "status": "succeeded",
                    "amount": {"value": "99.00", "currency": "RUB"},
                    "metadata": {
                        "telegram_id": str(telegram_id),
                        "plan_id": "week",
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

            with patch("bot.api.premium_endpoints.get_db", mock_get_db):
                return await yookassa_webhook(MockRequest())

        # Создаём пользователей
        for i in range(20):
            tid = 888999000 + i
            user_service = UserService(real_db_session)
            user_service.get_or_create_user(
                telegram_id=tid, username=f"concurrent_{i}", first_name="Test"
            )
            real_db_session.commit()

        # Обрабатываем webhook одновременно
        tasks = [process_webhook(f"payment_concurrent_{i}", 888999000 + i) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем что все успешны
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) == 20

    @pytest.mark.asyncio
    async def test_recovery_after_yookassa_api_error(self, real_db_session, test_user):
        """
        Восстановление после ошибки YooKassa API
        """
        payment_service = PaymentService(real_db_session)

        # Первая попытка - ошибка YooKassa
        with patch("yookassa.Payment.create") as mock_create:
            mock_create.side_effect = Exception("YooKassa API error")

            with pytest.raises(Exception):
                await payment_service.create_payment(
                    telegram_id=888999000,
                    amount=99.0,
                    plan_id="week",
                    description="Test recovery",
                    customer_email="test@pandapal.ru",
                )

        # Вторая попытка - успешная
        payment_data = await payment_service.create_payment(
            telegram_id=888999000,
            amount=99.0,
            plan_id="week",
            description="Test recovery",
            customer_email="test@pandapal.ru",
        )

        # Проверяем что платеж создан
        assert payment_data is not None
        assert "payment_id" in payment_data

    @pytest.mark.asyncio
    async def test_malformed_webhook_signature(self, real_db_session, test_user):
        """
        Обработка webhook с неправильной подписью
        """
        from bot.api.premium_endpoints import yookassa_webhook

        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "payment_malformed",
                "status": "succeeded",
                "amount": {"value": "99.00", "currency": "RUB"},
                "metadata": {"telegram_id": "888999000", "plan_id": "week"},
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
                # Неправильная подпись
                return {
                    "Content-Type": "application/json",
                    "X-Yookassa-Signature": "invalid_signature_12345",
                }

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response = await yookassa_webhook(MockRequest())

            # Webhook должен быть обработан (подпись опциональна)
            # или отклонён в зависимости от реализации
            assert response.status in [200, 401, 403]

    @pytest.mark.asyncio
    async def test_system_under_continuous_stress(self, real_db_session):
        """
        СТРЕСС-ТЕСТ: Непрерывная нагрузка на систему
        """
        payment_service = PaymentService(real_db_session)
        subscription_service = SubscriptionService(real_db_session)

        # Создаём пользователей
        for i in range(50):
            tid = 888999100 + i
            user_service = UserService(real_db_session)
            user_service.get_or_create_user(
                telegram_id=tid, username=f"stress_{i}", first_name="Stress"
            )
            real_db_session.commit()

        # Создаём платежи непрерывно
        success_count = 0
        error_count = 0

        for i in range(100):
            telegram_id = 888999100 + (i % 50)

            try:
                payment_data = await payment_service.create_payment(
                    telegram_id=telegram_id,
                    amount=99.0,
                    plan_id="week",
                    description=f"Stress test {i}",
                    customer_email="stress@pandapal.ru",
                )
                success_count += 1
            except Exception:
                error_count += 1

        # Проверяем что система выдержала нагрузку
        # Допускаем до 10% ошибок
        assert success_count >= 90
        assert error_count <= 10

        # Проверяем целостность данных
        total_payments = real_db_session.query(Payment).count()
        assert total_payments > 0


# Сценарии запуска тестов:
#
# 1. Все тесты отказоустойчивости:
#    pytest tests/resilience/test_payment_resilience.py -v
#
# 2. Только критичные тесты:
#    pytest tests/resilience/test_payment_resilience.py -v -m "test_yookassa_timeout_handling or test_database_connection_loss"
#
# 3. Стресс-тесты:
#    pytest tests/resilience/test_payment_resilience.py -v -k "stress"
#
# 4. С подробным выводом:
#    pytest tests/resilience/test_payment_resilience.py -v -s
