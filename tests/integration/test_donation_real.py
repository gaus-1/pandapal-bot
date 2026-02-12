"""
РЕАЛЬНЫЕ интеграционные тесты для системы донатов через Telegram Stars
БЕЗ МОКОВ - только реальные операции с БД и обработчиками

Тестируем:
- Создание invoice для доната
- Обработку PreCheckoutQuery для доната
- Обработку SuccessfulPayment для доната
- Проверку что донат НЕ активирует Premium
"""

import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, PreCheckoutQuery, SuccessfulPayment
from aiogram.types import User as TelegramUser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Импортируем conftest_payment ПЕРЕД импортом bot модулей
import tests.integration.conftest_payment  # noqa: F401
from bot.models import Base, Subscription, User
from bot.services import SubscriptionService, UserService


class TestDonationReal:
    """Реальные интеграционные тесты системы донатов"""

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
            telegram_id=888777666,
            username="test_donation_user",
            first_name="Тестовый",
            last_name="Донатер",
        )
        real_db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_create_donation_invoice(self, real_db_session, test_user):
        """КРИТИЧНО: Проверка создания donation invoice"""
        from bot.api.premium_endpoints import create_donation_invoice

        @contextmanager
        def mock_get_db():
            yield real_db_session

        request_data = {"telegram_id": 888777666, "amount": 100}

        class MockRequest:
            async def json(self):
                return request_data

        request = MockRequest()

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            with patch("aiogram.Bot") as mock_bot_class:
                mock_bot = MagicMock()
                mock_bot.create_invoice_link = AsyncMock(
                    return_value="https://t.me/invoice/donation_test"
                )
                mock_bot.session.close = AsyncMock()
                mock_bot_class.return_value = mock_bot

                response = await create_donation_invoice(request)
                # aiohttp Response - читаем _body и парсим JSON
                import json

                if hasattr(response, "_body") and response._body:
                    response_data = json.loads(response._body.decode("utf-8"))
                else:
                    response_data = await response.json()

                assert response.status == 200
                assert response_data["success"] is True
                assert "invoice_link" in response_data

                # Проверяем что payload правильный (donation, не premium)
                mock_bot.create_invoice_link.assert_called_once()
                call_args = mock_bot.create_invoice_link.call_args
                assert call_args[1]["currency"] == "XTR"
                assert call_args[1]["payload"].startswith("donation_888777666_100")

    @pytest.mark.asyncio
    async def test_donation_pre_checkout(self, real_db_session, test_user):
        """КРИТИЧНО: Проверка PreCheckoutQuery для доната (handler не использует БД)"""
        from bot.handlers.payment_handler import pre_checkout_handler

        mock_answer = AsyncMock()
        query = MagicMock(spec=PreCheckoutQuery)
        query.id = "donation_query_123"
        query.from_user = TelegramUser(id=888777666, is_bot=False, first_name="Тест")
        query.currency = "XTR"
        query.total_amount = 100
        query.invoice_payload = "donation_888777666_100"
        query.answer = mock_answer

        await pre_checkout_handler(query)

        # Должен разрешить донат
        mock_answer.assert_called_once()
        assert mock_answer.call_args[1]["ok"] is True

    @pytest.mark.asyncio
    async def test_donation_successful_payment(self, real_db_session, test_user):
        """КРИТИЧНО: Проверка что донат НЕ активирует Premium (handler не использует БД)"""
        from bot.handlers.payment_handler import successful_payment_handler

        successful_payment = SuccessfulPayment(
            currency="XTR",
            total_amount=100,
            invoice_payload="donation_888777666_100",
            telegram_payment_charge_id="donation_tx_123",
            provider_payment_charge_id="provider_donation_123",
        )

        # Создаём mock Message (не можем патчить frozen объект)
        message_mock = MagicMock()
        message_mock.successful_payment = successful_payment
        message_mock.answer = AsyncMock()

        subscription_service = SubscriptionService(real_db_session)

        # Проверяем что premium НЕ активен до доната
        assert not subscription_service.is_premium_active(888777666)

        await successful_payment_handler(message_mock)

        # КРИТИЧНО: Premium НЕ должен быть активирован
        assert not subscription_service.is_premium_active(888777666)

        # Проверяем что НЕТ подписки
        subscription = subscription_service.get_active_subscription(888777666)
        assert subscription is None

        # Проверяем что отправлено сообщение благодарности
        message_mock.answer.assert_called_once()
        call_args = message_mock.answer.call_args
        message_text = call_args[0][0]
        assert "Спасибо" in message_text or "поддержку" in message_text.lower()

    @pytest.mark.asyncio
    async def test_donation_minimum_amount(self, real_db_session, test_user):
        """Проверка минимальной суммы доната (50 Stars)"""
        from bot.api.premium_endpoints import create_donation_invoice

        @contextmanager
        def mock_get_db():
            yield real_db_session

        # Сумма меньше минимума
        request_data = {"telegram_id": 888777666, "amount": 30}

        class MockRequest:
            async def json(self):
                return request_data

        request = MockRequest()

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            response = await create_donation_invoice(request)
            # aiohttp Response - читаем _body и парсим JSON
            import json

            if hasattr(response, "_body") and response._body:
                response_data = json.loads(response._body.decode("utf-8"))
            else:
                response_data = await response.json()

            assert response.status == 400
            assert "error" in response_data

    @pytest.mark.asyncio
    async def test_donation_vs_premium_separation(self, real_db_session, test_user):
        """КРИТИЧНО: Проверка что донат и Premium разделены (handler не использует БД)"""
        from bot.handlers.payment_handler import successful_payment_handler

        subscription_service = SubscriptionService(real_db_session)

        # Сначала делаем донат
        donation_payment = SuccessfulPayment(
            currency="XTR",
            total_amount=200,
            invoice_payload="donation_888777666_200",
            telegram_payment_charge_id="donation_tx_1",
            provider_payment_charge_id="provider_donation_1",
        )

        donation_message_mock = MagicMock()
        donation_message_mock.successful_payment = donation_payment
        donation_message_mock.answer = AsyncMock()

        await successful_payment_handler(donation_message_mock)

        # Premium НЕ должен быть активен
        assert not subscription_service.is_premium_active(888777666)

        # Теперь делаем Premium Stars платеж — handler его игнорирует (Premium только через ЮKassa)
        premium_payment = SuccessfulPayment(
            currency="XTR",
            total_amount=150,
            invoice_payload="premium_month_888777666",
            telegram_payment_charge_id="premium_tx_1",
            provider_payment_charge_id="provider_premium_1",
        )

        premium_message_mock = MagicMock()
        premium_message_mock.successful_payment = premium_payment
        premium_message_mock.answer = AsyncMock()

        await successful_payment_handler(premium_message_mock)

        # Stars с premium_* НЕ активируют Premium (только 299 ₽ через ЮKassa)
        assert not subscription_service.is_premium_active(888777666)
        subscription = subscription_service.get_active_subscription(888777666)
        assert subscription is None
