"""
⚡ СИСТЕМА МОНИТОРИНГА ПРОИЗВОДИТЕЛЬНОСТИ
Отслеживание производительности и автоматическая оптимизация
"""

import asyncio
import time
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from loguru import logger


class PerformanceLevel(Enum):
    """Уровни производительности"""
    EXCELLENT = "excellent"  # > 80%
    GOOD = "good"           # 60-80%
    FAIR = "fair"           # 40-60%
    POOR = "poor"           # 20-40%
    CRITICAL = "critical"   # < 20%


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_percent: float
    disk_free: int
    active_connections: int
    response_time_avg: float
    error_rate: float
    queue_size: int


class PerformanceMonitor:
    """⚡ Монитор производительности системы"""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history = 100  # Максимум записей в истории
        self.current_performance = PerformanceLevel.EXCELLENT
        self.is_monitoring = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Пороги для уровней производительности
        self.thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "response_warning": 2.0,  # секунды
            "response_critical": 5.0,
            "error_rate_warning": 5.0,  # процент
            "error_rate_critical": 15.0,
        }
        
        # Статистика
        self.stats = {
            "optimizations_performed": 0,
            "last_optimization": None,
            "performance_degradations": 0,
            "recoveries": 0,
        }
    
    async def start_monitoring(self):
        """Запуск мониторинга производительности"""
        if self.is_monitoring:
            logger.warning("⚠️ Мониторинг производительности уже запущен")
            return
        
        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("⚡ Мониторинг производительности запущен")
    
    async def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("⚡ Мониторинг производительности остановлен")
    
    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.is_monitoring:
            try:
                await self._collect_metrics()
                await self._analyze_performance()
                await self._check_for_optimization()
                await asyncio.sleep(30)  # Проверяем каждые 30 секунд
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга производительности: {e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self):
        """Сбор метрик производительности"""
        try:
            # Системные метрики
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Метрики приложения
            active_connections = len(psutil.net_connections())
            
            # Метрики бота (если доступны)
            queue_size = 0
            response_time_avg = 0.0
            error_rate = 0.0
            
            try:
                from bot.services.bot_24_7_service import bot_24_7_service
                if bot_24_7_service:
                    queue_size = len(bot_24_7_service.message_queue)
                    # Здесь можно добавить расчет среднего времени ответа
            except Exception:
                pass
            
            # Создаем метрику
            metric = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available,
                disk_percent=disk.percent,
                disk_free=disk.free,
                active_connections=active_connections,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                queue_size=queue_size,
            )
            
            # Добавляем в историю
            self.metrics_history.append(metric)
            
            # Ограничиваем размер истории
            if len(self.metrics_history) > self.max_history:
                self.metrics_history = self.metrics_history[-self.max_history:]
            
            logger.debug(f"📊 Метрики собраны: CPU={cpu_percent:.1f}%, RAM={memory.percent:.1f}%, Queue={queue_size}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сбора метрик: {e}")
    
    async def _analyze_performance(self):
        """Анализ производительности"""
        if not self.metrics_history:
            return
        
        latest_metric = self.metrics_history[-1]
        
        # Определяем уровень производительности
        performance_score = self._calculate_performance_score(latest_metric)
        
        # Обновляем текущий уровень
        old_performance = self.current_performance
        self.current_performance = self._get_performance_level(performance_score)
        
        # Логируем изменения
        if old_performance != self.current_performance:
            if self._is_performance_degradation(old_performance, self.current_performance):
                self.stats["performance_degradations"] += 1
                logger.warning(f"⚠️ Деградация производительности: {old_performance.value} → {self.current_performance.value}")
            else:
                self.stats["recoveries"] += 1
                logger.info(f"✅ Восстановление производительности: {old_performance.value} → {self.current_performance.value}")
    
    def _calculate_performance_score(self, metric: PerformanceMetrics) -> float:
        """Расчет общего балла производительности"""
        scores = []
        
        # CPU (чем меньше, тем лучше)
        cpu_score = max(0, 100 - metric.cpu_percent)
        scores.append(cpu_score)
        
        # Memory (чем больше свободной, тем лучше)
        memory_score = max(0, 100 - metric.memory_percent)
        scores.append(memory_score)
        
        # Disk (чем больше свободной, тем лучше)
        disk_score = max(0, 100 - metric.disk_percent)
        scores.append(disk_score)
        
        # Response time (чем быстрее, тем лучше)
        if metric.response_time_avg > 0:
            response_score = max(0, 100 - (metric.response_time_avg * 20))  # 5 сек = 0 баллов
        else:
            response_score = 100
        scores.append(response_score)
        
        # Error rate (чем меньше ошибок, тем лучше)
        error_score = max(0, 100 - metric.error_rate * 5)  # 20% ошибок = 0 баллов
        scores.append(error_score)
        
        # Возвращаем средний балл
        return sum(scores) / len(scores)
    
    def _get_performance_level(self, score: float) -> PerformanceLevel:
        """Определение уровня производительности по баллу"""
        if score >= 80:
            return PerformanceLevel.EXCELLENT
        elif score >= 60:
            return PerformanceLevel.GOOD
        elif score >= 40:
            return PerformanceLevel.FAIR
        elif score >= 20:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    def _is_performance_degradation(self, old: PerformanceLevel, new: PerformanceLevel) -> bool:
        """Проверка деградации производительности"""
        levels = [PerformanceLevel.EXCELLENT, PerformanceLevel.GOOD, PerformanceLevel.FAIR, PerformanceLevel.POOR, PerformanceLevel.CRITICAL]
        old_index = levels.index(old)
        new_index = levels.index(new)
        return new_index > old_index
    
    async def _check_for_optimization(self):
        """Проверка необходимости оптимизации"""
        if not self.metrics_history:
            return
        
        latest_metric = self.metrics_history[-1]
        
        # Проверяем критические пороги
        optimizations_needed = []
        
        if latest_metric.cpu_percent > self.thresholds["cpu_critical"]:
            optimizations_needed.append("cpu_critical")
        elif latest_metric.cpu_percent > self.thresholds["cpu_warning"]:
            optimizations_needed.append("cpu_warning")
        
        if latest_metric.memory_percent > self.thresholds["memory_critical"]:
            optimizations_needed.append("memory_critical")
        elif latest_metric.memory_percent > self.thresholds["memory_warning"]:
            optimizations_needed.append("memory_warning")
        
        if latest_metric.disk_percent > self.thresholds["disk_critical"]:
            optimizations_needed.append("disk_critical")
        elif latest_metric.disk_percent > self.thresholds["disk_warning"]:
            optimizations_needed.append("disk_warning")
        
        if latest_metric.response_time_avg > self.thresholds["response_critical"]:
            optimizations_needed.append("response_critical")
        elif latest_metric.response_time_avg > self.thresholds["response_warning"]:
            optimizations_needed.append("response_warning")
        
        if latest_metric.error_rate > self.thresholds["error_rate_critical"]:
            optimizations_needed.append("error_rate_critical")
        elif latest_metric.error_rate > self.thresholds["error_rate_warning"]:
            optimizations_needed.append("error_rate_warning")
        
        # Выполняем оптимизации
        if optimizations_needed:
            await self._perform_optimizations(optimizations_needed, latest_metric)
    
    async def _perform_optimizations(self, optimizations: List[str], metric: PerformanceMetrics):
        """Выполнение оптимизаций"""
        logger.warning(f"⚡ Выполняем оптимизации: {', '.join(optimizations)}")
        
        for optimization in optimizations:
            try:
                if optimization == "cpu_critical" or optimization == "cpu_warning":
                    await self._optimize_cpu()
                
                elif optimization == "memory_critical" or optimization == "memory_warning":
                    await self._optimize_memory()
                
                elif optimization == "disk_critical" or optimization == "disk_warning":
                    await self._optimize_disk()
                
                elif optimization == "response_critical" or optimization == "response_warning":
                    await self._optimize_response_time()
                
                elif optimization == "error_rate_critical" or optimization == "error_rate_warning":
                    await self._optimize_error_rate()
                
                self.stats["optimizations_performed"] += 1
                self.stats["last_optimization"] = datetime.now()
                
            except Exception as e:
                logger.error(f"❌ Ошибка оптимизации {optimization}: {e}")
    
    async def _optimize_cpu(self):
        """Оптимизация CPU"""
        logger.info("⚡ Оптимизация CPU...")
        
        # Снижаем приоритет процесса
        try:
            import os
            os.nice(1)  # Увеличиваем nice value
        except:
            pass
        
        # Принудительная сборка мусора
        gc.collect()
        
        # Пауза для снижения нагрузки
        await asyncio.sleep(0.1)
    
    async def _optimize_memory(self):
        """Оптимизация памяти"""
        logger.info("⚡ Оптимизация памяти...")
        
        # Принудительная сборка мусора
        collected = gc.collect()
        logger.info(f"🧹 Собрано объектов: {collected}")
        
        # Очистка кэшей (если доступно)
        try:
            from bot.services.cache_service import cache_service
            if cache_service:
                cache_service.clear_expired()
        except:
            pass
    
    async def _optimize_disk(self):
        """Оптимизация дискового пространства"""
        logger.info("⚡ Оптимизация дискового пространства...")
        
        # Очистка временных файлов
        import tempfile
        import shutil
        
        try:
            temp_dir = tempfile.gettempdir()
            # Очищаем только наши временные файлы
            for item in os.listdir(temp_dir):
                if item.startswith('pandapal_'):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка очистки временных файлов: {e}")
    
    async def _optimize_response_time(self):
        """Оптимизация времени ответа"""
        logger.info("⚡ Оптимизация времени ответа...")
        
        # Очистка очереди сообщений (если переполнена)
        try:
            from bot.services.bot_24_7_service import bot_24_7_service
            if bot_24_7_service and len(bot_24_7_service.message_queue) > 100:
                # Удаляем старые сообщения с низким приоритетом
                bot_24_7_service.message_queue.sort(key=lambda x: (x.priority, x.timestamp))
                bot_24_7_service.message_queue = bot_24_7_service.message_queue[:50]
                logger.info("🧹 Очищена очередь сообщений")
        except:
            pass
    
    async def _optimize_error_rate(self):
        """Оптимизация частоты ошибок"""
        logger.info("⚡ Оптимизация частоты ошибок...")
        
        # Перезапуск проблемных сервисов
        try:
            from bot.services.ai_fallback_service import ai_fallback_service
            if ai_fallback_service:
                # Сброс счетчиков ошибок
                for provider in ai_fallback_service.provider_errors:
                    ai_fallback_service.provider_errors[provider] = 0
                logger.info("🔄 Сброшены счетчики ошибок AI провайдеров")
        except:
            pass
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Получение отчета о производительности"""
        if not self.metrics_history:
            return {"error": "Нет данных о производительности"}
        
        latest = self.metrics_history[-1]
        
        # Анализ трендов
        if len(self.metrics_history) >= 5:
            recent_avg_cpu = sum(m.cpu_percent for m in self.metrics_history[-5:]) / 5
            recent_avg_memory = sum(m.memory_percent for m in self.metrics_history[-5:]) / 5
        else:
            recent_avg_cpu = latest.cpu_percent
            recent_avg_memory = latest.memory_percent
        
        return {
            "current_performance": self.current_performance.value,
            "current_metrics": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_available_gb": latest.memory_available // (1024**3),
                "disk_percent": latest.disk_percent,
                "disk_free_gb": latest.disk_free // (1024**3),
                "queue_size": latest.queue_size,
                "active_connections": latest.active_connections,
            },
            "trends": {
                "avg_cpu_5min": recent_avg_cpu,
                "avg_memory_5min": recent_avg_memory,
            },
            "statistics": self.stats,
            "thresholds": self.thresholds,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Получение рекомендаций по оптимизации"""
        recommendations = []
        
        if not self.metrics_history:
            return recommendations
        
        latest = self.metrics_history[-1]
        
        if latest.cpu_percent > self.thresholds["cpu_warning"]:
            recommendations.append("Высокая нагрузка CPU - рассмотрите масштабирование")
        
        if latest.memory_percent > self.thresholds["memory_warning"]:
            recommendations.append("Высокое использование памяти - очистите кэши")
        
        if latest.disk_percent > self.thresholds["disk_warning"]:
            recommendations.append("Мало свободного места на диске - очистите логи")
        
        if latest.queue_size > 50:
            recommendations.append("Большая очередь сообщений - увеличьте производительность")
        
        if self.current_performance in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
            recommendations.append("Критическая производительность - требуется вмешательство")
        
        return recommendations


# Глобальный экземпляр монитора производительности
performance_monitor = PerformanceMonitor()