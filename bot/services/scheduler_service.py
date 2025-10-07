"""
Сервис планировщика задач
Запускает периодические задачи (напоминания, очистка, аналитика)
"""

import asyncio
from datetime import datetime, time
from typing import Optional

from aiogram import Bot
from loguru import logger

from bot.database import get_db
from bot.services.engagement_service import EngagementService


class SchedulerService:
    """
    Планировщик периодических задач
    Запускает задачи в фоновом режиме
    """
    
    def __init__(self, bot: Bot):
        """
        Инициализация планировщика
        
        Args:
            bot: Экземпляр Telegram бота
        """
        self.bot = bot
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        
        logger.info("⏰ Планировщик задач инициализирован")
    
    async def start(self):
        """Запускает планировщик"""
        if self.is_running:
            logger.warning("⚠️ Планировщик уже запущен")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        
        logger.info("✅ Планировщик задач запущен")
    
    async def stop(self):
        """Останавливает планировщик"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("⏹️ Планировщик задач остановлен")
    
    async def _run_scheduler(self):
        """
        Основной цикл планировщика
        Проверяет и запускает задачи каждый час
        """
        logger.info("🔄 Запущен цикл планировщика")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                current_hour = current_time.hour
                current_day = current_time.weekday()
                
                # Еженедельная кампания вовлечения (каждый понедельник в 10:00)
                if current_day == 0 and current_hour == 10:
                    await self._run_engagement_campaign()
                
                # Ежедневная очистка старых данных (каждый день в 03:00)
                if current_hour == 3:
                    await self._cleanup_old_data()
                
                # Ждем 1 час до следующей проверки
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                logger.info("🛑 Планировщик остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике: {e}")
                await asyncio.sleep(60)  # При ошибке ждем минуту
    
    async def _run_engagement_campaign(self):
        """Запускает кампанию вовлечения неактивных пользователей"""
        try:
            logger.info("📬 Запуск еженедельной кампании вовлечения...")
            
            with get_db() as db:
                engagement = EngagementService(db, self.bot)
                stats = await engagement.run_engagement_campaign()
            
            logger.info(
                f"✅ Кампания завершена: "
                f"отправлено {stats['sent']}/{stats['total']}, "
                f"ошибок {stats['failed']}"
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка кампании вовлечения: {e}")
    
    async def _cleanup_old_data(self):
        """Очистка старых данных (логи, временные файлы)"""
        try:
            logger.info("🧹 Запуск очистки старых данных...")
            
            # Здесь можно добавить очистку старых логов, кэша и т.д.
            # Например, удаление логов старше 30 дней
            
            logger.info("✅ Очистка завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных: {e}")


# Глобальный экземпляр планировщика
_scheduler: Optional[SchedulerService] = None


def get_scheduler(bot: Bot) -> SchedulerService:
    """
    Получить глобальный экземпляр планировщика
    
    Args:
        bot: Экземпляр бота
    
    Returns:
        SchedulerService: Планировщик
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = SchedulerService(bot)
    
    return _scheduler

