"""
Тесты для Prometheus метрик.

Проверяет:
- Инициализацию метрик
- Счетчики, гистограммы, gauge метрики
- Экспорт в Prometheus и JSON форматах
- Декораторы для отслеживания
- Интеграцию метрик
"""

import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestPrometheusMetrics:
    """Тесты для PrometheusMetrics класса."""

    @pytest.mark.unit
    def test_metrics_initialization(self):
        """Проверка инициализации метрик."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=True, endpoint="/metrics", port=8001)
        metrics = PrometheusMetrics(config)

        assert metrics.config.enabled is True
        assert metrics.config.endpoint == "/metrics"
        assert metrics.start_time > 0

    @pytest.mark.unit
    def test_metrics_disabled(self):
        """Проверка отключенных метрик."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=False)
        metrics = PrometheusMetrics(config)

        # Счетчики не должны увеличиваться при отключенных метриках
        metrics.increment_counter("test_counter")
        data = metrics.get_metrics()
        assert data.get("test_counter", 0) == 0

    @pytest.mark.unit
    def test_increment_counter(self):
        """Проверка инкремента счетчика."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=True)
        metrics = PrometheusMetrics(config)

        metrics.increment_counter("ai_requests_total")
        metrics.increment_counter("ai_requests_total")

        data = metrics.get_metrics()
        assert data["ai_requests_total"] == 2

    @pytest.mark.unit
    def test_increment_counter_with_labels(self):
        """Проверка инкремента счетчика с метками."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=True)
        metrics = PrometheusMetrics(config)

        metrics.increment_counter("errors_total", {"type": "ValueError"})
        metrics.increment_counter("errors_total", {"type": "ValueError"})
        metrics.increment_counter("errors_total", {"type": "TypeError"})

        data = metrics.get_metrics()
        error_types = data.get("error_types", {})
        assert isinstance(error_types, dict)

    @pytest.mark.unit
    def test_record_histogram(self):
        """Проверка записи в гистограмму."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=True)
        metrics = PrometheusMetrics(config)

        metrics.record_histogram("ai_response_time_seconds", 0.5)
        metrics.record_histogram("ai_response_time_seconds", 1.0)
        metrics.record_histogram("ai_response_time_seconds", 0.3)

        data = metrics.get_metrics()
        assert len(data["ai_response_time_seconds"]) == 3

    @pytest.mark.unit
    def test_set_gauge(self):
        """Проверка установки gauge метрики."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=True)
        metrics = PrometheusMetrics(config)

        metrics.set_gauge("active_users_count", 10)
        data = metrics.get_metrics()
        assert data["active_users_count"] == 10

        metrics.set_gauge("active_users_count", 15)
        data = metrics.get_metrics()
        assert data["active_users_count"] == 15

    @pytest.mark.unit
    def test_export_prometheus_format(self):
        """Проверка экспорта в формате Prometheus."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=True)
        metrics = PrometheusMetrics(config)

        metrics.increment_counter("ai_requests_total")
        metrics.set_gauge("active_users_count", 5)

        prometheus_text = metrics.export_prometheus_format()

        assert "pandapal_ai_requests_total" in prometheus_text
        assert "pandapal_active_users_count" in prometheus_text
        assert "# HELP" in prometheus_text

    @pytest.mark.unit
    def test_export_prometheus_disabled(self):
        """Проверка экспорта при отключенных метриках."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=False)
        metrics = PrometheusMetrics(config)

        prometheus_text = metrics.export_prometheus_format()
        assert "отключены" in prometheus_text

    @pytest.mark.unit
    def test_histogram_limit(self):
        """Проверка лимита записей в гистограмме."""
        from bot.monitoring.prometheus_metrics import MetricConfig, PrometheusMetrics

        config = MetricConfig(enabled=True)
        metrics = PrometheusMetrics(config)

        # Записываем больше лимита
        for i in range(1100):
            metrics.record_histogram("ai_response_time_seconds", 0.1 * i)

        data = metrics.get_metrics()
        # Должно быть не больше 1000 записей (или 500 после очистки)
        assert len(data["ai_response_time_seconds"]) <= 1000


