"""
Упрощенный сервис вовлечения - все в одном классе
Напоминания + планировщик без избыточной сложности
"""

import asyncio
from datetime import datetime, timedelta

from aiogram import Bot
from loguru import logger
from sqlalchemy import and_, func, select

from bot.models import User


class SimpleEngagementService:
    """Упрощенный сервис вовлечения пользователей"""

    def __init__(self, bot: Bot):
        """Инициализация сервиса"""
        self.bot = bot
        self.is_running = False
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
            from bot.services.analytics_service import AnalyticsService

            with next(get_db()) as db:
                # Находим неактивных пользователей (7 дней без сообщений)
                week_ago = datetime.now() - timedelta(days=7)

                # Проверяем, что напоминание не отправлялось в последние 6 дней
                # (чтобы не спамить, но можно отправить снова через неделю)
                reminder_threshold = datetime.now() - timedelta(days=6)

                inactive_users = db.scalars(
                    select(User).where(
                        and_(
                            User.is_active.is_(True),
                            User.last_activity < week_ago,
                            # Либо напоминание не отправлялось, либо прошло больше 6 дней
                            (
                                (User.reminder_sent_at.is_(None))
                                | (User.reminder_sent_at < reminder_threshold)
                            ),
                        )
                    )
                ).all()

                sent_count = 0
                failed_count = 0
                analytics_service = AnalyticsService(db)

                for user in inactive_users:
                    try:
                        message = self._get_reminder_message(user.age)
                        await self.bot.send_message(chat_id=user.telegram_id, text=message)

                        # Обновляем дату отправки напоминания в БД
                        user.reminder_sent_at = datetime.now()
                        db.flush()

                        # Записываем метрику
                        analytics_service.record_education_metric(
                            metric_name="weekly_reminder_sent",
                            value=1.0,
                            user_telegram_id=user.telegram_id,
                        )

                        sent_count += 1
                        logger.info(
                            f"📧 Отправлено напоминание пользователю {user.telegram_id} ({user.first_name})"
                        )

                        # Пауза между сообщениями
                        await asyncio.sleep(1)

                    except Exception as e:
                        failed_count += 1
                        logger.error(
                            f"❌ Ошибка отправки напоминания пользователю {user.telegram_id}: {e}"
                        )

                # Записываем общую метрику
                if sent_count > 0 or failed_count > 0:
                    analytics_service.record_technical_metric(
                        metric_name="weekly_reminders_campaign",
                        value=sent_count,
                        tags={
                            "total_found": len(inactive_users),
                            "sent": sent_count,
                            "failed": failed_count,
                        },
                    )
                    logger.info(
                        f"📧 Еженедельная кампания завершена: найдено {len(inactive_users)} неактивных, "
                        f"отправлено {sent_count}, ошибок {failed_count}"
                    )

        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминаний: {e}", exc_info=True)

    def _get_reminder_message(self, user_age: int | None) -> str:
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

    async def send_immediate_reminder(self, telegram_id: int, user_age: int | None = None):
        """Отправка немедленного напоминания"""
        try:
            message = self._get_reminder_message(user_age)
            await self.bot.send_message(chat_id=telegram_id, text=message)
            logger.info(f"📧 Отправлено немедленное напоминание пользователю {telegram_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки немедленного напоминания: {e}")

    def get_stats(self) -> dict:
        """Получение статистики сервиса"""
        try:
            from bot.database import get_db

            with next(get_db()) as db:
                # Подсчитываем пользователей с отправленными напоминаниями
                week_ago = datetime.now() - timedelta(days=7)
                total_with_reminders = (
                    db.scalar(
                        select(func.count(User.id)).where(
                            and_(
                                User.reminder_sent_at.isnot(None),
                                User.reminder_sent_at >= week_ago,
                            )
                        )
                    )
                    or 0
                )

                return {
                    "is_running": self.is_running,
                    "reminders_sent_last_week": total_with_reminders,
                }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {
                "is_running": self.is_running,
                "reminders_sent_last_week": 0,
                "error": str(e),
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
