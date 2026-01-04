"""
Валидаторы для API endpoints.

Использует Pydantic для валидации входных данных.
Защита от injection атак через строгую типизацию.
"""

from typing import Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


class UpdateUserRequest(BaseModel):
    """Валидация запроса на обновление профиля пользователя."""

    age: Optional[int] = Field(None, ge=6, le=18, description="Возраст пользователя (6-18)")
    grade: Optional[int] = Field(None, ge=1, le=11, description="Класс пользователя (1-11)")

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: Optional[int]) -> Optional[int]:
        """Валидация возраста."""
        if v is not None and not (6 <= v <= 18):
            raise ValueError("Age must be between 6 and 18")
        return v

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: Optional[int]) -> Optional[int]:
        """Валидация класса."""
        if v is not None and not (1 <= v <= 11):
            raise ValueError("Grade must be between 1 and 11")
        return v


class AIChatRequest(BaseModel):
    """Валидация запроса на AI чат."""

    telegram_id: int = Field(..., ge=1, description="Telegram ID пользователя")
    message: Optional[str] = Field(None, max_length=4000, description="Текстовое сообщение")
    photo_base64: Optional[str] = Field(
        None, max_length=15 * 1024 * 1024, description="Base64 фото"
    )
    audio_base64: Optional[str] = Field(
        None, max_length=15 * 1024 * 1024, description="Base64 аудио"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: Optional[str]) -> Optional[str]:
        """Валидация сообщения."""
        # Если пустая строка - преобразуем в None (разрешено если есть фото/аудио)
        if v is not None and len(v.strip()) == 0:
            return None
        return v

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id(cls, v: int) -> int:
        """Валидация Telegram ID."""
        if v <= 0:
            raise ValueError("telegram_id must be positive")
        return v

    def model_post_init(self, __context) -> None:  # noqa: ARG002
        """Проверка что есть хотя бы одно поле (message, photo или audio)."""
        if not any([self.message, self.photo_base64, self.audio_base64]):
            raise ValueError(
                "At least one of message, photo_base64, or audio_base64 must be provided"
            )


class AuthRequest(BaseModel):
    """Валидация запроса на аутентификацию."""

    initData: str = Field(..., min_length=10, max_length=10000, description="Telegram initData")


class PremiumInvoiceRequest(BaseModel):
    """Валидация запроса на создание invoice."""

    telegram_id: int = Field(..., ge=1, description="Telegram ID пользователя")
    plan_id: str = Field(..., pattern="^(week|month|year)$", description="ID тарифного плана")
    payment_method: Optional[str] = Field(
        default="stars", pattern="^(stars)$", description="Способ оплаты (только stars для invoice)"
    )


class PremiumPaymentRequest(BaseModel):
    """Валидация запроса на обработку оплаты."""

    telegram_id: int = Field(..., ge=1, description="Telegram ID пользователя")
    plan_id: str = Field(..., pattern="^(week|month|year)$", description="ID тарифного плана")
    transaction_id: Optional[str] = Field(None, max_length=255, description="ID транзакции")
    payment_method: Optional[str] = Field(
        default="stars",
        pattern="^(stars|yookassa_card|yookassa_sbp|yookassa_other)$",
        description="Способ оплаты",
    )


class PremiumYooKassaRequest(BaseModel):
    """Валидация запроса на создание платежа через ЮKassa."""

    telegram_id: int = Field(
        ..., ge=1, description="Telegram ID пользователя (требуется авторизация)"
    )
    plan_id: str = Field(..., pattern="^(week|month|year)$", description="ID тарифного плана")
    user_email: Optional[str] = Field(
        None, max_length=255, description="Email пользователя (для чека)"
    )
    user_phone: Optional[str] = Field(
        None, max_length=20, description="Телефон пользователя (для чека)"
    )


def validate_telegram_id(telegram_id_str: str) -> int:
    """
    Безопасная валидация telegram_id из URL path.

    Args:
        telegram_id_str: Строка из URL path

    Returns:
        int: Валидный telegram_id

    Raises:
        ValueError: Если telegram_id невалиден
    """
    try:
        telegram_id = int(telegram_id_str)
        if telegram_id <= 0:
            raise ValueError("telegram_id must be positive")
        return telegram_id
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Invalid telegram_id format: {telegram_id_str}") from e
        raise


def validate_limit(limit_str: Optional[str], default: int = 50, max_limit: int = 100) -> int:
    """
    Безопасная валидация limit из query параметров.

    Args:
        limit_str: Строка из query параметров
        default: Значение по умолчанию
        max_limit: Максимальное значение

    Returns:
        int: Валидный limit
    """
    if not limit_str:
        return default

    try:
        limit = int(limit_str)
        if limit < 1:
            return default
        if limit > max_limit:
            return max_limit
        return limit
    except ValueError:
        return default
