"""
Сервис для работы с подписками Premium.

Обеспечивает управление подписками: активация после оплаты,
проверка статуса подписки, деактивация истёкших подписок.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.models import Subscription, User


class SubscriptionService:
    """
    Сервис управления подписками Premium.

    Обеспечивает полный цикл работы с подписками:
    активация после успешной оплаты через Telegram Stars,
    проверка статуса активной подписки, автоматическая деактивация
    истёкших подписок и управление данными подписок.
    """

    # Тарифные планы (дни доступа)
    PLANS = {
        "week": 7,
        "month": 30,
        "year": 365,
    }

    def __init__(self, db: Session):
        """
        Инициализация сервиса

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db

    def is_premium_active(self, telegram_id: int) -> bool:
        """
        Проверка активной Premium подписки

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если есть активная подписка
        """
        now = datetime.now(timezone.utc)

        # Проверяем активную подписку
        stmt = (
            select(Subscription)
            .where(Subscription.user_telegram_id == telegram_id)
            .where(Subscription.is_active.is_(True))
            .where(Subscription.expires_at > now)
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )

        subscription = self.db.execute(stmt).scalar_one_or_none()

        if subscription:
            # Также проверяем premium_until в User для быстрого доступа
            user = self.db.execute(
                select(User).where(User.telegram_id == telegram_id)
            ).scalar_one_or_none()
            if user and user.premium_until:
                # Убеждаемся что premium_until timezone-aware
                premium_until = user.premium_until
                if premium_until.tzinfo is None:
                    premium_until = premium_until.replace(tzinfo=timezone.utc)
                return premium_until > now

        return False

    def get_active_subscription(self, telegram_id: int) -> Optional[Subscription]:
        """
        Получить активную подписку пользователя

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Optional[Subscription]: Активная подписка или None
        """
        now = datetime.now(timezone.utc)

        stmt = (
            select(Subscription)
            .where(Subscription.user_telegram_id == telegram_id)
            .where(Subscription.is_active.is_(True))
            .where(Subscription.expires_at > now)
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    def activate_subscription(
        self,
        telegram_id: int,
        plan_id: str,
        transaction_id: Optional[str] = None,
        invoice_payload: Optional[str] = None,
        payment_method: Optional[str] = None,
        payment_id: Optional[str] = None,
        saved_payment_method_id: Optional[str] = None,
    ) -> Subscription:
        """
        Активировать Premium подписку

        Args:
            telegram_id: Telegram ID пользователя
            plan_id: Тип плана ('week', 'month', 'year')
            transaction_id: ID транзакции от Telegram (для Stars)
            invoice_payload: Payload из invoice (для Stars)
            payment_method: Способ оплаты ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other')
            payment_id: ID платежа в платежной системе
            saved_payment_method_id: ID сохраненного метода оплаты в ЮKassa (для автоплатежа)

        Returns:
            Subscription: Созданная подписка

        Raises:
            ValueError: Если plan_id невалидный
        """
        if plan_id not in self.PLANS:
            raise ValueError(f"Invalid plan_id: {plan_id}")

        days = self.PLANS[plan_id]
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=days)

        # Определяем автоплатеж:
        # - Для ЮKassa подписок month и year - включаем автоплатеж по умолчанию
        # - Stars не используется для подписок (только для донатов)
        auto_renew = False
        if (
            payment_method
            and payment_method.startswith("yookassa_")
            and plan_id in ("month", "year")
        ):
            auto_renew = True

        # Создаем подписку
        subscription = Subscription(
            user_telegram_id=telegram_id,
            plan_id=plan_id,
            starts_at=now,
            expires_at=expires_at,
            is_active=True,
            transaction_id=transaction_id,
            invoice_payload=invoice_payload,
            payment_method=payment_method,
            payment_id=payment_id,
            saved_payment_method_id=saved_payment_method_id,
            auto_renew=auto_renew,
        )

        self.db.add(subscription)
        self.db.flush()

        # Обновляем premium_until в User
        user = self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        if user:
            # Если уже есть premium_until и он больше текущей даты, продлеваем
            if user.premium_until:
                # Убеждаемся что premium_until timezone-aware для сравнения
                premium_until = user.premium_until
                if premium_until.tzinfo is None:
                    premium_until = premium_until.replace(tzinfo=timezone.utc)
                if premium_until > now:
                    user.premium_until = max(premium_until, expires_at)
                else:
                    user.premium_until = expires_at
            else:
                user.premium_until = expires_at
            self.db.flush()

        logger.info(
            f"✅ Premium активирован: user={telegram_id}, plan={plan_id}, "
            f"expires={expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return subscription

    def deactivate_expired_subscriptions(self) -> int:
        """
        Деактивировать истекшие подписки

        Returns:
            int: Количество деактивированных подписок
        """
        now = datetime.now(timezone.utc)

        stmt = (
            select(Subscription)
            .where(Subscription.is_active.is_(True))
            .where(Subscription.expires_at <= now)
        )

        expired = self.db.execute(stmt).scalars().all()
        count = 0

        for subscription in expired:
            subscription.is_active = False
            count += 1

            # Обновляем premium_until в User если это последняя активная подписка
            user = self.db.execute(
                select(User).where(User.telegram_id == subscription.user_telegram_id)
            ).scalar_one_or_none()
            if user:
                # Проверяем есть ли другие активные подписки
                active = self.get_active_subscription(subscription.user_telegram_id)
                if not active:
                    user.premium_until = None

        if count > 0:
            self.db.commit()
            logger.info(f"🔄 Деактивировано истекших подписок: {count}")

        return count

    def get_user_subscriptions(self, telegram_id: int, limit: int = 10) -> list[Subscription]:
        """
        Получить все подписки пользователя

        Args:
            telegram_id: Telegram ID пользователя
            limit: Максимальное количество записей

        Returns:
            list[Subscription]: Список подписок
        """
        stmt = (
            select(Subscription)
            .where(Subscription.user_telegram_id == telegram_id)
            .order_by(Subscription.created_at.desc())
            .limit(limit)
        )

        return list(self.db.execute(stmt).scalars().all())
