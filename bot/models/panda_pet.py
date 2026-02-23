"""
Модель виртуального питомца «Моя панда» (тамагочи).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

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
    Модель питомца панды для пользователя.
    Хранит hunger, mood, energy и лимиты кормления/игры/сна.
    """

    __tablename__ = "panda_pet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    hunger: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="60")
    mood: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="70")
    energy: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="50")

    last_fed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_slept_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_toilet_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_climb_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_fall_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    feed_count_since_hour_start: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    feed_hour_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_fed_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_played_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    consecutive_visit_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_visit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    achievements: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_telegram_id])

    __table_args__ = (Index("idx_panda_pet_user", "user_telegram_id"),)

    def __repr__(self) -> str:
        return (
            f"<PandaPet(id={self.id}, user={self.user_telegram_id}, "
            f"hunger={self.hunger}, mood={self.mood}, energy={self.energy})>"
        )
