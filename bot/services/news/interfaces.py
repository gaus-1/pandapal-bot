"""
Интерфейсы для работы с новостями (Interface Segregation Principle).

Каждый интерфейс определяет минимальный набор методов для конкретной задачи.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from bot.models.news import News


class INewsSource(ABC):
    """
    Интерфейс источника новостей.

    Определяет контракт для получения новостей из различных источников.
    """

    @abstractmethod
    async def fetch_news(self, limit: int = 10) -> list[dict]:
        """
        Получить новости из источника.

        Args:
            limit: Максимальное количество новостей

        Returns:
            List[dict]: Список новостей в формате:
                {
                    "title": str,
                    "content": str,
                    "url": str | None,
                    "source": str,
                    "published_date": datetime | None,
                    "image_url": str | None,
                }
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Получить название источника."""
        pass


class INewsAdapter(ABC):
    """
    Интерфейс адаптации новостей под возраст.

    Определяет контракт для адаптации контента под возраст ребенка.
    """

    @abstractmethod
    async def adapt_content(
        self, content: str, age: int | None = None, grade: int | None = None
    ) -> str:
        """
        Адаптировать контент под возраст ребенка.

        Args:
            content: Исходный текст новости
            age: Возраст ребенка (6-15)
            grade: Класс ребенка (1-9)

        Returns:
            str: Адаптированный текст
        """
        pass


class INewsModerator(ABC):
    """
    Интерфейс модерации новостей.

    Определяет контракт для проверки безопасности контента.
    """

    @abstractmethod
    async def moderate(self, news_item: dict) -> tuple[bool, str]:
        """
        Проверить новость на безопасность.

        Args:
            news_item: Новость в формате словаря

        Returns:
            tuple[bool, str]: (is_safe, reason)
                - is_safe: True если новость безопасна
                - reason: Причина отклонения (если is_safe=False)
        """
        pass


class INewsRepository(Protocol):
    """
    Интерфейс репозитория для работы с БД.

    Определяет контракт для сохранения и получения новостей.
    """

    def save(self, news: News) -> News:
        """Сохранить новость в БД."""
        ...

    def find_by_category(
        self, category: str, age: int | None = None, grade: int | None = None, limit: int = 10
    ) -> list[News]:
        """Найти новости по категории с фильтрацией по возрасту/классу."""
        ...

    def find_by_age(self, age: int, limit: int = 10) -> list[News]:
        """Найти новости для указанного возраста."""
        ...

    def find_by_grade(self, grade: int, limit: int = 10) -> list[News]:
        """Найти новости для указанного класса."""
        ...

    def find_recent(self, limit: int = 10) -> list[News]:
        """Найти последние новости."""
        ...
