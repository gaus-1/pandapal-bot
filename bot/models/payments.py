"""
Модели платежей и подписок.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Subscription(Base):
    """
    Модель подписки на Premium доступ.

    Хранит информацию о покупках Premium подписки пользователями,
    включая срок действия, тип плана и транзакции.

    Attributes:
        id: Уникальный идентификатор подписки.
        user_telegram_id: ID пользователя в Telegram.
        plan_id: Тип плана ('month', 'year').
        starts_at: Дата начала подписки.
        expires_at: Дата окончания подписки.
        is_active: Статус активности подписки.
        transaction_id: ID транзакции от Telegram.
        created_at: Дата создания записи.
    """

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan_id: Mapped[str] = mapped_column(String(20), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_payload: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Платежная информация
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Сохраненный метод оплаты для автоплатежа (ЮKassa)
    saved_payment_method_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Автоплатеж
    auto_renew: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")

    __table_args__ = (
        Index("idx_subscriptions_user_active", "user_telegram_id", "is_active"),
        Index("idx_subscriptions_expires", "expires_at"),
        Index("idx_subscriptions_payment_id", "payment_id"),
        CheckConstraint("plan_id IN ('month', 'year')", name="ck_subscriptions_plan_id"),
        CheckConstraint(
            "payment_method IS NULL OR payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other')",
            name="ck_subscriptions_payment_method",
        ),
    )

    def __repr__(self) -> str:
        """Строковое представление подписки"""
        return (
            f"<Subscription(id={self.id}, user={self.user_telegram_id}, "
            f"plan={self.plan_id}, expires='{self.expires_at}', active={self.is_active})>"
        )

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "payment_method": self.payment_method,
            "auto_renew": self.auto_renew,
            "has_saved_payment_method": bool(self.saved_payment_method_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Payment(Base):
    """
    Модель платежа для хранения истории всех платежей.

    Хранит полную информацию о платежах (успешных и неуспешных),
    включая детали от ЮKassa и Telegram Stars для аудита и аналитики.

    Attributes:
        id: Уникальный идентификатор платежа в БД.
        payment_id: Уникальный ID платежа в платежной системе (ЮKassa/Telegram).
        user_telegram_id: ID пользователя в Telegram.
        subscription_id: ID подписки (если платеж успешен и создана подписка).
        payment_method: Способ оплаты ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other').
        plan_id: Тип плана ('month', 'year').
        amount: Сумма платежа.
        currency: Валюта платежа (RUB, XTR для Stars).
        status: Статус платежа ('pending', 'succeeded', 'cancelled', 'failed').
        payment_metadata: Дополнительные данные платежа (JSON).
        webhook_data: Полные данные webhook для отладки (JSON).
        created_at: Дата создания записи.
        updated_at: Дата последнего обновления.
        paid_at: Дата успешной оплаты.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    plan_id: Mapped[str] = mapped_column(String(20), nullable=False)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    payment_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    webhook_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_telegram_id])
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", foreign_keys=[subscription_id]
    )

    __table_args__ = (
        Index("idx_payments_user_status", "user_telegram_id", "status"),
        Index("idx_payments_created", "created_at"),
        Index("idx_payments_paid", "paid_at"),
        CheckConstraint(
            "payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other')",
            name="ck_payments_payment_method",
        ),
        CheckConstraint("plan_id IN ('month', 'year')", name="ck_payments_plan_id"),
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'cancelled', 'failed')",
            name="ck_payments_status",
        ),
    )

    def __repr__(self) -> str:
        """Строковое представление платежа"""
        return (
            f"<Payment(id={self.id}, payment_id='{self.payment_id}', "
            f"user={self.user_telegram_id}, status='{self.status}', amount={self.amount} {self.currency})>"
        )

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "user_telegram_id": self.user_telegram_id,
            "subscription_id": self.subscription_id,
            "payment_method": self.payment_method,
            "plan_id": self.plan_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "payment_metadata": self.payment_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }
