"""
Скрипт нагрузочного тестирования для PandaPal Bot.

Безопасно тестирует систему под нагрузкой, не нарушая работу production.
Включает тестирование AI API, базы данных и веб-сервера.

Особенности:
- Конфигурируемая нагрузка
- Безопасное тестирование (не влияет на production)
- Подробная отчетность
- Graceful degradation при ошибках
"""

import argparse
import asyncio
import json
import os
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger


@dataclass
class TestResult:
    """Результат одного теста."""

    test_name: str
    success: bool
    response_time_ms: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    response_size_bytes: Optional[int] = None


@dataclass
class LoadTestConfig:
    """Конфигурация нагрузочного тестирования."""

    base_url: str = "http://localhost:8000"
    concurrent_users: int = 10
    requests_per_user: int = 10
    test_duration_seconds: int = 60
    ramp_up_seconds: int = 10
    timeout_seconds: int = 30

    # Endpoints для тестирования
    endpoints: List[str] = None

    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = [
                "/api/v1/health",
                "/api/v1/analytics/metrics",
            ]


class LoadTester:
    """
    Класс для проведения нагрузочного тестирования.

    Безопасно тестирует различные компоненты системы
    под контролируемой нагрузкой.
    """

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        # Статистика
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        logger.info(f"🧪 Нагрузочное тестирование настроено:")
        logger.info(f"  - URL: {config.base_url}")
        logger.info(f"  - Пользователей: {config.concurrent_users}")
        logger.info(f"  - Запросов на пользователя: {config.requests_per_user}")
        logger.info(f"  - Длительность: {config.test_duration_seconds}с")

    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: str) -> TestResult:
        """
        Тестирование одного endpoint.

        Args:
            session: HTTP сессия
            endpoint: URL endpoint для тестирования

        Returns:
            TestResult: Результат теста
        """
        url = f"{self.config.base_url}{endpoint}"
        start_time = time.time()

        try:
            async with session.get(url, timeout=self.config.timeout_seconds) as response:
                response_time = (time.time() - start_time) * 1000
                response_text = await response.text()

                return TestResult(
                    test_name=endpoint,
                    success=200 <= response.status < 400,
                    response_time_ms=response_time,
                    status_code=response.status,
                    response_size_bytes=len(response_text.encode("utf-8")),
                )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                test_name=endpoint,
                success=False,
                response_time_ms=response_time,
                error_message="Timeout",
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                test_name=endpoint,
                success=False,
                response_time_ms=response_time,
                error_message=str(e),
            )

    async def simulate_user(self, user_id: int) -> List[TestResult]:
        """
        Симуляция одного пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            List[TestResult]: Результаты тестов пользователя
        """
        user_results = []

        async with aiohttp.ClientSession() as session:
            for request_num in range(self.config.requests_per_user):
                # Выбираем endpoint для тестирования
                endpoint = self.config.endpoints[request_num % len(self.config.endpoints)]

                # Тестируем endpoint
                result = await self.test_endpoint(session, endpoint)
                result.test_name = f"user_{user_id}_{result.test_name}"
                user_results.append(result)

                # Небольшая задержка между запросами
                await asyncio.sleep(0.1)

        return user_results

    async def run_load_test(self) -> Dict[str, Any]:
        """
        Запуск нагрузочного тестирования.

        Returns:
            Dict[str, Any]: Результаты тестирования
        """
        logger.info("🚀 Запуск нагрузочного тестирования...")

        self.start_time = time.time()

        # Создаем задачи для всех пользователей
        tasks = []
        for user_id in range(self.config.concurrent_users):
            task = asyncio.create_task(self.simulate_user(user_id))
            tasks.append(task)

            # Постепенное увеличение нагрузки (ramp-up)
            if user_id < self.config.concurrent_users - 1:
                await asyncio.sleep(self.config.ramp_up_seconds / self.config.concurrent_users)

        # Ждем завершения всех задач или истечения времени
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.test_duration_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning("⏰ Время тестирования истекло")

        self.end_time = time.time()

        # Собираем результаты
        for task in tasks:
            if not task.done():
                task.cancel()
            else:
                try:
                    user_results = task.result()
                    if isinstance(user_results, list):
                        self.results.extend(user_results)
                except Exception as e:
                    logger.error(f"❌ Ошибка в задаче: {e}")

        # Анализируем результаты
        return self.analyze_results()

    def analyze_results(self) -> Dict[str, Any]:
        """
        Анализ результатов тестирования.

        Returns:
            Dict[str, Any]: Анализ результатов
        """
        if not self.results:
            return {"error": "Нет результатов для анализа"}

        # Общая статистика
        self.total_requests = len(self.results)
        self.successful_requests = sum(1 for r in self.results if r.success)
        self.failed_requests = self.total_requests - self.successful_requests

        # Время ответа
        response_times = [r.response_time_ms for r in self.results]

        # Статистика по endpoint'ам
        endpoint_stats = {}
        for result in self.results:
            endpoint = (
                result.test_name.split("_", 2)[-1] if "_" in result.test_name else result.test_name
            )
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "response_times": [],
                    "errors": [],
                }

            endpoint_stats[endpoint]["total_requests"] += 1
            if result.success:
                endpoint_stats[endpoint]["successful_requests"] += 1
                endpoint_stats[endpoint]["response_times"].append(result.response_time_ms)
            else:
                endpoint_stats[endpoint]["errors"].append(result.error_message)

        # Вычисляем статистики для каждого endpoint
        for endpoint, stats in endpoint_stats.items():
            if stats["response_times"]:
                stats["avg_response_time_ms"] = statistics.mean(stats["response_times"])
                stats["min_response_time_ms"] = min(stats["response_times"])
                stats["max_response_time_ms"] = max(stats["response_times"])
                stats["median_response_time_ms"] = statistics.median(stats["response_times"])
                if len(stats["response_times"]) > 1:
                    stats["std_deviation_ms"] = statistics.stdev(stats["response_times"])

            stats["success_rate_percent"] = (
                stats["successful_requests"] / stats["total_requests"]
            ) * 100

        # Общая статистика
        test_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        requests_per_second = self.total_requests / test_duration if test_duration > 0 else 0

        analysis = {
            "test_config": asdict(self.config),
            "test_summary": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate_percent": (self.successful_requests / self.total_requests) * 100,
                "test_duration_seconds": test_duration,
                "requests_per_second": requests_per_second,
                "concurrent_users": self.config.concurrent_users,
            },
            "response_time_stats": (
                {
                    "avg_response_time_ms": statistics.mean(response_times),
                    "min_response_time_ms": min(response_times),
                    "max_response_time_ms": max(response_times),
                    "median_response_time_ms": statistics.median(response_times),
                    "p95_response_time_ms": self._percentile(response_times, 95),
                    "p99_response_time_ms": self._percentile(response_times, 99),
                }
                if response_times
                else {}
            ),
            "endpoint_stats": endpoint_stats,
            "test_timestamp": datetime.now().isoformat(),
        }

        return analysis

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Вычисление процентиля."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def generate_report(self, analysis: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Генерация отчета о тестировании.

        Args:
            analysis: Результаты анализа
            output_file: Файл для сохранения отчета

        Returns:
            str: Текст отчета
        """
        report_lines = []

        # Заголовок
        report_lines.append("=" * 80)
        report_lines.append("🧪 ОТЧЕТ О НАГРУЗОЧНОМ ТЕСТИРОВАНИИ PANDA PAL BOT")
        report_lines.append("=" * 80)
        report_lines.append(f"Время тестирования: {analysis['test_timestamp']}")
        report_lines.append("")

        # Конфигурация теста
        config = analysis["test_config"]
        report_lines.append("📋 КОНФИГУРАЦИЯ ТЕСТА:")
        report_lines.append(f"  URL: {config['base_url']}")
        report_lines.append(f"  Пользователей: {config['concurrent_users']}")
        report_lines.append(f"  Запросов на пользователя: {config['requests_per_user']}")
        report_lines.append(f"  Длительность: {config['test_duration_seconds']}с")
        report_lines.append("")

        # Общая статистика
        summary = analysis["test_summary"]
        report_lines.append("📊 ОБЩАЯ СТАТИСТИКА:")
        report_lines.append(f"  Всего запросов: {summary['total_requests']}")
        report_lines.append(f"  Успешных запросов: {summary['successful_requests']}")
        report_lines.append(f"  Неудачных запросов: {summary['failed_requests']}")
        report_lines.append(f"  Процент успеха: {summary['success_rate_percent']:.2f}%")
        report_lines.append(f"  Длительность теста: {summary['test_duration_seconds']:.2f}с")
        report_lines.append(f"  Запросов в секунду: {summary['requests_per_second']:.2f}")
        report_lines.append("")

        # Статистика времени ответа
        if "response_time_stats" in analysis and analysis["response_time_stats"]:
            rt_stats = analysis["response_time_stats"]
            report_lines.append("⏱️ ВРЕМЯ ОТВЕТА:")
            report_lines.append(f"  Среднее: {rt_stats['avg_response_time_ms']:.2f}мс")
            report_lines.append(f"  Минимальное: {rt_stats['min_response_time_ms']:.2f}мс")
            report_lines.append(f"  Максимальное: {rt_stats['max_response_time_ms']:.2f}мс")
            report_lines.append(f"  Медиана: {rt_stats['median_response_time_ms']:.2f}мс")
            report_lines.append(f"  95-й процентиль: {rt_stats['p95_response_time_ms']:.2f}мс")
            report_lines.append(f"  99-й процентиль: {rt_stats['p99_response_time_ms']:.2f}мс")
            report_lines.append("")

        # Статистика по endpoint'ам
        if "endpoint_stats" in analysis:
            report_lines.append("🔗 СТАТИСТИКА ПО ENDPOINT'АМ:")
            for endpoint, stats in analysis["endpoint_stats"].items():
                report_lines.append(f"  {endpoint}:")
                report_lines.append(f"    Запросов: {stats['total_requests']}")
                report_lines.append(f"    Успешных: {stats['successful_requests']}")
                report_lines.append(f"    Процент успеха: {stats['success_rate_percent']:.2f}%")
                if "avg_response_time_ms" in stats:
                    report_lines.append(
                        f"    Среднее время ответа: {stats['avg_response_time_ms']:.2f}мс"
                    )
                if stats["errors"]:
                    report_lines.append(f"    Ошибки: {len(set(stats['errors']))}")
                report_lines.append("")

        # Рекомендации
        report_lines.append("💡 РЕКОМЕНДАЦИИ:")
        if summary["success_rate_percent"] < 95:
            report_lines.append("  ⚠️ Низкий процент успеха - проверить стабильность системы")
        if (
            "response_time_stats" in analysis
            and analysis["response_time_stats"]["avg_response_time_ms"] > 1000
        ):
            report_lines.append("  ⚠️ Высокое время ответа - оптимизировать производительность")
        if summary["requests_per_second"] < 10:
            report_lines.append("  ⚠️ Низкая пропускная способность - увеличить ресурсы")

        if summary["success_rate_percent"] >= 95 and summary["requests_per_second"] >= 10:
            report_lines.append("  ✅ Система показывает хорошую производительность")

        report_lines.append("")
        report_lines.append("=" * 80)

        report_text = "\n".join(report_lines)

        # Сохраняем отчет в файл
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            logger.info(f"📄 Отчет сохранен в файл: {output_file}")

        return report_text


async def main():
    """Главная функция для запуска нагрузочного тестирования."""
    parser = argparse.ArgumentParser(description="Нагрузочное тестирование PandaPal Bot")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Базовый URL для тестирования"
    )
    parser.add_argument(
        "--users", type=int, default=10, help="Количество одновременных пользователей"
    )
    parser.add_argument("--requests", type=int, default=10, help="Запросов на пользователя")
    parser.add_argument("--duration", type=int, default=60, help="Длительность теста в секундах")
    parser.add_argument("--output", help="Файл для сохранения отчета")
    parser.add_argument("--endpoints", nargs="+", help="Список endpoint'ов для тестирования")

    args = parser.parse_args()

    # Создаем конфигурацию
    config = LoadTestConfig(
        base_url=args.url,
        concurrent_users=args.users,
        requests_per_user=args.requests,
        test_duration_seconds=args.duration,
    )

    if args.endpoints:
        config.endpoints = args.endpoints

    # Создаем тестер
    tester = LoadTester(config)

    try:
        # Запускаем тестирование
        analysis = await tester.run_load_test()

        # Генерируем отчет
        output_file = (
            args.output or f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        report = tester.generate_report(analysis, output_file)

        # Выводим краткий отчет в консоль
        print("\n" + report)

        logger.info("✅ Нагрузочное тестирование завершено")

    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при проведении тестирования: {e}")


if __name__ == "__main__":
    # Настраиваем логирование
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
    )

    # Запускаем тестирование
    asyncio.run(main())
