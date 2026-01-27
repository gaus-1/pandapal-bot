"""
Модели для хранения новостей для детского новостного бота.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    pass


class News(Base):
    """
    Модель новости для детского новостного бота.

    Хранит новости, адаптированные для детей 6-15 лет (1-9 класс).
    Новости проходят модерацию и адаптацию под возраст ребенка.

    Attributes:
        id: Уникальный идентификатор новости.
        title: Заголовок новости.
        content: Текст новости (адаптированный для детей).
        url: Ссылка на оригинальный источник.
        source: Источник новости (world_news_api, newsapi, mel_fm, deti_mail_ru, umorashka_ru).
        category: Категория новости (игры, мода, образование, еда, спорт, животные, природа, факты, события, приколы).
        age_min: Минимальный возраст (6-15).
        age_max: Максимальный возраст (6-15).
        grade_min: Минимальный класс (1-9).
        grade_max: Максимальный класс (1-9).
        published_date: Дата публикации оригинальной новости.
        created_at: Дата создания записи в БД.
        is_active: Активна ли новость (показывать ли пользователям).
        is_moderated: Прошла ли новость модерацию.
        image_url: URL изображения (опционально).
    """

    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Основная информация
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Категория
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Фильтрация по возрасту и классу
    age_min: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    age_max: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    grade_min: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    grade_max: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Даты
    published_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Статусы
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False, index=True
    )
    is_moderated: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Медиа
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_news_category_active", "category", "is_active"),
        Index("idx_news_age_range", "age_min", "age_max"),
        Index("idx_news_grade_range", "grade_min", "grade_max"),
        Index("idx_news_published_date", "published_date"),
        Index("idx_news_created_at", "created_at"),
        CheckConstraint(
            "category IN ('игры', 'мода', 'образование', 'еда', 'спорт', 'животные', 'природа', 'факты', 'события', 'приколы')",
            name="ck_news_category",
        ),
        CheckConstraint(
            "age_min IS NULL OR (age_min >= 6 AND age_min <= 15)",
            name="ck_news_age_min",
        ),
        CheckConstraint(
            "age_max IS NULL OR (age_max >= 6 AND age_max <= 15)",
            name="ck_news_age_max",
        ),
        CheckConstraint(
            "grade_min IS NULL OR (grade_min >= 1 AND grade_min <= 9)",
            name="ck_news_grade_min",
        ),
        CheckConstraint(
            "grade_max IS NULL OR (grade_max >= 1 AND grade_max <= 9)",
            name="ck_news_grade_max",
        ),
    )

    def __repr__(self) -> str:
        """Строковое представление новости"""
        preview = self.title[:50] + "..." if len(self.title) > 50 else self.title
        return (
            f"<News(id={self.id}, category={self.category}, "
            f"title='{preview}', active={self.is_active})>"
        )

    def to_dict(self) -> dict:
        """Преобразование модели в словарь для API"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "age_min": self.age_min,
            "age_max": self.age_max,
            "grade_min": self.grade_min,
            "grade_max": self.grade_max,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "is_moderated": self.is_moderated,
            "image_url": self.image_url,
        }
