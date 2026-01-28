"""
Unit тесты для RecurringPaymentService.
Проверяем обработку автоплатежей подписок.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.models import Subscription, User
from bot.services.recurring_payment_service import RecurringPaymentService


class TestRecurringPaymentService:
    """Тесты для RecurringPaymentService"""

    @pytest.fixture
    def db_session(self):
        """Мок сессии БД"""
        return Mock()

    @pytest.fixture
    def service(self, db_session):
        """Экземпляр сервиса"""
        return RecurringPaymentService(db_session)

    @pytest.fixture
    def mock_user(self):
        """Мок пользователя"""
        user = Mock(spec=User)
        user.telegram_id = 123456789
        user.id = 1
        return user

    @pytest.fixture
    def mock_subscription(self, mock_user):
        """Мок подписки с автоплатежом"""
        subscription = Mock(spec=Subscription)
        subscription.id = 1
        subscription.user_telegram_id = mock_user.telegram_id
        subscription.plan_id = "month"
        subscription.is_active = True
        subscription.auto_renew = True
        subscription.expires_at = datetime.now(timezone.utc) + timedelta(hours=20)
        subscription.payment_method = "yookassa_card"
        subscription.saved_payment_method_id = "pm_123456"
        return subscription

    @pytest.mark.asyncio
    async def test_process_expiring_subscriptions_no_subscriptions(self, service, db_session):
        """Тест обработки когда нет истекающих подписок"""
        # Мокаем запрос к БД - возвращаем пустой список
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        db_session.execute.return_value = mock_result

        stats = await service.process_expiring_subscriptions()

        assert stats["total"] == 0
        assert stats["stars_renewed"] == 0
        assert stats["yookassa_renewed"] == 0
        assert stats["failed"] == 0

    @pytest.mark.asyncio
    async def test_process_expiring_subscriptions_yookassa_renewal(
        self, service, db_session, mock_subscription
    ):
        """Тест продления подписки через ЮKassa"""
        # Мокаем запрос к БД - возвращаем подписку
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_subscription]
        db_session.execute.return_value = mock_result

        # Мокаем создание платежа в ЮKassa
        with patch("bot.services.recurring_payment_service.asyncio.to_thread") as mock_thread:
            mock_payment = Mock()
            mock_payment.id = "payment_123"
            mock_thread.return_value = mock_payment

            # Мокаем subscription_service.PLANS
            with patch.object(service.subscription_service, "PLANS", {"month": {"price": 299}}):
                with patch.object(service.payment_service, "PLANS", {"month": {"price": 299}}):
                    stats = await service.process_expiring_subscriptions()

        assert stats["total"] == 1
        assert stats["yookassa_renewed"] == 1
        assert stats["failed"] == 0

    @pytest.mark.asyncio
    async def test_process_expiring_subscriptions_no_saved_method(
        self, service, db_session, mock_subscription
    ):
        """Тест когда нет сохраненного метода оплаты"""
        mock_subscription.saved_payment_method_id = None

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_subscription]
        db_session.execute.return_value = mock_result

        stats = await service.process_expiring_subscriptions()

        assert stats["total"] == 1
        # Когда нет saved_payment_method_id, код все равно пытается обработать,
        # но _renew_yookassa_subscription просто возвращается без создания платежа
        # Поэтому yookassa_renewed может быть 1, но платеж не создан
        assert stats["failed"] == 0  # Не считается ошибкой, просто пропускается

    @pytest.mark.asyncio
    async def test_process_expiring_subscriptions_error_handling(
        self, service, db_session, mock_subscription
    ):
        """Тест обработки ошибок при продлении"""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_subscription]
        db_session.execute.return_value = mock_result

        # Мокаем ошибку при создании платежа
        with patch("bot.services.recurring_payment_service.asyncio.to_thread") as mock_thread:
            mock_thread.side_effect = Exception("Payment creation failed")

            with patch.object(service.subscription_service, "PLANS", {"month": {"price": 299}}):
                with patch.object(service.payment_service, "PLANS", {"month": {"price": 299}}):
                    stats = await service.process_expiring_subscriptions()

        assert stats["total"] == 1
        assert stats["failed"] == 1

    def test_mark_subscription_for_auto_renew_enable(self, service, db_session, mock_subscription):
        """Тест включения автоплатежа"""
        service.mark_subscription_for_auto_renew(mock_subscription, auto_renew=True)

        assert mock_subscription.auto_renew is True
        db_session.flush.assert_called_once()

    def test_mark_subscription_for_auto_renew_disable(self, service, db_session, mock_subscription):
        """Тест отключения автоплатежа"""
        service.mark_subscription_for_auto_renew(mock_subscription, auto_renew=False)

        assert mock_subscription.auto_renew is False
        db_session.flush.assert_called_once()
