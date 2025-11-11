"""
Упрощенный сервис вовлечения - все в одном классе
Напоминания + планировщик без избыточной сложности
"""

import asyncio
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional

from aiogram import Bot
from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from bot.models import ChatHistory, User


class SimpleEngagementService:
    """Упрощенный сервис вовлечения пользователей"""

    def __init__(self, bot: Bot):
        """Инициализация сервиса"""
        self.bot = bot
        self.is_running = False
        self.last_reminder_sent: Dict[int, datetime] = {}  # telegram_id -> datetime
        logger.info("✅ Simple Engagement Service инициализирован")

    async def start(self):
        """Запуск сервиса"""
        if self.is_running:
            return

        self.is_running = True
        logger.info("⏰ Служба напоминаний запущена")

        # Запускаем фоновую задачу
        asyncio.create_task(self._reminder_loop())

    async def stop(self):
        """Остановка сервиса"""
        self.is_running = False
        logger.info("⏰ Служба напоминаний остановлена")

    async def _reminder_loop(self):
        """Основной цикл напоминаний"""
        while self.is_running:
            try:
                # Проверяем каждый час
                await asyncio.sleep(3600)

                # Отправляем напоминания по понедельникам в 10:00
                now = datetime.now()
                if now.weekday() == 0 and now.hour == 10:  # Понедельник 10:00
                    await self._send_weekly_reminders()

            except Exception as e:
                logger.error(f"❌ Ошибка в цикле напоминаний: {e}")

    async def _send_weekly_reminders(self):
        """Отправка еженедельных напоминаний"""
        try:
            from bot.database import get_db

            with next(get_db()) as db:
                # Находим неактивных пользователей (7 дней без сообщений)
                week_ago = datetime.now() - timedelta(days=7)

                inactive_users = db.scalars(
                    select(User).where(
                        and_(
                            User.is_active.is_(True),
                            User.last_activity < week_ago,
                            User.telegram_id.notin_(self.last_reminder_sent.keys()),
                        )
                    )
                ).all()

                sent_count = 0
                for user in inactive_users:
                    try:
                        message = self._get_reminder_message(user.age)
                        await self.bot.send_message(chat_id=user.telegram_id, text=message)

                        self.last_reminder_sent[user.telegram_id] = datetime.now()
                        sent_count += 1

                        # Пауза между сообщениями
                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(
                            f"❌ Ошибка отправки напоминания пользователю {user.telegram_id}: {e}"
                        )

                if sent_count > 0:
                    logger.info(f"📧 Отправлено {sent_count} напоминаний")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминаний: {e}")

    def _get_reminder_message(self, user_age: Optional[int]) -> str:
        """Получение сообщения напоминания в зависимости от возраста"""
        if user_age and user_age <= 8:
            return (
                "🐼 Привет! Я соскучился по тебе!\n\n"
                "Давай продолжим учиться вместе! "
                "У меня есть много интересных задачек для тебя.\n\n"
                "Напиши мне /start и давай играть! 🎮"
            )
        elif user_age and user_age <= 12:
            return (
                "🐼 Привет! Давно не виделись!\n\n"
                "Как дела с уроками? Может, нужна помощь? "
                "Я готов объяснить любую тему простыми словами!\n\n"
                "Напиши /start и давай заниматься! 📚"
            )
        else:
            return (
                "🐼 Привет! Как дела?\n\n"
                "Помнишь, мы учились вместе? "
                "Если нужна помощь с уроками - я всегда готов помочь!\n\n"
                "Напиши /start для продолжения! ✨"
            )

    async def send_immediate_reminder(self, telegram_id: int, user_age: Optional[int] = None):
        """Отправка немедленного напоминания"""
        try:
            message = self._get_reminder_message(user_age)
            await self.bot.send_message(chat_id=telegram_id, text=message)
            logger.info(f"📧 Отправлено немедленное напоминание пользователю {telegram_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки немедленного напоминания: {e}")

    def get_stats(self) -> dict:
        """Получение статистики сервиса"""
        return {
            "is_running": self.is_running,
            "reminders_sent": len(self.last_reminder_sent),
            "last_reminders": list(self.last_reminder_sent.keys())[-5:],  # Последние 5
        }


# Глобальный экземпляр
_simple_engagement = None


def get_simple_engagement(bot: Bot) -> SimpleEngagementService:
    """
    Получить глобальный экземпляр сервиса вовлечения пользователей.

    Реализует паттерн Singleton для обеспечения единого экземпляра
    сервиса вовлечения во всем приложении.

    Args:
        bot (Bot): Экземпляр Telegram бота для отправки сообщений.

    Returns:
        SimpleEngagementService: Глобальный экземпляр сервиса вовлечения.
    """
    global _simple_engagement
    if _simple_engagement is None:
        _simple_engagement = SimpleEngagementService(bot)
    return _simple_engagement
