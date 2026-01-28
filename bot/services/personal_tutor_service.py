"""
Сервис персонального плана обучения для Premium пользователей.

Создает персональный план обучения на основе активности пользователя,
его успехов и предпочтений.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bot.models import ChatHistory, User


class PersonalTutorService:
    """
    Сервис персонального плана обучения.

    Создает и управляет персональным планом обучения для Premium пользователей.
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса.

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db

    def get_learning_plan(self, telegram_id: int) -> dict:
        """
        Получить персональный план обучения.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict: Персональный план обучения
        """
        # Получаем пользователя
        user = self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()

        if not user:
            return {"error": "User not found"}

        # Анализируем активность пользователя
        activity = self._analyze_user_activity(telegram_id)

        # Определяем слабые места
        weak_subjects = self._identify_weak_subjects(telegram_id)

        # Рекомендации по предметам
        recommendations = self._generate_recommendations(activity, weak_subjects, user)

        return {
            "user_id": telegram_id,
            "grade": user.grade,
            "age": user.age,
            "activity_summary": activity,
            "weak_subjects": weak_subjects,
            "recommendations": recommendations,
            "weekly_goals": self._generate_weekly_goals(activity, user),
            "created_at": datetime.utcnow().isoformat(),
        }

    def _analyze_user_activity(self, telegram_id: int) -> dict:
        """Анализ активности пользователя."""
        # Подсчет сообщений за последние 7 дней
        week_ago = datetime.utcnow() - timedelta(days=7)

        messages_count = (
            self.db.scalar(
                select(func.count(ChatHistory.id))
                .where(ChatHistory.user_telegram_id == telegram_id)
                .where(ChatHistory.timestamp >= week_ago)
            )
            or 0
        )

        # Подсчет вопросов
        questions_count = (
            self.db.scalar(
                select(func.count(ChatHistory.id))
                .where(ChatHistory.user_telegram_id == telegram_id)
                .where(ChatHistory.message_type == "user")
                .where(ChatHistory.message_text.like("%?%"))
                .where(ChatHistory.timestamp >= week_ago)
            )
            or 0
        )

        # Определяем наиболее активные предметы
        all_messages = (
            self.db.execute(
                select(ChatHistory.message_text)
                .where(ChatHistory.user_telegram_id == telegram_id)
                .where(ChatHistory.message_type == "user")
                .where(ChatHistory.timestamp >= week_ago)
            )
            .scalars()
            .all()
        )

        subject_keywords = {
            "математика": ["математик", "алгебр", "геометр", "уравнен", "задач", "пример"],
            "русский": ["русск", "грамматик", "орфограф", "пунктуац"],
            "английский": ["английск", "english", "grammar"],
            "физика": ["физик", "механик", "электричеств"],
            "химия": ["хими", "реакц", "элемент"],
            "биология": ["биолог", "растен", "животн"],
        }

        subject_activity = {}
        for subject, keywords in subject_keywords.items():
            count = sum(1 for msg in all_messages if any(kw in msg.lower() for kw in keywords))
            if count > 0:
                subject_activity[subject] = count

        return {
            "messages_last_week": messages_count,
            "questions_last_week": questions_count,
            "subject_activity": subject_activity,
        }

    def _identify_weak_subjects(self, telegram_id: int) -> list[str]:
        """Определение слабых предметов."""
        # Анализируем вопросы по предметам
        activity = self._analyze_user_activity(telegram_id)
        subject_activity = activity.get("subject_activity", {})

        # Если по предмету мало активности - это слабое место
        weak_subjects = []
        for subject, count in subject_activity.items():
            if count < 3:  # Меньше 3 упоминаний за неделю
                weak_subjects.append(subject)

        return weak_subjects

    def _generate_recommendations(
        self, activity: dict, weak_subjects: list[str], user: User
    ) -> list[dict]:
        """Генерация рекомендаций."""
        recommendations = []

        # Рекомендации по слабым предметам
        if weak_subjects:
            recommendations.append(
                {
                    "type": "weak_subject",
                    "title": "Улучши знания по предметам",
                    "description": f"Рекомендуем больше практиковаться: {', '.join(weak_subjects)}",
                    "priority": "high",
                }
            )

        # Рекомендации по активности
        if activity.get("messages_last_week", 0) < 10:
            recommendations.append(
                {
                    "type": "activity",
                    "title": "Увеличь активность",
                    "description": "Попробуй задавать больше вопросов для лучшего прогресса",
                    "priority": "medium",
                }
            )

        # Рекомендации по возрасту/классу
        if user.grade:
            if user.grade <= 4:
                recommendations.append(
                    {
                        "type": "grade",
                        "title": "Основа основ",
                        "description": "Сфокусируйся на математике, русском и чтении",
                        "priority": "high",
                    }
                )
            elif user.grade >= 7:
                recommendations.append(
                    {
                        "type": "grade",
                        "title": "Подготовка к экзаменам",
                        "description": "Начни готовиться к ОГЭ/ЕГЭ заранее",
                        "priority": "medium",
                    }
                )

        return recommendations

    def _generate_weekly_goals(self, activity: dict, user: User) -> list[dict]:  # noqa: ARG002
        """Генерация недельных целей."""
        goals = []

        # Цель по активности
        current_activity = activity.get("messages_last_week", 0)
        goals.append(
            {
                "type": "messages",
                "current": current_activity,
                "target": max(20, current_activity + 5),
                "description": "Задавай больше вопросов",
            }
        )

        # Цель по предметам
        subject_activity = activity.get("subject_activity", {})
        if len(subject_activity) < 3:
            goals.append(
                {
                    "type": "subjects",
                    "current": len(subject_activity),
                    "target": 3,
                    "description": "Изучи 3 разных предмета",
                }
            )

        return goals
