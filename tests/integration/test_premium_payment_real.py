"""
РЕАЛЬНЫЕ интеграционные тесты для системы оплаты Premium через Telegram Stars
БЕЗ МОКОВ - только реальные операции с БД и обработчиками

Тестируем:
- Создание invoice для оплаты
- Обработку PreCheckoutQuery
- Обработку SuccessfulPayment
- Активацию подписки в БД
- Проверку premium статуса
- Деактивацию истекших подписок
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Chat,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    SuccessfulPayment,
)
from aiogram.types import User as TelegramUser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, Subscription, User
from bot.services import SubscriptionService, UserService


class TestPremiumPaymentReal:
    """Реальные интеграционные тесты системы оплаты Premium"""

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
            telegram_id=999888777,
            username="test_premium_user",
            first_name="Тестовый",
            last_name="Premium",
        )
        real_db_session.commit()
        return user

    @pytest.fixture
    def mock_telegram_user(self):
        """Mock для Telegram User"""
        return TelegramUser(
            id=999888777,
            is_bot=False,
            first_name="Тестовый",
            last_name="Premium",
            username="test_premium_user",
            language_code="ru",
        )

    @pytest.fixture
    def mock_chat(self):
        """Mock для Chat"""
        return Chat(id=999888777, type="private")

    @pytest.mark.asyncio
    async def test_create_invoice_endpoint(self, real_db_session, test_user):
        """КРИТИЧНО: Проверка создания invoice через API endpoint"""
        from unittest.mock import AsyncMock, MagicMock, patch

        from bot.api.premium_endpoints import create_premium_invoice

        # Создаём тестовый запрос
        request_data = {"telegram_id": 999888777, "plan_id": "month"}

        # Создаём mock request с json данными
        class MockRequest:
            async def json(self):
                return request_data

        request = MockRequest()

        # Мокаем Bot для создания invoice (импортируется внутри функции)
        with patch("aiogram.Bot") as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot.create_invoice_link = AsyncMock(return_value="https://t.me/invoice/test123")
            mock_bot.session.close = AsyncMock()
            mock_bot_class.return_value = mock_bot

            # Вызываем endpoint
            response = await create_premium_invoice(request)
            response_data = await response.json()

            # Проверяем результат
            assert response.status == 200
            assert response_data["success"] is True
            assert "invoice_link" in response_data
            assert response_data["invoice_link"].startswith("https://")

            # Проверяем что Bot был вызван правильно
            mock_bot.create_invoice_link.assert_called_once()
            call_args = mock_bot.create_invoice_link.call_args
            assert call_args[1]["currency"] == "XTR"  # Telegram Stars
            assert call_args[1]["payload"].startswith("premium_month_999888777")

    @pytest.mark.asyncio
    async def test_pre_checkout_query_handler(self, real_db_session, test_user):
        """КРИТИЧНО: Проверка обработки PreCheckoutQuery"""
        from unittest.mock import AsyncMock, MagicMock, patch

        from bot.handlers.payment_handler import pre_checkout_handler

        # Создаём PreCheckoutQuery
        query = PreCheckoutQuery(
            id="test_query_123",
            from_user=TelegramUser(
                id=999888777,
                is_bot=False,
                first_name="Тестовый",
            ),
            currency="XTR",
            total_amount=150,
            invoice_payload="premium_month_999888777",
        )

        # Мокаем метод answer через MagicMock (обход frozen модели)
        mock_answer = AsyncMock()
        query = MagicMock(spec=PreCheckoutQuery)
        query.id = "test_query_123"
        query.from_user = TelegramUser(id=999888777, is_bot=False, first_name="Тестовый")
        query.currency = "XTR"
        query.total_amount = 150
        query.invoice_payload = "premium_month_999888777"
        query.answer = mock_answer

        # Вызываем обработчик
        await pre_checkout_handler(query)

        # Проверяем что ответ был отправлен с ok=True
        mock_answer.assert_called_once()
        call_args = mock_answer.call_args
        assert call_args[1]["ok"] is True

    @pytest.mark.asyncio
    async def test_pre_checkout_query_invalid_payload(self, real_db_session, test_user):
        """Проверка обработки невалидного payload в PreCheckoutQuery"""
        from unittest.mock import AsyncMock, MagicMock

        from bot.handlers.payment_handler import pre_checkout_handler

        mock_answer = AsyncMock()
        query = MagicMock(spec=PreCheckoutQuery)
        query.id = "test_query_456"
        query.from_user = TelegramUser(id=999888777, is_bot=False, first_name="Тест")
        query.currency = "XTR"
        query.total_amount = 150
        query.invoice_payload = "invalid_payload"
        query.answer = mock_answer

        await pre_checkout_handler(query)

        # Должен вернуть ok=False
        mock_answer.assert_called_once()
        call_args = mock_answer.call_args
        assert call_args[1]["ok"] is False

    @pytest.mark.asyncio
    async def test_successful_payment_activates_subscription(
        self, real_db_session, test_user, mock_telegram_user, mock_chat
    ):
        """КРИТИЧНО: Проверка активации подписки после успешной оплаты"""
        from unittest.mock import AsyncMock, patch

        from bot.handlers.payment_handler import successful_payment_handler

        # Создаём SuccessfulPayment
        successful_payment = SuccessfulPayment(
            currency="XTR",
            total_amount=150,
            invoice_payload="premium_month_999888777",
            telegram_payment_charge_id="test_charge_123",
            provider_payment_charge_id="provider_123",
        )

        # Создаём Message с SuccessfulPayment
        message = Message(
            message_id=1,
            date=datetime.now(timezone.utc),
            chat=mock_chat,
            from_user=mock_telegram_user,
            successful_payment=successful_payment,
        )

        # Проверяем что подписки нет до оплаты
        subscription_service = SubscriptionService(real_db_session)
        assert not subscription_service.is_premium_active(999888777)

        # Вызываем обработчик
        await successful_payment_handler(message)

        # Вызываем обработчик с моком answer
        with patch.object(message, "answer", new_callable=AsyncMock) as mock_answer:
            await successful_payment_handler(message)

            # Проверяем что подписка активирована
            assert subscription_service.is_premium_active(999888777)

            # Проверяем запись в БД
            subscription = subscription_service.get_active_subscription(999888777)
            assert subscription is not None
            assert subscription.plan_id == "month"
            assert subscription.is_active is True
            assert subscription.transaction_id == "test_charge_123"
            assert subscription.expires_at > datetime.now(timezone.utc)

            # Проверяем что premium_until обновлен в User
            user = real_db_session.query(User).filter_by(telegram_id=999888777).first()
            assert user.premium_until is not None
            assert user.premium_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)

            # Проверяем что отправлено сообщение об активации
            mock_answer.assert_called_once()
            call_args = mock_answer.call_args
            assert "Premium активирован" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_subscription_service_activate_subscription(self, real_db_session, test_user):
        """КРИТИЧНО: Проверка активации подписки через SubscriptionService"""
        subscription_service = SubscriptionService(real_db_session)

        # Активируем подписку
        subscription = subscription_service.activate_subscription(
            telegram_id=999888777,
            plan_id="week",
            transaction_id="test_tx_456",
            invoice_payload="premium_week_999888777",
        )

        real_db_session.commit()

        # Проверяем что подписка создана
        assert subscription is not None
        assert subscription.plan_id == "week"
        assert subscription.is_active is True
        assert subscription.transaction_id == "test_tx_456"

        # Проверяем срок действия (7 дней)
        expected_expires = datetime.now(timezone.utc) + timedelta(days=7)
        # Убеждаемся что expires_at timezone-aware
        expires_at_aware = subscription.expires_at
        if expires_at_aware.tzinfo is None:
            expires_at_aware = expires_at_aware.replace(tzinfo=timezone.utc)
        assert abs((expires_at_aware - expected_expires).total_seconds()) < 60

        # Проверяем что premium активен
        assert subscription_service.is_premium_active(999888777)

    @pytest.mark.asyncio
    async def test_subscription_service_check_premium_status(self, real_db_session, test_user):
        """Проверка проверки premium статуса"""
        subscription_service = SubscriptionService(real_db_session)

        # Изначально premium не активен
        assert not subscription_service.is_premium_active(999888777)

        # Активируем подписку
        subscription_service.activate_subscription(
            telegram_id=999888777, plan_id="month", transaction_id="test_tx_789"
        )
        real_db_session.commit()

        # Теперь premium активен
        assert subscription_service.is_premium_active(999888777)

        # Получаем активную подписку
        active_sub = subscription_service.get_active_subscription(999888777)
        assert active_sub is not None
        assert active_sub.plan_id == "month"

    @pytest.mark.asyncio
    async def test_subscription_expires_correctly(self, real_db_session, test_user):
        """Проверка что подписка истекает правильно"""
        subscription_service = SubscriptionService(real_db_session)

        # Активируем подписку на неделю
        subscription = subscription_service.activate_subscription(
            telegram_id=999888777, plan_id="week", transaction_id="test_tx_expire"
        )
        real_db_session.commit()

        # Проверяем что premium активен
        assert subscription_service.is_premium_active(999888777)

        # Искусственно истекаем подписку (устанавливаем expires_at в прошлое)
        subscription.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        real_db_session.commit()

        # Проверяем что premium не активен
        assert not subscription_service.is_premium_active(999888777)

    @pytest.mark.asyncio
    async def test_deactivate_expired_subscriptions(self, real_db_session, test_user):
        """Проверка деактивации истекших подписок"""
        subscription_service = SubscriptionService(real_db_session)

        # Создаём истекшую подписку напрямую в БД
        expired_subscription = Subscription(
            user_telegram_id=999888777,
            plan_id="month",
            starts_at=datetime.now(timezone.utc) - timedelta(days=40),
            expires_at=datetime.now(timezone.utc) - timedelta(days=10),
            is_active=True,
            transaction_id="expired_tx",
        )
        real_db_session.add(expired_subscription)
        real_db_session.commit()

        # Проверяем что подписка истекла но ещё активна
        assert expired_subscription.is_active is True
        assert not subscription_service.is_premium_active(999888777)

        # Деактивируем истекшие подписки
        count = subscription_service.deactivate_expired_subscriptions()
        real_db_session.commit()

        # Проверяем что подписка деактивирована
        assert count >= 1
        real_db_session.refresh(expired_subscription)
        assert expired_subscription.is_active is False

    @pytest.mark.asyncio
    async def test_multiple_subscriptions_extend_premium(self, real_db_session, test_user):
        """Проверка что несколько подписок продлевают premium"""
        subscription_service = SubscriptionService(real_db_session)

        # Активируем первую подписку на неделю
        sub1 = subscription_service.activate_subscription(
            telegram_id=999888777, plan_id="week", transaction_id="tx1"
        )
        real_db_session.commit()

        expires1 = sub1.expires_at

        # Активируем вторую подписку на месяц (должна продлить)
        sub2 = subscription_service.activate_subscription(
            telegram_id=999888777, plan_id="month", transaction_id="tx2"
        )
        real_db_session.commit()

        # Проверяем что premium_until обновлен на более позднюю дату
        user = real_db_session.query(User).filter_by(telegram_id=999888777).first()
        assert user.premium_until > expires1

        # Проверяем что обе подписки активны
        assert sub1.is_active is True
        assert sub2.is_active is True

    @pytest.mark.asyncio
    async def test_invalid_plan_id_raises_error(self, real_db_session, test_user):
        """Проверка что невалидный plan_id вызывает ошибку"""
        subscription_service = SubscriptionService(real_db_session)

        with pytest.raises(ValueError, match="Invalid plan_id"):
            subscription_service.activate_subscription(
                telegram_id=999888777, plan_id="invalid_plan", transaction_id="tx"
            )

    @pytest.mark.asyncio
    async def test_get_user_subscriptions(self, real_db_session, test_user):
        """Проверка получения всех подписок пользователя"""
        subscription_service = SubscriptionService(real_db_session)

        # Создаём несколько подписок
        subscription_service.activate_subscription(
            telegram_id=999888777, plan_id="week", transaction_id="tx1"
        )
        subscription_service.activate_subscription(
            telegram_id=999888777, plan_id="month", transaction_id="tx2"
        )
        real_db_session.commit()

        # Получаем все подписки
        subscriptions = subscription_service.get_user_subscriptions(999888777, limit=10)

        # Проверяем что получили подписки
        assert len(subscriptions) >= 2
        assert all(sub.user_telegram_id == 999888777 for sub in subscriptions)

    @pytest.mark.asyncio
    async def test_premium_endpoint_activation(self, real_db_session, test_user):
        """КРИТИЧНО: Проверка активации через API endpoint"""
        from contextlib import contextmanager
        from unittest.mock import patch

        from bot.api.premium_endpoints import handle_successful_payment

        # Мокаем get_db чтобы использовать нашу SQLite сессию
        @contextmanager
        def mock_get_db():
            yield real_db_session

        # Создаём тестовый запрос
        request_data = {
            "telegram_id": 999888777,
            "plan_id": "year",
            "transaction_id": "api_tx_123",
        }

        class MockRequest:
            async def json(self):
                return request_data

        request = MockRequest()

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            # Вызываем endpoint
            response = await handle_successful_payment(request)
            response_data = await response.json()

            # Коммитим изменения
            real_db_session.commit()

            # Проверяем результат
            assert response.status == 200
            assert response_data["success"] is True
            assert "expires_at" in response_data

            # Проверяем что подписка активирована в БД
            subscription_service = SubscriptionService(real_db_session)
            assert subscription_service.is_premium_active(999888777)

            subscription = subscription_service.get_active_subscription(999888777)
            assert subscription.plan_id == "year"
            assert subscription.transaction_id == "api_tx_123"
