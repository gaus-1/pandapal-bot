"""Валидаторы для API endpoints.

Использует Pydantic для валидации входных данных.
Защита от injection атак через строгую типизацию.
"""

from aiohttp import web
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from bot.security.telegram_auth import TelegramWebAppAuth


class UpdateUserRequest(BaseModel):
    """Валидация запроса на обновление профиля пользователя."""

    age: int | None = Field(None, ge=6, le=18, description="Возраст пользователя (6-18)")
    grade: int | None = Field(None, ge=1, le=11, description="Класс пользователя (1-11)")

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int | None) -> int | None:
        """Валидация возраста."""
        if v is not None and not (6 <= v <= 18):
            raise ValueError("Age must be between 6 and 18")
        return v

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: int | None) -> int | None:
        """Валидация класса."""
        if v is not None and not (1 <= v <= 11):
            raise ValueError("Grade must be between 1 and 11")
        return v


class AIChatRequest(BaseModel):
    """Валидация запроса на AI чат."""

    telegram_id: int = Field(..., ge=1, description="Telegram ID пользователя")
    message: str | None = Field(None, max_length=4000, description="Текстовое сообщение")
    photo_base64: str | None = Field(None, max_length=15 * 1024 * 1024, description="Base64 фото")
    audio_base64: str | None = Field(None, max_length=15 * 1024 * 1024, description="Base64 аудио")
    language_code: str | None = Field(
        None, max_length=10, description="Язык для распознавания речи (ru, en)"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str | None) -> str | None:
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

    def model_post_init(self, __context) -> None:
        """Проверка что есть хотя бы одно поле (message, photo или audio)."""
        if not any([self.message, self.photo_base64, self.audio_base64]):
            raise ValueError(
                "At least one of message, photo_base64, or audio_base64 must be provided"
            )
        _ = __context  # Pydantic требует этот параметр


class HomeworkCheckRequest(BaseModel):
    """Валидация запроса на проверку домашнего задания."""

    telegram_id: int = Field(..., ge=1, description="Telegram ID пользователя")
    photo_base64: str = Field(..., max_length=15 * 1024 * 1024, description="Base64 фото ДЗ")
    subject: str | None = Field(
        None, max_length=100, description="Предмет (математика, русский и т.д.)"
    )
    topic: str | None = Field(None, max_length=255, description="Тема задания")
    message: str | None = Field(
        None, max_length=1000, description="Дополнительный вопрос/комментарий"
    )

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id(cls, v: int) -> int:
        """Валидация Telegram ID."""
        if v <= 0:
            raise ValueError("telegram_id must be positive")
        return v


class AuthRequest(BaseModel):
    """Валидация запроса на аутентификацию."""

    initData: str | None = Field(
        None, min_length=10, max_length=10000, description="Telegram initData (camelCase)"
    )
    init_data: str | None = Field(
        None, min_length=10, max_length=10000, description="Telegram initData (snake_case)"
    )

    def model_post_init(self, __context) -> None:
        """Проверка что есть хотя бы одно поле и нормализация."""
        _ = __context  # Pydantic требует этот параметр
        # Поддержка обоих форматов для обратной совместимости
        if self.init_data and not self.initData:
            self.initData = self.init_data
        elif not self.initData and not self.init_data:
            raise ValueError("Either initData or init_data must be provided")


class PremiumInvoiceRequest(BaseModel):
    """Валидация запроса на создание invoice."""

    telegram_id: int = Field(..., ge=1, description="Telegram ID пользователя")
    plan_id: str = Field(..., pattern="^(month|year)$", description="ID тарифного плана")
    payment_method: str | None = Field(
        default="stars", pattern="^(stars)$", description="Способ оплаты (только stars для invoice)"
    )


class PremiumPaymentRequest(BaseModel):
    """Валидация запроса на обработку оплаты."""

    telegram_id: int = Field(..., ge=1, description="Telegram ID пользователя")
    plan_id: str = Field(..., pattern="^(month|year)$", description="ID тарифного плана")
    transaction_id: str | None = Field(None, max_length=255, description="ID транзакции")
    payment_method: str | None = Field(
        default="stars",
        pattern="^(stars|yookassa_card|yookassa_sbp|yookassa_other)$",
        description="Способ оплаты",
    )


