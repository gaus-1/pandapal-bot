"""
SQLAlchemy модели для PandaPal
Описывают структуру таблиц базы данных
@module bot.models
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""

    pass


class User(Base):
    """
    Модель пользователя (ребёнок, родитель или учитель)

    Связи:
    - parent: родитель этого пользователя (если user_type='child')
    - children: дети этого родителя (если user_type='parent')
    - sessions: учебные сессии пользователя
    - progress: прогресс по предметам
    - messages: история чата с AI
    """

    __tablename__ = "users"

    # Первичный ключ
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Telegram ID (уникальный идентификатор из Telegram)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,  # Индекс для быстрого поиска
        comment="Уникальный Telegram ID пользователя",
    )

    # Данные пользователя из Telegram
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Возраст и класс (для детей)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Тип пользователя: child, parent, teacher
    user_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="child",
        comment="Роль: child/parent/teacher",
    )

    # Связь с родителем (для детей)
    parent_telegram_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="SET NULL"),
        nullable=True,
        comment="Telegram ID родителя (если user_type=child)",
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="Дата регистрации"
    )

    # Статус активности
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", comment="Активен ли пользователь"
    )

    # Relationships (связи с другими таблицами)
    parent: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[telegram_id],
        foreign_keys=[parent_telegram_id],
        back_populates="children",
    )

    children: Mapped[List["User"]] = relationship(
        "User", back_populates="parent", foreign_keys=[parent_telegram_id]
    )

    sessions: Mapped[List["LearningSession"]] = relationship(
        "LearningSession", back_populates="user", cascade="all, delete-orphan"
    )

    progress: Mapped[List["UserProgress"]] = relationship(
        "UserProgress", back_populates="user", cascade="all, delete-orphan"
    )

    messages: Mapped[List["ChatHistory"]] = relationship(
        "ChatHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="ChatHistory.timestamp.desc()",
    )

    # Constraints (ограничения)
    __table_args__ = (
        CheckConstraint(
            "user_type IN ('child', 'parent', 'teacher')", name="ck_users_user_type"
        ),
        CheckConstraint(
            "age IS NULL OR (age >= 6 AND age <= 18)", name="ck_users_age_range"
        ),
        CheckConstraint(
            "grade IS NULL OR (grade >= 1 AND grade <= 11)", name="ck_users_grade_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, type={self.user_type})>"


class LearningSession(Base):
    """
    Модель учебной сессии (один урок/тест)
    Хранит информацию о процессе обучения
    """

    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Связь с пользователем
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Telegram ID ученика",
    )

    # Информация о сессии
    subject: Mapped[Optional[str]] = mapped_column(
        String(100), comment="Предмет (математика, русский и т.д.)"
    )

    topic: Mapped[Optional[str]] = mapped_column(String(255), comment="Тема урока")

    difficulty_level: Mapped[Optional[int]] = mapped_column(
        Integer, comment="Уровень сложности (1-5)"
    )

    # Статистика
    questions_answered: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="Количество отвеченных вопросов"
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="Количество правильных ответов"
    )

    # Временные метки
    session_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="Начало сессии"
    )

    session_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Конец сессии"
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", comment="Завершена ли сессия"
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user_date", "user_telegram_id", "session_start"),
    )

    def __repr__(self) -> str:
        return f"<LearningSession(id={self.id}, subject={self.subject})>"


class UserProgress(Base):
    """
    Модель прогресса пользователя по предметам
    Хранит уровень, очки и достижения
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
    subject: Mapped[Optional[str]] = mapped_column(String(100), comment="Предмет")

    level: Mapped[Optional[int]] = mapped_column(
        Integer, comment="Текущий уровень владения (1-10)"
    )

    # Геймификация
    points: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="Накопленные очки"
    )

    achievements: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="Достижения (JSON: {achievement_id: date_earned})"
    )

    # Последняя активность
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последней активности",
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="progress")

    __table_args__ = (
        Index("idx_progress_user_subject", "user_telegram_id", "subject"),
    )

    def __repr__(self) -> str:
        return f"<UserProgress(user_id={self.user_telegram_id}, subject={self.subject}, level={self.level})>"


class ChatHistory(Base):
    """
    Модель истории чата с AI
    Хранит последние 50 сообщений для контекста
    """

    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Связь с пользователем
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Telegram ID пользователя",
    )

    # Содержание сообщения
    message_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Текст сообщения"
    )

    # Тип сообщения: user, ai, system
    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Тип: user (от ребёнка) / ai (от PandaPal) / system (служебное)",
    )

    # Временная метка
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,  # Индекс для сортировки по дате
        comment="Дата и время сообщения",
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="messages")

    __table_args__ = (
        # Составной индекс для быстрой выборки последних N сообщений пользователя
        Index("idx_chat_history_user_time", "user_telegram_id", "timestamp"),
        CheckConstraint(
            "message_type IN ('user', 'ai', 'system')", name="ck_chat_message_type"
        ),
    )

    def __repr__(self) -> str:
        preview = (
            self.message_text[:50] + "..."
            if len(self.message_text) > 50
            else self.message_text
        )
        return (
            f"<ChatHistory(id={self.id}, type={self.message_type}, text='{preview}')>"
        )
