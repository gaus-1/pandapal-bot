"""Управление игровыми сессиями и статистикой."""

from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from bot.models import GameSession, GameStats
from bot.services.gamification_service import GamificationService


class GamesServiceBase:
    """Базовый класс: CRUD сессий, статистика, достижения."""

    def __init__(self, db: Session):  # noqa: D107
        from bot.services.game_ai import TicTacToeAI

        self.db = db
        self.tic_tac_toe_ai = TicTacToeAI(difficulty="medium")

    def create_game_session(
        self, telegram_id: int, game_type: str, initial_state: dict | None = None
    ) -> GameSession:
        """
        Создать новую игровую сессию.

        Args:
            telegram_id: Telegram ID пользователя
            game_type: Тип игры ('tic_tac_toe', 'checkers', '2048')
            initial_state: Начальное состояние игры

        Returns:
            GameSession: Созданная сессия
        """
        session = GameSession(
            user_telegram_id=telegram_id,
            game_type=game_type,
            game_state=initial_state or {},
            result="in_progress",
        )
        self.db.add(session)
        self.db.flush()
        logger.info(f"🎮 Создана игровая сессия: user={telegram_id}, game={game_type}")
        return session

    def update_game_session(
        self, session_id: int, game_state: dict, result: str | None = None
    ) -> GameSession:
        """
        Обновить игровую сессию.

        Args:
            session_id: ID сессии
            game_state: Новое состояние игры
            result: Результат ('win', 'loss', 'draw', 'in_progress')

        Returns:
            GameSession: Обновленная сессия
        """
        session = self.db.get(GameSession, session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        if game_state:
            if session.game_state is None:
                session.game_state = {}
            if isinstance(game_state, dict):
                # SQLAlchemy JSON требует явного присваивания нового объекта
                current_state = (
                    dict(session.game_state) if isinstance(session.game_state, dict) else {}
                )
                current_state.update(game_state)
                session.game_state = current_state
            else:
                session.game_state = game_state

        if result:
            session.result = result
            if result != "in_progress":
                session.finished_at = datetime.now(UTC)
                if session.started_at:
                    # Нормализуем timezone для обоих datetime
                    finished = session.finished_at
                    started = session.started_at
                    if finished.tzinfo is None:
                        finished = finished.replace(tzinfo=UTC)
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=UTC)
                    delta = finished - started
                    session.duration_seconds = int(delta.total_seconds())

        self.db.flush()
        return session

    def finish_game_session(
        self, session_id: int, result: str, score: int | None = None
    ) -> GameSession:
        """
        Завершить игровую сессию и обновить статистику.

        Args:
            session_id: ID сессии
            result: Результат ('win', 'loss', 'draw')
            score: Финальный счет (для 2048)

        Returns:
            GameSession: Завершенная сессия
        """
        session = self.update_game_session(session_id, {}, result)
        if score is not None:
            session.score = score

        # Обновляем статистику
        self._update_game_stats(session.user_telegram_id, session.game_type, result, score)

        # Проверяем достижения
        self._check_game_achievements(session.user_telegram_id, session.game_type, result)

        self.db.commit()
        logger.info(f"🎮 Игра завершена: session={session_id}, result={result}, score={score}")
        return session

    def _update_game_stats(
        self, telegram_id: int, game_type: str, result: str, score: int | None = None
    ) -> None:
        """Обновить статистику игры."""
        stmt = select(GameStats).where(
            and_(
                GameStats.user_telegram_id == telegram_id,
                GameStats.game_type == game_type,
            )
        )
        stats = self.db.scalar(stmt)

        if not stats:
            stats = GameStats(
                user_telegram_id=telegram_id,
                game_type=game_type,
                total_games=0,
                wins=0,
                losses=0,
                draws=0,
            )
            self.db.add(stats)

        stats.total_games += 1
        stats.last_played_at = datetime.now(UTC)

        if result == "win":
            stats.wins += 1
        elif result == "loss":
            stats.losses += 1
        elif result == "draw":
            stats.draws += 1

        if score is not None:
            if stats.total_score is None:
                stats.total_score = 0
            stats.total_score += score
            if stats.best_score is None or score > stats.best_score:
                stats.best_score = score

        self.db.flush()

    def _check_game_achievements(self, telegram_id: int, game_type: str, result: str) -> None:
        """Проверить и разблокировать игровые достижения."""
        gamification_service = GamificationService(self.db)

        # Получаем статистику игры (возвращает dict)
        stats = self.get_game_stats(telegram_id, game_type)

        # Проверяем достижения за победы
        if result == "win":
            wins = stats.get("wins", 0)
            if wins >= 1:
                gamification_service.check_and_unlock_achievements(telegram_id)

        # "Сыграл 100 партий"
        total_games = stats.get("total_games", 0)
        if total_games >= 100:
            gamification_service.check_and_unlock_achievements(telegram_id)

    def get_game_stats(self, telegram_id: int, game_type: str | None = None) -> dict:
        """
        Получить статистику игр пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            game_type: Тип игры (опционально)

        Returns:
            Dict: Статистика игры или всех игр
        """
        if game_type:
            stmt = select(GameStats).where(
                and_(
                    GameStats.user_telegram_id == telegram_id,
                    GameStats.game_type == game_type,
                )
            )
            stats = self.db.scalar(stmt)
            if stats:
                return stats.to_dict()
            return {
                "game_type": game_type,
                "total_games": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_rate": 0.0,
                "best_score": None,
                "total_score": 0,
                "last_played_at": None,
            }

        # Все игры
        stmt = select(GameStats).where(GameStats.user_telegram_id == telegram_id)
        all_stats = self.db.scalars(stmt).all()

        result = {}
        for stats in all_stats:
            result[stats.game_type] = stats.to_dict()

        return result

    def get_recent_sessions(
        self, telegram_id: int, game_type: str | None = None, limit: int = 10
    ) -> list[GameSession]:
        """
        Получить последние игровые сессии.

        Args:
            telegram_id: Telegram ID пользователя
            game_type: Тип игры (опционально)
            limit: Количество сессий

        Returns:
            List[GameSession]: Список сессий
        """
        stmt = (
            select(GameSession)
            .where(GameSession.user_telegram_id == telegram_id)
            .order_by(GameSession.started_at.desc())
            .limit(limit)
        )

        if game_type:
            stmt = stmt.where(GameSession.game_type == game_type)

        return list(self.db.scalars(stmt).all())
