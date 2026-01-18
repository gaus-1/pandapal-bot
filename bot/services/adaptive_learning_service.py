"""
Сервис адаптивного обучения для PandaPal Bot.

Реализует систему отслеживания проблемных тем, автоматического определения уровня сложности
и рекомендации по повторению материала.

Основные возможности:
- Отслеживание ошибок по темам
- Определение проблемных тем для повторения
- Автоматическая оценка уровня сложности
- Рекомендации по повторению проблемных тем
"""

from datetime import UTC, datetime

import sqlalchemy as sa
from loguru import logger
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from bot.models import ProblemTopic, UserProgress


class AdaptiveLearningService:
    """Сервис адаптивного обучения для отслеживания проблемных тем и уровня сложности"""

    def __init__(self, db: Session):
        """
        Инициализация сервиса.

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db

    def record_error(
        self, telegram_id: int, subject: str, topic: str, is_error: bool = True
    ) -> ProblemTopic:
        """
        Записать ошибку по теме для адаптивного обучения.

        Args:
            telegram_id: Telegram ID пользователя
            subject: Предмет (математика, русский и т.д.)
            topic: Тема (например, "дроби", "таблица умножения")
            is_error: True если была ошибка, False если правильный ответ

        Returns:
            ProblemTopic: Запись проблемной темы
        """
        # Ищем существующую запись
        stmt = select(ProblemTopic).where(
            and_(
                ProblemTopic.user_telegram_id == telegram_id,
                ProblemTopic.subject == subject,
                ProblemTopic.topic == topic,
            )
        )
        problem_topic = self.db.scalar(stmt)

        now = datetime.now(UTC)

        if not problem_topic:
            # Создаем новую запись
            problem_topic = ProblemTopic(
                user_telegram_id=telegram_id,
                subject=subject,
                topic=topic,
                error_count=1 if is_error else 0,
                total_attempts=1,
                last_error_at=now if is_error else None,
            )
            self.db.add(problem_topic)
        else:
            # Обновляем существующую
            problem_topic.total_attempts += 1
            if is_error:
                problem_topic.error_count += 1
                problem_topic.last_error_at = now
            problem_topic.updated_at = now

        self.db.flush()

        logger.debug(
            f"📝 Записана ошибка: user={telegram_id}, subject={subject}, topic={topic}, "
            f"error_count={problem_topic.error_count}/{problem_topic.total_attempts}"
        )

        return problem_topic

    def get_problem_topics(
        self, telegram_id: int, limit: int = 10, min_error_rate: float = 0.3
    ) -> list[ProblemTopic]:
        """
        Получить проблемные темы для пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            limit: Максимальное количество тем
            min_error_rate: Минимальный процент ошибок (0.0-1.0)

        Returns:
            List[ProblemTopic]: Список проблемных тем
        """
        stmt = (
            select(ProblemTopic)
            .where(ProblemTopic.user_telegram_id == telegram_id)
            .where(ProblemTopic.total_attempts > 0)
            .order_by(
                (
                    func.cast(ProblemTopic.error_count, sa.Float)
                    / func.nullif(ProblemTopic.total_attempts, 0)
                ).desc(),
                ProblemTopic.last_error_at.desc().nullslast(),
            )
            .limit(limit)
        )

        topics = list(self.db.scalars(stmt).all())

        # Фильтруем по минимальному проценту ошибок
        filtered_topics = []
        for topic in topics:
            error_rate = (
                topic.error_count / topic.total_attempts if topic.total_attempts > 0 else 0.0
            )
            if error_rate >= min_error_rate:
                filtered_topics.append(topic)

        return filtered_topics

    def mark_topic_reviewed(self, telegram_id: int, subject: str, topic: str) -> bool:
        """
        Отметить тему как повторенную.

        Args:
            telegram_id: Telegram ID пользователя
            subject: Предмет
            topic: Тема

        Returns:
            bool: True если тема найдена и обновлена
        """
        stmt = select(ProblemTopic).where(
            and_(
                ProblemTopic.user_telegram_id == telegram_id,
                ProblemTopic.subject == subject,
                ProblemTopic.topic == topic,
            )
        )
        problem_topic = self.db.scalar(stmt)

        if problem_topic:
            problem_topic.last_reviewed_at = datetime.now(UTC)
            problem_topic.updated_at = problem_topic.last_reviewed_at
            self.db.flush()
            return True

        return False

    def get_user_difficulty_level(self, telegram_id: int, subject: str) -> int:
        """
        Получить текущий уровень сложности для пользователя по предмету.

        Args:
            telegram_id: Telegram ID пользователя
            subject: Предмет

        Returns:
            int: Уровень сложности (1-5, где 1 - легкий, 5 - сложный)
        """
        # Получаем прогресс пользователя по предмету
        stmt = select(UserProgress).where(
            and_(
                UserProgress.user_telegram_id == telegram_id,
                UserProgress.subject == subject,
            )
        )
        progress = self.db.scalar(stmt)

        if progress and progress.difficulty_level:
            return progress.difficulty_level

        # Если уровня нет, вычисляем на основе проблемных тем
        problem_topics = self.get_problem_topics(telegram_id, limit=20)

        # Вычисляем средний процент ошибок
        total_errors = sum(t.error_count for t in problem_topics)
        total_attempts = sum(t.total_attempts for t in problem_topics)

        if total_attempts == 0:
            return 1  # Начинающий уровень

        error_rate = total_errors / total_attempts

        # Определяем уровень на основе процента ошибок
        if error_rate < 0.1:
            difficulty = 5  # Очень легко
        elif error_rate < 0.2:
            difficulty = 4  # Легко
        elif error_rate < 0.4:
            difficulty = 3  # Средне
        elif error_rate < 0.6:
            difficulty = 2  # Сложно
        else:
            difficulty = 1  # Очень сложно (много ошибок)

        # Сохраняем уровень в прогресс
        if not progress:
            progress = UserProgress(
                user_telegram_id=telegram_id,
                subject=subject,
                level=1,
                difficulty_level=difficulty,
            )
            self.db.add(progress)
        else:
            progress.difficulty_level = difficulty

        self.db.flush()

        return difficulty

    def update_mastery_score(self, telegram_id: int, subject: str) -> float:
        """
        Обновить оценку освоения предмета (mastery score).

        Args:
            telegram_id: Telegram ID пользователя
            subject: Предмет

        Returns:
            float: Оценка освоения (0.0-1.0)
        """
        # Получаем все проблемные темы по предмету
        stmt = (
            select(ProblemTopic)
            .where(
                and_(
                    ProblemTopic.user_telegram_id == telegram_id,
                    ProblemTopic.subject == subject,
                )
            )
            .where(ProblemTopic.total_attempts > 0)
        )
        topics = list(self.db.scalars(stmt).all())

        if not topics:
            mastery_score = 1.0  # Если нет данных, считаем полное освоение
        else:
            # Вычисляем средний процент правильных ответов
            total_correct = sum(t.total_attempts - t.error_count for t in topics)
            total_attempts = sum(t.total_attempts for t in topics)
            mastery_score = total_correct / total_attempts if total_attempts > 0 else 1.0

        # Сохраняем в прогресс
        stmt = select(UserProgress).where(
            and_(
                UserProgress.user_telegram_id == telegram_id,
                UserProgress.subject == subject,
            )
        )
        progress = self.db.scalar(stmt)

        if not progress:
            progress = UserProgress(
                user_telegram_id=telegram_id,
                subject=subject,
                level=1,
                mastery_score=mastery_score,
            )
            self.db.add(progress)
        else:
            progress.mastery_score = mastery_score

        self.db.flush()

        return mastery_score

    def get_recommendations_for_review(self, telegram_id: int, limit: int = 5) -> list[dict]:
        """
        Получить рекомендации по повторению проблемных тем.

        Args:
            telegram_id: Telegram ID пользователя
            limit: Максимальное количество рекомендаций

        Returns:
            List[Dict]: Список рекомендаций с темой и причиной
        """
        problem_topics = self.get_problem_topics(telegram_id, limit=limit * 2, min_error_rate=0.2)

        recommendations = []

        for topic in problem_topics[:limit]:
            error_rate = (
                topic.error_count / topic.total_attempts if topic.total_attempts > 0 else 0.0
            )

            # Определяем приоритет рекомендации
            if error_rate >= 0.6:
                priority = "high"
                reason = "Много ошибок по этой теме"
            elif error_rate >= 0.4:
                priority = "medium"
                reason = "Нужно повторить эту тему"
            else:
                priority = "low"
                reason = "Для закрепления материала"

            recommendations.append(
                {
                    "subject": topic.subject,
                    "topic": topic.topic,
                    "error_rate": round(error_rate * 100, 1),
                    "error_count": topic.error_count,
                    "total_attempts": topic.total_attempts,
                    "priority": priority,
                    "reason": reason,
                    "last_error_at": topic.last_error_at.isoformat()
                    if topic.last_error_at
                    else None,
                }
            )

        return recommendations

    def extract_topic_from_message(
        self, message_text: str, subject: str | None = None
    ) -> str | None:
        """
        Извлечь тему из сообщения пользователя (базовая реализация).

        Args:
            message_text: Текст сообщения
            subject: Предмет (если известен)

        Returns:
            Optional[str]: Извлеченная тема или None
        """
        # Базовая реализация - можно улучшить с помощью NLP
        message_lower = message_text.lower()

        # Ключевые слова для определения темы
        topic_keywords = {
            "дробь": "дроби",
            "уравнен": "уравнения",
            "геометр": "геометрия",
            "алгебр": "алгебра",
            "таблица умножения": "таблица умножения",
            "процент": "проценты",
            "степен": "степени",
            "корень": "корни",
            "тригонометр": "тригонометрия",
            "производн": "производные",
            "интеграл": "интегралы",
        }

        for keyword, topic in topic_keywords.items():
            if keyword in message_lower:
                return topic

        # Если не найдено, возвращаем общую тему
        if subject:
            return f"общие вопросы по {subject}"

        return None
