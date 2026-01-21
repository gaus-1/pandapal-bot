"""
Модели базы данных для PandaPal Bot.

Этот модуль содержит все SQLAlchemy модели для хранения данных приложения.
Включает модели для пользователей, истории чатов, достижений и базы знаний.

Все модели наследуются от DeclarativeBase и используют современный синтаксис
Mapped для типизации полей.
"""

from datetime import UTC, datetime
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
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.

    Все модели приложения наследуются от этого класса для обеспечения
    единообразной структуры и поведения.
    """

    pass


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

    parent: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[telegram_id],
        foreign_keys=[parent_telegram_id],
        back_populates="children",
    )

    children: Mapped[list["User"]] = relationship(
        "User", back_populates="parent", foreign_keys=[parent_telegram_id]
    )

    sessions: Mapped[list["LearningSession"]] = relationship(
        "LearningSession", back_populates="user", cascade="all, delete-orphan"
    )

    progress: Mapped[list["UserProgress"]] = relationship(
        "UserProgress", back_populates="user", cascade="all, delete-orphan"
    )

    messages: Mapped[list["ChatHistory"]] = relationship(
        "ChatHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="ChatHistory.timestamp.desc()",
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
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

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        from datetime import datetime

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
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    __table_args__ = (Index("idx_sessions_user_date", "user_telegram_id", "session_start"),)

    def __repr__(self) -> str:
        """Строковое представление учебной сессии"""
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
    user: Mapped["User"] = relationship("User", back_populates="progress")

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
        index=True,  # Индекс для сортировки по дате
    )

    # URL изображения визуализации (base64 data URL для графиков/таблиц)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="messages")

    __table_args__ = (
        # Составной индекс для быстрой выборки последних N сообщений пользователя
        Index("idx_chat_history_user_time", "user_telegram_id", "timestamp"),
        CheckConstraint("message_type IN ('user', 'ai', 'system')", name="ck_chat_message_type"),
    )

    def __repr__(self) -> str:
        """Строковое представление истории чата"""
        preview = (
            self.message_text[:50] + "..." if len(self.message_text) > 50 else self.message_text
        )
        return f"<ChatHistory(id={self.id}, type={self.message_type}, text='{preview}')>"


# МОДЕЛИ АНАЛИТИКИ


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
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    user_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        Index("idx_analytics_metrics_name_time", "metric_name", "timestamp"),
        Index("idx_analytics_metrics_user_time", "user_telegram_id", "timestamp"),
        Index("idx_analytics_metrics_period", "period"),
    )

    def __repr__(self) -> str:
        """Строковое представление аналитической метрики"""
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
    session_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_interactions: Mapped[int] = mapped_column(Integer, default=0)
    voice_messages: Mapped[int] = mapped_column(Integer, default=0)
    blocked_messages: Mapped[int] = mapped_column(Integer, default=0)
    subjects_covered: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    safety_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    session_type: Mapped[str] = mapped_column(String(50), default="regular")
    device_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_user_sessions_user_start", "user_telegram_id", "session_start"),
        Index("idx_user_sessions_duration", "session_duration"),
        Index("idx_user_sessions_type", "session_type"),
    )

    def __repr__(self) -> str:
        """Строковое представление пользовательской сессии"""
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
    event_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    session_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    importance: Mapped[str] = mapped_column(String(20), default="normal")
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_user_events_user_time", "user_telegram_id", "timestamp"),
        Index("idx_user_events_type", "event_type"),
        Index("idx_user_events_importance", "importance"),
        Index("idx_user_events_processed", "processed"),
    )

    def __repr__(self) -> str:
        """Строковое представление события пользователя"""
        return (
            f"<UserEvent(id={self.id}, user={self.user_telegram_id}, "
            f"type='{self.event_type}', importance='{self.importance}')>"
        )


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


class AnalyticsReport(Base):
    """
    Модель для хранения аналитических отчетов
    Сохраняет сгенерированные отчеты для родителей и администраторов
    """

    __tablename__ = "analytics_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_period: Mapped[str] = mapped_column(String(20), nullable=False)
    report_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    generated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    child_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_analytics_reports_type_period", "report_type", "report_period"),
        Index("idx_analytics_reports_parent", "parent_telegram_id"),
        Index("idx_analytics_reports_generated", "generated_at"),
    )

    def __repr__(self) -> str:
        """Строковое представление аналитического отчета"""
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
    prediction_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
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
        """Строковое представление аналитического тренда"""
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
    alert_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    child_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_analytics_alerts_type_level", "alert_type", "alert_level"),
        Index("idx_analytics_alerts_parent", "parent_telegram_id"),
        Index("idx_analytics_alerts_triggered", "triggered_at"),
        Index("idx_analytics_alerts_resolved", "resolved_at"),
    )

    def __repr__(self) -> str:
        """Строковое представление аналитического алерта"""
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
    config_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    config_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        """Строковое представление конфигурации аналитики"""
        return (
            f"<AnalyticsConfig(id={self.id}, key='{self.config_key}', "
            f"type='{self.config_type}', updated='{self.updated_at}')>"
        )


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
    payment_method: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 'stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other'
    payment_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # ID платежа в ЮKassa или Telegram

    # Сохраненный метод оплаты для автоплатежа (ЮKassa)
    saved_payment_method_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # ID сохраненного метода оплаты в ЮKassa для автоплатежа

    # Автоплатеж
    auto_renew: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )  # Автоматическое продление подписки

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
    payment_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )  # Уникальный ID от ЮKassa или Telegram

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

    payment_method: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other'

    plan_id: Mapped[str] = mapped_column(String(20), nullable=False)  # 'month', 'year'

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # 'pending', 'succeeded', 'cancelled', 'failed'

    payment_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Дополнительные данные платежа
    webhook_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Полные данные webhook для отладки

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Дата успешной оплаты

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


# МОДЕЛИ ИГР


class GameSession(Base):
    """
    Модель игровой сессии.
    Хранит информацию о каждой партии игры пользователя.
    """

    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    game_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'tic_tac_toe', 'checkers', '2048'
    game_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Состояние игры (JSON)
    result: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 'win', 'loss', 'draw', 'in_progress'
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Финальный счет (для 2048)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", foreign_keys=[user_telegram_id])

    __table_args__ = (
        Index("idx_game_sessions_user_type", "user_telegram_id", "game_type"),
        Index("idx_game_sessions_started", "started_at"),
        CheckConstraint(
            "game_type IN ('tic_tac_toe', 'checkers', '2048', 'erudite')",
            name="ck_game_sessions_game_type",
        ),
        CheckConstraint(
            "result IS NULL OR result IN ('win', 'loss', 'draw', 'in_progress')",
            name="ck_game_sessions_result",
        ),
    )

    def __repr__(self) -> str:
        """Строковое представление игровой сессии"""
        return (
            f"<GameSession(id={self.id}, user={self.user_telegram_id}, "
            f"game={self.game_type}, result={self.result})>"
        )

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        return {
            "id": self.id,
            "game_type": self.game_type,
            "game_state": self.game_state,
            "result": self.result,
            "score": self.score,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
        }


class GameStats(Base):
    """
    Модель статистики игр пользователя.
    Агрегированная статистика по каждой игре.
    """

    __tablename__ = "game_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    game_type: Mapped[str] = mapped_column(String(50), nullable=False)
    total_games: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    wins: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    losses: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    draws: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    best_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Для 2048
    total_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    last_played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    user: Mapped["User"] = relationship("User", foreign_keys=[user_telegram_id])

    __table_args__ = (
        Index("idx_game_stats_user_type", "user_telegram_id", "game_type"),
        Index("idx_game_stats_updated", "updated_at"),
        CheckConstraint(
            "game_type IN ('tic_tac_toe', 'checkers', '2048', 'erudite')",
            name="ck_game_stats_game_type",
        ),
        # Уникальность: один статистика на пользователя + тип игры
        Index("uq_game_stats_user_type", "user_telegram_id", "game_type", unique=True),
    )

    def __repr__(self) -> str:
        """Строковое представление статистики игры"""
        return (
            f"<GameStats(user={self.user_telegram_id}, game={self.game_type}, "
            f"wins={self.wins}, losses={self.losses})>"
        )

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        win_rate = (self.wins / self.total_games * 100) if self.total_games > 0 else 0.0

        return {
            "game_type": self.game_type,
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "win_rate": round(win_rate, 1),
            "best_score": self.best_score,
            "total_score": self.total_score,
            "last_played_at": self.last_played_at.isoformat() if self.last_played_at else None,
        }


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
    user: Mapped["User"] = relationship("User")

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
    user: Mapped["User"] = relationship("User")

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
