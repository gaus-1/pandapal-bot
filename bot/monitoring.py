"""
Модуль мониторинга и метрик для PandaPal
Отслеживает производительность, ошибки и пользовательскую активность
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional

from aiohttp import web

logger = logging.getLogger(__name__)


@dataclass
class Metrics:
    """Метрики производительности"""

    timestamp: datetime
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_connections: int
    error_count: int
    success_count: int


@dataclass
class UserActivity:
    """Активность пользователя"""

    user_id: int
    action: str
    timestamp: datetime
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


class MonitoringService:
    """Сервис мониторинга и метрик"""

    def __init__(self):
        self.metrics_history: list[Metrics] = []
        self.user_activities: list[UserActivity] = []
        self.error_counts: Dict[str, int] = {}
        self.performance_stats: Dict[str, Any] = {}

    def record_metrics(self, metrics: Metrics):
        """Записывает метрики производительности"""
        self.metrics_history.append(metrics)

        # Ограничиваем историю последними 1000 записями
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]

        logger.info(
            f"📊 Метрики записаны: {metrics.response_time_ms}ms, {metrics.memory_usage_mb}MB"
        )

    def record_user_activity(self, activity: UserActivity):
        """Записывает активность пользователя"""
        self.user_activities.append(activity)

        # Ограничиваем историю последними 5000 записями
        if len(self.user_activities) > 5000:
            self.user_activities = self.user_activities[-5000:]

        if not activity.success:
            error_key = f"{activity.action}_{activity.error_message}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        logger.info(f"👤 Активность: {activity.user_id} - {activity.action}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по производительности"""
        if not self.metrics_history:
            return {"status": "no_data"}

        recent_metrics = [
            m for m in self.metrics_history if m.timestamp > datetime.now() - timedelta(hours=1)
        ]

        if not recent_metrics:
            return {"status": "no_recent_data"}

        return {
            "avg_response_time": sum(m.response_time_ms for m in recent_metrics)
            / len(recent_metrics),
            "max_response_time": max(m.response_time_ms for m in recent_metrics),
            "avg_memory_usage": sum(m.memory_usage_mb for m in recent_metrics)
            / len(recent_metrics),
            "error_rate": sum(m.error_count for m in recent_metrics) / len(recent_metrics),
            "total_requests": sum(m.success_count + m.error_count for m in recent_metrics),
            "timestamp": datetime.now().isoformat(),
        }

    def get_user_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Возвращает статистику пользователей"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_activities = [a for a in self.user_activities if a.timestamp > cutoff_time]

        if not recent_activities:
            return {"status": "no_data"}

        unique_users = len(set(a.user_id for a in recent_activities))
        success_rate = sum(1 for a in recent_activities if a.success) / len(recent_activities)

        action_counts = {}
        for activity in recent_activities:
            action_counts[activity.action] = action_counts.get(activity.action, 0) + 1

        return {
            "unique_users": unique_users,
            "total_activities": len(recent_activities),
            "success_rate": success_rate,
            "action_breakdown": action_counts,
            "error_counts": self.error_counts,
            "timestamp": datetime.now().isoformat(),
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Возвращает статус здоровья системы"""
        performance = self.get_performance_summary()

        # Критерии здоровья
        is_healthy = True
        issues = []

        if performance.get("status") != "no_data":
            if performance.get("avg_response_time", 0) > 2000:  # 2 секунды
                is_healthy = False
                issues.append("high_response_time")

            if performance.get("avg_memory_usage", 0) > 500:  # 500MB
                is_healthy = False
                issues.append("high_memory_usage")

            if performance.get("error_rate", 0) > 0.1:  # 10% ошибок
                is_healthy = False
                issues.append("high_error_rate")

        return {
            "healthy": is_healthy,
            "issues": issues,
            "performance": performance,
            "timestamp": datetime.now().isoformat(),
        }


# Глобальный экземпляр сервиса мониторинга
monitoring_service = MonitoringService()


def monitor_performance(func):
    """Декоратор для мониторинга производительности функций"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = _get_memory_usage()

        try:
            result = await func(*args, **kwargs)

            # Записываем успешную метрику
            duration = (time.time() - start_time) * 1000  # в миллисекундах
            memory_used = _get_memory_usage() - start_memory

            metrics = Metrics(
                timestamp=datetime.now(),
                response_time_ms=duration,
                memory_usage_mb=memory_used,
                cpu_usage_percent=_get_cpu_usage(),
                active_connections=_get_active_connections(),
                error_count=0,
                success_count=1,
            )

            monitoring_service.record_metrics(metrics)
            return result

        except Exception as e:
            # Записываем ошибку
            duration = (time.time() - start_time) * 1000

            metrics = Metrics(
                timestamp=datetime.now(),
                response_time_ms=duration,
                memory_usage_mb=_get_memory_usage() - start_memory,
                cpu_usage_percent=_get_cpu_usage(),
                active_connections=_get_active_connections(),
                error_count=1,
                success_count=0,
            )

            monitoring_service.record_metrics(metrics)
            logger.error(f"❌ Ошибка в {func.__name__}: {e}")
            raise

    return wrapper


def log_user_activity(user_id: int, action: str, success: bool = True, error_message: str = None):
    """Логирует активность пользователя"""
    activity = UserActivity(
        user_id=user_id,
        action=action,
        timestamp=datetime.now(),
        success=success,
        error_message=error_message,
    )

    monitoring_service.record_user_activity(activity)


def _get_memory_usage() -> float:
    """Получает использование памяти в MB"""
    try:
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        return 0.0


def _get_cpu_usage() -> float:
    """Получает использование CPU в процентах"""
    try:
        import psutil

        return psutil.cpu_percent()
    except ImportError:
        return 0.0


def _get_active_connections() -> int:
    """Получает количество активных соединений"""
    # Простая реализация - можно расширить
    return len(monitoring_service.user_activities)


# HTTP endpoints для мониторинга
async def health_check(request):
    """Health check endpoint"""
    health = monitoring_service.get_health_status()
    status_code = 200 if health["healthy"] else 503

    return web.json_response(health, status=status_code)


async def metrics_endpoint(request):
    """Endpoint для метрик"""
    performance = monitoring_service.get_performance_summary()
    return web.json_response(performance)


async def user_stats_endpoint(request):
    """Endpoint для статистики пользователей"""
    stats = monitoring_service.get_user_stats()
    return web.json_response(stats)


async def detailed_metrics_endpoint(request):
    """Подробные метрики для администраторов"""
    data = {
        "performance": monitoring_service.get_performance_summary(),
        "user_stats": monitoring_service.get_user_stats(),
        "health": monitoring_service.get_health_status(),
        "error_counts": monitoring_service.error_counts,
        "recent_activities_count": len(monitoring_service.user_activities),
        "metrics_history_count": len(monitoring_service.metrics_history),
    }

    return web.json_response(data)
