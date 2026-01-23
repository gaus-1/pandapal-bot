"""
Модели обучения: сессии, проблемные темы, домашние задания.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
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


class LearningSession(Base):
    """
    Модель учебной сессии (один урок/тест).
    Хранит информацию о процессе обучения.
    """

    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Связь с пользователем
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Информация о сессии
    subject: Mapped[str | None] = mapped_column(String(100))
    topic: Mapped[str | None] = mapped_column(String(255))
    difficulty_level: Mapped[int | None] = mapped_column(Integer)

    # Статистика
    questions_answered: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Временные метки
    session_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    session_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Relationship
    user: Mapped[User] = relationship("User", back_populates="sessions")

    __table_args__ = (Index("idx_sessions_user_date", "user_telegram_id", "session_start"),)

    def __repr__(self) -> str:
        """Строковое представление учебной сессии"""
        return f"<LearningSession(id={self.id}, subject={self.subject})>"


class ProblemTopic(Base):
    """
    Модель проблемных тем для адаптивного обучения.
    Отслеживает темы, в которых пользователь допускает ошибки.
    """

    __tablename__ = "problem_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Связь с пользователем
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Предмет и тема
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)

    # Статистика ошибок
    error_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    total_attempts: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )

    # Временные метки
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    # Relationship
    user: Mapped[User] = relationship("User")

    __table_args__ = (
        Index("idx_problem_topics_user", "user_telegram_id"),
        Index("idx_problem_topics_subject", "subject"),
        Index("idx_problem_topics_error_count", "error_count"),
        Index("idx_problem_topics_last_error", "last_error_at"),
        Index(
            "uq_problem_topics_user_subject_topic",
            "user_telegram_id",
            "subject",
            "topic",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        """Строковое представление проблемной темы"""
        return f"<ProblemTopic(user={self.user_telegram_id}, subject={self.subject}, topic={self.topic}, errors={self.error_count})>"

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        error_rate = (
            (self.error_count / self.total_attempts * 100) if self.total_attempts > 0 else 0.0
        )
        return {
            "id": self.id,
            "subject": self.subject,
            "topic": self.topic,
            "error_count": self.error_count,
            "total_attempts": self.total_attempts,
            "error_rate": round(error_rate, 1),
            "last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
            "last_reviewed_at": self.last_reviewed_at.isoformat()
            if self.last_reviewed_at
            else None,
        }


class HomeworkSubmission(Base):
    """
    Модель проверки домашних заданий.
    Хранит информацию о проверенных ДЗ через фото.
    """

    __tablename__ = "homework_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Связь с пользователем
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Фото задания
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Предмет и тема
    subject: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # OCR и анализ
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Результаты проверки
    has_errors: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    errors_found: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Временная метка
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    user: Mapped[User] = relationship("User")

    __table_args__ = (
        Index("idx_homework_submissions_user", "user_telegram_id"),
        Index("idx_homework_submissions_subject", "subject"),
        Index("idx_homework_submissions_submitted", "submitted_at"),
        Index("idx_homework_submissions_has_errors", "has_errors"),
    )

    def __repr__(self) -> str:
        """Строковое представление проверки ДЗ"""
        return f"<HomeworkSubmission(user={self.user_telegram_id}, subject={self.subject}, has_errors={self.has_errors})>"

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        return {
            "id": self.id,
            "subject": self.subject,
            "topic": self.topic,
            "has_errors": self.has_errors,
            "errors_found": self.errors_found or [],
            "ai_feedback": self.ai_feedback,
            "score": self.score,
            "max_score": self.max_score,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }
