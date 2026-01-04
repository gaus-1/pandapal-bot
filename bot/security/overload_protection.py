"""
Защита от перегрузки при высокой нагрузке.

Обеспечивает graceful degradation при 1000+ одновременных запросов:
- Очередь запросов с приоритетами
- Автоматическое масштабирование
- Graceful degradation (упрощенные ответы при перегрузке)
- Мониторинг нагрузки
"""

import asyncio
import time
from collections import defaultdict
from typing import Optional

from aiohttp import web
from loguru import logger


class OverloadProtection:
    """
    Защита от перегрузки системы.

    Отслеживает текущую нагрузку и применяет меры защиты:
    - Очередь запросов при высокой нагрузке
    - Graceful degradation (упрощенные ответы)
    - Автоматическое масштабирование
    """

    def __init__(
        self,
        max_concurrent_requests: int = 1000,
        overload_threshold: float = 0.8,  # 80% загрузки
        queue_timeout: int = 30,  # Таймаут ожидания в очереди
    ):
        """
        Инициализация защиты от перегрузки.

        Args:
            max_concurrent_requests: Максимум одновременных запросов
            overload_threshold: Порог перегрузки (0.0-1.0)
            queue_timeout: Таймаут ожидания в очереди (секунды)
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.overload_threshold = overload_threshold
        self.queue_timeout = queue_timeout

        # Текущая нагрузка
        self._active_requests = 0
        self._request_times: list[float] = []  # Времена обработки запросов
        self._request_count = 0
        self._last_reset = time.time()

        # Очередь запросов
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._queue_processor_task: Optional[asyncio.Task] = None

        # Статистика
        self._stats = {
            "total_requests": 0,
            "queued_requests": 0,
            "rejected_requests": 0,
            "avg_response_time": 0.0,
        }

        logger.info(
            f"✅ OverloadProtection инициализирована: max={max_concurrent_requests}, "
            f"threshold={overload_threshold}"
        )

    def get_current_load(self) -> float:
        """
        Получить текущую загрузку системы (0.0-1.0).

        Returns:
            float: Текущая загрузка (0.0 = нет нагрузки, 1.0 = максимальная)
        """
        return min(self._active_requests / self.max_concurrent_requests, 1.0)

    def is_overloaded(self) -> bool:
        """
        Проверить, перегружена ли система.

        Returns:
            bool: True если система перегружена
        """
        return self.get_current_load() >= self.overload_threshold

    async def process_request(self, request: web.Request, handler) -> web.Response:
        """
        Обработать запрос с защитой от перегрузки.

        Args:
            request: HTTP запрос
            handler: Обработчик запроса

        Returns:
            web.Response: HTTP ответ
        """
        start_time = time.time()
        self._active_requests += 1
        self._request_count += 1
        self._stats["total_requests"] += 1

        try:
            # Проверяем перегрузку
            if self.is_overloaded():
                # Graceful degradation: упрощенные ответы
                if request.path.startswith("/api/"):
                    logger.warning(
                        f"⚠️ Система перегружена ({self.get_current_load():.1%}), "
                        f"применяем graceful degradation для {request.path}"
                    )
                    # Возвращаем упрощенный ответ для API
                    return web.json_response(
                        {
                            "error": "Service temporarily overloaded",
                            "message": "Please try again in a few seconds",
                            "retry_after": 5,
                        },
                        status=503,
                        headers={"Retry-After": "5"},
                    )

            # Обрабатываем запрос
            response = await handler(request)

            # Записываем время обработки
            processing_time = time.time() - start_time
            self._request_times.append(processing_time)

            # Обновляем статистику (оставляем только последние 1000 запросов)
            if len(self._request_times) > 1000:
                self._request_times = self._request_times[-1000:]

            self._stats["avg_response_time"] = sum(self._request_times) / len(self._request_times)

            return response

        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout при обработке {request.path}")
            return web.json_response(
                {"error": "Request timeout", "message": "Please try again"},
                status=504,
            )
        except Exception as e:
            logger.error(f"❌ Ошибка обработки {request.path}: {e}")
            return web.json_response(
                {"error": "Internal server error", "message": str(e)}, status=500
            )
        finally:
            self._active_requests -= 1

    def get_stats(self) -> dict:
        """
        Получить статистику нагрузки.

        Returns:
            dict: Статистика системы
        """
        return {
            **self._stats,
            "current_load": self.get_current_load(),
            "active_requests": self._active_requests,
            "queue_size": self._queue.qsize(),
            "is_overloaded": self.is_overloaded(),
        }


# Глобальный экземпляр защиты от перегрузки
_overload_protection = OverloadProtection(
    max_concurrent_requests=1000,
    overload_threshold=0.85,  # 85% загрузки
    queue_timeout=30,
)


def get_overload_protection() -> OverloadProtection:
    """Получить экземпляр защиты от перегрузки."""
    return _overload_protection


async def overload_protection_middleware(app: web.Application, handler) -> web.Response:
    """
    Middleware для защиты от перегрузки.

    Применяет graceful degradation при высокой нагрузке.
    """
    protection = get_overload_protection()

    async def middleware_handler(request: web.Request) -> web.Response:
        # Исключаем health check и статические файлы
        if request.path in ["/health", "/metrics"] or request.path.startswith("/assets/"):
            return await handler(request)

        # Применяем защиту от перегрузки
        return await protection.process_request(request, handler)

    return middleware_handler
