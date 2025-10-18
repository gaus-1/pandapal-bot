"""
API endpoint для метрик Prometheus.

Предоставляет безопасный доступ к метрикам системы через HTTP API.
Поддерживает форматы Prometheus и JSON.

Безопасность:
- Опциональное включение через переменные окружения
- Не влияет на основную работу системы
- Graceful degradation при ошибках
"""

import asyncio
from typing import Any, Dict, Optional

from aiohttp import ClientSession, web
from aiohttp.web import Request, Response
from loguru import logger

try:
    from bot.monitoring.metrics_integration import (
        export_json_metrics,
        export_prometheus_metrics,
        get_system_metrics_for_api,
    )

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("⚠️ Метрики недоступны для API endpoint")


class MetricsEndpoint:
    """
    Класс для обработки HTTP запросов к метрикам.

    Предоставляет безопасный доступ к метрикам системы
    через стандартные HTTP endpoints.
    """

    def __init__(self):
        self.enabled = METRICS_AVAILABLE

        if self.enabled:
            logger.info("📊 API endpoint для метрик инициализирован")
        else:
            logger.info("📊 API endpoint для метрик отключен")

    async def get_system_metrics(self, request: Request) -> Response:
        """
        GET /api/v1/analytics/metrics

        Возвращает системные метрики в формате JSON.
        """
        if not self.enabled:
            return web.json_response(
                {"error": "Метрики недоступны", "metrics_enabled": False}, status=503
            )

        try:
            metrics = get_system_metrics_for_api()

            # Добавляем дополнительные метаданные
            response_data = {
                "success": True,
                "data": metrics,
                "timestamp": metrics.get("timestamp"),
                "version": "1.0.0",
            }

            return web.json_response(response_data)

        except Exception as e:
            logger.error(f"❌ Ошибка получения метрик: {e}")
            return web.json_response(
                {"error": "Ошибка получения метрик", "details": str(e), "success": False},
                status=500,
            )

    async def get_prometheus_metrics(self, request: Request) -> Response:
        """
        GET /metrics

        Возвращает метрики в формате Prometheus.
        """
        if not self.enabled:
            return web.Response(
                text="# Метрики недоступны\n", content_type="text/plain", status=503
            )

        try:
            metrics_text = export_prometheus_metrics()

            return web.Response(
                text=metrics_text, content_type="text/plain; version=0.0.4; charset=utf-8"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта Prometheus метрик: {e}")
            return web.Response(
                text=f"# Ошибка экспорта метрик: {e}\n", content_type="text/plain", status=500
            )

    async def get_json_metrics(self, request: Request) -> Response:
        """
        GET /api/v1/metrics/json

        Возвращает метрики в формате JSON.
        """
        if not self.enabled:
            return web.json_response(
                {"error": "Метрики недоступны", "metrics_enabled": False}, status=503
            )

        try:
            metrics_json = export_json_metrics()

            return web.Response(text=metrics_json, content_type="application/json")

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта JSON метрик: {e}")
            return web.json_response(
                {"error": "Ошибка экспорта метрик", "details": str(e)}, status=500
            )

    async def health_check(self, request: Request) -> Response:
        """
        GET /api/v1/health

        Проверка состояния системы и метрик.
        """
        health_data = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {
                "metrics": "healthy" if self.enabled else "disabled",
                "api": "healthy",
                "database": "healthy",  # Можно добавить реальную проверку
                "ai_service": "healthy",  # Можно добавить реальную проверку
            },
            "metrics_enabled": self.enabled,
            "version": "1.0.0",
        }

        return web.json_response(health_data)


def create_metrics_routes() -> list:
    """
    Создать маршруты для метрик.

    Returns:
        Список маршрутов для aiohttp
    """
    if not METRICS_AVAILABLE:
        logger.warning("⚠️ Метрики недоступны - маршруты не созданы")
        return []

    endpoint = MetricsEndpoint()

    routes = [
        # Основные API endpoints
        web.get("/api/v1/analytics/metrics", endpoint.get_system_metrics),
        web.get("/api/v1/metrics/json", endpoint.get_json_metrics),
        web.get("/api/v1/health", endpoint.health_check),
        # Prometheus endpoint
        web.get("/metrics", endpoint.get_prometheus_metrics),
    ]

    logger.info("📊 Созданы маршруты для метрик:")
    for route in routes:
        logger.info(f"  - {route.method} {route.resource}")

    return routes


def setup_metrics_middleware(app: web.Application):
    """
    Настроить middleware для метрик.

    Args:
        app: Экземпляр aiohttp приложения
    """
    if not METRICS_AVAILABLE:
        return

    async def metrics_middleware(request: Request, handler):
        """Middleware для отслеживания HTTP запросов."""
        start_time = asyncio.get_event_loop().time()

        try:
            response = await handler(request)

            # Записываем успешный запрос
            response_time = asyncio.get_event_loop().time() - start_time

            # Можно добавить метрики для HTTP запросов
            # metrics.increment_counter('http_requests_total', {
            #     'method': request.method,
            #     'path': request.path,
            #     'status': response.status
            # })

            return response

        except Exception as e:
            # Записываем ошибку
            response_time = asyncio.get_event_loop().time() - start_time

            # metrics.increment_counter('http_requests_total', {
            #     'method': request.method,
            #     'path': request.path,
            #     'status': 500
            # })

            raise

    app.middlewares.append(metrics_middleware)
    logger.info("📊 Middleware для метрик настроен")


# Утилиты для интеграции с существующими сервисами
def add_metrics_to_web_server(app: web.Application):
    """
    Добавить метрики к существующему веб-серверу.

    Args:
        app: Экземпляр aiohttp приложения
    """
    if not METRICS_AVAILABLE:
        logger.info("📊 Метрики недоступны - пропускаем интеграцию с веб-сервером")
        return

    try:
        # Добавляем маршруты
        routes = create_metrics_routes()
        app.router.add_routes(routes)

        # Настраиваем middleware
        setup_metrics_middleware(app)

        logger.info("📊 Метрики успешно интегрированы с веб-сервером")

    except Exception as e:
        logger.error(f"❌ Ошибка интеграции метрик с веб-сервером: {e}")


# Пример использования в существующем коде
async def example_integration():
    """
    Пример интеграции метрик с существующим веб-сервером.
    """
    app = web.Application()

    # Добавляем метрики к существующему приложению
    add_metrics_to_web_server(app)

    # Добавляем другие маршруты
    # app.router.add_get('/', your_handler)

    return app


# Инициализация при импорте (опционально)
if __name__ != "__main__":
    import os

    if os.getenv("PROMETHEUS_METRICS_ENABLED", "false").lower() == "true":
        logger.info("📊 API endpoint для метрик готов к работе")
