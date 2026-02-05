"""
Модели реферальной программы.

Referrer — whitelist рефереров (преподаватели, партнёры).
ReferralPayout — начисление рефереру за оплату привлечённого пользователя.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
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
from .user import User


class Referrer(Base):
    """
    Реферер (преподаватель, партнёр). Только id из этой таблицы валидны для ref_<id>.

    Ссылка: https://t.me/PandaPalBot?startapp=ref_<telegram_id>
    """

    __tablename__ = "referrers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Referrer(telegram_id={self.telegram_id}, comment={self.comment})>"


class ReferralPayout(Base):
    """
    Начисление рефереру за успешную оплату привлечённого пользователя.

    Один платёж = одна запись (уникальность по payment_id).
    """

    __tablename__ = "referral_payouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    amount_rub: Mapped[float] = mapped_column(Float, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_telegram_id])

    __table_args__ = (
        Index("idx_referral_payouts_referrer_paid", "referrer_telegram_id", "paid_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReferralPayout(referrer={self.referrer_telegram_id}, "
            f"user={self.user_telegram_id}, amount={self.amount_rub} RUB)>"
        )
