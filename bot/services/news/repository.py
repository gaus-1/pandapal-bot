"""
Репозиторий для работы с новостями в БД.

Реализует паттерн Repository для изоляции логики доступа к данным.
"""

from typing import Any

from loguru import logger
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from bot.models.news import News


class NewsRepository:
    """
    Репозиторий для работы с новостями в БД.

    Предоставляет методы для сохранения и получения новостей
    с поддержкой фильтрации по категории, возрасту, классу.
    """

    def __init__(self, db: Session):
        """
        Инициализация репозитория.

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db

    def save(self, news_data: dict[str, Any]) -> News:
        """
        Сохранить новость в БД.

        Args:
            news_data: Данные новости в формате словаря

        Returns:
            News: Сохраненная новость
        """
        try:
            news = News(
                title=news_data.get("title", ""),
                content=news_data.get("content", ""),
                url=news_data.get("url"),
                source=news_data.get("source", "unknown"),
                category=news_data.get("category", "события"),
                age_min=news_data.get("age_min"),
                age_max=news_data.get("age_max"),
                grade_min=news_data.get("grade_min"),
                grade_max=news_data.get("grade_max"),
                published_date=news_data.get("published_date"),
                is_active=news_data.get("is_active", True),
                is_moderated=news_data.get("is_moderated", False),
                image_url=news_data.get("image_url"),
            )

            self.db.add(news)
            self.db.flush()

            logger.info(f"✅ Новость сохранена: id={news.id}, category={news.category}")
            return news

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения новости: {e}")
            self.db.rollback()
            raise

    def find_by_category(
        self, category: str, age: int | None = None, grade: int | None = None, limit: int = 10
    ) -> list[News]:
        """
        Найти новости по категории с фильтрацией по возрасту/классу.

        Args:
            category: Категория новости
            age: Возраст ребенка (для фильтрации)
            grade: Класс ребенка (для фильтрации)
            limit: Максимальное количество новостей

        Returns:
            List[News]: Список новостей
        """
        try:
            query = select(News).where(
                and_(
                    News.category == category,
                    News.is_active == True,  # noqa: E712
                    News.is_moderated == True,  # noqa: E712
                )
            )

            # Фильтрация по возрасту
            if age is not None:
                query = query.where(
                    or_(
                        News.age_min.is_(None),
                        News.age_min <= age,
                    )
                ).where(
                    or_(
                        News.age_max.is_(None),
                        News.age_max >= age,
                    )
                )

            # Фильтрация по классу
            if grade is not None:
                query = query.where(
                    or_(
                        News.grade_min.is_(None),
                        News.grade_min <= grade,
                    )
                ).where(
                    or_(
                        News.grade_max.is_(None),
                        News.grade_max >= grade,
                    )
                )

            query = query.order_by(News.published_date.desc().nullslast(), News.created_at.desc())
            query = query.limit(limit)

            result = self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"❌ Ошибка поиска новостей по категории: {e}")
            return []

    def find_by_age(self, age: int, limit: int = 10) -> list[News]:
        """
        Найти новости для указанного возраста.

        Args:
            age: Возраст ребенка
            limit: Максимальное количество новостей

        Returns:
            List[News]: Список новостей
        """
        try:
            query = (
                select(News)
                .where(
                    and_(
                        News.is_active == True,  # noqa: E712
                        News.is_moderated == True,  # noqa: E712
                        or_(
                            News.age_min.is_(None),
                            News.age_min <= age,
                        ),
                        or_(
                            News.age_max.is_(None),
                            News.age_max >= age,
                        ),
                    )
                )
                .order_by(News.published_date.desc().nullslast(), News.created_at.desc())
                .limit(limit)
            )

            result = self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"❌ Ошибка поиска новостей по возрасту: {e}")
            return []

    def find_by_grade(self, grade: int, limit: int = 10) -> list[News]:
        """
        Найти новости для указанного класса.

        Args:
            grade: Класс ребенка
            limit: Максимальное количество новостей

        Returns:
            List[News]: Список новостей
        """
        try:
            query = (
                select(News)
                .where(
                    and_(
                        News.is_active == True,  # noqa: E712
                        News.is_moderated == True,  # noqa: E712
                        or_(
                            News.grade_min.is_(None),
                            News.grade_min <= grade,
                        ),
                        or_(
                            News.grade_max.is_(None),
                            News.grade_max >= grade,
                        ),
                    )
                )
                .order_by(News.published_date.desc().nullslast(), News.created_at.desc())
                .limit(limit)
            )

            result = self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"❌ Ошибка поиска новостей по классу: {e}")
            return []

    def find_recent(self, limit: int = 10) -> list[News]:
        """
        Найти последние новости.

        Args:
            limit: Максимальное количество новостей

        Returns:
            List[News]: Список новостей
        """
        try:
            query = (
                select(News)
                .where(News.is_active == True)  # noqa: E712
                .order_by(News.published_date.desc().nullslast(), News.created_at.desc())
                .limit(limit)
            )

            result = self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"❌ Ошибка поиска последних новостей: {e}")
            return []

    def count_all(self) -> int:
        """
        Подсчитать общее количество новостей в БД.

        Returns:
            int: Количество новостей
        """
        try:
            from sqlalchemy import func

            query = select(func.count(News.id))
            result = self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"❌ Ошибка подсчета новостей: {e}")
            return 0
