"""
Конфигурация Sentry для production мониторинга.

Безопасно настраивает Sentry для отслеживания ошибок
и производительности в production среде.
"""

import logging
import os

try:
    import sentry_sdk
    from sentry_sdk.integrations.aiohttp import AioHttpIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logging.warning("⚠️ Sentry не установлен - мониторинг отключен")


class SentryConfig:
    """
    Конфигурация Sentry для PandaPal Bot.

    Предоставляет безопасную настройку мониторинга ошибок
    с маскировкой чувствительных данных.
    """

    def __init__(self):
        """Инициализация конфигурации Sentry."""
        self.dsn: str | None = os.getenv("SENTRY_DSN")
        self.environment: str = os.getenv("SENTRY_ENVIRONMENT", "development")
        self.enabled: bool = bool(self.dsn and SENTRY_AVAILABLE)

        if self.enabled:
            self._setup_sentry()

    def _setup_sentry(self):
        """Настройка Sentry с интеграциями."""
        sentry_sdk.init(
            dsn=self.dsn,
            environment=self.environment,
            integrations=[
                AioHttpIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Настройки для маскировки чувствительных данных
            before_send=self._before_send_filter,
            before_send_transaction=self._before_send_transaction,
            # Настройки производительности
            traces_sample_rate=0.1,  # 10% транзакций
            profiles_sample_rate=0.1,  # 10% профилей
            # Настройки релизов
            release=os.getenv("RENDER_GIT_COMMIT", "unknown"),
            # Дополнительные теги
            initial_scope={"tags": {"service": "pandapal-bot", "component": "telegram-bot"}},
        )

        logging.info(f"✅ Sentry инициализирован для среды: {self.environment}")

    def _before_send_filter(self, event, hint):
        """
        Фильтрация событий перед отправкой в Sentry.

        Маскирует чувствительные данные и фильтрует неважные ошибки.
        """
        _ = hint  # Sentry передает hint, но мы его не используем
        # Маскируем чувствительные данные в extra
        if "extra" in event:
            for key in ["token", "password", "secret", "key"]:
                if key in event["extra"]:
                    event["extra"][key] = "[MASKED]"
        # Маскируем заголовки запроса с токенами и подписями
        if "request" in event and isinstance(event.get("request"), dict):
            req = event["request"]
            if "headers" in req and isinstance(req["headers"], dict):
                sensitive = ("authorization", "x-telegram-init-data", "cookie")
                for hkey, _ in list(req["headers"].items()):
                    if hkey and any(s in (hkey or "").lower() for s in sensitive):
                        req["headers"][hkey] = "[MASKED]"

        # Фильтруем неважные ошибки
        if "exception" in event:
            exc = event["exception"]
            if exc and exc.get("values"):
                # Игнорируем некоторые типы ошибок
                error_type = exc["values"][0].get("type", "")
                if error_type in ["KeyboardInterrupt", "SystemExit"]:
                    return None

        return event

    def _before_send_transaction(self, event, hint):
        """
        Фильтрация транзакций перед отправкой в Sentry.
        """
        _ = hint  # Sentry передает hint, но мы его не используем
        # Маскируем URL с токенами
        if "request" in event and "url" in event["request"]:
            url = event["request"]["url"]
            if "token=" in url:
                event["request"]["url"] = url.split("token=")[0] + "token=[MASKED]"

        return event

    def capture_exception(self, exc: Exception, **kwargs):
        """Захват исключения в Sentry."""
        if self.enabled:
            sentry_sdk.capture_exception(exc, **kwargs)

    def capture_message(self, message: str, level: str = "info", **kwargs):
        """Захват сообщения в Sentry."""
        if self.enabled:
            sentry_sdk.capture_message(message, level=level, **kwargs)

    def add_breadcrumb(self, message: str, category: str = "info", **kwargs):
        """Добавление хлебных крошек."""
        if self.enabled:
            sentry_sdk.add_breadcrumb(message=message, category=category, **kwargs)

    def set_user_context(self, user_id: str, **kwargs):
        """Установка контекста пользователя."""
        if self.enabled:
            sentry_sdk.set_user({"id": user_id, **kwargs})

    def set_tag(self, key: str, value: str):
        """Установка тега."""
        if self.enabled:
            sentry_sdk.set_tag(key, value)

    def set_context(self, key: str, value: dict):
        """Установка контекста."""
        if self.enabled:
            sentry_sdk.set_context(key, value)


# Глобальный экземпляр конфигурации Sentry
sentry_config = SentryConfig()


def get_sentry_config() -> SentryConfig:
    """
    Получить конфигурацию Sentry.

    Returns:
        SentryConfig: Экземпляр конфигурации Sentry
    """
    return sentry_config


def is_sentry_enabled() -> bool:
    """
    Проверить, включен ли Sentry.

    Returns:
        bool: True если Sentry включен
    """
    return sentry_config.enabled


# Утилиты для быстрого использования
def capture_error(exc: Exception, user_id: str | None = None, **kwargs):
    """Быстрый захват ошибки."""
    if user_id:
        sentry_config.set_user_context(user_id)
    sentry_config.capture_exception(exc, **kwargs)


def capture_info(message: str, user_id: str | None = None, **kwargs):
    """Быстрый захват информационного сообщения."""
    if user_id:
        sentry_config.set_user_context(user_id)
    sentry_config.capture_message(message, level="info", **kwargs)


def capture_warning(message: str, user_id: str | None = None, **kwargs):
    """Быстрый захват предупреждения."""
    if user_id:
        sentry_config.set_user_context(user_id)
    sentry_config.capture_message(message, level="warning", **kwargs)


def add_breadcrumb(message: str, category: str = "info", **kwargs):
    """Быстрое добавление хлебных крошек."""
    sentry_config.add_breadcrumb(message, category, **kwargs)


# Декоратор для автоматического захвата ошибок
def sentry_capture_errors(func):
    """
    Декоратор для автоматического захвата ошибок в Sentry.
    """
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            capture_error(e)
            raise

    return wrapper


# Инициализация при импорте
if __name__ != "__main__":
    if sentry_config.enabled:
        logging.info("🛡️ Sentry мониторинг активен")
    else:
        logging.info("🛡️ Sentry мониторинг отключен")
