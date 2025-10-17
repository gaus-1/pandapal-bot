"""
Сервис для работы с пользователями
CRUD операции, регистрация, получение данных

"""

from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.config import MAX_AGE, MAX_GRADE, MIN_AGE, MIN_GRADE
from bot.models import User


class UserService:
    """
    Сервис управления пользователями
    Регистрация, обновление данных, получение информации
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
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """
        Получить существующего пользователя или создать нового
        Используется при первом запуске бота (/start)

        Args:
            telegram_id: Telegram ID пользователя
            username: Username из Telegram
            first_name: Имя из Telegram
            last_name: Фамилия из Telegram

        Returns:
            User: Объект пользователя
        """
        # Ищем существующего пользователя
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = self.db.execute(stmt).scalar_one_or_none()

        if user:
            # Пользователь найден — обновляем данные из Telegram (могли измениться)
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True

            logger.info(f"👤 Существующий пользователь: {telegram_id} ({first_name})")
        else:
            # Создаём нового пользователя
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                user_type="child",  # По умолчанию — ребёнок
                is_active=True,
            )

            self.db.add(user)
            self.db.flush()  # Получаем ID

            logger.info(f"✨ Новый пользователь зарегистрирован: {telegram_id} ({first_name})")

        return user

    def update_user_profile(
        self,
        telegram_id: int,
        age: Optional[int] = None,
        grade: Optional[int] = None,
        user_type: Optional[str] = None,
    ) -> Optional[User]:
        """
        Обновить профиль пользователя

        Args:
            telegram_id: Telegram ID
            age: Возраст (6-18)
            grade: Класс (1-11)
            user_type: Тип пользователя (child/parent)

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
            if user_type not in ["child", "parent"]:
                raise ValueError("user_type должен быть child/parent")
            user.user_type = user_type

        self.db.flush()
        logger.info(f"📝 Профиль обновлён: {telegram_id}")

        return user

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получить пользователя по Telegram ID

        Args:
            telegram_id: Telegram ID

        Returns:
            User: Пользователь или None
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def link_parent_to_child(self, child_telegram_id: int, parent_telegram_id: int) -> bool:
        """
        Связать родителя с ребёнком
        Используется для родительского контроля

        Args:
            child_telegram_id: Telegram ID ребёнка
            parent_telegram_id: Telegram ID родителя

        Returns:
            bool: True если успешно
        """
        child = self.get_user_by_telegram_id(child_telegram_id)
        parent = self.get_user_by_telegram_id(parent_telegram_id)

        if not child or not parent:
            logger.error(
                f"❌ Пользователь не найден: child={child_telegram_id}, parent={parent_telegram_id}"
            )
            return False

        # Проверяем типы пользователей
        if child.user_type != "child":
            logger.error(f"❌ {child_telegram_id} не является ребёнком")
            return False

        if parent.user_type != "parent":
            logger.error(f"❌ {parent_telegram_id} не является родителем")
            return False

        # Связываем
        child.parent_telegram_id = parent_telegram_id
        self.db.flush()

        logger.info(f"👨‍👧 Родитель {parent_telegram_id} связан с ребёнком {child_telegram_id}")

        return True

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
