"""
Модели игр: сессии и статистика.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


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

    game_type: Mapped[str] = mapped_column(String(50), nullable=False)
    game_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    best_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
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
