"""
Сервис для обработки автоплатежей (recurring subscriptions).

Обеспечивает:
- Автоматическое продление подписок через Telegram Stars (subscription_period)
- Автоматическое продление подписок через ЮKassa (saved payment methods)
- Обработку событий продления подписок
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.config import settings
from bot.models import Payment as PaymentModel
from bot.models import Subscription, User
from bot.services.payment_service import PaymentService
from bot.services.subscription_service import SubscriptionService


class RecurringPaymentService:
    """
    Сервис для обработки автоплатежей подписок.

    Поддерживает:
    - Telegram Stars subscriptions (через subscription_period)
    - ЮKassa saved payment methods (через payment_method_id)
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db
        self.payment_service = PaymentService()
        self.subscription_service = SubscriptionService(db)

    async def process_expiring_subscriptions(self) -> dict:
        """
        Обработать подписки, которые скоро истекают (за 1 день до истечения).

        Для Stars subscriptions - Telegram автоматически продлевает
        Для ЮKassa - создаем новый платеж используя сохраненный метод

        Returns:
            dict: Статистика обработки
        """
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)

        # Находим активные подписки, которые истекают завтра
        stmt = (
            select(Subscription)
            .where(Subscription.is_active.is_(True))
            .where(Subscription.expires_at >= now)
            .where(Subscription.expires_at <= tomorrow)
            .where(Subscription.auto_renew.is_(True))  # Только с автоплатежом
        )

        expiring_subscriptions = self.db.execute(stmt).scalars().all()

        stats = {
            "total": len(expiring_subscriptions),
            "stars_renewed": 0,
            "yookassa_renewed": 0,
            "failed": 0,
        }

        for subscription in expiring_subscriptions:
            try:
                # Подписки только через ЮKassa (Stars используется только для донатов)
                if subscription.payment_method and subscription.payment_method.startswith(
                    "yookassa_"
                ):
                    # Для ЮKassa - создаем новый платеж используя сохраненный payment_method_id
                    await self._renew_yookassa_subscription(subscription)
                    stats["yookassa_renewed"] += 1
                else:
                    logger.warning(
                        f"⚠️ Неизвестный payment_method для автоплатежа: "
                        f"{subscription.payment_method}, subscription_id={subscription.id}"
                    )

            except Exception as e:
                logger.error(
                    f"❌ Ошибка продления подписки {subscription.id}: {e}",
                    exc_info=True,
                )
                stats["failed"] += 1

        if stats["total"] > 0:
            logger.info(
                f"🔄 Обработано подписок: всего={stats['total']}, "
                f"stars={stats['stars_renewed']}, yookassa={stats['yookassa_renewed']}, "
                f"ошибок={stats['failed']}"
            )

        return stats

    async def _renew_yookassa_subscription(self, subscription: Subscription) -> None:
        """
        Продлить подписку через ЮKassa используя сохраненный метод оплаты.

        Args:
            subscription: Подписка для продления
        """
        if not subscription.saved_payment_method_id:
            logger.warning(
                f"⚠️ Нет saved_payment_method_id для подписки {subscription.id}, "
                f"автоплатеж невозможен"
            )
            return

        try:
            import uuid

            from yookassa import Payment as YooKassaPayment

            plan = self.subscription_service.PLANS[subscription.plan_id]
            plan_price = PaymentService.PLANS[subscription.plan_id]["price"]

            # Создаем новый платеж используя сохраненный метод оплаты
            payment_data = {
                "amount": {
                    "value": f"{plan_price:.2f}",
                    "currency": "RUB",
                },
                "payment_method_id": subscription.saved_payment_method_id,
                "capture": True,
                "description": f"PandaPal Premium: автоматическое продление {subscription.plan_id}",
                "metadata": {
                    "telegram_id": str(subscription.user_telegram_id),
                    "plan_id": subscription.plan_id,
                    "subscription_id": str(subscription.id),
                    "is_recurring": "true",
                },
            }

            idempotence_key = str(uuid.uuid4())
            payment = await asyncio.to_thread(YooKassaPayment.create, payment_data, idempotence_key)

            logger.info(
                f"🔄 Создан автоплатеж для подписки {subscription.id}: "
                f"payment_id={payment.id}, user={subscription.user_telegram_id}"
            )

            # Webhook от ЮKassa автоматически активирует новую подписку
            # через yookassa_webhook в premium_endpoints.py

        except Exception as e:
            logger.error(
                f"❌ Ошибка создания автоплатежа для подписки {subscription.id}: {e}",
                exc_info=True,
            )
            raise

    def mark_subscription_for_auto_renew(
        self, subscription: Subscription, auto_renew: bool = True
    ) -> None:
        """
        Пометить подписку для автоплатежа.

        Args:
            subscription: Подписка
            auto_renew: Включить автоплатеж
        """
        subscription.auto_renew = auto_renew
        self.db.flush()
        logger.info(
            f"{'✅' if auto_renew else '❌'} Автоплатеж {'включен' if auto_renew else 'отключен'}: "
            f"subscription_id={subscription.id}, user={subscription.user_telegram_id}"
        )
