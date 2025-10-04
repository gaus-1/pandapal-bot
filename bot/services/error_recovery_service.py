"""
🛠️ СИСТЕМА АВТОМАТИЧЕСКОГО ВОССТАНОВЛЕНИЯ ПОСЛЕ ОШИБОК
Graceful degradation и автоматическое восстановление сервисов
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import traceback
import functools

from loguru import logger
from sqlalchemy.exc import OperationalError, DisconnectionError
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError, TelegramRetryAfter
import aiohttp
from aiohttp import ClientError, ServerTimeoutError


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""
    LOW = "low"           # Незначительные ошибки, не влияют на работу
    MEDIUM = "medium"     # Средние ошибки, частичная деградация
    HIGH = "high"         # Серьезные ошибки, требуют вмешательства
    CRITICAL = "critical" # Критические ошибки, полная остановка


@dataclass
class ErrorInfo:
    """Информация об ошибке"""
    error_type: str
    severity: ErrorSeverity
    message: str
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3
    last_retry: Optional[datetime] = None
    recovery_strategy: Optional[str] = None


class ErrorRecoveryService:
    """🛠️ Сервис автоматического восстановления после ошибок"""
    
    def __init__(self):
        self.error_history: List[ErrorInfo] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, bool] = {}  # Circuit breaker pattern
        self.max_error_history = 100
        self.is_monitoring = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Инициализация стратегий восстановления
        self._init_recovery_strategies()
    
    def _init_recovery_strategies(self):
        """Инициализация стратегий восстановления"""
        
        # Стратегии для различных типов ошибок
        self.recovery_strategies = {
            "database_connection": self._recover_database_connection,
            "telegram_api": self._recover_telegram_api,
            "gemini_api": self._recover_gemini_api,
            "web_server": self._recover_web_server,
            "rate_limit": self._recover_rate_limit,
            "timeout": self._recover_timeout,
            "network": self._recover_network,
            "memory": self._recover_memory,
            "disk_space": self._recover_disk_space,
        }
    
    def handle_error(
        self, 
        error: Exception, 
        context: str = "",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retry_func: Optional[Callable] = None,
        max_retries: int = 3
    ) -> bool:
        """Обработка ошибки с автоматическим восстановлением"""
        
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            severity=severity,
            message=str(error),
            timestamp=datetime.now(),
            max_retries=max_retries
        )
        
        # Добавляем в историю
        self._add_to_history(error_info)
        
        # Логируем ошибку
        self._log_error(error_info, context)
        
        # Определяем стратегию восстановления
        strategy = self._determine_recovery_strategy(error_info)
        error_info.recovery_strategy = strategy
        
        # Выполняем восстановление
        if strategy and retry_func:
            return asyncio.create_task(
                self._execute_recovery(error_info, retry_func)
            )
        
        return False
    
    def _add_to_history(self, error_info: ErrorInfo):
        """Добавление ошибки в историю"""
        self.error_history.append(error_info)
        
        # Ограничиваем размер истории
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]
    
    def _log_error(self, error_info: ErrorInfo, context: str):
        """Логирование ошибки с учетом уровня серьезности"""
        
        log_message = f"❌ {error_info.error_type}: {error_info.message}"
        if context:
            log_message += f" | Context: {context}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _determine_recovery_strategy(self, error_info: ErrorInfo) -> Optional[str]:
        """Определение стратегии восстановления"""
        
        error_type = error_info.error_type.lower()
        error_message = error_info.message.lower()
        
        # База данных
        if "operationalerror" in error_type or "disconnectionerror" in error_type:
            return "database_connection"
        
        # Telegram API
        elif "telegramapi" in error_type or "telegramnetwork" in error_type:
            if "rate limit" in error_message or "too many requests" in error_message:
                return "rate_limit"
            else:
                return "telegram_api"
        
        # Gemini AI
        elif "google" in error_message or "gemini" in error_message:
            return "gemini_api"
        
        # Таймауты
        elif "timeout" in error_message or "timed out" in error_message:
            return "timeout"
        
        # Сетевые ошибки
        elif "connection" in error_message or "network" in error_message:
            return "network"
        
        # Память
        elif "memory" in error_message or "out of memory" in error_message:
            return "memory"
        
        # Дисковое пространство
        elif "disk" in error_message or "space" in error_message:
            return "disk_space"
        
        # Веб-сервер
        elif "http" in error_type or "server" in error_message:
            return "web_server"
        
        return None
    
    async def _execute_recovery(self, error_info: ErrorInfo, retry_func: Callable) -> bool:
        """Выполнение восстановления"""
        
        if error_info.retry_count >= error_info.max_retries:
            logger.error(f"💀 Превышено максимальное количество попыток восстановления для {error_info.error_type}")
            return False
        
        error_info.retry_count += 1
        error_info.last_retry = datetime.now()
        
        # Получаем стратегию восстановления
        strategy = self.recovery_strategies.get(error_info.recovery_strategy)
        if not strategy:
            logger.warning(f"⚠️ Неизвестная стратегия восстановления: {error_info.recovery_strategy}")
            return False
        
        try:
            logger.info(f"🔄 Попытка восстановления {error_info.retry_count}/{error_info.max_retries} для {error_info.error_type}")
            
            # Выполняем предварительные действия восстановления
            await strategy(error_info)
            
            # Ждем перед повторной попыткой
            await asyncio.sleep(min(error_info.retry_count * 2, 10))  # Экспоненциальная задержка
            
            # Повторяем оригинальную операцию
            result = await retry_func()
            
            if result:
                logger.success(f"✅ Восстановление успешно для {error_info.error_type}")
                return True
            else:
                logger.warning(f"⚠️ Повторная попытка не удалась для {error_info.error_type}")
                return False
                
        except Exception as recovery_error:
            logger.error(f"❌ Ошибка восстановления для {error_info.error_type}: {recovery_error}")
            return False
    
    async def _recover_database_connection(self, error_info: ErrorInfo):
        """Восстановление подключения к базе данных"""
        try:
            from bot.database import engine
            
            logger.info("🔄 Восстановление подключения к базе данных...")
            
            # Закрываем все соединения
            engine.dispose()
            
            # Ждем перед переподключением
            await asyncio.sleep(2)
            
            # Проверяем подключение
            from bot.database import DatabaseService
            if DatabaseService.check_connection():
                logger.success("✅ Подключение к базе данных восстановлено")
            else:
                raise Exception("Не удалось восстановить подключение к БД")
                
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления БД: {e}")
            raise
    
    async def _recover_telegram_api(self, error_info: ErrorInfo):
        """Восстановление Telegram API"""
        try:
            from bot.main import bot
            
            logger.info("🔄 Восстановление Telegram API...")
            
            # Сбрасываем webhook
            await bot.delete_webhook()
            await asyncio.sleep(1)
            
            # Проверяем подключение
            me = await bot.get_me()
            if me:
                logger.success("✅ Telegram API восстановлен")
            else:
                raise Exception("Не удалось восстановить Telegram API")
                
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления Telegram API: {e}")
            raise
    
    async def _recover_gemini_api(self, error_info: ErrorInfo):
        """Восстановление Gemini API"""
        try:
            logger.info("🔄 Восстановление Gemini API...")
            
            # Переинициализация AI сервиса
            from bot.services.ai_service import AIService
            ai_service = AIService()
            
            # Простой тест
            test_response = await ai_service.generate_response("Тест")
            if test_response:
                logger.success("✅ Gemini API восстановлен")
            else:
                raise Exception("Не удалось восстановить Gemini API")
                
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления Gemini API: {e}")
            raise
    
    async def _recover_web_server(self, error_info: ErrorInfo):
        """Восстановление веб-сервера"""
        try:
            logger.info("🔄 Восстановление веб-сервера...")
            
            # Проверяем доступность
            import os
            port = os.getenv("PORT", "8000")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}/health", timeout=5) as response:
                    if response.status == 200:
                        logger.success("✅ Веб-сервер восстановлен")
                    else:
                        raise Exception(f"Веб-сервер недоступен: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления веб-сервера: {e}")
            raise
    
    async def _recover_rate_limit(self, error_info: ErrorInfo):
        """Восстановление после rate limit"""
        logger.info("🔄 Ожидание снятия rate limit...")
        await asyncio.sleep(60)  # Ждем минуту
    
    async def _recover_timeout(self, error_info: ErrorInfo):
        """Восстановление после таймаута"""
        logger.info("🔄 Восстановление после таймаута...")
        await asyncio.sleep(5)
    
    async def _recover_network(self, error_info: ErrorInfo):
        """Восстановление сетевого подключения"""
        logger.info("🔄 Восстановление сетевого подключения...")
        await asyncio.sleep(3)
    
    async def _recover_memory(self, error_info: ErrorInfo):
        """Восстановление после проблем с памятью"""
        logger.info("🔄 Очистка памяти...")
        import gc
        gc.collect()
        await asyncio.sleep(2)
    
    async def _recover_disk_space(self, error_info: ErrorInfo):
        """Восстановление после проблем с дисковым пространством"""
        logger.info("🔄 Очистка дискового пространства...")
        # Здесь можно добавить очистку временных файлов
        await asyncio.sleep(1)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Получение статистики ошибок"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        recent_errors = [e for e in self.error_history if e.timestamp > last_hour]
        daily_errors = [e for e in self.error_history if e.timestamp > last_day]
        
        return {
            "total_errors": len(self.error_history),
            "errors_last_hour": len(recent_errors),
            "errors_last_day": len(daily_errors),
            "error_types": {
                error_type: len([e for e in self.error_history if e.error_type == error_type])
                for error_type in set(e.error_type for e in self.error_history)
            },
            "severity_distribution": {
                severity.value: len([e for e in self.error_history if e.severity == severity])
                for severity in ErrorSeverity
            },
            "recent_errors": [
                {
                    "type": e.error_type,
                    "severity": e.severity.value,
                    "message": e.message[:100],
                    "timestamp": e.timestamp.isoformat(),
                    "retry_count": e.retry_count
                }
                for e in recent_errors[-10:]  # Последние 10 ошибок
            ]
        }
    
    def clear_error_history(self):
        """Очистка истории ошибок"""
        self.error_history.clear()
        logger.info("🧹 История ошибок очищена")


# Декоратор для автоматической обработки ошибок
def auto_recovery(
    error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    max_retries: int = 3,
    context: str = ""
):
    """Декоратор для автоматического восстановления после ошибок"""
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            recovery_service = ErrorRecoveryService()
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    if attempt == max_retries:
                        # Последняя попытка - логируем и пробрасываем ошибку
                        recovery_service.handle_error(
                            e, context, ErrorSeverity.CRITICAL
                        )
                        raise
                    
                    # Пытаемся восстановиться
                    success = recovery_service.handle_error(
                        e, context, error_severity, 
                        lambda: func(*args, **kwargs), max_retries
                    )
                    
                    if not success:
                        await asyncio.sleep(min(attempt * 2, 10))
                        
            return None
            
        return wrapper
    return decorator


# Глобальный экземпляр сервиса восстановления
error_recovery_service = ErrorRecoveryService()
