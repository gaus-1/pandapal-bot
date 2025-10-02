"""
Базовые классы для сервисов
Реализация SOLID принципов и ООП паттернов
@module bot.services.base
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """
    Базовый класс для всех сервисов
    Реализует принцип единственной ответственности (SRP)
    и обеспечивает единообразный интерфейс
    """

    def __init__(self, db: Optional[Session] = None):
        """
        Инициализация базового сервиса

        Args:
            db: Сессия базы данных (опционально)
        """
        self.db = db

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Валидация входных данных
        Реализуется в наследниках

        Args:
            data: Данные для валидации

        Returns:
            bool: True если данные валидны
        """
        pass

    def log_operation(self, operation: str, **kwargs) -> None:
        """
        Логирование операций сервиса

        Args:
            operation: Название операции
            **kwargs: Дополнительные параметры
        """
        from loguru import logger
        logger.info(f"🔧 {self.__class__.__name__}: {operation}", **kwargs)


class DatabaseService(BaseService[T]):
    """
    Базовый сервис для работы с базой данных
    Реализует принцип открытости/закрытости (OCP)
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса БД

        Args:
            db: Сессия SQLAlchemy
        """
        super().__init__(db)

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> T:
        """
        Создание записи в БД

        Args:
            data: Данные для создания

        Returns:
            T: Созданный объект
        """
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Получение записи по ID

        Args:
            id: ID записи

        Returns:
            Optional[T]: Найденная запись или None
        """
        pass

    @abstractmethod
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Обновление записи

        Args:
            id: ID записи
            data: Новые данные

        Returns:
            Optional[T]: Обновленная запись или None
        """
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Удаление записи

        Args:
            id: ID записи

        Returns:
            bool: True если удаление успешно
        """
        pass

    def commit(self) -> None:
        """Сохранение изменений в БД"""
        if self.db:
            self.db.commit()
            self.log_operation("commit")

    def rollback(self) -> None:
        """Откат изменений"""
        if self.db:
            self.db.rollback()
            self.log_operation("rollback")


class SingletonService(BaseService[T]):
    """
    Сервис с паттерном Singleton
    Реализует принцип единственной ответственности (SRP)
    """

    _instance: Optional['SingletonService'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db: Optional[Session] = None):
        if not self._initialized:
            super().__init__(db)
            self._initialized = True

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Базовая валидация для singleton сервисов"""
        return isinstance(data, dict) and len(data) > 0


class CacheService(BaseService[T]):
    """
    Сервис с кэшированием
    Реализует принцип подстановки Лисков (LSP)
    """

    def __init__(self, db: Optional[Session] = None, cache_size: int = 100):
        """
        Инициализация сервиса с кэшем

        Args:
            db: Сессия БД
            cache_size: Размер кэша
        """
        super().__init__(db)
        self.cache: Dict[str, Any] = {}
        self.cache_size = cache_size

    def get_from_cache(self, key: str) -> Optional[T]:
        """
        Получение данных из кэша

        Args:
            key: Ключ кэша

        Returns:
            Optional[T]: Данные из кэша или None
        """
        return self.cache.get(key)

    def set_to_cache(self, key: str, value: T) -> None:
        """
        Сохранение в кэш

        Args:
            key: Ключ кэша
            value: Значение для кэширования
        """
        if len(self.cache) >= self.cache_size:
            # Удаляем старые записи (простая стратегия)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = value

    def clear_cache(self) -> None:
        """Очистка кэша"""
        self.cache.clear()
        self.log_operation("cache_cleared")


class ValidationMixin:
    """
    Миксин для валидации данных
    Реализует принцип разделения интерфейсов (ISP)
    """

    @staticmethod
    def validate_telegram_id(telegram_id: int) -> bool:
        """Валидация Telegram ID"""
        return isinstance(telegram_id, int) and telegram_id > 0

    @staticmethod
    def validate_age(age: int) -> bool:
        """Валидация возраста"""
        from bot.config import MAX_AGE, MIN_AGE
        return isinstance(age, int) and MIN_AGE <= age <= MAX_AGE

    @staticmethod
    def validate_grade(grade: int) -> bool:
        """Валидация класса"""
        from bot.config import MAX_GRADE, MIN_GRADE
        return isinstance(grade, int) and MIN_GRADE <= grade <= MAX_GRADE

    @staticmethod
    def validate_text(text: str, max_length: int = 4000) -> bool:
        """Валидация текста"""
        return isinstance(text, str) and len(text.strip()) > 0 and len(text) <= max_length
