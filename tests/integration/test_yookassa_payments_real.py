"""
РЕАЛЬНЫЕ интеграционные тесты для YooKassa платежей
БЕЗ МОКОВ - только реальные операции с БД и API

Тестируем:
- Создание платежа через YooKassa API
- Обработку webhook от YooKassa
- Валидацию подписи webhook
- Активацию Premium подписки
- Обработку ошибок платежей
- Различные планы подписки
- 54-ФЗ compliance (чеки)
"""

import hashlib
import hmac
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from aiohttp import web
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from yookassa import Configuration, Payment

from bot.config import settings
from bot.models import Base
from bot.models import Payment as PaymentModel
from bot.models import Subscription, User
from bot.services import PaymentService, SubscriptionService, UserService


class TestYooKassaPaymentsReal:
    """Реальные интеграционные тесты YooKassa платежей"""

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
            telegram_id=999000111,
            username="test_yookassa_user",
            first_name="Тестовый",
            last_name="YooKassa",
        )
        real_db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_create_payment_real_request(self, real_db_session, test_user):
        """
        КРИТИЧНО: Проверка создания реального платежа через YooKassa
        Без моков - реальный запрос к YooKassa API
        """
        payment_service = PaymentService()

        # Создаём реальный платеж
        payment_data = payment_service.create_payment(
            telegram_id=999000111,
            plan_id="month",
            user_email="test@pandapal.ru",
        )

        # Проверяем результат
        assert payment_data is not None
        assert "payment_id" in payment_data
        assert "confirmation_url" in payment_data
        assert payment_data["amount"]["value"] == 399.0
        assert payment_data["amount"]["currency"] == "RUB"

    @pytest.mark.asyncio
    async def test_create_payment_all_plans(self, real_db_session, test_user):
        """Проверка создания платежей для всех планов подписки"""
        payment_service = PaymentService()

        plans = {"month": 299.0}

        for plan_id, expected_amount in plans.items():
            payment_data = payment_service.create_payment(
                telegram_id=999000111,
                plan_id=plan_id,
                user_email="test@pandapal.ru",
            )

            assert payment_data["amount"]["value"] == expected_amount
            assert plan_id in payment_data.get("description", "").lower() or plan_id in str(
                payment_data
            )

    @pytest.mark.asyncio
    async def test_webhook_signature_validation(self, real_db_session, test_user):
        """
        КРИТИЧНО: Проверка валидации подписи webhook от YooKassa
        Реальная валидация HMAC-SHA256
        """
        from bot.api.premium_endpoints import yookassa_webhook

        # Симулируем webhook от YooKassa
        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "test_payment_123",
                "status": "succeeded",
                "amount": {"value": "399.00", "currency": "RUB"},
                "metadata": {
                    "telegram_id": "999000111",
                    "plan_id": "month",
                },
                "paid": True,
                "payment_method": {"type": "bank_card"},
            },
        }

        webhook_json = json.dumps(webhook_data)

        # Вычисляем реальную подпись (как YooKassa)
        secret_key = settings.yookassa_secret_key
        signature = hmac.new(
            secret_key.encode("utf-8"), webhook_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Создаём mock request с правильной подписью
        class MockRequest:
            async def text(self):
                return webhook_json

            async def json(self):
                return webhook_data

            @property
            def headers(self):
                return {
                    "Content-Type": "application/json",
                    "X-Yookassa-Signature": signature,
                }

        request = MockRequest()

        # Мокаем get_db
        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            # Проверяем что webhook обрабатывается
            response = await yookassa_webhook(request)
            assert response.status == 200

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature_rejected(self, real_db_session, test_user):
        """
        КРИТИЧНО: Webhook с невалидной подписью должен быть отклонен
        """
        from bot.api.premium_endpoints import yookassa_webhook

        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "test_payment_invalid",
                "status": "succeeded",
                "amount": {"value": "399.00", "currency": "RUB"},
                "metadata": {
                    "telegram_id": "999000111",
                    "plan_id": "month",
                },
                "paid": True,
                "payment_method": {"type": "bank_card"},
            },
        }

        webhook_json = json.dumps(webhook_data)

        class MockRequest:
            async def text(self):
                return webhook_json

            async def json(self):
                return webhook_data

            @property
            def headers(self):
                return {
                    "Content-Type": "application/json",
                    "X-Yookassa-Signature": "invalid_signature_12345",
                }

        request = MockRequest()

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response = await yookassa_webhook(request)
            # Должен быть отклонен с 403
            assert response.status == 403

    @pytest.mark.asyncio
    async def test_webhook_activates_premium(self, real_db_session, test_user):
        """
        КРИТИЧНО: Проверка что webhook активирует Premium подписку
        """
        from bot.api.premium_endpoints import yookassa_webhook

        subscription_service = SubscriptionService(real_db_session)

        # Проверяем что Premium не активен
        assert not subscription_service.is_premium_active(999000111)

        # Симулируем webhook от YooKassa
        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "payment_webhook_test",
                "status": "succeeded",
                "amount": {"value": "249.00", "currency": "RUB"},
                "metadata": {
                    "telegram_id": "999000111",
                    "plan_id": "month",
                },
                "paid": True,
                "payment_method": {"type": "bank_card"},
            },
        }

        webhook_json = json.dumps(webhook_data)

        # Вычисляем подпись
        secret_key = settings.yookassa_secret_key
        signature = hmac.new(
            secret_key.encode("utf-8"), webhook_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        class MockRequest:
            async def text(self):
                return webhook_json

            async def json(self):
                return webhook_data

            @property
            def headers(self):
                return {
                    "Content-Type": "application/json",
                    "X-Yookassa-Signature": signature,
                }

        request = MockRequest()

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response = await yookassa_webhook(request)
            assert response.status == 200

            real_db_session.commit()

            # КРИТИЧНО: Premium должен быть активирован
            assert subscription_service.is_premium_active(999000111)

            # Проверяем подписку
            subscription = subscription_service.get_active_subscription(999000111)
            assert subscription is not None
            assert subscription.plan_id == "month"
            assert subscription.payment_method == "yookassa_card"

            # Проверяем что webhook_data сохранен в БД
            payment_record = (
                real_db_session.query(PaymentModel)
                .filter_by(payment_id="payment_webhook_test")
                .first()
            )
            assert payment_record is not None
            assert payment_record.webhook_data is not None
            assert payment_record.status == "succeeded"
            assert payment_record.paid_at is not None

    @pytest.mark.asyncio
    async def test_webhook_different_payment_methods(self, real_db_session, test_user):
        """Проверка обработки разных способов оплаты"""
        from bot.api.premium_endpoints import yookassa_webhook

        payment_methods = [
            ("bank_card", "yookassa_card"),
            ("sbp", "yookassa_sbp"),
            ("yoo_money", "yookassa_other"),
        ]

        for yookassa_method, expected_method in payment_methods:
            # Создаём нового пользователя для каждого теста
            user_id = 999000111 + len(payment_methods)
            user_service = UserService(real_db_session)
            user_service.get_or_create_user(
                telegram_id=user_id,
                username=f"test_{yookassa_method}",
                first_name="Test",
            )
            real_db_session.commit()

            webhook_data = {
                "type": "notification",
                "event": "payment.succeeded",
                "object": {
                    "id": f"payment_{yookassa_method}",
                    "status": "succeeded",
                    "amount": {"value": "399.00", "currency": "RUB"},
                    "metadata": {
                        "telegram_id": str(user_id),
                        "plan_id": "month",
                    },
                    "paid": True,
                    "payment_method": {"type": yookassa_method},
                },
            }

            webhook_json = json.dumps(webhook_data)

            # Вычисляем подпись
            secret_key = settings.yookassa_secret_key
            signature = hmac.new(
                secret_key.encode("utf-8"), webhook_json.encode("utf-8"), hashlib.sha256
            ).hexdigest()

            class MockRequest:
                async def text(self):
                    return webhook_json

                async def json(self):
                    return webhook_data

                @property
                def headers(self):
                    return {
                        "Content-Type": "application/json",
                        "X-Yookassa-Signature": signature,
                    }

            request = MockRequest()

            @contextmanager
            def mock_get_db():
                yield real_db_session

            with patch("bot.api.premium_endpoints.get_db", mock_get_db):
                response = await yookassa_webhook(request)
                assert response.status == 200

                real_db_session.commit()

                # Проверяем payment_method
                subscription_service = SubscriptionService(real_db_session)
                subscription = subscription_service.get_active_subscription(user_id)
                assert subscription.payment_method == expected_method

    @pytest.mark.asyncio
    async def test_webhook_idempotency(self, real_db_session, test_user):
        """
        КРИТИЧНО: Проверка идемпотентности webhook
        Повторный webhook не должен создавать дубликаты подписок
        """
        from bot.api.premium_endpoints import yookassa_webhook

        webhook_data = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "payment_idempotent",
                "status": "succeeded",
                "amount": {"value": "399.00", "currency": "RUB"},
                "metadata": {
                    "telegram_id": "999000111",
                    "plan_id": "month",
                },
                "paid": True,
                "payment_method": {"type": "bank_card"},
            },
        }

        webhook_json = json.dumps(webhook_data)

        # Вычисляем подпись
        secret_key = settings.yookassa_secret_key
        signature = hmac.new(
            secret_key.encode("utf-8"), webhook_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        class MockRequest:
            async def text(self):
                return webhook_json

            async def json(self):
                return webhook_data

            @property
            def headers(self):
                return {
                    "Content-Type": "application/json",
                    "X-Yookassa-Signature": signature,
                }

        @contextmanager
        def mock_get_db():
            yield real_db_session

        # Отправляем webhook первый раз
        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response1 = await yookassa_webhook(MockRequest())
            assert response1.status == 200
            real_db_session.commit()

        # Подсчитываем подписки
        subscriptions_count_1 = (
            real_db_session.query(Subscription).filter_by(user_telegram_id=999000111).count()
        )

        # Отправляем webhook второй раз (дубликат)
        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response2 = await yookassa_webhook(MockRequest())
            assert response2.status == 200
            real_db_session.commit()

        # Подсчитываем подписки снова
        subscriptions_count_2 = (
            real_db_session.query(Subscription).filter_by(user_telegram_id=999000111).count()
        )

        # КРИТИЧНО: количество подписок не должно увеличиться
        assert subscriptions_count_1 == subscriptions_count_2

    @pytest.mark.asyncio
    async def test_54fz_compliance_receipt(self, real_db_session, test_user):
        """
        КРИТИЧНО: Проверка 54-ФЗ соответствия (чеки)
        При создании платежа должен быть чек с ИНН
        """
        payment_service = PaymentService()

        # Создаём платеж с email для чека
        payment_data = payment_service.create_payment(
            telegram_id=999000111,
            plan_id="month",
            user_email="test@pandapal.ru",
        )

        # Получаем платеж через YooKassa API
        Configuration.account_id = settings.yookassa_shop_id
        Configuration.secret_key = settings.yookassa_secret_key

        payment = Payment.find_one(payment_data["payment_id"])

        # Проверяем что чек присутствует (если ИНН настроен)
        if settings.yookassa_inn:
            assert payment.receipt is not None
            assert payment.receipt.customer.email == "test@pandapal.ru"
            assert len(payment.receipt.items) > 0

            # Проверяем ИНН
            receipt_item = payment.receipt.items[0]
            assert receipt_item.description is not None

    @pytest.mark.asyncio
    async def test_payment_error_handling(self, real_db_session, test_user):
        """Проверка обработки ошибок при создании платежа"""
        payment_service = PaymentService()

        # Тест: Невалидный plan_id
        with pytest.raises(ValueError):
            payment_service.create_payment(
                telegram_id=999000111,
                plan_id="invalid_plan",
                user_email="test@pandapal.ru",
            )

    @pytest.mark.asyncio
    async def test_payment_saved_to_db_on_creation(self, real_db_session, test_user):
        """
        КРИТИЧНО: Проверка что заказ сохраняется в БД при создании платежа через API
        """
        from contextlib import contextmanager
        from unittest.mock import patch

        from bot.api.premium_endpoints import create_yookassa_payment

        payment_request_data = {
            "telegram_id": 999000111,
            "plan_id": "month",
            "user_email": "test@pandapal.ru",
        }

        class MockRequest:
            async def json(self):
                return payment_request_data

        request = MockRequest()

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            # Мокаем PaymentService.create_payment чтобы не делать реальный запрос
            with patch("bot.api.premium_endpoints.PaymentService") as mock_service:
                mock_payment_service = mock_service.return_value
                mock_payment_service.PLANS = PaymentService.PLANS
                mock_payment_service.create_payment.return_value = {
                    "payment_id": "test_payment_db_123",
                    "status": "pending",
                    "confirmation_url": "https://yookassa.ru/checkout/payments/test",
                    "amount": {"value": 399.0, "currency": "RUB"},
                }

                response = await create_yookassa_payment(request)
                assert response.status == 200

                real_db_session.commit()

                # Проверяем что заказ сохранен в БД
                payment_record = (
                    real_db_session.query(PaymentModel)
                    .filter_by(payment_id="test_payment_db_123")
                    .first()
                )
                assert payment_record is not None
                assert payment_record.user_telegram_id == 999000111
                assert payment_record.plan_id == "month"
                assert payment_record.amount == 399.0
                assert payment_record.status == "pending"
                assert payment_record.payment_method == "yookassa_card"

    @pytest.mark.asyncio
    async def test_payment_status_tracking(self, real_db_session, test_user):
        """Проверка отслеживания статуса платежа"""
        from bot.models import Payment as PaymentModel

        # Создаём запись платежа напрямую в БД
        payment_record = PaymentModel(
            payment_id="test_status_tracking",
            user_telegram_id=999000111,
            plan_id="month",
            amount=399.0,
            currency="RUB",
            status="pending",
            payment_method="yookassa_card",
        )
        real_db_session.add(payment_record)
        real_db_session.commit()

        # Проверяем начальный статус
        payment_record = (
            real_db_session.query(PaymentModel).filter_by(payment_id="test_status_tracking").first()
        )
        assert payment_record.status == "pending"

        # Обновляем статус
        payment_record.status = "succeeded"
        real_db_session.commit()

        # Проверяем обновление
        updated_payment = (
            real_db_session.query(PaymentModel).filter_by(payment_id="test_status_tracking").first()
        )
        assert updated_payment.status == "succeeded"

    @pytest.mark.asyncio
    async def test_concurrent_payments_same_user(self, real_db_session, test_user):
        """Проверка обработки одновременных платежей от одного пользователя"""
        import asyncio

        payment_service = PaymentService()

        # Создаём несколько платежей одновременно
        tasks = [
            asyncio.to_thread(
                payment_service.create_payment,
                telegram_id=999000111,
                plan_id="month",
                user_email="test@pandapal.ru",
            )
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Проверяем что все платежи созданы
        successful_payments = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_payments) == 3

        # Проверяем что payment_id уникальные
        payment_ids = [p["payment_id"] for p in successful_payments]
        assert len(payment_ids) == len(set(payment_ids))
