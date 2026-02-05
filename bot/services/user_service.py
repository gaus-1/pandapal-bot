"""
Сервис для работы с пользователями.

Обеспечивает CRUD операции для управления пользователями:
регистрация, обновление профиля, получение данных пользователя.
"""

from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.config import MAX_AGE, MAX_GRADE, MIN_AGE, MIN_GRADE
from bot.interfaces import IUserService
from bot.models import User


class UserService(IUserService):
    """
    Сервис управления пользователями.

    Обеспечивает полный цикл работы с пользователями:
    регистрация при первом запуске бота, обновление профиля,
    получение информации о пользователе и управление данными.
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db

    def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        referrer_telegram_id: int | None = None,
    ) -> User:
        """
        Получить существующего пользователя или создать нового.
        Реферер привязывается один раз (первый заход по ссылке).

        Args:
            telegram_id: Telegram ID пользователя
            username: Username из Telegram
            first_name: Имя из Telegram
            last_name: Фамилия из Telegram
            referrer_telegram_id: ID реферера (если заход по ref_<id>)

        Returns:
            User: Объект пользователя
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = self.db.execute(stmt).scalar_one_or_none()

        if user:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.last_activity = datetime.now(UTC)
            if referrer_telegram_id is not None and user.referrer_telegram_id is None:
                user.referrer_telegram_id = referrer_telegram_id
                logger.info(
                    "Referrer attached: user=%s referrer=%s",
                    telegram_id,
                    referrer_telegram_id,
                )
            logger.info(f"👤 Существующий пользователь: {telegram_id} ({first_name})")
        else:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                user_type="child",
                is_active=True,
                referrer_telegram_id=referrer_telegram_id,
            )
            self.db.add(user)
            self.db.flush()
            if referrer_telegram_id is not None:
                logger.info(
                    "New user with referrer: user=%s referrer=%s",
                    telegram_id,
                    referrer_telegram_id,
                )
            logger.info(f"✨ Новый пользователь зарегистрирован: {telegram_id} ({first_name})")

        return user

    def update_user_age(self, telegram_id: int, age: int) -> bool:
        """
        Обновить возраст пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            age: Возраст (6-18)

        Returns:
            bool: True если успешно обновлено
        """
        try:
            user = self.update_user_profile(telegram_id, age=age)
            return user is not None
        except ValueError:
            return False

    def update_user_grade(self, telegram_id: int, grade: int) -> bool:
        """
        Обновить класс пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            grade: Класс (1-11)

        Returns:
            bool: True если успешно обновлено
        """
        try:
            user = self.update_user_profile(telegram_id, grade=grade)
            return user is not None
        except ValueError:
            return False

    def update_user_profile(
        self,
        telegram_id: int,
        age: int | None = None,
        grade: int | None = None,
        user_type: str | None = None,
    ) -> User | None:
        """
        Обновить профиль пользователя

        Args:
            telegram_id: Telegram ID
            age: Возраст (6-18)
            grade: Класс (1-11)
            user_type: Тип пользователя (child)

        Returns:
            User: Обновлённый пользователь или None если не найден

        Raises:
            ValueError: Если данные некорректны
        """
        user = self.get_user_by_telegram_id(telegram_id)

        if not user:
            logger.error(f"❌ Пользователь {telegram_id} не найден")
            return None

        # Валидация возраста
        if age is not None:
            if age < MIN_AGE or age > MAX_AGE:
                raise ValueError(f"Возраст должен быть от {MIN_AGE} до {MAX_AGE} лет")
            user.age = age

        # Валидация класса
        if grade is not None:
            if grade < MIN_GRADE or grade > MAX_GRADE:
                raise ValueError(f"Класс должен быть от {MIN_GRADE} до {MAX_GRADE}")
            user.grade = grade

        # Обновление типа пользователя
        if user_type is not None:
            if user_type != "child":
                raise ValueError("user_type должен быть child")
            user.user_type = user_type

        self.db.flush()
        logger.info(f"📝 Профиль обновлён: {telegram_id}")

        return user

    def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        """
        Получить пользователя по Telegram ID

        Args:
            telegram_id: Telegram ID

        Returns:
            User: Пользователь или None
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_display_name(self, user: User) -> str:
        """
        Получить отображаемое имя пользователя

        Args:
            user: Объект пользователя

        Returns:
            str: Имя для отображения
        """
        if user.first_name:
            name = user.first_name
            if user.last_name:
                name += f" {user.last_name}"
            return name

        if user.username:
            return f"@{user.username}"

        return f"User{user.telegram_id}"

    def is_registered(self, telegram_id: int) -> bool:
        """
        Проверить, зарегистрирован ли пользователь

        Args:
            telegram_id: Telegram ID

        Returns:
            bool: True если пользователь существует
        """
        user = self.get_user_by_telegram_id(telegram_id)
        return user is not None

    def deactivate_user(self, telegram_id: int) -> bool:
        """
        Деактивировать пользователя (мягкое удаление)

        Args:
            telegram_id: Telegram ID

        Returns:
            bool: True если успешно
        """
        user = self.get_user_by_telegram_id(telegram_id)

        if not user:
            return False

        user.is_active = False
        self.db.flush()

        logger.info(f"🚫 Пользователь деактивирован: {telegram_id}")

        return True

    def increment_message_count(self, telegram_id: int) -> bool:
        """
        Увеличить счетчик сообщений и обновить активность пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            True если успешно, False иначе
        """
        try:
            stmt = select(User).where(User.telegram_id == telegram_id)
            user = self.db.execute(stmt).scalar_one_or_none()

            if user:
                user.message_count += 1
                user.last_activity = datetime.now(UTC)
                self.db.commit()
                logger.debug(f"✅ Счетчик сообщений: {user.message_count} для {telegram_id}")
                return True

            logger.warning(f"⚠️ Пользователь {telegram_id} не найден")
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка обновления счетчика для {telegram_id}: {e}")
            self.db.rollback()
            return False
