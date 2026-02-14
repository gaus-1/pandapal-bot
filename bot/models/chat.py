"""
Модели истории чата и счетчиков запросов.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .user import User


class ChatHistory(Base):
    """
    Модель истории чата с AI ассистентом.

    Хранит историю сообщений пользователя и ответов AI для обеспечения
    контекстного общения. Используется для построения контекста при генерации
    ответов и анализа активности пользователя.

    Attributes:
        id: Уникальный идентификатор записи.
        user_id: ID пользователя (FK на users.id).
        role: Роль отправителя ('user' или 'assistant').
        content: Текст сообщения.
        timestamp: Время отправки сообщения.
        tokens_used: Количество использованных токенов (для AI ответов).
    """

    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Связь с пользователем
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Содержание сообщения
    message_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Тип сообщения: user, ai, system
    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Временная метка
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    # URL изображения визуализации (base64 data URL для графиков/таблиц)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Реакция панды на фидбек пользователя (happy, eating, offended, questioning)
    panda_reaction: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="messages")

    __table_args__ = (
        Index("idx_chat_history_user_time", "user_telegram_id", "timestamp"),
        CheckConstraint("message_type IN ('user', 'ai', 'system')", name="ck_chat_message_type"),
    )

    def __repr__(self) -> str:
        """Строковое представление истории чата"""
        preview = (
            self.message_text[:50] + "..." if len(self.message_text) > 50 else self.message_text
        )
        return f"<ChatHistory(id={self.id}, type={self.message_type}, text='{preview}')>"


class DailyRequestCount(Base):
    """
    Модель для подсчета дневных AI запросов пользователя.

    Используется для контроля лимитов бесплатных пользователей.
    Не зависит от ChatHistory, поэтому не сбрасывается при очистке истории.

    Attributes:
        id: Уникальный идентификатор записи
        user_telegram_id: Telegram ID пользователя
        date: Дата запроса (только дата, без времени)
        request_count: Количество запросов за день
        last_request_at: Время последнего запроса
    """

    __tablename__ = "daily_request_counts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_request_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_daily_request_user_date", "user_telegram_id", "date", unique=True),
    )

    def __repr__(self) -> str:
        """Строковое представление счетчика запросов"""
        return (
            f"<DailyRequestCount(user={self.user_telegram_id}, "
            f"date={self.date.date()}, count={self.request_count})>"
        )
