"""
Сервис управления предпочтениями пользователей новостного бота.

Сохранение возраста, класса, категорий и истории прочитанных новостей.
"""

from typing import Any

from loguru import logger
from sqlalchemy import JSON, BigInteger, Boolean, Column, Integer, Table, insert, select, update
from sqlalchemy.orm import Session

from bot.models.base import Base

# Таблица для хранения предпочтений пользователей новостного бота
# Используем отдельную таблицу, чтобы не модифицировать основную таблицу users
news_user_preferences = Table(
    "news_user_preferences",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("user_telegram_id", BigInteger, nullable=False, unique=True, index=True),
    Column("age", Integer, nullable=True),
    Column("grade", Integer, nullable=True),
    Column("categories", JSON, nullable=True),  # Список выбранных категорий
    Column("read_news_ids", JSON, nullable=True),  # ID прочитанных новостей
    Column("daily_notifications", Boolean, default=False, server_default="false"),
)


class UserPreferencesService:
    """
    Сервис управления предпочтениями пользователей.

    Сохраняет настройки пользователя для персонализации новостей.
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса.

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db

    def get_or_create_preferences(self, telegram_id: int) -> dict[str, Any]:
        """
        Получить или создать предпочтения пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            dict: Предпочтения пользователя
        """
        try:
            stmt = select(news_user_preferences).where(
                news_user_preferences.c.user_telegram_id == telegram_id
            )
            result = self.db.execute(stmt).first()

            if result:
                return dict(result._mapping)
            else:
                # Создаем новые предпочтения
                self.db.execute(
                    insert(news_user_preferences).values(
                        user_telegram_id=telegram_id,
                        categories=[],
                        read_news_ids=[],
                    )
                )
                self.db.commit()

                return {
                    "user_telegram_id": telegram_id,
                    "age": None,
                    "grade": None,
                    "categories": [],
                    "read_news_ids": [],
                    "daily_notifications": False,
                }

        except Exception as e:
            logger.error(f"❌ Ошибка получения предпочтений: {e}")
            self.db.rollback()
            return {
                "user_telegram_id": telegram_id,
                "age": None,
                "grade": None,
                "categories": [],
                "read_news_ids": [],
                "daily_notifications": False,
            }

    def update_age(self, telegram_id: int, age: int) -> bool:
        """
        Обновить возраст пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            age: Возраст (6-15)

        Returns:
            bool: True если обновлено
        """
        try:
            if not (6 <= age <= 15):
                logger.warning(f"⚠️ Некорректный возраст: {age}")
                return False

            self.db.execute(
                update(news_user_preferences)
                .where(news_user_preferences.c.user_telegram_id == telegram_id)
                .values(age=age)
            )
            self.db.commit()

            logger.info(f"✅ Возраст обновлен: user={telegram_id}, age={age}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления возраста: {e}")
            self.db.rollback()
            return False

    def update_grade(self, telegram_id: int, grade: int) -> bool:
        """
        Обновить класс пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            grade: Класс (1-9)

        Returns:
            bool: True если обновлено
        """
        try:
            if not (1 <= grade <= 9):
                logger.warning(f"⚠️ Некорректный класс: {grade}")
                return False

            from sqlalchemy import update

            self.db.execute(
                update(news_user_preferences)
                .where(news_user_preferences.c.user_telegram_id == telegram_id)
                .values(grade=grade)
            )
            self.db.commit()

            logger.info(f"✅ Класс обновлен: user={telegram_id}, grade={grade}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления класса: {e}")
            self.db.rollback()
            return False

    def update_categories(self, telegram_id: int, categories: list[str]) -> bool:
        """
        Обновить выбранные категории.

        Args:
            telegram_id: Telegram ID пользователя
            categories: Список категорий

        Returns:
            bool: True если обновлено
        """
        try:
            self.db.execute(
                update(news_user_preferences)
                .where(news_user_preferences.c.user_telegram_id == telegram_id)
                .values(categories=categories)
            )
            self.db.commit()

            logger.info(f"✅ Категории обновлены: user={telegram_id}, categories={categories}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления категорий: {e}")
            self.db.rollback()
            return False

    def mark_news_read(self, telegram_id: int, news_id: int) -> bool:
        """
        Отметить новость как прочитанную.

        Args:
            telegram_id: Telegram ID пользователя
            news_id: ID новости

        Returns:
            bool: True если обновлено
        """
        try:
            prefs = self.get_or_create_preferences(telegram_id)
            read_ids = prefs.get("read_news_ids", [])

            if news_id not in read_ids:
                read_ids.append(news_id)
                # Ограничиваем историю последними 100 новостями
                read_ids = read_ids[-100:]

                self.db.execute(
                    update(news_user_preferences)
                    .where(news_user_preferences.c.user_telegram_id == telegram_id)
                    .values(read_news_ids=read_ids)
                )
                self.db.commit()

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка отметки новости: {e}")
            self.db.rollback()
            return False

    def is_news_read(self, telegram_id: int, news_id: int) -> bool:
        """
        Проверить, прочитана ли новость.

        Args:
            telegram_id: Telegram ID пользователя
            news_id: ID новости

        Returns:
            bool: True если новость прочитана
        """
        try:
            prefs = self.get_or_create_preferences(telegram_id)
            read_ids = prefs.get("read_news_ids", [])
            return news_id in read_ids

        except Exception as e:
            logger.error(f"❌ Ошибка проверки новости: {e}")
            return False
