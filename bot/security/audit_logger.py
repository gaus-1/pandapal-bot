"""
Модуль аудита и безопасного логирования для PandaPal Bot.
OWASP A09:2021 - Security Logging and Monitoring Failures

Обеспечивает:
- Безопасное логирование без утечки чувствительных данных
- Аудит критических событий безопасности
- Мониторинг подозрительной активности
- Защита от инъекций в логи
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger


class SecurityEventType(Enum):
    """Типы событий безопасности."""

    # Аутентификация и авторизация
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    AUTHENTICATION_FAILURE = "authentication_failure"

    # Модерация контента
    CONTENT_BLOCKED = "content_blocked"
    INAPPROPRIATE_CONTENT = "inappropriate_content"

    # Подозрительная активность
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"

    # Системные события
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"

    # Критические события
    SECURITY_VIOLATION = "security_violation"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"

    # Платежи и подписки (критические операции)
    PAYMENT_CREATED = "payment_created"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_ACTIVATED = "subscription_activated"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"

    # Доступ к данным
    USER_DATA_ACCESSED = "user_data_accessed"
    USER_DATA_MODIFIED = "user_data_modified"
    SENSITIVE_DATA_EXPORT = "sensitive_data_export"


class SecurityEventSeverity(Enum):
    """Уровни критичности событий."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """
    Класс для безопасного аудита и логирования.

    Особенности:
    - Маскировка чувствительных данных
    - Структурированное логирование
    - Защита от log injection
    - Централизованный аудит событий безопасности
    """

    # Поля, которые нужно маскировать в логах
    SENSITIVE_FIELDS = [
        "password",
        "token",
        "api_key",
        "secret",
        "apikey",
        "authorization",
        "auth",
        "session",
        "cookie",
        "telegram_id",
        "user_id",
        "email",
        "phone",
    ]

    @staticmethod
    def mask_sensitive_data(data: Any) -> Any:
        """
        Маскирует чувствительные данные для безопасного логирования.

        Args:
            data: Данные для маскировки

        Returns:
            Any: Данные с замаскированными чувствительными полями
        """
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                key_lower = key.lower()

                # Проверяем, является ли ключ чувствительным
                is_sensitive = any(
                    sensitive in key_lower for sensitive in AuditLogger.SENSITIVE_FIELDS
                )

                if is_sensitive and isinstance(value, str):
                    # Маскируем значение
                    if len(value) > 4:
                        masked[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
                    else:
                        masked[key] = "*" * len(value)
                elif isinstance(value, dict | list):
                    # Рекурсивно маскируем вложенные структуры
                    masked[key] = AuditLogger.mask_sensitive_data(value)
                else:
                    masked[key] = value

            return masked

        elif isinstance(data, list):
            return [AuditLogger.mask_sensitive_data(item) for item in data]

        else:
            return data

    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """
        Очищает сообщение лога от инъекций.

        Args:
            message: Сообщение для логирования

        Returns:
            str: Безопасное сообщение
        """
        # Удаляем управляющие символы (кроме переноса строки)
        sanitized = "".join(char for char in message if char.isprintable() or char == "\n")

        # Ограничиваем длину
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "... (truncated)"

        return sanitized

    @staticmethod
    def log_security_event(
        event_type: SecurityEventType,
        severity: SecurityEventSeverity,
        message: str,
        user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Логирует событие безопасности.

        Args:
            event_type: Тип события
            severity: Критичность события
            message: Описание события
            user_id: ID пользователя (опционально)
            metadata: Дополнительные метаданные (опционально)
        """
        # Очищаем сообщение
        safe_message = AuditLogger.sanitize_log_message(message)

        # Маскируем чувствительные данные в метаданных
        safe_metadata = AuditLogger.mask_sensitive_data(metadata) if metadata else {}

        # Формируем структурированное сообщение
        from datetime import UTC

        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "message": safe_message,
            "user_id": f"***{str(user_id)[-4:]}" if user_id else None,  # Маскируем ID
            "metadata": safe_metadata,
        }

        # Логируем в зависимости от критичности
        log_message = f"SECURITY_EVENT | {json.dumps(log_entry, ensure_ascii=False)}"

        if severity == SecurityEventSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == SecurityEventSeverity.ERROR:
            logger.error(log_message)
        elif severity == SecurityEventSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    @staticmethod
    def log_blocked_content(user_id: int, content: str, reason: str) -> None:
        """
        Логирует заблокированный контент.

        Args:
            user_id: ID пользователя
            content: Заблокированный контент
            reason: Причина блокировки
        """
        AuditLogger.log_security_event(
            event_type=SecurityEventType.CONTENT_BLOCKED,
            severity=SecurityEventSeverity.WARNING,
            message=f"Контент заблокирован: {reason}",
            user_id=user_id,
            metadata={
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "reason": reason,
            },
        )

    @staticmethod
    def log_unauthorized_access(user_id: int | None, resource: str, action: str) -> None:
        """
        Логирует попытку несанкционированного доступа.

        Args:
            user_id: ID пользователя
            resource: Ресурс, к которому пытались получить доступ
            action: Действие, которое пытались выполнить
        """
        AuditLogger.log_security_event(
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            severity=SecurityEventSeverity.ERROR,
            message=f"Несанкционированный доступ к {resource}",
            user_id=user_id,
            metadata={
                "resource": resource,
                "action": action,
            },
        )

    @staticmethod
    def log_rate_limit_exceeded(
        user_id: int, limit_type: str, current_count: int, limit: int
    ) -> None:
        """
        Логирует превышение лимита запросов.

        Args:
            user_id: ID пользователя
            limit_type: Тип лимита
            current_count: Текущее количество запросов
            limit: Максимальный лимит
        """
        AuditLogger.log_security_event(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=SecurityEventSeverity.WARNING,
            message=f"Превышен лимит {limit_type}",
            user_id=user_id,
            metadata={
                "limit_type": limit_type,
                "current_count": current_count,
                "limit": limit,
            },
        )

    @staticmethod
    def log_api_error(service: str, error_message: str, user_id: int | None = None) -> None:
        """
        Логирует ошибку API.

        Args:
            service: Название сервиса
            error_message: Сообщение об ошибке
            user_id: ID пользователя (опционально)
        """
        AuditLogger.log_security_event(
            event_type=SecurityEventType.API_ERROR,
            severity=SecurityEventSeverity.ERROR,
            message=f"Ошибка API {service}",
            user_id=user_id,
            metadata={
                "service": service,
                "error": AuditLogger.sanitize_log_message(error_message),
            },
        )

    @staticmethod
    def log_payment_event(
        event_type: SecurityEventType,
        user_id: int,
        payment_id: str,
        amount: float,
        currency: str,
        plan_id: str,
        payment_method: str | None = None,
        additional_metadata: dict | None = None,
    ) -> None:
        """
        Логирует события связанные с платежами.

        Args:
            event_type: Тип события (PAYMENT_CREATED, PAYMENT_SUCCEEDED, PAYMENT_FAILED)
            user_id: ID пользователя
            payment_id: ID платежа
            amount: Сумма платежа
            currency: Валюта
            plan_id: ID плана подписки
            payment_method: Метод оплаты
            additional_metadata: Дополнительные метаданные
        """
        metadata = {
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "plan_id": plan_id,
            "payment_method": payment_method,
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        severity = SecurityEventSeverity.INFO
        if event_type == SecurityEventType.PAYMENT_FAILED:
            severity = SecurityEventSeverity.WARNING

        AuditLogger.log_security_event(
            event_type=event_type,
            severity=severity,
            message=f"Платеж {event_type.value}: {payment_id}",
            user_id=user_id,
            metadata=metadata,
        )

    @staticmethod
    def log_subscription_event(
        event_type: SecurityEventType,
        user_id: int,
        subscription_id: int,
        plan_id: str,
        additional_metadata: dict | None = None,
    ) -> None:
        """
        Логирует события связанные с подписками.

        Args:
            event_type: Тип события (SUBSCRIPTION_ACTIVATED, SUBSCRIPTION_EXPIRED, SUBSCRIPTION_CANCELLED)
            user_id: ID пользователя
            subscription_id: ID подписки
            plan_id: ID плана
            additional_metadata: Дополнительные метаданные
        """
        metadata = {
            "subscription_id": subscription_id,
            "plan_id": plan_id,
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        severity = SecurityEventSeverity.INFO
        if event_type == SecurityEventType.SUBSCRIPTION_EXPIRED:
            severity = SecurityEventSeverity.WARNING

        AuditLogger.log_security_event(
            event_type=event_type,
            severity=severity,
            message=f"Подписка {event_type.value}: {subscription_id}",
            user_id=user_id,
            metadata=metadata,
        )

    @staticmethod
    def log_user_data_access(
        user_id: int,
        accessed_user_id: int,
        resource: str,
        action: str,
        ip_address: str | None = None,
    ) -> None:
        """
        Логирует доступ к данным пользователя.

        Args:
            user_id: ID пользователя, выполняющего доступ
            accessed_user_id: ID пользователя, чьи данные запрашиваются
            resource: Ресурс, к которому был доступ
            action: Действие (read, update, delete)
            ip_address: IP адрес
        """
        severity = SecurityEventSeverity.INFO

        # Если пользователь обращается к чужим данным - повышаем критичность
        if user_id != accessed_user_id:
            severity = SecurityEventSeverity.WARNING

        AuditLogger.log_security_event(
            event_type=SecurityEventType.USER_DATA_ACCESSED,
            severity=severity,
            message=f"Доступ к данным пользователя: {resource}",
            user_id=user_id,
            metadata={
                "accessed_user_id": f"***{str(accessed_user_id)[-4:]}",
                "resource": resource,
                "action": action,
                "ip_address": ip_address,
                "is_own_data": user_id == accessed_user_id,
            },
        )


# Утилиты для быстрого доступа
def log_security_event(
    event_type: SecurityEventType,
    message: str,
    severity: SecurityEventSeverity = SecurityEventSeverity.WARNING,
    user_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Быстрое логирование события безопасности."""
    AuditLogger.log_security_event(event_type, severity, message, user_id, metadata)


def mask_sensitive(data: Any) -> Any:
    """Быстрая маскировка чувствительных данных."""
    return AuditLogger.mask_sensitive_data(data)
