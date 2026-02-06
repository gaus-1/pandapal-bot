"""
Модель питомца-панды (тамагочи).

Один питомец на пользователя. Состояние пересчитывается по времени при каждом запросе.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .user import User


class PandaPet(Base):
    """
    Питомец-панда пользователя.

    Шкалы: hunger, mood, energy (0-100, минимум 5-10 по требованию).
    Decay: голод раз в час, настроение раз в 2 часа, энергия от еды и сна.
    """

    __tablename__ = "panda_pet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    hunger: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    mood: Mapped[int] = mapped_column(SmallInteger, default=70, nullable=False)
    energy: Mapped[int] = mapped_column(SmallInteger, default=50, nullable=False)

    last_fed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_slept_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    feed_count_since_hour_start: Mapped[int] = mapped_column(
        SmallInteger, default=0, nullable=False
    )
    feed_hour_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    total_fed_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    total_played_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    consecutive_visit_days: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    last_visit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    achievements: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_telegram_id])

    __table_args__ = (Index("idx_panda_pet_user", "user_telegram_id"),)

    def __repr__(self) -> str:
        return f"<PandaPet(user={self.user_telegram_id}, hunger={self.hunger}, mood={self.mood})>"
