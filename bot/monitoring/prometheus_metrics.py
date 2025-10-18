"""
Модуль для сбора метрик Prometheus для PandaPal Bot.

Этот модуль предоставляет безопасный и ненавязчивый способ сбора метрик
для мониторинга производительности и использования системы.

Основные метрики:
- Количество активных пользователей
- Запросы к AI API
- Игровые сессии
- Время ответа системы
- Ошибки и исключения

Безопасность:
- Метрики не содержат персональных данных
- Агрегированные данные только
- Опциональное включение (не влияет на основную работу)
"""

import json
import os
import threading
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Dict, Optional

from loguru import logger

# Глобальный словарь для хранения метрик (thread-safe)
_metrics_lock = threading.Lock()
_metrics_data: Dict[str, Any] = {}


@dataclass
class MetricConfig:
    """Конфигурация для метрик Prometheus."""

    enabled: bool = True
    endpoint: str = "/metrics"
    port: int = 8001
    collect_interval: int = 60  # секунды
    retention_days: int = 7


class PrometheusMetrics:
    """
    Класс для сбора и хранения метрик в формате Prometheus.

    Безопасно интегрируется с существующей системой мониторинга,
    не нарушая работу основных компонентов.
    """

    def __init__(self, config: Optional[MetricConfig] = None):
        """
        Инициализация системы метрик.

        Args:
            config: Конфигурация метрик (опционально)
        """
        self.config = config or MetricConfig()
        self.start_time = time.time()
        self._initialize_metrics()

        if self.config.enabled:
            logger.info("📊 Prometheus метрики включены")
        else:
            logger.info("📊 Prometheus метрики отключены")

    def _initialize_metrics(self):
        """Инициализация базовых метрик."""
        with _metrics_lock:
            _metrics_data.update(
                {
                    # Счетчики
                    "ai_requests_total": 0,
                    "game_sessions_total": 0,
                    "user_messages_total": 0,
                    "errors_total": 0,
                    # Гистограммы (время ответа)
                    "ai_response_time_seconds": [],
                    "game_session_duration_seconds": [],
                    "db_query_time_seconds": [],
                    # Gauge метрики
                    "active_users_count": 0,
                    "active_game_sessions_count": 0,
                    "system_uptime_seconds": 0,
                    "memory_usage_bytes": 0,
                    "cpu_usage_percent": 0,
                    # Метки для детализации
                    "error_types": {},
                    "user_activity_by_hour": {},
                    "popular_commands": {},
                }
            )

    def increment_counter(
        self, metric_name: str, labels: Optional[Dict[str, str]] = None, value: int = 1
    ):
        """
        Увеличить счетчик метрики.

        Args:
            metric_name: Название метрики
            labels: Дополнительные метки
            value: Значение для увеличения
        """
        if not self.config.enabled:
            return

        with _metrics_lock:
            if metric_name in _metrics_data:
                if isinstance(_metrics_data[metric_name], dict):
                    # Для метрик с метками
                    label_key = str(labels) if labels else "default"
                    _metrics_data[metric_name][label_key] = (
                        _metrics_data[metric_name].get(label_key, 0) + value
                    )
                else:
                    # Для простых счетчиков
                    _metrics_data[metric_name] += value

    def record_histogram(
        self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """
        Записать значение в гистограмму.

        Args:
            metric_name: Название метрики
            value: Значение для записи
            labels: Дополнительные метки
        """
        if not self.config.enabled:
            return

        with _metrics_lock:
            if metric_name in _metrics_data and isinstance(_metrics_data[metric_name], list):
                # Ограничиваем количество записей для предотвращения утечек памяти
                if len(_metrics_data[metric_name]) < 1000:
                    _metrics_data[metric_name].append(
                        {"value": value, "timestamp": time.time(), "labels": labels or {}}
                    )
                else:
                    # Удаляем старые записи
                    _metrics_data[metric_name] = _metrics_data[metric_name][-500:]

    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Установить значение gauge метрики.

        Args:
            metric_name: Название метрики
            value: Значение
            labels: Дополнительные метки
        """
        if not self.config.enabled:
            return

        with _metrics_lock:
            if metric_name in _metrics_data:
                if labels:
                    label_key = str(labels)
                    if not isinstance(_metrics_data[metric_name], dict):
                        _metrics_data[metric_name] = {}
                    _metrics_data[metric_name][label_key] = value
                else:
                    _metrics_data[metric_name] = value

    def get_metrics(self) -> Dict[str, Any]:
        """
        Получить все метрики в формате Prometheus.

        Returns:
            Словарь с метриками
        """
        with _metrics_lock:
            # Обновляем системные метрики
            _metrics_data["system_uptime_seconds"] = time.time() - self.start_time

            # Возвращаем копию данных
            return _metrics_data.copy()

    def export_prometheus_format(self) -> str:
        """
        Экспортировать метрики в формате Prometheus.

        Returns:
            Строка с метриками в формате Prometheus
        """
        if not self.config.enabled:
            return "# Метрики отключены\n"

        metrics = self.get_metrics()
        output = []

        # Заголовок
        output.append("# HELP pandapal_bot_metrics PandaPal Bot Prometheus Metrics")
        output.append("# TYPE pandapal_bot_metrics counter")
        output.append("")

        # Счетчики
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and not isinstance(value, dict):
                prom_name = f"pandapal_{metric_name}"
                output.append(f"{prom_name} {value}")
            elif isinstance(value, list) and metric_name.endswith("_seconds"):
                # Гистограммы
                prom_name = f"pandapal_{metric_name}"
                if value:
                    avg_value = sum(item["value"] for item in value) / len(value)
                    output.append(f"{prom_name}_avg {avg_value}")
                    output.append(f"{prom_name}_count {len(value)}")
                    output.append(f"{prom_name}_sum {sum(item['value'] for item in value)}")
            elif isinstance(value, dict) and metric_name.endswith("_count"):
                # Метрики с метками
                prom_name = f"pandapal_{metric_name}"
                for label_key, label_value in value.items():
                    if label_key != "default":
                        output.append(f'{prom_name}{{labels="{label_key}"}} {label_value}')
                    else:
                        output.append(f"{prom_name} {label_value}")

        return "\n".join(output)


# Глобальный экземпляр метрик
_metrics_instance: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """
    Получить глобальный экземпляр метрик.

    Returns:
        Экземпляр PrometheusMetrics
    """
    global _metrics_instance

    if _metrics_instance is None:
        # Проверяем переменную окружения для включения/отключения
        enabled = os.getenv("PROMETHEUS_METRICS_ENABLED", "false").lower() == "true"

        config = MetricConfig(
            enabled=enabled,
            endpoint=os.getenv("PROMETHEUS_ENDPOINT", "/metrics"),
            port=int(os.getenv("PROMETHEUS_PORT", "8001")),
        )

        _metrics_instance = PrometheusMetrics(config)

    return _metrics_instance


def track_ai_request(func):
    """
    Декоратор для отслеживания запросов к AI API.

    Безопасно добавляет метрики к существующим функциям без изменения их логики.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        metrics = get_metrics()
        start_time = time.time()

        try:
            # Выполняем оригинальную функцию
            result = await func(*args, **kwargs)

            # Записываем успешный запрос
            response_time = time.time() - start_time
            metrics.increment_counter("ai_requests_total", {"status": "success"})
            metrics.record_histogram("ai_response_time_seconds", response_time)

            return result

        except Exception as e:
            # Записываем ошибку
            response_time = time.time() - start_time
            metrics.increment_counter("ai_requests_total", {"status": "error"})
            metrics.increment_counter("errors_total", {"type": type(e).__name__})
            metrics.record_histogram("ai_response_time_seconds", response_time)

            # Перебрасываем исключение
            raise

    return wrapper


def track_game_session(func):
    """
    Декоратор для отслеживания игровых сессий.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        metrics = get_metrics()
        start_time = time.time()

        try:
            # Увеличиваем счетчик активных сессий
            metrics.set_gauge(
                "active_game_sessions_count",
                metrics.get_metrics().get("active_game_sessions_count", 0) + 1,
            )

            result = await func(*args, **kwargs)

            # Записываем завершенную сессию
            session_duration = time.time() - start_time
            metrics.increment_counter("game_sessions_total", {"status": "completed"})
            metrics.record_histogram("game_session_duration_seconds", session_duration)

            return result

        except Exception as e:
            # Записываем ошибку
            session_duration = time.time() - start_time
            metrics.increment_counter("game_sessions_total", {"status": "error"})
            metrics.increment_counter("errors_total", {"type": type(e).__name__})

            raise
        finally:
            # Уменьшаем счетчик активных сессий
            metrics.set_gauge(
                "active_game_sessions_count",
                max(0, metrics.get_metrics().get("active_game_sessions_count", 0) - 1),
            )

    return wrapper


def track_user_activity(func):
    """
    Декоратор для отслеживания активности пользователей.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        metrics = get_metrics()

        try:
            result = await func(*args, **kwargs)

            # Записываем активность
            metrics.increment_counter("user_messages_total")

            # Обновляем счетчик активных пользователей (упрощенно)
            current_hour = time.strftime("%H")
            metrics.set_gauge("user_activity_by_hour", 1, {"hour": current_hour})

            return result

        except Exception as e:
            metrics.increment_counter("errors_total", {"type": type(e).__name__})
            raise

    return wrapper


# Утилиты для экспорта метрик
def export_metrics_json() -> str:
    """
    Экспортировать метрики в формате JSON для API.

    Returns:
        JSON строка с метриками
    """
    metrics = get_metrics()
    return json.dumps(metrics.get_metrics(), indent=2, default=str)


def export_metrics_prometheus() -> str:
    """
    Экспортировать метрики в формате Prometheus.

    Returns:
        Строка с метриками в формате Prometheus
    """
    metrics = get_metrics()
    return metrics.export_prometheus_format()


# Безопасная инициализация
def initialize_metrics():
    """
    Инициализировать систему метрик.
    Вызывается при старте приложения.
    """
    try:
        metrics = get_metrics()
        logger.info("📊 Система метрик Prometheus инициализирована")
        return metrics
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации метрик: {e}")
        return None
