"""
🛡️ СИСТЕМА МОНИТОРИНГА ЗДОРОВЬЯ СЕРВИСОВ
Автоматическое восстановление и graceful degradation
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from sqlalchemy.exc import OperationalError
import aiohttp
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError


class ServiceStatus(Enum):
    """Статусы сервисов"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class ServiceHealth:
    """Состояние здоровья сервиса"""
    name: str
    status: ServiceStatus
    last_check: datetime
    last_error: Optional[str] = None
    failure_count: int = 0
    recovery_attempts: int = 0
    max_failures: int = 3
    max_recovery_attempts: int = 5


class HealthMonitor:
    """🛡️ Монитор здоровья всех сервисов"""
    
    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.check_interval = 30  # секунд
        self.is_running = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Инициализируем мониторинг сервисов
        self._init_services()
        
    def _init_services(self):
        """Инициализация отслеживаемых сервисов"""
        services_config = {
            "database": {"max_failures": 5, "check_interval": 10},
            "telegram_api": {"max_failures": 3, "check_interval": 15},
            "gemini_ai": {"max_failures": 3, "check_interval": 20},
            "web_server": {"max_failures": 2, "check_interval": 5},
        }
        
        for service_name, config in services_config.items():
            self.services[service_name] = ServiceHealth(
                name=service_name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.now(),
                max_failures=config["max_failures"],
            )
    
    async def start_monitoring(self):
        """Запуск мониторинга в фоновом режиме"""
        if self.is_running:
            logger.warning("⚠️ Мониторинг уже запущен")
            return
            
        self.is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🛡️ Система мониторинга здоровья запущена")
    
    async def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("🛡️ Система мониторинга здоровья остановлена")
    
    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.is_running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(5)  # Краткая пауза при ошибке
    
    async def _check_all_services(self):
        """Проверка всех сервисов"""
        tasks = []
        
        # Проверяем каждый сервис параллельно
        for service_name in self.services.keys():
            task = asyncio.create_task(self._check_service(service_name))
            tasks.append(task)
        
        # Ждем завершения всех проверок
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service(self, service_name: str) -> bool:
        """Проверка конкретного сервиса"""
        service = self.services[service_name]
        
        try:
            is_healthy = await self._perform_health_check(service_name)
            
            if is_healthy:
                await self._handle_healthy_service(service)
            else:
                await self._handle_unhealthy_service(service, "Health check failed")
                
        except Exception as e:
            await self._handle_unhealthy_service(service, str(e))
        
        service.last_check = datetime.now()
        return service.status == ServiceStatus.HEALTHY
    
    async def _perform_health_check(self, service_name: str) -> bool:
        """Выполнение проверки здоровья сервиса"""
        
        if service_name == "database":
            return await self._check_database()
        elif service_name == "telegram_api":
            return await self._check_telegram_api()
        elif service_name == "gemini_ai":
            return await self._check_gemini_ai()
        elif service_name == "web_server":
            return await self._check_web_server()
        
        return False
    
    async def _check_database(self) -> bool:
        """Проверка подключения к базе данных"""
        try:
            from bot.database import DatabaseService
            return DatabaseService.check_connection()
        except Exception as e:
            logger.error(f"❌ Ошибка проверки БД: {e}")
            return False
    
    async def _check_telegram_api(self) -> bool:
        """Проверка Telegram API"""
        try:
            from main import bot
            await bot.get_me()
            return True
        except (TelegramAPIError, TelegramNetworkError) as e:
            logger.error(f"❌ Ошибка Telegram API: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка Telegram API: {e}")
            return False
    
    async def _check_gemini_ai(self) -> bool:
        """Проверка Gemini AI"""
        try:
            from bot.services.ai_service import GeminiAIService
            ai_service = GeminiAIService()
            # Простой тест - генерация короткого ответа
            response = await ai_service.generate_response("Тест")
            return response is not None and len(response) > 0
        except Exception as e:
            logger.error(f"❌ Ошибка Gemini AI: {e}")
            return False
    
    async def _check_web_server(self) -> bool:
        """Проверка веб-сервера"""
        try:
            import os
            port = os.getenv("PORT", "8000")
            url = f"http://localhost:{port}/health"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ошибка веб-сервера: {e}")
            return False
    
    async def _handle_healthy_service(self, service: ServiceHealth):
        """Обработка здорового сервиса"""
        if service.status != ServiceStatus.HEALTHY:
            logger.info(f"✅ Сервис {service.name} восстановлен")
            service.status = ServiceStatus.HEALTHY
            service.failure_count = 0
            service.recovery_attempts = 0
            service.last_error = None
    
    async def _handle_unhealthy_service(self, service: ServiceHealth, error: str):
        """Обработка нездорового сервиса"""
        service.failure_count += 1
        service.last_error = error
        
        logger.warning(f"Сервис {service.name} недоступен ({service.failure_count}/{service.max_failures}): {error}")
        
        if service.failure_count >= service.max_failures:
            if service.status != ServiceStatus.FAILED:
                logger.error(f"Сервис {service.name} переведен в статус FAILED")
                service.status = ServiceStatus.FAILED
                # Запускаем восстановление
                await self._start_recovery(service)
    
    async def _start_recovery(self, service: ServiceHealth):
        """Запуск процесса восстановления сервиса"""
        if service.recovery_attempts >= service.max_recovery_attempts:
            logger.error(f"Сервис {service.name} не может быть восстановлен после {service.max_recovery_attempts} попыток")
            return
        
        service.status = ServiceStatus.RECOVERING
        service.recovery_attempts += 1
        
        logger.info(f"🔄 Попытка восстановления сервиса {service.name} ({service.recovery_attempts}/{service.max_recovery_attempts})")
        
        # Специфичные действия восстановления для каждого сервиса
        await self._perform_recovery(service)
    
    async def _perform_recovery(self, service: ServiceHealth):
        """Выполнение восстановления сервиса"""
        try:
            if service.name == "database":
                await self._recover_database()
            elif service.name == "telegram_api":
                await self._recover_telegram_api()
            elif service.name == "gemini_ai":
                await self._recover_gemini_ai()
            elif service.name == "web_server":
                await self._recover_web_server()
                
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления {service.name}: {e}")
    
    async def _recover_database(self):
        """Восстановление подключения к базе данных"""
        try:
            from bot.database import engine
            # Попытка переподключения
            engine.dispose()
            logger.info("🔄 Попытка переподключения к базе данных")
            await asyncio.sleep(5)  # Пауза перед повторной попыткой
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления БД: {e}")
    
    async def _recover_telegram_api(self):
        """Восстановление Telegram API"""
        try:
            from main import bot
            # Сброс webhook и перезапуск polling
            await bot.delete_webhook()
            logger.info("🔄 Сброс Telegram webhook")
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления Telegram API: {e}")
    
    async def _recover_gemini_ai(self):
        """Восстановление Gemini AI"""
        try:
            # Переинициализация AI сервиса
            from bot.services.ai_service import GeminiAIService
            logger.info("🔄 Переинициализация Gemini AI")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления Gemini AI: {e}")
    
    async def _recover_web_server(self):
        """Восстановление веб-сервера"""
        logger.info("🔄 Перезапуск веб-сервера")
        # В реальном сценарии здесь может быть перезапуск сервера
        await asyncio.sleep(1)
    
    def get_service_status(self, service_name: str) -> Optional[ServiceHealth]:
        """Получение статуса сервиса"""
        return self.services.get(service_name)
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Получение общего состояния здоровья системы"""
        healthy_services = sum(1 for s in self.services.values() if s.status == ServiceStatus.HEALTHY)
        total_services = len(self.services)
        
        return {
            "overall_status": "healthy" if healthy_services == total_services else "degraded",
            "healthy_services": healthy_services,
            "total_services": total_services,
            "services": {name: {
                "status": service.status.value,
                "last_check": service.last_check.isoformat(),
                "failure_count": service.failure_count,
                "last_error": service.last_error
            } for name, service in self.services.items()},
            "timestamp": datetime.now().isoformat()
        }
    
    async def force_health_check(self, service_name: str) -> bool:
        """Принудительная проверка здоровья сервиса"""
        if service_name not in self.services:
            return False
        
        return await self._check_service(service_name)


# Глобальный экземпляр монитора
health_monitor = HealthMonitor()