class TestGlobalMetrics:
    """Тесты для глобальных функций метрик."""

    @pytest.mark.unit
    def test_get_metrics_singleton(self):
        """Проверка singleton паттерна."""
        from bot.monitoring.prometheus_metrics import get_metrics

        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2

    @pytest.mark.unit
    def test_export_metrics_json(self):
        """Проверка экспорта в JSON."""
        from bot.monitoring.prometheus_metrics import export_metrics_json, get_metrics

        metrics = get_metrics()
        metrics.increment_counter("user_messages_total")

        json_str = export_metrics_json()
        data = json.loads(json_str)

        assert isinstance(data, dict)
        assert "user_messages_total" in data

    @pytest.mark.unit
    def test_export_metrics_prometheus(self):
        """Проверка экспорта в Prometheus формате."""
        from bot.monitoring.prometheus_metrics import export_metrics_prometheus

        prometheus_text = export_metrics_prometheus()

        assert isinstance(prometheus_text, str)
        assert "pandapal_" in prometheus_text

    @pytest.mark.unit
    def test_initialize_metrics(self):
        """Проверка инициализации метрик."""
        from bot.monitoring.prometheus_metrics import initialize_metrics

        metrics = initialize_metrics()
        assert metrics is not None


class TestMetricsDecorators:
    """Тесты для декораторов метрик."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_track_ai_request_success(self):
        """Проверка декоратора track_ai_request при успехе."""
        from bot.monitoring.prometheus_metrics import get_metrics, track_ai_request

        @track_ai_request
        async def mock_ai_call():
            return "AI response"

        metrics = get_metrics()
        initial_count = metrics.get_metrics().get("ai_requests_total", 0)

        result = await mock_ai_call()

        assert result == "AI response"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_track_ai_request_error(self):
        """Проверка декоратора track_ai_request при ошибке."""
        from bot.monitoring.prometheus_metrics import get_metrics, track_ai_request

        @track_ai_request
        async def failing_ai_call():
            raise ValueError("AI error")

        with pytest.raises(ValueError):
            await failing_ai_call()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_track_game_session(self):
        """Проверка декоратора track_game_session."""
        from bot.monitoring.prometheus_metrics import get_metrics, track_game_session

        @track_game_session
        async def mock_game():
            return "game result"

        result = await mock_game()
        assert result == "game result"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_track_user_activity(self):
        """Проверка декоратора track_user_activity."""
        from bot.monitoring.prometheus_metrics import (
            get_metrics,
            track_user_activity as prom_track_user_activity,
        )

        @prom_track_user_activity
        async def mock_user_action():
            return "action done"

        result = await mock_user_action()
        assert result == "action done"


class TestMetricsIntegration:
    """Тесты для интеграции метрик."""

    @pytest.mark.unit
    def test_metrics_integration_init(self):
        """Проверка инициализации интеграции метрик."""
        from bot.monitoring.metrics_integration import MetricsIntegration

        integration = MetricsIntegration()
        assert integration.enabled is True

    @pytest.mark.unit
    def test_get_metrics_integration_singleton(self):
        """Проверка singleton паттерна для интеграции."""
        from bot.monitoring.metrics_integration import get_metrics_integration

        integration1 = get_metrics_integration()
        integration2 = get_metrics_integration()

        assert integration1 is integration2

    @pytest.mark.unit
    def test_get_system_metrics(self):
        """Проверка получения системных метрик."""
        from bot.monitoring.metrics_integration import get_system_metrics_for_api

        metrics = get_system_metrics_for_api()

        assert isinstance(metrics, dict)
        assert "metrics_enabled" in metrics
        assert "timestamp" in metrics

    @pytest.mark.unit
    def test_export_prometheus_metrics(self):
        """Проверка экспорта Prometheus метрик."""
        from bot.monitoring.metrics_integration import export_prometheus_metrics

        text = export_prometheus_metrics()

        assert isinstance(text, str)

    @pytest.mark.unit
    def test_export_json_metrics(self):
        """Проверка экспорта JSON метрик."""
        from bot.monitoring.metrics_integration import export_json_metrics

        json_str = export_json_metrics()
        data = json.loads(json_str)

        assert isinstance(data, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_safe_track_ai_service(self):
        """Проверка безопасного декоратора для AI сервиса."""
        from bot.monitoring.metrics_integration import safe_track_ai_service

        @safe_track_ai_service
        async def mock_ai_service():
            return "AI result"

        result = await mock_ai_service()
        assert result == "AI result"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_safe_track_database(self):
        """Проверка безопасного декоратора для БД."""
        from bot.monitoring.metrics_integration import safe_track_database

        @safe_track_database
        async def mock_db_query():
            return {"id": 1}

        result = await mock_db_query()
        assert result == {"id": 1}


class TestMetricsEndpoint:
    """Тесты для API endpoint метрик."""

    @pytest.mark.unit
    def test_create_metrics_routes(self):
        """Проверка создания маршрутов метрик."""
        from bot.api.metrics_endpoint import create_metrics_routes

        routes = create_metrics_routes()

        assert isinstance(routes, list)
        assert len(routes) > 0

    @pytest.mark.unit
    def test_metrics_endpoint_init(self):
        """Проверка инициализации endpoint метрик."""
        from bot.api.metrics_endpoint import MetricsEndpoint

        endpoint = MetricsEndpoint()
        assert endpoint.enabled is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_prometheus_metrics_endpoint(self):
        """Проверка Prometheus endpoint."""
        from bot.api.metrics_endpoint import MetricsEndpoint

        endpoint = MetricsEndpoint()
        mock_request = Mock()

        response = await endpoint.get_prometheus_metrics(mock_request)

        assert response.status == 200
        assert "text/plain" in response.content_type

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_json_metrics_endpoint(self):
        """Проверка JSON metrics endpoint."""
        from bot.api.metrics_endpoint import MetricsEndpoint

        endpoint = MetricsEndpoint()
        mock_request = Mock()

        response = await endpoint.get_json_metrics(mock_request)

        assert response.status == 200
        assert "application/json" in response.content_type

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_system_metrics_endpoint(self):
        """Проверка system metrics endpoint."""
        from bot.api.metrics_endpoint import MetricsEndpoint

        endpoint = MetricsEndpoint()
        mock_request = Mock()

        response = await endpoint.get_system_metrics(mock_request)

        assert response.status == 200


class TestLegacyCompatibility:
    """Тесты совместимости с legacy кодом."""

    @pytest.mark.unit
    def test_legacy_imports_from_monitoring(self):
        """Проверка legacy импортов из bot.monitoring."""
        from bot.monitoring import (
            Metrics,
            MonitoringService,
            UserActivity,
            log_user_activity,
            monitor_performance,
            monitoring_service,
        )

        assert Metrics is not None
        assert UserActivity is not None
        assert MonitoringService is not None
        assert monitoring_service is not None
        assert log_user_activity is not None
        assert monitor_performance is not None

    @pytest.mark.unit
    def test_prometheus_imports_from_monitoring(self):
        """Проверка Prometheus импортов из bot.monitoring."""
        from bot.monitoring import (
            MetricConfig,
            PrometheusMetrics,
            export_metrics_json,
            export_metrics_prometheus,
            get_metrics,
        )

        assert MetricConfig is not None
        assert PrometheusMetrics is not None
        assert get_metrics is not None
        assert export_metrics_json is not None
        assert export_metrics_prometheus is not None

    @pytest.mark.unit
    def test_integration_imports_from_monitoring(self):
        """Проверка импортов интеграции из bot.monitoring."""
        from bot.monitoring import (
            MetricsIntegration,
            get_metrics_integration,
            safe_track_ai_service,
            safe_track_database,
        )

        assert MetricsIntegration is not None
        assert get_metrics_integration is not None
        assert safe_track_ai_service is not None
        assert safe_track_database is not None

    @pytest.mark.unit
    def test_log_user_activity(self):
        """Проверка log_user_activity."""
        from bot.monitoring import log_user_activity

        # Не должно вызывать ошибок
        log_user_activity(123, "test_action", True)
        log_user_activity(456, "another_action", False, "error message")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitor_performance_decorator(self):
        """Проверка monitor_performance декоратора."""
        from bot.monitoring import monitor_performance

        @monitor_performance
        async def test_func(message, state=None):
            return "result"

        mock_message = Mock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123

        result = await test_func(mock_message)
        assert result == "result"
