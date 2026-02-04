"""
Сервис учебных сессий: создание, обновление и завершение по таймауту неактивности.

Одна учебная сессия = непрерывный период образовательных вопросов пользователя.
Сессия завершается при отсутствии образовательных вопросов SESSION_IDLE_MINUTES минут.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.models import LearningSession

SESSION_IDLE_MINUTES = 30


class LearningSessionService:
    """Управление учебными сессиями пользователя."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_active_session(self, user_telegram_id: int) -> LearningSession | None:
        """
        Возвращает активную сессию пользователя (не завершённую и не старше SESSION_IDLE_MINUTES).
        Если последняя сессия старше порога — помечает её завершённой и возвращает None.
        """
        cutoff = datetime.now(UTC) - timedelta(minutes=SESSION_IDLE_MINUTES)
        stmt = (
            select(LearningSession)
            .where(
                LearningSession.user_telegram_id == user_telegram_id,
                LearningSession.is_completed.is_(False),
            )
            .order_by(LearningSession.session_start.desc())
            .limit(1)
        )
        session = self._db.execute(stmt).scalar_one_or_none()
        if session is None:
            return None
        # SQLite возвращает naive datetime — нормализуем для сравнения
        session_start = session.session_start
        if session_start.tzinfo is None:
            session_start = session_start.replace(tzinfo=UTC)
        if session_start < cutoff:
            session.is_completed = True
            session.session_end = datetime.now(UTC)
            self._db.flush()
            return None
        return session

    def record_educational_question(
        self,
        user_telegram_id: int,
        subject: str | None = None,
    ) -> None:
        """
        Учитывает один образовательный вопрос: создаёт новую сессию или обновляет активную.
        """
        active = self.get_active_session(user_telegram_id)
        if active:
            active.questions_answered += 1
            self._db.flush()
            return
        new_session = LearningSession(
            user_telegram_id=user_telegram_id,
            subject=subject,
            questions_answered=1,
            correct_answers=0,
            is_completed=False,
        )
        self._db.add(new_session)
        self._db.flush()
