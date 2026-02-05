"""
Модели пользователей и их прогресса.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from .chat import ChatHistory
    from .learning import LearningSession, UserProgress
    from .payments import Subscription


class User(Base):
    """
    Модель пользователя системы PandaPal.

    Хранит информацию о детях и родителях, включая профильные данные,
    связи между родителями и детьми, и статистику активности.

    Attributes:
        id: Уникальный идентификатор пользователя в БД.
        telegram_id: ID пользователя в Telegram (уникальный).
        username: Username пользователя в Telegram.
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        age: Возраст ребенка (для детских аккаунтов).
        grade: Класс обучения (1-9).
        user_type: Тип пользователя ('child').
        parent_telegram_id: ID родителя (не используется, оставлено для совместимости БД).
        created_at: Дата создания аккаунта.
        is_active: Статус активности аккаунта.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)

    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user_type: Mapped[str] = mapped_column(String(20), nullable=False, default="child")
    parent_telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=True
    )
    referrer_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Активность и напоминания
    message_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_activity: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_name_mention_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    skip_name_asking: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    non_educational_questions_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    panda_lazy_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Отдых панды: предложение игры после N ответов подряд
    consecutive_since_rest: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    rest_offers_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    last_ai_was_rest: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Пол пользователя для грамматически корректных формулировок (male / female / None)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    parent: Mapped[User | None] = relationship(
        "User",
        remote_side=[telegram_id],
        foreign_keys=[parent_telegram_id],
        back_populates="children",
    )

    children: Mapped[list[User]] = relationship(
        "User", back_populates="parent", foreign_keys=[parent_telegram_id]
    )

    sessions: Mapped[list[LearningSession]] = relationship(
        "LearningSession", back_populates="user", cascade="all, delete-orphan"
    )

    progress: Mapped[list[UserProgress]] = relationship(
        "UserProgress", back_populates="user", cascade="all, delete-orphan"
    )

    messages: Mapped[list[ChatHistory]] = relationship(
        "ChatHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="ChatHistory.timestamp.desc()",
    )

    subscriptions: Mapped[list[Subscription]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Subscription.created_at.desc()",
    )

    # Constraints (ограничения)
    __table_args__ = (
        CheckConstraint("user_type IN ('child', 'parent')", name="ck_users_user_type"),
        CheckConstraint("age IS NULL OR (age >= 6 AND age <= 18)", name="ck_users_age_range"),
        CheckConstraint(
            "grade IS NULL OR (grade >= 1 AND grade <= 11)", name="ck_users_grade_range"
        ),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, type={self.user_type})>"

    @property
    def is_premium(self) -> bool:
        """Активна ли Premium подписка (по premium_until или активной подписке)."""
        now = datetime.now(UTC)
        if self.premium_until:
            pt = self.premium_until
            if pt.tzinfo is None:
                pt = pt.replace(tzinfo=UTC)
            if pt > now:
                return True
        if self.subscriptions:
            for sub in self.subscriptions:
                if sub.is_active and sub.expires_at:
                    exp = sub.expires_at
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=UTC)
                    if exp > now:
                        return True
        return False

    @property
    def full_name(self) -> str:
        """Полное имя (first_name + last_name)."""
        parts = [self.first_name, self.last_name] if self.last_name else [self.first_name]
        return " ".join(p or "" for p in parts).strip() or ""

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        now = datetime.now(UTC)
        is_premium = False
        premium_days_left = None

        if self.premium_until:
            premium_until = self.premium_until
            if premium_until.tzinfo is None:
                premium_until = premium_until.replace(tzinfo=UTC)
            is_premium = premium_until > now
            if is_premium:
                delta = premium_until - now
                premium_days_left = delta.days

        # Получаем активную подписку если есть
        active_subscription = None
        if self.subscriptions:
            for sub in self.subscriptions:
                if sub.is_active:
                    expires_at = sub.expires_at
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=UTC)
                    if expires_at > now:
                        active_subscription = sub.to_dict()
                        break

        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "grade": self.grade,
            "user_type": self.user_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "premium_until": self.premium_until.isoformat() if self.premium_until else None,
            "is_premium": is_premium,
            "premium_days_left": premium_days_left,
            "active_subscription": active_subscription,
        }


class UserProgress(Base):
    """
    Модель прогресса пользователя по предметам.
    Хранит уровень, очки и достижения.
    """

    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Связь с пользователем
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Предмет и уровень
    subject: Mapped[str] = mapped_column(String(100), nullable=False, default="general")

    level: Mapped[int | None] = mapped_column(Integer)

    # Адаптивное обучение
    difficulty_level: Mapped[int | None] = mapped_column(Integer, server_default="1")
    mastery_score: Mapped[float | None] = mapped_column(Float, server_default="0.0")

    # Геймификация
    points: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    achievements: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Последняя активность
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship
    user: Mapped[User] = relationship("User", back_populates="progress")

    __table_args__ = (Index("idx_progress_user_subject", "user_telegram_id", "subject"),)

    def __repr__(self) -> str:
        """Строковое представление прогресса пользователя"""
        return f"<UserProgress(user_id={self.user_telegram_id}, subject={self.subject}, level={self.level})>"

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        return {
            "subject": self.subject,
            "level": self.level,
            "difficulty_level": self.difficulty_level,
            "mastery_score": self.mastery_score,
            "points": self.points,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "achievements": self.achievements or {},
        }
