"""
Сервис для работы с подписками Premium
Активация, проверка статуса, управление подписками
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.models import Subscription, User


class SubscriptionService:
    """
    Сервис управления подписками Premium
    Активация, проверка статуса, обновление данных
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
                return user.premium_until > now

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
    ) -> Subscription:
        """
        Активировать Premium подписку

        Args:
            telegram_id: Telegram ID пользователя
            plan_id: Тип плана ('week', 'month', 'year')
            transaction_id: ID транзакции от Telegram
            invoice_payload: Payload из invoice

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

        # Создаем подписку
        subscription = Subscription(
            user_telegram_id=telegram_id,
            plan_id=plan_id,
            starts_at=now,
            expires_at=expires_at,
            is_active=True,
            transaction_id=transaction_id,
            invoice_payload=invoice_payload,
        )

        self.db.add(subscription)
        self.db.flush()

        # Обновляем premium_until в User
        user = self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()
        if user:
            # Если уже есть premium_until и он больше текущей даты, продлеваем
            if user.premium_until and user.premium_until > now:
                user.premium_until = max(user.premium_until, expires_at)
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
