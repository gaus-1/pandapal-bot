"""
SQLAlchemy модели для PandaPal
"""

from datetime import datetime
from typing import Dict, List, Optional

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
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""

    pass


class User(Base):
    """
    Модель пользователя системы PandaPal.
    Хранит информацию о детях и родителях.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)

    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    user_type: Mapped[str] = mapped_column(String(20), nullable=False, default="child")
    parent_telegram_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

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
        CheckConstraint("user_type IN ('child', 'parent')", name="ck_users_user_type"),
        CheckConstraint("age IS NULL OR (age >= 6 AND age <= 18)", name="ck_users_age_range"),
        CheckConstraint(
            "grade IS NULL OR (grade >= 1 AND grade <= 11)", name="ck_users_grade_range"
        ),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
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
    )

    # Информация о сессии
    subject: Mapped[Optional[str]] = mapped_column(String(100))

    topic: Mapped[Optional[str]] = mapped_column(String(255))

    difficulty_level: Mapped[Optional[int]] = mapped_column(Integer)

    # Статистика
    questions_answered: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    correct_answers: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Временные метки
    session_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    __table_args__ = (Index("idx_sessions_user_date", "user_telegram_id", "session_start"),)

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
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
    subject: Mapped[Optional[str]] = mapped_column(String(100))

    level: Mapped[Optional[int]] = mapped_column(Integer)

    # Геймификация
    points: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    achievements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Последняя активность
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="progress")

    __table_args__ = (Index("idx_progress_user_subject", "user_telegram_id", "subject"),)

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return f"<UserProgress(user_id={self.user_telegram_id}, subject={self.subject}, level={self.level})>"


class ChatHistory(Base):
    """
    Модель истории чата с AI
    Хранит историю сообщений для контекста
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
        index=True,  # Индекс для сортировки по дате
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="messages")

    __table_args__ = (
        # Составной индекс для быстрой выборки последних N сообщений пользователя
        Index("idx_chat_history_user_time", "user_telegram_id", "timestamp"),
        CheckConstraint("message_type IN ('user', 'ai', 'system')", name="ck_chat_message_type"),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        preview = (
            self.message_text[:50] + "..." if len(self.message_text) > 50 else self.message_text
        )
        return f"<ChatHistory(id={self.id}, type={self.message_type}, text='{preview}')>"


# ============ МОДЕЛИ АНАЛИТИКИ ============


class AnalyticsMetric(Base):
    """
    Модель для хранения аналитических метрик
    Собирает различные показатели производительности и использования
    """

    __tablename__ = "analytics_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tags: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    user_telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        Index("idx_analytics_metrics_name_time", "metric_name", "timestamp"),
        Index("idx_analytics_metrics_user_time", "user_telegram_id", "timestamp"),
        Index("idx_analytics_metrics_period", "period"),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return (
            f"<AnalyticsMetric(id={self.id}, name='{self.metric_name}', "
            f"value={self.metric_value}, type='{self.metric_type}')>"
        )


class UserSession(Base):
    """
    Модель для хранения пользовательских сессий
    Отслеживает активность пользователей во времени
    """

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    session_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    session_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    session_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_interactions: Mapped[int] = mapped_column(Integer, default=0)
    voice_messages: Mapped[int] = mapped_column(Integer, default=0)
    blocked_messages: Mapped[int] = mapped_column(Integer, default=0)
    subjects_covered: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    engagement_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    safety_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    session_type: Mapped[str] = mapped_column(String(50), default="regular")
    device_info: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_user_sessions_user_start", "user_telegram_id", "session_start"),
        Index("idx_user_sessions_duration", "session_duration"),
        Index("idx_user_sessions_type", "session_type"),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return (
            f"<UserSession(id={self.id}, user={self.user_telegram_id}, "
            f"start='{self.session_start}', duration={self.session_duration})>"
        )


class UserEvent(Base):
    """
    Модель для хранения событий пользователей
    Логирует важные события в системе
    """

    __tablename__ = "user_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    session_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    importance: Mapped[str] = mapped_column(String(20), default="normal")
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_user_events_user_time", "user_telegram_id", "timestamp"),
        Index("idx_user_events_type", "event_type"),
        Index("idx_user_events_importance", "importance"),
        Index("idx_user_events_processed", "processed"),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return (
            f"<UserEvent(id={self.id}, user={self.user_telegram_id}, "
            f"type='{self.event_type}', importance='{self.importance}')>"
        )


class AnalyticsReport(Base):
    """
    Модель для хранения аналитических отчетов
    Сохраняет сгенерированные отчеты для родителей и администраторов
    """

    __tablename__ = "analytics_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_period: Mapped[str] = mapped_column(String(20), nullable=False)
    report_data: Mapped[Dict] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    generated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parent_telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    child_telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_analytics_reports_type_period", "report_type", "report_period"),
        Index("idx_analytics_reports_parent", "parent_telegram_id"),
        Index("idx_analytics_reports_generated", "generated_at"),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return (
            f"<AnalyticsReport(id={self.id}, type='{self.report_type}', "
            f"period='{self.report_period}', generated='{self.generated_at}')>"
        )


class AnalyticsTrend(Base):
    """
    Модель для хранения трендов и прогнозов
    Анализирует изменения метрик во времени
    """

    __tablename__ = "analytics_trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    trend_direction: Mapped[str] = mapped_column(String(20), nullable=False)
    trend_strength: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prediction_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_analytics_trends_metric", "metric_name"),
        Index("idx_analytics_trends_period", "period_start", "period_end"),
        Index("idx_analytics_trends_confidence", "confidence"),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return (
            f"<AnalyticsTrend(id={self.id}, metric='{self.metric_name}', "
            f"direction='{self.trend_direction}', strength={self.trend_strength:.2f})>"
        )


class AnalyticsAlert(Base):
    """
    Модель для хранения алертов и уведомлений
    Управляет системой оповещений о важных событиях
    """

    __tablename__ = "analytics_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    alert_level: Mapped[str] = mapped_column(String(20), nullable=False)
    alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    alert_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parent_telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    child_telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_analytics_alerts_type_level", "alert_type", "alert_level"),
        Index("idx_analytics_alerts_parent", "parent_telegram_id"),
        Index("idx_analytics_alerts_triggered", "triggered_at"),
        Index("idx_analytics_alerts_resolved", "resolved_at"),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return (
            f"<AnalyticsAlert(id={self.id}, type='{self.alert_type}', "
            f"level='{self.alert_level}', triggered='{self.triggered_at}')>"
        )


class AnalyticsConfig(Base):
    """
    Модель для хранения конфигурации аналитики
    Управляет настройками системы аналитики
    """

    __tablename__ = "analytics_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config_value: Mapped[Dict] = mapped_column(JSON, nullable=False)
    config_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_analytics_config_key", "config_key"),
        # Уникальный индекс на ключ конфигурации
        Index("uq_analytics_config_key", "config_key", unique=True),
    )

    def __repr__(self) -> str:
        """Строковое представление пользователя"""
        return (
            f"<AnalyticsConfig(id={self.id}, key='{self.config_key}', "
            f"type='{self.config_type}', updated='{self.updated_at}')>"
        )
