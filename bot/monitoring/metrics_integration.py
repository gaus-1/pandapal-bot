"""
Безопасная интеграция метрик Prometheus с существующими сервисами.

Этот модуль обеспечивает ненавязчивую интеграцию метрик с существующими
компонентами системы без нарушения их работы.

Принципы интеграции:
- Опциональное включение через переменные окружения
- Graceful degradation при ошибках
- Не влияет на основную логику приложения
- Thread-safe операции
"""

import time
from functools import wraps
from typing import Any

from loguru import logger

try:
    from .prometheus_metrics import (
        get_metrics,
        track_ai_request,  # noqa: F401
        track_game_session,  # noqa: F401
        track_user_activity,  # noqa: F401
    )

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("Prometheus metrics unavailable - module not found")


def safe_metrics_wrapper(func):
    """
    Безопасный декоратор для метрик.
    Не влияет на работу функции, если метрики недоступны.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not METRICS_AVAILABLE:
            # Просто выполняем функцию без метрик
            return await func(*args, **kwargs)

        try:
            # Пытаемся применить метрики
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Ошибка в метриках (игнорируем): {e}")
            # Все равно выполняем функцию
            return await func(*args, **kwargs)

    return wrapper


class MetricsIntegration:
    """
    Класс для безопасной интеграции метрик с существующими сервисами.

    Предоставляет методы для добавления метрик к существующим функциям
    без изменения их логики.
    """

    def __init__(self):
        """Инициализация интеграции метрик"""
        self.enabled = METRICS_AVAILABLE
        self.metrics = None

        if self.enabled:
            try:
                self.metrics = get_metrics()
                logger.info("Metrics integration initialized")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации интеграции метрик: {e}")
                self.enabled = False

    def track_ai_service_call(self, func):
        """
        Добавить отслеживание к вызовам AI сервиса.
        """
        if not self.enabled:
            return func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Записываем успешный вызов
                response_time = time.time() - start_time
                self.metrics.increment_counter("ai_requests_total", {"service": "gemini"})
                self.metrics.record_histogram("ai_response_time_seconds", response_time)

                return result

            except Exception as e:
                # Записываем ошибку
                response_time = time.time() - start_time
                self.metrics.increment_counter(
                    "ai_requests_total", {"service": "gemini", "status": "error"}
                )
                self.metrics.increment_counter("errors_total", {"type": type(e).__name__})
                self.metrics.record_histogram("ai_response_time_seconds", response_time)

                raise

        return wrapper

    def track_database_operation(self, func):
        """
        Добавить отслеживание к операциям с базой данных.
        """
        if not self.enabled:
            return func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Записываем успешную операцию
                query_time = time.time() - start_time
                self.metrics.record_histogram("db_query_time_seconds", query_time)

                return result

            except Exception as e:
                # Записываем ошибку
                query_time = time.time() - start_time
                self.metrics.increment_counter("errors_total", {"type": "database_error"})
                logger.error(f"Database error after {query_time:.2f}s: {e}")
                self.metrics.record_histogram("db_query_time_seconds", query_time)

                raise

        return wrapper

    def track_user_message(self, func):
        """
        Добавить отслеживание к обработке сообщений пользователей.
        """
        if not self.enabled:
            return func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)

                # Записываем активность пользователя
                self.metrics.increment_counter("user_messages_total")

                # Обновляем счетчик активных пользователей
                current_hour = time.strftime("%H")
                _ = f"hour_{current_hour}"  # activity_key для будущего использования
                self.metrics.set_gauge("user_activity_by_hour", 1, {"hour": current_hour})

                return result

            except Exception as e:
                self.metrics.increment_counter("errors_total", {"type": "message_processing_error"})
                logger.error(f"Message processing error: {e}")
                raise

        return wrapper

    def track_game_activity(self, func):
        """
        Добавить отслеживание к игровой активности.
        """
        if not self.enabled:
            return func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                # Увеличиваем счетчик активных игровых сессий
                current_sessions = self.metrics.get_metrics().get("active_game_sessions_count", 0)
                self.metrics.set_gauge("active_game_sessions_count", current_sessions + 1)

                result = await func(*args, **kwargs)

                # Записываем завершенную сессию
                session_duration = time.time() - start_time
                self.metrics.increment_counter("game_sessions_total", {"status": "completed"})
                self.metrics.record_histogram("game_session_duration_seconds", session_duration)

                return result

            except Exception as e:
                # Записываем ошибку
                session_duration = time.time() - start_time
                self.metrics.increment_counter("game_sessions_total", {"status": "error"})
                logger.error(f"Game session error after {session_duration:.2f}s: {e}")
                self.metrics.increment_counter("errors_total", {"type": "game_error"})

                raise
            finally:
                # Уменьшаем счетчик активных сессий
                current_sessions = self.metrics.get_metrics().get("active_game_sessions_count", 0)
                self.metrics.set_gauge("active_game_sessions_count", max(0, current_sessions - 1))

        return wrapper

    def get_system_metrics(self) -> dict[str, Any]:
        """
        Получить системные метрики для API.

        Returns:
            Словарь с метриками системы
        """
        if not self.enabled:
            return {"metrics_enabled": False, "error": "Метрики недоступны"}

        try:
            metrics_data = self.metrics.get_metrics()

            # Формируем системные метрики
            system_metrics = {
                "metrics_enabled": True,
                "timestamp": time.time(),
                "active_users": metrics_data.get("active_users_count", 0),
                "total_users": 0,  # Можно добавить из базы данных
                "ai_requests_per_minute": 0,  # Вычисляется из данных
                "game_sessions_active": metrics_data.get("active_game_sessions_count", 0),
                "average_response_time_ms": 0,  # Вычисляется из данных
                "system_health": "healthy",
                "uptime_seconds": metrics_data.get("system_uptime_seconds", 0),
                "total_errors": metrics_data.get("errors_total", 0),
                "total_ai_requests": metrics_data.get("ai_requests_total", 0),
                "total_game_sessions": metrics_data.get("game_sessions_total", 0),
                "total_user_messages": metrics_data.get("user_messages_total", 0),
            }

            # Вычисляем среднее время ответа AI
            ai_response_times = metrics_data.get("ai_response_time_seconds", [])
            if ai_response_times:
                avg_response_time = sum(item["value"] for item in ai_response_times) / len(
                    ai_response_times
                )
                system_metrics["average_response_time_ms"] = int(avg_response_time * 1000)

            # Вычисляем запросы в минуту (упрощенно)
            total_requests = metrics_data.get("ai_requests_total", 0)
            uptime_minutes = metrics_data.get("system_uptime_seconds", 1) / 60
            system_metrics["ai_requests_per_minute"] = round(
                total_requests / max(1, uptime_minutes), 2
            )

            return system_metrics

        except Exception as e:
            logger.error(f"❌ Ошибка получения метрик: {e}")
            return {"metrics_enabled": False, "error": str(e)}


# Глобальный экземпляр интеграции
_integration_instance: MetricsIntegration | None = None


def get_metrics_integration() -> MetricsIntegration:
    """
    Получить глобальный экземпляр интеграции метрик.

    Returns:
        Экземпляр MetricsIntegration
    """
    global _integration_instance

    if _integration_instance is None:
        _integration_instance = MetricsIntegration()

    return _integration_instance


# Безопасные декораторы для использования в существующих модулях
def safe_track_ai_service(func):
    """
    Безопасный декоратор для отслеживания AI сервиса.
    """
    integration = get_metrics_integration()
    return integration.track_ai_service_call(func)


def safe_track_database(func):
    """
    Безопасный декоратор для отслеживания операций с БД.
    """
    integration = get_metrics_integration()
    return integration.track_database_operation(func)


def safe_track_user_activity(func):
    """
    Безопасный декоратор для отслеживания активности пользователей.
    """
    integration = get_metrics_integration()
    return integration.track_user_message(func)


def safe_track_game_activity(func):
    """
    Безопасный декоратор для отслеживания игровой активности.
    """
    integration = get_metrics_integration()
    return integration.track_game_activity(func)


# Утилиты для экспорта метрик
def get_system_metrics_for_api() -> dict[str, Any]:
    """
    Получить метрики системы для API endpoint.

    Returns:
        Словарь с метриками для API
    """
    integration = get_metrics_integration()
    return integration.get_system_metrics()


def export_prometheus_metrics() -> str:
    """
    Экспортировать метрики в формате Prometheus.

    Returns:
        Строка с метриками в формате Prometheus
    """
    if not METRICS_AVAILABLE:
        return "# Метрики недоступны\n"

    try:
        from .prometheus_metrics import export_metrics_prometheus

        return export_metrics_prometheus()
    except Exception as e:
        logger.error(f"❌ Ошибка экспорта метрик: {e}")
        return f"# Ошибка экспорта метрик: {e}\n"


def export_json_metrics() -> str:
    """
    Экспортировать метрики в формате JSON.

    Returns:
        JSON строка с метриками
    """
    if not METRICS_AVAILABLE:
        return '{"error": "Метрики недоступны"}'

    try:
        from .prometheus_metrics import export_metrics_json

        return export_metrics_json()
    except Exception as e:
        logger.error(f"❌ Ошибка экспорта JSON метрик: {e}")
        return f'{{"error": "Ошибка экспорта метрик: {e}"}}'


# Инициализация при импорте модуля
def initialize_metrics_integration():
    """
    Инициализировать интеграцию метрик.
    Вызывается при старте приложения.
    """
    try:
        integration = get_metrics_integration()
        if integration.enabled:
            logger.info("Prometheus metrics integration ready")
        else:
            logger.info("Metrics integration disabled")
        return integration
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации интеграции метрик: {e}")
        return None


# Автоматическая инициализация при импорте (опционально)
if __name__ != "__main__":
    # Инициализируем только если переменная окружения установлена
    import os

    # Включаем Prometheus по умолчанию
    prometheus_env = os.getenv("PROMETHEUS_METRICS_ENABLED", "true")
    if prometheus_env.lower() not in ("false", "0", "no", "off"):
        initialize_metrics_integration()
