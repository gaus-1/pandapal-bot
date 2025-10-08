"""
Упрощенный мониторинг - все в одном классе
Здоровье, производительность и аналитика без избыточной сложности
"""

import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from bot.models import User, ChatHistory
from bot.database import get_db


@dataclass
class SystemStatus:
    """Статус системы"""
    healthy: bool
    cpu_percent: float
    memory_percent: float
    active_users: int
    messages_today: int
    last_update: datetime


class SimpleMonitor:
    """Упрощенный мониторинг системы"""
    
    def __init__(self):
        """Инициализация мониторинга"""
        self.start_time = datetime.now()
        self.last_check = None
        self.is_monitoring = False
        logger.info("✅ Simple Monitor инициализирован")

    async def start_monitoring(self):
        """Запуск мониторинга"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        logger.info("🛡️ Мониторинг системы запущен")
        
        # Запускаем фоновую задачу
        asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_monitoring = False
        logger.info("🛡️ Мониторинг системы остановлен")

    async def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self.is_monitoring:
            try:
                await self._check_system_health()
                await asyncio.sleep(60)  # Проверка каждую минуту
            except Exception as e:
                logger.error(f"❌ Ошибка мониторинга: {e}")
                await asyncio.sleep(60)

    async def _check_system_health(self):
        """Проверка здоровья системы"""
        try:
            # Проверка ресурсов
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Проверка БД
            db_healthy = await self._check_database()
            
            # Логирование
            if cpu_percent > 80 or memory_percent > 80:
                logger.warning(f"⚠️ Высокая нагрузка: CPU {cpu_percent}%, RAM {memory_percent}%")
            
            if not db_healthy:
                logger.error("❌ Проблемы с базой данных")
            
            self.last_check = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья: {e}")

    async def _check_database(self) -> bool:
        """Проверка подключения к БД"""
        try:
            with next(get_db()) as db:
                db.execute(select(1))
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка БД: {e}")
            return False

    async def get_system_status(self) -> SystemStatus:
        """Получение статуса системы"""
        try:
            # Системные ресурсы
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Статистика пользователей
            with next(get_db()) as db:
                active_users = db.scalar(
                    select(func.count(User.id)).where(User.is_active == True)
                ) or 0
                
                today = datetime.now().date()
                messages_today = db.scalar(
                    select(func.count(ChatHistory.id)).where(
                        func.date(ChatHistory.timestamp) == today
                    )
                ) or 0
            
            # Определение здоровья системы
            healthy = (
                cpu_percent < 80 and 
                memory_percent < 80 and 
                await self._check_database()
            )
            
            return SystemStatus(
                healthy=healthy,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                active_users=active_users,
                messages_today=messages_today,
                last_update=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            return SystemStatus(
                healthy=False,
                cpu_percent=0,
                memory_percent=0,
                active_users=0,
                messages_today=0,
                last_update=datetime.now()
            )

    def get_uptime(self) -> str:
        """Время работы системы"""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"

    async def get_simple_analytics(self) -> Dict[str, Any]:
        """Простая аналитика"""
        try:
            with next(get_db()) as db:
                # Общая статистика
                total_users = db.scalar(select(func.count(User.id)))
                active_users = db.scalar(
                    select(func.count(User.id)).where(User.is_active == True)
                )
                
                # Сообщения за последние 7 дней
                week_ago = datetime.now() - timedelta(days=7)
                messages_week = db.scalar(
                    select(func.count(ChatHistory.id)).where(
                        ChatHistory.timestamp >= week_ago
                    )
                )
                
                return {
                    "total_users": total_users or 0,
                    "active_users": active_users or 0,
                    "messages_week": messages_week or 0,
                    "uptime": self.get_uptime(),
                    "last_check": self.last_check.isoformat() if self.last_check else None
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка аналитики: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "messages_week": 0,
                "uptime": self.get_uptime(),
                "error": str(e)
            }


# Глобальный экземпляр
_simple_monitor = None

def get_simple_monitor() -> SimpleMonitor:
    """Получение глобального экземпляра"""
    global _simple_monitor
    if _simple_monitor is None:
        _simple_monitor = SimpleMonitor()
    return _simple_monitor
