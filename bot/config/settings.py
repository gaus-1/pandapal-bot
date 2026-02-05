"""
Основной класс конфигурации приложения.

Содержит все настройки для работы бота. Параметры загружаются
из переменных окружения с поддержкой множественных алиасов.
"""

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Основной класс конфигурации приложения."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    database_url: str = Field(..., validation_alias=AliasChoices("DATABASE_URL", "database_url"))
    telegram_bot_token: str = Field(
        ...,
        description="Токен Telegram бота от @BotFather",
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "telegram_bot_token"),
    )

    sentry_dsn: str = Field(
        default="",
        description="Sentry DSN для мониторинга ошибок",
        validation_alias=AliasChoices("SENTRY_DSN", "sentry_dsn"),
    )

    # AI / YANDEX CLOUD (ОСНОВНОЙ)
    yandex_cloud_api_key: str = Field(
        ...,
        description="Yandex Cloud API ключ для YandexGPT, SpeechKit, Vision",
        validation_alias=AliasChoices("YANDEX_CLOUD_API_KEY", "yandex_cloud_api_key"),
    )

    yandex_cloud_folder_id: str = Field(
        ...,
        description="Yandex Cloud Folder ID (каталог)",
        validation_alias=AliasChoices("YANDEX_CLOUD_FOLDER_ID", "yandex_cloud_folder_id"),
    )

    yandex_gpt_model: str = Field(
        default="yandexgpt/latest",
        description="Модель YandexGPT Pro (yandexgpt/latest - это YandexGPT Pro 5, yandexgpt/rc - Pro 5.1)",
        validation_alias=AliasChoices("YANDEX_GPT_MODEL", "yandex_gpt_model"),
    )

    # Yandex Maps
    yandex_maps_api_key: str | None = Field(
        default=None,
        description="API ключ для Yandex Maps Static API (для генерации карт стран)",
        validation_alias=AliasChoices("YANDEX_MAPS_API_KEY", "yandex_maps_api_key"),
    )

    # AI SETTINGS
    ai_temperature: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Температура для Pro модели (рекомендуется 0.4 для баланса точности и естественности)",
        validation_alias=AliasChoices("AI_TEMPERATURE", "ai_temperature"),
    )

    ai_max_tokens: int = Field(
        default=8192,
        ge=100,
        le=8192,
        description="Максимум токенов для Pro модели (8192 - максимальная полнота ответов)",
        validation_alias=AliasChoices("AI_MAX_TOKENS", "ai_max_tokens"),
    )

    # Настройки для Pro модели (для обратной совместимости, используются как основные)
    ai_temperature_pro: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Температура для Pro модели (рекомендуется 0.4 для баланса точности и естественности)",
        validation_alias=AliasChoices("AI_TEMPERATURE_PRO", "ai_temperature_pro"),
    )

    ai_max_tokens_pro: int = Field(
        default=8192,
        ge=100,
        le=8192,
        description="Максимум токенов для Pro модели (8192 - максимальная полнота ответов)",
        validation_alias=AliasChoices("AI_MAX_TOKENS_PRO", "ai_max_tokens_pro"),
    )

    # CONTENT MODERATION
    forbidden_topics: str = Field(
        default="политика,насилие,оружие,наркотики,кокаин,героин,марихуана,экстремизм,18+",
        description="Запрещённые темы (через запятую в .env)",
        validation_alias=AliasChoices("FORBIDDEN_TOPICS", "forbidden_topics"),
    )

    content_filter_level: int = Field(
        default=5,
        ge=1,
        le=5,
        description="Уровень строгости фильтра (1=мягкий, 5=максимальный)",
        validation_alias=AliasChoices("CONTENT_FILTER_LEVEL", "content_filter_level"),
    )

    # RATE LIMITING
    ai_rate_limit_per_minute: int = Field(
        default=30,
        ge=1,
        description="Лимит AI запросов в минуту на пользователя (защита от abuse)",
        validation_alias=AliasChoices("AI_RATE_LIMIT_PER_MINUTE", "ai_rate_limit_per_minute"),
    )

    daily_message_limit: int = Field(
        default=500,
        ge=1,
        description="Дневной лимит сообщений на пользователя",
        validation_alias=AliasChoices("DAILY_MESSAGE_LIMIT", "daily_message_limit"),
    )

    # MEMORY / HISTORY
    chat_history_limit: int = Field(
        default=50,
        ge=1,
        description="Количество сообщений в истории для контекста AI",
        validation_alias=AliasChoices("CHAT_HISTORY_LIMIT", "chat_history_limit"),
    )

    # SECURITY
    secret_key: str = Field(
        ...,
        min_length=16,
        description="Секретный ключ для шифрования",
        validation_alias=AliasChoices("SECRET_KEY", "secret_key"),
    )

    # Frontend
    frontend_url: str = Field(
        default="https://pandapal.ru",
        description="URL фронтенда",
        validation_alias=AliasChoices("FRONTEND_URL", "frontend_url"),
    )

    # WEBHOOK
    webhook_domain: str = Field(
        default="pandapal-bot-production.up.railway.app",
        description="Домен для webhook (без https://). Railway URL",
        validation_alias=AliasChoices("WEBHOOK_DOMAIN", "webhook_domain"),
    )

    # LOGGING
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования (DEBUG, INFO, WARNING, ERROR)",
        validation_alias=AliasChoices("LOG_LEVEL", "log_level"),
    )

    # ENVIRONMENT
    environment: str = Field(
        default="production",
        description="Окружение приложения (development, test, production)",
        validation_alias=AliasChoices("ENVIRONMENT", "environment"),
    )

    # YOOKASSA PAYMENTS
    yookassa_test_mode: bool = Field(
        default=False,
        description="Тестовый режим ЮKassa. True = тестовый магазин, False = продакшн",
        validation_alias=AliasChoices("YOOKASSA_TEST_MODE", "yookassa_test_mode"),
    )

    yookassa_shop_id: str = Field(
        default="1240345",
        description="Идентификатор магазина ЮKassa (shop_id) - продакшн",
        validation_alias=AliasChoices("YOOKASSA_SHOP_ID", "yookassa_shop_id"),
    )

    yookassa_test_shop_id: str = Field(
        default="1242170",
        description="Идентификатор тестового магазина ЮKassa (Test, pandapal.ru)",
        validation_alias=AliasChoices("YOOKASSA_TEST_SHOP_ID", "yookassa_test_shop_id"),
    )

    yookassa_secret_key: str = Field(
        default="",
        description="Секретный ключ ЮKassa (продакшн)",
        validation_alias=AliasChoices("YOOKASSA_SECRET_KEY", "yookassa_secret_key"),
    )

    yookassa_test_secret_key: str = Field(
        default="",
        description="Секретный ключ тестового магазина ЮKassa",
        validation_alias=AliasChoices("YOOKASSA_TEST_SECRET_KEY", "yookassa_test_secret_key"),
    )

    @property
    def active_yookassa_shop_id(self) -> str:
        """Получить активный shop_id в зависимости от режима"""
        return self.yookassa_test_shop_id if self.yookassa_test_mode else self.yookassa_shop_id

    @property
    def active_yookassa_secret_key(self) -> str:
        """Получить активный secret_key в зависимости от режима"""
        return (
            self.yookassa_test_secret_key if self.yookassa_test_mode else self.yookassa_secret_key
        )

    yookassa_return_url: str = Field(
        default="https://pandapal.ru/premium/success",
        description="URL возврата после оплаты",
        validation_alias=AliasChoices("YOOKASSA_RETURN_URL", "yookassa_return_url"),
    )

    yookassa_inn: str = Field(
        default="371104743407",
        description="ИНН самозанятого для чеков",
        validation_alias=AliasChoices("YOOKASSA_INN", "yookassa_inn"),
    )

    yookassa_merchant_name: str = Field(
        default="PandaPal",
        description="Короткое имя магазина для банковской выписки (14 символов: YM* + 11). Настраивается в личном кабинете ЮKassa",
        validation_alias=AliasChoices("YOOKASSA_MERCHANT_NAME", "yookassa_merchant_name"),
    )

    yookassa_recurring_enabled: bool = Field(
        default=False,
        description="Автоплатежи активированы в ЮKassa. Установите True после активации автоплатежей менеджером",
        validation_alias=AliasChoices("YOOKASSA_RECURRING_ENABLED", "yookassa_recurring_enabled"),
    )

    referral_payout_rub: float = Field(
        default=100.0,
        ge=0,
        description="Сумма начисления рефереру за одну оплату (руб)",
        validation_alias=AliasChoices("REFERRAL_PAYOUT_RUB", "referral_payout_rub"),
    )

    # Redis (session storage)
    redis_url: str = Field(
        default="",
        description="Redis URL для хранения сессий (опционально, fallback на in-memory)",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )

    # ADMIN (безлимит запросов)
    admin_usernames: str = Field(
        default="SavinVE",
        description="Список username админов через запятую",
        validation_alias=AliasChoices("ADMIN_USERNAMES", "admin_usernames"),
    )
    admin_telegram_ids: str = Field(
        default="963126718,8198136020,729414271",
        description="Список Telegram ID админов через запятую (безлимит запросов); 729414271 — преподаватель-реферер",
        validation_alias=AliasChoices("ADMIN_TELEGRAM_IDS", "admin_telegram_ids"),
    )

    def get_forbidden_topics_list(self) -> list[str]:
        """Получить список запрещённых тем."""
        return [topic.strip() for topic in self.forbidden_topics.split(",") if topic.strip()]

    def get_admin_usernames_list(self) -> list[str]:
        """Получить список username админов."""
        return [
            username.strip().lower()
            for username in self.admin_usernames.split(",")
            if username.strip()
        ]

    def get_admin_telegram_ids_list(self) -> list[int]:
        """Получить список Telegram ID админов."""
        result = []
        for part in self.admin_telegram_ids.split(","):
            part = part.strip()
            if part and part.isdigit():
                result.append(int(part))
        return result

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Проверка корректности DATABASE_URL и нормализация драйвера."""
        # Разрешаем SQLite для локальной разработки/тестов
        if v.startswith("sqlite"):
            return v

        # Для продакшена требуем PostgreSQL
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL должен быть postgresql:// или sqlite:// (для тестов)")

        # Нормализуем драйвер: заставляем использовать psycopg v3 для PostgreSQL
        if v.startswith("postgresql://") and "+psycopg" not in v:
            v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        elif v.startswith("postgres://"):
            # Railway может использовать postgres:// вместо postgresql://
            v = v.replace("postgres://", "postgresql+psycopg://", 1)

        return v

    @field_validator("yandex_cloud_api_key")
    @classmethod
    def validate_yandex_api_key(cls, v: str) -> str:
        """Проверка Yandex Cloud API ключа."""
        if not v or v in ("your_yandex_key", "test_key"):
            raise ValueError("YANDEX_CLOUD_API_KEY не установлен в .env")
        return v

    @field_validator("yandex_cloud_folder_id")
    @classmethod
    def validate_yandex_folder_id(cls, v: str) -> str:
        """Проверка Yandex Cloud Folder ID."""
        if not v or v == "your_folder_id":
            raise ValueError("YANDEX_CLOUD_FOLDER_ID не установлен в .env")
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Проверка и нормализация Redis URL."""
        if not v:
            return v  # Пустой URL допустим (fallback на in-memory)

        # Проверяем формат для redis-py (rediss:// или redis://)
        if not v.startswith(("rediss://", "redis://")):
            raise ValueError(
                "REDIS_URL должен начинаться с rediss:// или redis://. "
                "Для Upstash используйте формат: rediss://default:TOKEN@host:6379"
            )

        # Для Upstash проверяем наличие upstash.io в хосте
        if "upstash.io" in v and "default:" not in v:
            raise ValueError(
                "Для Upstash Redis URL должен содержать 'default:' в формате: "
                "rediss://default:TOKEN@host:6379"
            )

        return v


# Singleton instance настроек
# Создаётся один раз при импорте модуля
# Pydantic автоматически загружает значения из переменных окружения
settings = Settings()  # type: Settings  # Явный тип вместо ignore

# Возрастные границы
MIN_AGE = 6
MAX_AGE = 18
MIN_GRADE = 1
MAX_GRADE = 11

# Лимиты для безопасности
MAX_MESSAGE_LENGTH = 4000  # Максимальная длина сообщения
MAX_FILE_SIZE_MB = 10  # Максимальный размер файла в МБ
ALLOWED_FILE_TYPES = [".pdf", ".docx", ".txt", ".jpg", ".png", ".jpeg"]
