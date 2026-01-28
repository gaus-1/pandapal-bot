"""
Сервис бонусных уроков для Premium пользователей (годовая подписка).

Предоставляет доступ к эксклюзивным бонусным урокам для VIP пользователей.
"""

from sqlalchemy.orm import Session

from bot.services.premium_features_service import PremiumFeaturesService


class BonusLesson:
    """Бонусный урок."""

    def __init__(  # noqa: D107
        self,
        id: str,
        title: str,
        description: str,
        subject: str,
        difficulty: str,
        duration_minutes: int,
        content: str,
    ):
        self.id = id
        self.title = title
        self.description = description
        self.subject = subject
        self.difficulty = difficulty
        self.duration_minutes = duration_minutes
        self.content = content


# Бонусные уроки (только для годовой подписки)
BONUS_LESSONS = [
    BonusLesson(
        id="bonus_math_advanced",
        title="Продвинутая математика",
        description="Секреты решения сложных задач",
        subject="математика",
        difficulty="advanced",
        duration_minutes=30,
        content="Углубленный курс по решению олимпиадных задач по математике...",
    ),
    BonusLesson(
        id="bonus_russian_creative",
        title="Творческое письмо",
        description="Как писать интересные сочинения",
        subject="русский",
        difficulty="intermediate",
        duration_minutes=25,
        content="Мастер-класс по написанию сочинений и эссе...",
    ),
    BonusLesson(
        id="bonus_english_fluency",
        title="Разговорный английский",
        description="Секреты беглой речи",
        subject="английский",
        difficulty="advanced",
        duration_minutes=35,
        content="Курс по развитию разговорных навыков английского языка...",
    ),
    BonusLesson(
        id="bonus_science_experiments",
        title="Научные эксперименты",
        description="Домашние опыты по физике и химии",
        subject="физика",
        difficulty="intermediate",
        duration_minutes=40,
        content="Безопасные эксперименты, которые можно провести дома...",
    ),
]


class BonusLessonsService:
    """
    Сервис бонусных уроков.

    Предоставляет доступ к эксклюзивным урокам для VIP пользователей.
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса.

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db
        self.premium_service = PremiumFeaturesService(db)

    def can_access_bonus_lessons(self, telegram_id: int) -> bool:
        """
        Проверка доступа к бонусным урокам.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            bool: True если доступ разрешен (только годовая подписка)
        """
        return self.premium_service.can_access_bonus_lessons(telegram_id)

    def get_available_lessons(self, telegram_id: int) -> list[dict]:
        """
        Получить список доступных бонусных уроков.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            List[Dict]: Список доступных уроков
        """
        if not self.can_access_bonus_lessons(telegram_id):
            return []

        return [
            {
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.description,
                "subject": lesson.subject,
                "difficulty": lesson.difficulty,
                "duration_minutes": lesson.duration_minutes,
            }
            for lesson in BONUS_LESSONS
        ]

    def get_lesson_content(self, telegram_id: int, lesson_id: str) -> dict | None:
        """
        Получить содержание урока.

        Args:
            telegram_id: Telegram ID пользователя
            lesson_id: ID урока

        Returns:
            Optional[Dict]: Содержание урока или None
        """
        if not self.can_access_bonus_lessons(telegram_id):
            return None

        lesson = next(
            (lesson_item for lesson_item in BONUS_LESSONS if lesson_item.id == lesson_id), None
        )
        if not lesson:
            return None

        return {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "subject": lesson.subject,
            "difficulty": lesson.difficulty,
            "duration_minutes": lesson.duration_minutes,
            "content": lesson.content,
        }