class PremiumYooKassaRequest(BaseModel):
    """Валидация запроса на создание платежа через ЮKassa."""

    telegram_id: int = Field(
        ..., ge=1, description="Telegram ID пользователя (требуется авторизация)"
    )
    plan_id: str = Field(..., pattern="^(month|year)$", description="ID тарифного плана")
    user_email: str | None = Field(
        None, max_length=255, description="Email пользователя (для чека)"
    )
    user_phone: str | None = Field(
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


def verify_resource_owner(request: web.Request, target_telegram_id: int) -> tuple[bool, str | None]:
    """
    Проверка владельца ресурса (OWASP A01: Broken Access Control).

    Верифицирует, что пользователь из initData имеет право доступа к ресурсу.
    Используется для защиты всех endpoints с telegram_id в URL.

    Args:
        request: HTTP запрос с заголовком X-Telegram-Init-Data
        target_telegram_id: ID ресурса к которому запрашивается доступ

    Returns:
        (allowed, error_message): Разрешен ли доступ и сообщение об ошибке
    """
    # Получаем initData из заголовка
    init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data:
        # Без initData - запрещаем доступ к защищенным ресурсам
        logger.warning(
            f"🚫 A01: Запрос без X-Telegram-Init-Data к ресурсу user={target_telegram_id}"
        )
        return False, "Authorization required: X-Telegram-Init-Data header missing"

    # Валидируем initData
    auth_validator = TelegramWebAppAuth()
    validated_data = auth_validator.validate_init_data(init_data)

    if not validated_data:
        logger.warning(f"🚫 A01: Невалидный initData для ресурса user={target_telegram_id}")
        return False, "Invalid authorization data"

    # Извлекаем telegram_id из initData
    user_data = auth_validator.extract_user_data(validated_data)
    if not user_data or not user_data.get("id"):
        logger.warning(
            f"🚫 A01: Не удалось извлечь user_id из initData для user={target_telegram_id}"
        )
        return False, "Invalid user data in authorization"

    requester_id = user_data["id"]

    # Проверяем что запрашивающий == владелец ресурса
    if requester_id != target_telegram_id:
        logger.warning(
            f"🚫 A01: Access denied - user {requester_id} пытался получить доступ к user {target_telegram_id}"
        )
        return False, "Access denied: you can only access your own resources"

    return True, None


def require_owner(request: web.Request, target_telegram_id: int) -> web.Response | None:
    """
    Декоратор-хелпер для проверки владельца ресурса.

    Возвращает готовый Response с ошибкой 403 если доступ запрещен,
    или None если доступ разрешен.

    Использование:
        error_response = require_owner(request, telegram_id)
        if error_response:
            return error_response
        # ... продолжить обработку

    Args:
        request: HTTP запрос
        target_telegram_id: ID пользователя-владельца ресурса

    Returns:
        web.Response с ошибкой 403, или None если доступ разрешен
    """
    allowed, error_msg = verify_resource_owner(request, target_telegram_id)
    if not allowed:
        return web.json_response({"error": error_msg}, status=403)
    return None


def validate_limit(limit_str: str | None, default: int = 50, max_limit: int = 100) -> int:
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


# RESPONSE MODELS (Явные контракты данных)


class DetailedAnalyticsResponse(BaseModel):
    """Детальная аналитика для Premium пользователей."""

    messages_per_day: list[dict] = Field(default_factory=list, description="Сообщений в день")
    most_active_subjects: list[dict] = Field(
        default_factory=list, description="Самые активные предметы"
    )
    learning_trends: list[dict] = Field(default_factory=list, description="Тренды обучения")


class DashboardStatsResponse(BaseModel):
    """Статистика дашборда пользователя."""

    total_messages: int = Field(..., ge=0, description="Всего сообщений")
    learning_sessions: int = Field(..., ge=0, description="Учебных сессий")
    total_points: int = Field(..., ge=0, description="Всего очков")
    subjects_studied: int = Field(..., ge=0, description="Изучено предметов")
    current_streak: int = Field(..., ge=0, description="Текущая серия дней")
    detailed_analytics: DetailedAnalyticsResponse | None = Field(
        None, description="Детальная аналитика (только для Premium)"
    )


class PaymentAmountResponse(BaseModel):
    """Сумма платежа."""

    value: float = Field(..., ge=0, description="Сумма")
    currency: str = Field(..., description="Валюта")


class PaymentStatusResponse(BaseModel):
    """Статус платежа."""

    payment_id: str = Field(..., description="ID платежа")
    status: str = Field(..., description="Статус платежа")
    paid: bool = Field(..., description="Оплачен ли")
    amount: PaymentAmountResponse = Field(..., description="Сумма платежа")
    payment_metadata: dict = Field(default_factory=dict, description="Метаданные платежа")


class PaymentCreateResponse(BaseModel):
    """Ответ при создании платежа."""

    payment_id: str = Field(..., description="ID платежа")
    confirmation_url: str = Field(..., description="URL для подтверждения оплаты")
    amount: PaymentAmountResponse = Field(..., description="Сумма платежа")
    description: str = Field(..., description="Описание платежа")
