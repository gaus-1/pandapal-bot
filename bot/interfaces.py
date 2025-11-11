"""
Интерфейсы для сервисов
Реализация принципа инверсии зависимостей (DIP)

"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from bot.models import ChatHistory, User


class IUserService(ABC):
    """
    Интерфейс для сервиса пользователей
    Реализует принцип разделения интерфейсов (ISP)
    """

    @abstractmethod
    def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Получить или создать пользователя"""
        pass

    @abstractmethod
    def update_user_age(self, telegram_id: int, age: int) -> bool:
        """Обновить возраст пользователя"""
        pass

    @abstractmethod
    def update_user_grade(self, telegram_id: int, grade: int) -> bool:
        """Обновить класс пользователя"""
        pass

    @abstractmethod
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        pass


class IModerationService(ABC):
    """
    Интерфейс для сервиса модерации
    Реализует принцип единственной ответственности (SRP)
    """

    @abstractmethod
    def is_safe_content(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Проверка безопасности контента

        Returns:
            Tuple[bool, Optional[str]]: (безопасен, причина блокировки)
        """
        pass

    @abstractmethod
    def sanitize_ai_response(self, response: str) -> str:
        """Очистка ответа ИИ"""
        pass

    @abstractmethod
    def get_safe_response_alternative(self, reason: str) -> str:
        """Получить безопасный альтернативный ответ"""
        pass

    @abstractmethod
    def log_blocked_content(self, telegram_id: int, content: str, reason: str) -> None:
        """Логирование заблокированного контента"""
        pass


class IAIService(ABC):
    """
    Интерфейс для сервиса ИИ
    Реализует принцип подстановки Лисков (LSP)
    """

    @abstractmethod
    async def generate_response(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]],
        user_age: Optional[int] = None,
        user_grade: Optional[int] = None,  # noqa: ARG002
    ) -> str:
        """Генерация ответа ИИ"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности ИИ сервиса"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        pass


class IChatHistoryService(ABC):
    """
    Интерфейс для сервиса истории чата
    Реализует принцип единственной ответственности (SRP)
    """

    @abstractmethod
    def add_message(
        self,
        telegram_id: int,
        message_text: str,
        message_type: str,
    ) -> None:
        """Добавить сообщение в историю"""
        pass

    @abstractmethod
    def get_formatted_history_for_ai(
        self, telegram_id: int, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Получить форматированную историю для ИИ"""
        pass

    @abstractmethod
    def get_recent_messages(self, telegram_id: int, limit: int = 10) -> List[ChatHistory]:
        """Получить последние сообщения"""
        pass

    @abstractmethod
    def clear_history(self, telegram_id: int) -> bool:
        """Очистить историю пользователя"""
        pass


class IDatabaseService(ABC):
    """
    Интерфейс для сервиса базы данных
    Реализует принцип инверсии зависимостей (DIP)
    """

    @abstractmethod
    def check_connection(self) -> bool:
        """Проверка подключения к БД"""
        pass

    @abstractmethod
    def init_db(self) -> None:
        """Инициализация БД"""
        pass

    @abstractmethod
    def get_session(self):
        """Получение сессии БД"""
        pass

    @abstractmethod
    def close_session(self, session) -> None:
        """Закрытие сессии БД"""
        pass


class IConfigService(ABC):
    """
    Интерфейс для сервиса конфигурации
    Реализует принцип единственной ответственности (SRP)
    """

    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:  # noqa: ARG002
        """Получить настройку"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Валидация конфигурации"""
        pass

    @abstractmethod
    def reload_config(self) -> None:
        """Перезагрузка конфигурации"""
        pass


class ILoggerService(ABC):
    """
    Интерфейс для сервиса логирования
    Реализует принцип разделения интерфейсов (ISP)
    """

    @abstractmethod
    def log_info(self, message: str, **kwargs) -> None:
        """Логирование информации"""
        pass

    @abstractmethod
    def log_warning(self, message: str, **kwargs) -> None:
        """Логирование предупреждения"""
        pass

    @abstractmethod
    def log_error(self, message: str, **kwargs) -> None:
        """Логирование ошибки"""
        pass

    @abstractmethod
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Логирование событий безопасности"""
        pass
