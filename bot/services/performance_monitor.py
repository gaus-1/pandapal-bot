"""
Система мониторинга производительности PandaPal
Отслеживает метрики в реальном времени и предоставляет аналитику
@module bot.services.performance_monitor
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import json

from loguru import logger

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil не установлен, мониторинг системы недоступен")


@dataclass
class PerformanceMetric:
    """Метрика производительности"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class SystemMetrics:
    """Системные метрики"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_mb: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: datetime


@dataclass
class DatabaseMetrics:
    """Метрики базы данных"""
    connection_count: int
    active_connections: int
    query_count: int
    slow_queries: int
    avg_query_time_ms: float
    cache_hit_ratio: float
    timestamp: datetime


@dataclass
class ApplicationMetrics:
    """Метрики приложения"""
    active_users: int
    messages_per_minute: int
    ai_requests_per_minute: int
    moderation_blocks_per_minute: int
    cache_hit_rate: float
    error_rate: float
    response_time_avg_ms: float
    timestamp: datetime


class PerformanceMonitor:
    """
    Монитор производительности PandaPal
    Собирает и анализирует метрики в реальном времени
    """
    
    def __init__(self, metrics_retention_hours: int = 24):
        """
        Инициализация монитора производительности
        
        Args:
            metrics_retention_hours: Время хранения метрик в часах
        """
        self.metrics_retention_hours = metrics_retention_hours
        
        # Хранилище метрик
        self._system_metrics: deque = deque(maxlen=1000)
        self._database_metrics: deque = deque(maxlen=1000)
        self._application_metrics: deque = deque(maxlen=1000)
        self._custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Счетчики для расчета метрик
        self._message_count = 0
        self._ai_request_count = 0
        self._moderation_block_count = 0
        self._error_count = 0
        self._response_times: deque = deque(maxlen=100)
        
        # Время последнего сброса счетчиков
        self._last_reset = datetime.utcnow()
        
        # Блокировка для потокобезопасности
        self._lock = threading.Lock()
        
        # Флаг работы монитора
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info("📊 Монитор производительности инициализирован")
    
    async def start(self, interval_seconds: int = 60):
        """
        Запуск мониторинга
        
        Args:
            interval_seconds: Интервал сбора метрик в секундах
        """
        if self._running:
            logger.warning("⚠️ Монитор производительности уже запущен")
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        
        logger.info(f"🚀 Мониторинг производительности запущен (интервал: {interval_seconds}с)")
    
    async def stop(self):
        """Остановка мониторинга"""
        if not self._running:
            return
        
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Мониторинг производительности остановлен")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Основной цикл мониторинга"""
        while self._running:
            try:
                # Собираем все метрики
                await self._collect_system_metrics()
                await self._collect_database_metrics()
                await self._collect_application_metrics()
                
                # Очищаем старые метрики
                await self._cleanup_old_metrics()
                
                # Ждем следующий цикл
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _collect_system_metrics(self):
        """Сбор системных метрик"""
        if not PSUTIL_AVAILABLE:
            return
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Память
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_available_mb = memory.available / 1024 / 1024
            
            # Диск
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_mb = disk.free / 1024 / 1024
            
            # Сеть
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_mb=disk_free_mb,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                timestamp=datetime.utcnow()
            )
            
            with self._lock:
                self._system_metrics.append(metrics)
                
        except Exception as e:
            logger.error(f"❌ Ошибка сбора системных метрик: {e}")
    
    async def _collect_database_metrics(self):
        """Сбор метрик базы данных"""
        try:
            # Здесь можно добавить реальные метрики БД
            # Пока используем заглушки
            
            metrics = DatabaseMetrics(
                connection_count=10,  # TODO: получить из БД
                active_connections=5,  # TODO: получить из БД
                query_count=self._get_query_count(),
                slow_queries=self._get_slow_query_count(),
                avg_query_time_ms=self._get_avg_query_time(),
                cache_hit_ratio=self._get_cache_hit_ratio(),
                timestamp=datetime.utcnow()
            )
            
            with self._lock:
                self._database_metrics.append(metrics)
                
        except Exception as e:
            logger.error(f"❌ Ошибка сбора метрик БД: {e}")
    
    async def _collect_application_metrics(self):
        """Сбор метрик приложения"""
        try:
            now = datetime.utcnow()
            time_diff = (now - self._last_reset).total_seconds()
            
            # Рассчитываем метрики в минуту
            messages_per_minute = (self._message_count / time_diff) * 60 if time_diff > 0 else 0
            ai_requests_per_minute = (self._ai_request_count / time_diff) * 60 if time_diff > 0 else 0
            moderation_blocks_per_minute = (self._moderation_block_count / time_diff) * 60 if time_diff > 0 else 0
            
            # Рассчитываем среднее время ответа
            avg_response_time = 0
            if self._response_times:
                avg_response_time = sum(self._response_times) / len(self._response_times)
            
            # Рассчитываем процент ошибок
            total_requests = self._message_count + self._ai_request_count
            error_rate = (self._error_count / total_requests * 100) if total_requests > 0 else 0
            
            metrics = ApplicationMetrics(
                active_users=self._get_active_users_count(),
                messages_per_minute=messages_per_minute,
                ai_requests_per_minute=ai_requests_per_minute,
                moderation_blocks_per_minute=moderation_blocks_per_minute,
                cache_hit_rate=self._get_cache_hit_rate(),
                error_rate=error_rate,
                response_time_avg_ms=avg_response_time,
                timestamp=now
            )
            
            with self._lock:
                self._application_metrics.append(metrics)
                
        except Exception as e:
            logger.error(f"❌ Ошибка сбора метрик приложения: {e}")
    
    def record_message(self):
        """Записать отправку сообщения"""
        with self._lock:
            self._message_count += 1
    
    def record_ai_request(self):
        """Записать запрос к AI"""
        with self._lock:
            self._ai_request_count += 1
    
    def record_moderation_block(self):
        """Записать блокировку модерацией"""
        with self._lock:
            self._moderation_block_count += 1
    
    def record_error(self):
        """Записать ошибку"""
        with self._lock:
            self._error_count += 1
    
    def record_response_time(self, response_time_ms: float):
        """Записать время ответа"""
        with self._lock:
            self._response_times.append(response_time_ms)
    
    def record_custom_metric(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
        """Записать пользовательскую метрику"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit
        )
        
        with self._lock:
            self._custom_metrics[name].append(metric)
    
    def get_system_metrics(self, limit: int = 100) -> List[SystemMetrics]:
        """Получить системные метрики"""
        with self._lock:
            return list(self._system_metrics)[-limit:]
    
    def get_database_metrics(self, limit: int = 100) -> List[DatabaseMetrics]:
        """Получить метрики базы данных"""
        with self._lock:
            return list(self._database_metrics)[-limit:]
    
    def get_application_metrics(self, limit: int = 100) -> List[ApplicationMetrics]:
        """Получить метрики приложения"""
        with self._lock:
            return list(self._application_metrics)[-limit:]
    
    def get_custom_metrics(self, name: str, limit: int = 100) -> List[PerformanceMetric]:
        """Получить пользовательские метрики"""
        with self._lock:
            return list(self._custom_metrics.get(name, []))[-limit:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получить сводку по производительности"""
        with self._lock:
            now = datetime.utcnow()
            
            # Последние метрики
            latest_system = self._system_metrics[-1] if self._system_metrics else None
            latest_db = self._database_metrics[-1] if self._database_metrics else None
            latest_app = self._application_metrics[-1] if self._application_metrics else None
            
            # Рассчитываем тренды за последний час
            hour_ago = now - timedelta(hours=1)
            
            system_trend = self._calculate_trend(self._system_metrics, 'cpu_percent', hour_ago)
            db_trend = self._calculate_trend(self._database_metrics, 'avg_query_time_ms', hour_ago)
            app_trend = self._calculate_trend(self._application_metrics, 'response_time_avg_ms', hour_ago)
            
            return {
                "timestamp": now.isoformat(),
                "system": {
                    "cpu_percent": latest_system.cpu_percent if latest_system else 0,
                    "memory_percent": latest_system.memory_percent if latest_system else 0,
                    "disk_usage_percent": latest_system.disk_usage_percent if latest_system else 0,
                    "cpu_trend": system_trend
                },
                "database": {
                    "avg_query_time_ms": latest_db.avg_query_time_ms if latest_db else 0,
                    "cache_hit_ratio": latest_db.cache_hit_ratio if latest_db else 0,
                    "query_time_trend": db_trend
                },
                "application": {
                    "active_users": latest_app.active_users if latest_app else 0,
                    "messages_per_minute": latest_app.messages_per_minute if latest_app else 0,
                    "error_rate": latest_app.error_rate if latest_app else 0,
                    "response_time_trend": app_trend
                },
                "health": self._calculate_health_score(latest_system, latest_db, latest_app)
            }
    
    def _calculate_trend(self, metrics_deque: deque, field_name: str, since: datetime) -> float:
        """Рассчитать тренд метрики"""
        if not metrics_deque:
            return 0.0
        
        # Получаем метрики за указанный период
        recent_metrics = [
            getattr(metric, field_name) 
            for metric in metrics_deque 
            if metric.timestamp >= since
        ]
        
        if len(recent_metrics) < 2:
            return 0.0
        
        # Простое вычисление тренда (изменение за период)
        return recent_metrics[-1] - recent_metrics[0]
    
    def _calculate_health_score(self, system: SystemMetrics, db: DatabaseMetrics, app: ApplicationMetrics) -> float:
        """Рассчитать общий индекс здоровья системы (0-100)"""
        score = 100.0
        
        # Штрафы за высокую нагрузку
        if system and system.cpu_percent > 80:
            score -= 20
        if system and system.memory_percent > 90:
            score -= 20
        if system and system.disk_usage_percent > 95:
            score -= 15
        
        # Штрафы за медленные запросы
        if db and db.avg_query_time_ms > 1000:
            score -= 15
        if db and db.cache_hit_ratio < 0.8:
            score -= 10
        
        # Штрафы за ошибки приложения
        if app and app.error_rate > 5:
            score -= 20
        if app and app.response_time_avg_ms > 5000:
            score -= 15
        
        return max(0.0, score)
    
    async def _cleanup_old_metrics(self):
        """Очистка старых метрик"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metrics_retention_hours)
        
        with self._lock:
            # Очищаем системные метрики
            while self._system_metrics and self._system_metrics[0].timestamp < cutoff_time:
                self._system_metrics.popleft()
            
            # Очищаем метрики БД
            while self._database_metrics and self._database_metrics[0].timestamp < cutoff_time:
                self._database_metrics.popleft()
            
            # Очищаем метрики приложения
            while self._application_metrics and self._application_metrics[0].timestamp < cutoff_time:
                self._application_metrics.popleft()
            
            # Очищаем пользовательские метрики
            for metric_name in list(self._custom_metrics.keys()):
                while (self._custom_metrics[metric_name] and 
                       self._custom_metrics[metric_name][0].timestamp < cutoff_time):
                    self._custom_metrics[metric_name].popleft()
                
                # Удаляем пустые коллекции
                if not self._custom_metrics[metric_name]:
                    del self._custom_metrics[metric_name]
    
    def _get_query_count(self) -> int:
        """Получить количество запросов к БД"""
        # TODO: реализовать подсчет запросов
        return 0
    
    def _get_slow_query_count(self) -> int:
        """Получить количество медленных запросов"""
        # TODO: реализовать подсчет медленных запросов
        return 0
    
    def _get_avg_query_time(self) -> float:
        """Получить среднее время выполнения запроса"""
        # TODO: реализовать расчет среднего времени
        return 0.0
    
    def _get_cache_hit_ratio(self) -> float:
        """Получить коэффициент попаданий в кэш"""
        # TODO: получить из сервиса кэширования
        return 0.0
    
    def _get_active_users_count(self) -> int:
        """Получить количество активных пользователей"""
        # TODO: реализовать подсчет активных пользователей
        return 0
    
    async def export_metrics(self, format_type: str = "json") -> str:
        """
        Экспорт метрик в различных форматах
        
        Args:
            format_type: Тип формата (json, prometheus)
            
        Returns:
            Строка с метриками
        """
        if format_type == "json":
            summary = self.get_performance_summary()
            return json.dumps(summary, indent=2, ensure_ascii=False)
        
        elif format_type == "prometheus":
            return self._export_prometheus_metrics()
        
        else:
            raise ValueError(f"Неподдерживаемый формат: {format_type}")
    
    def _export_prometheus_metrics(self) -> str:
        """Экспорт метрик в формате Prometheus"""
        lines = []
        
        # Системные метрики
        if self._system_metrics:
            latest = self._system_metrics[-1]
            lines.append(f"# HELP system_cpu_percent CPU usage percentage")
            lines.append(f"# TYPE system_cpu_percent gauge")
            lines.append(f"system_cpu_percent {latest.cpu_percent}")
            
            lines.append(f"# HELP system_memory_percent Memory usage percentage")
            lines.append(f"# TYPE system_memory_percent gauge")
            lines.append(f"system_memory_percent {latest.memory_percent}")
        
        # Метрики приложения
        if self._application_metrics:
            latest = self._application_metrics[-1]
            lines.append(f"# HELP app_messages_per_minute Messages per minute")
            lines.append(f"# TYPE app_messages_per_minute gauge")
            lines.append(f"app_messages_per_minute {latest.messages_per_minute}")
            
            lines.append(f"# HELP app_error_rate Error rate percentage")
            lines.append(f"# TYPE app_error_rate gauge")
            lines.append(f"app_error_rate {latest.error_rate}")
        
        return "\n".join(lines)


# Глобальный экземпляр монитора производительности
performance_monitor = PerformanceMonitor()


# Декораторы для автоматического мониторинга
def monitor_performance(func):
    """Декоратор для мониторинга производительности функций"""
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            performance_monitor.record_response_time((time.time() - start_time) * 1000)
            return result
        except Exception as e:
            performance_monitor.record_error()
            raise
    
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            performance_monitor.record_response_time((time.time() - start_time) * 1000)
            return result
        except Exception as e:
            performance_monitor.record_error()
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
