"""
Интерфейсы для сервисов
Реализация принципа инверсии зависимостей (DIP)

"""

from abc import ABC, abstractmethod
from typing import Any

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
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
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
    def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        """Получить пользователя по Telegram ID"""
        pass


class IModerationService(ABC):
    """
    Интерфейс для сервиса модерации
    Реализует принцип единственной ответственности (SRP)
    """

    @abstractmethod
    def is_safe_content(self, text: str) -> tuple[bool, str | None]:
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
        chat_history: list[dict[str, str]],
        user_age: int | None = None,
        user_name: str | None = None,
        user_grade: int | None = None,
        is_history_cleared: bool = False,
        message_count_since_name: int = 0,
        skip_name_asking: bool = False,
        non_educational_questions_count: int = 0,
        is_premium: bool = False,
        is_auto_greeting_sent: bool = False,
        user_gender: str | None = None,
    ) -> str:
        """Генерация ответа ИИ"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности ИИ сервиса"""
        pass

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
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
    ) -> list[dict[str, Any]]:
        """Получить форматированную историю для ИИ"""
        pass

    @abstractmethod
    def get_recent_messages(self, telegram_id: int, limit: int = 10) -> list[ChatHistory]:
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
    def log_security_event(self, event_type: str, _details: dict[str, Any]) -> None:
        """
        Логирование событий безопасности

        Args:
            event_type: Тип события безопасности
            _details: Детали события (используется в реализации)
        """
        pass
