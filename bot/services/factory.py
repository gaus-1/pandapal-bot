"""
Фабрика сервисов
Реализация паттерна Factory для создания сервисов
Реализует принцип инверсии зависимостей (DIP)

"""

from typing import Dict, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from bot.interfaces import (
    IAIService,
    IChatHistoryService,
    IConfigService,
    IDatabaseService,
    ILoggerService,
    IModerationService,
    IUserService,
)
from bot.services.ai_service import GeminiAIService
from bot.services.history_service import ChatHistoryService
from bot.services.moderation_service import ContentModerationService
from bot.services.user_service import UserService

T = TypeVar("T")


class ServiceFactory:
    """
    Фабрика для создания сервисов
    Реализует паттерн Singleton и Factory
    """

    _instance: Optional["ServiceFactory"] = None
    _services: Dict[str, object] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ServiceFactory":
        """Получить экземпляр фабрики"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_user_service(self, db: Session) -> IUserService:
        """
        Создание сервиса пользователей

        Args:
            db: Сессия БД

        Returns:
            IUserService: Сервис пользователей
        """
        service_key = f"user_service_{id(db)}"
        if service_key not in self._services:
            self._services[service_key] = UserService(db)
        return self._services[service_key]

    def create_moderation_service(self) -> IModerationService:
        """
        Создание сервиса модерации

        Returns:
            IModerationService: Сервис модерации
        """
        service_key = "moderation_service"
        if service_key not in self._services:
            self._services[service_key] = ContentModerationService()
        return self._services[service_key]

    def create_ai_service(self) -> IAIService:
        """
        Создание сервиса ИИ

        Returns:
            IAIService: Сервис ИИ
        """
        service_key = "ai_service"
        if service_key not in self._services:
            self._services[service_key] = GeminiAIService()
        return self._services[service_key]

    def create_chat_history_service(self, db: Session) -> IChatHistoryService:
        """
        Создание сервиса истории чата

        Args:
            db: Сессия БД

        Returns:
            IChatHistoryService: Сервис истории чата
        """
        service_key = f"chat_history_service_{id(db)}"
        if service_key not in self._services:
            self._services[service_key] = ChatHistoryService(db)
        return self._services[service_key]

    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        Получение сервиса по типу

        Args:
            service_type: Тип сервиса

        Returns:
            Optional[T]: Сервис или None
        """
        for service in self._services.values():
            if isinstance(service, service_type):
                return service
        return None

    def clear_services(self) -> None:
        """Очистка всех сервисов"""
        self._services.clear()

    def get_services_count(self) -> int:
        """Получение количества созданных сервисов"""
        return len(self._services)


class ServiceRegistry:
    """
    Реестр сервисов
    Управление жизненным циклом сервисов
    """

    def __init__(self):
        self._services: Dict[str, object] = {}
        self._factories: Dict[str, callable] = {}

    def register_factory(self, name: str, factory: callable) -> None:
        """
        Регистрация фабрики сервиса

        Args:
            name: Имя сервиса
            factory: Фабрика для создания сервиса
        """
        self._factories[name] = factory

    def get_service(self, name: str, *args, **kwargs) -> Optional[object]:
        """
        Получение сервиса

        Args:
            name: Имя сервиса
            *args: Аргументы для создания
            **kwargs: Ключевые аргументы

        Returns:
            Optional[object]: Сервис или None
        """
        if name in self._services:
            return self._services[name]

        if name in self._factories:
            service = self._factories[name](*args, **kwargs)
            self._services[name] = service
            return service

        return None

    def unregister_service(self, name: str) -> bool:
        """
        Отмена регистрации сервиса

        Args:
            name: Имя сервиса

        Returns:
            bool: True если сервис был зарегистрирован
        """
        if name in self._services:
            del self._services[name]
            return True
        return False

    def clear_all(self) -> None:
        """Очистка всех сервисов"""
        self._services.clear()
        self._factories.clear()


# Глобальный экземпляр фабрики
service_factory = ServiceFactory.get_instance()

# Глобальный реестр сервисов
service_registry = ServiceRegistry()
