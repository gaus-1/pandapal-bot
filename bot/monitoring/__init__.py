"""
Модуль мониторинга PandaPal Bot.

Обеспечивает:
- Prometheus метрики для мониторинга производительности
- Legacy функции для совместимости с существующим кодом
- Интеграцию с внешними системами мониторинга
"""

# Re-export legacy (monitoring_legacy) для обратной совместимости; новый код — metrics_integration/prometheus_metrics
# Интеграция метрик
from bot.monitoring.metrics_integration import (
    MetricsIntegration,
    export_json_metrics,
    export_prometheus_metrics,
    get_metrics_integration,
    get_system_metrics_for_api,
    initialize_metrics_integration,
    safe_metrics_wrapper,
    safe_track_ai_service,
    safe_track_database,
    safe_track_game_activity,
    safe_track_user_activity,
)

# Prometheus метрики
from bot.monitoring.prometheus_metrics import (
    MetricConfig,
    PrometheusMetrics,
    export_metrics_json,
    export_metrics_prometheus,
    get_metrics,
    initialize_metrics,
    track_ai_request,
    track_game_session,
    track_user_activity,
)
from bot.monitoring_legacy import (
    Metrics,
    MonitoringService,
    UserActivity,
    detailed_metrics_endpoint,
    health_check,
    log_user_activity,
    metrics_endpoint,
    monitor_performance,
    monitoring_service,
    user_stats_endpoint,
)

__all__ = [
    # Legacy
    "Metrics",
    "UserActivity",
    "MonitoringService",
    "monitoring_service",
    "monitor_performance",
    "log_user_activity",
    "health_check",
    "metrics_endpoint",
    "user_stats_endpoint",
    "detailed_metrics_endpoint",
    # Prometheus
    "MetricConfig",
    "PrometheusMetrics",
    "get_metrics",
    "track_ai_request",
    "track_game_session",
    "track_user_activity",
    "export_metrics_json",
    "export_metrics_prometheus",
    "initialize_metrics",
    # Integration
    "MetricsIntegration",
    "get_metrics_integration",
    "safe_metrics_wrapper",
    "safe_track_ai_service",
    "safe_track_database",
    "safe_track_user_activity",
    "safe_track_game_activity",
    "get_system_metrics_for_api",
    "export_prometheus_metrics",
    "export_json_metrics",
    "initialize_metrics_integration",
]
