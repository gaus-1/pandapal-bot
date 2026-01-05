"""
Сервис напоминаний для пользователей.

Отправляет дружелюбные напоминания от Панды, если пользователь не был активен 7 дней.
"""

from datetime import datetime, timedelta
from typing import List

from aiogram import Bot
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.database import get_db
from bot.models import User


class ReminderService:
    """Сервис для отправки напоминаний неактивным пользователям."""

    INACTIVITY_DAYS = 7
    REMINDER_MESSAGES = [
        "👋 Привет! Я скучаю по тебе! 🐼\n\nДавно не общались... "
        "У меня есть много интересного для тебя! Давай позанимаемся? 📚",
        "🐼 Привет, друг!\n\nЗаметил, что ты давно не заходил... "
        "Может, нужна помощь с домашкой? Я всегда рад помочь! 😊",
        "✨ Эй, давно не виделись! 🐼\n\nЯ тут узнал много нового и хочу с тобой поделиться! "
        "Заходи, расскажу! 📖",
        "🎓 Привет!\n\nПанда ждет тебя! Может, есть вопросы по учебе? "
        "Или просто хочешь поболтать? Заходи! 🐼💬",
        "🌟 Соскучился по нашим беседам! 🐼\n\nУ меня для тебя припасены интересные задачки! "
        "Заглядывай, будет весело! 😄",
    ]

    @staticmethod
    def get_inactive_users() -> List[User]:
        """
        Получает список пользователей, неактивных последние 7 дней.

        Returns:
            Список пользователей для напоминания
        """
        threshold_date = datetime.utcnow() - timedelta(days=ReminderService.INACTIVITY_DAYS)

        with get_db() as db:
            stmt = (
                select(User)
                .where(User.is_active == True)  # noqa: E712
                .where(User.last_activity < threshold_date)
                .where(User.reminder_sent_at.is_(None) | (User.reminder_sent_at < threshold_date))
            )

            result = db.execute(stmt)
            users = result.scalars().all()

            logger.info(f"📊 Найдено {len(users)} неактивных пользователей")
            return list(users)

    @staticmethod
    async def send_reminder(bot: Bot, user: User) -> bool:
        """
        Отправляет напоминание пользователю.

        Args:
            bot: Экземпляр Telegram бота
            user: Пользователь для напоминания

        Returns:
            True если отправка успешна, False иначе
        """
        import random

        try:
            message = random.choice(ReminderService.REMINDER_MESSAGES)

            await bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode=None,
            )

            # Обновляем время отправки напоминания
            with get_db() as db:
                stmt = select(User).where(User.telegram_id == user.telegram_id)
                db_user = db.execute(stmt).scalar_one_or_none()

                if db_user:
                    db_user.reminder_sent_at = datetime.utcnow()
                    db.commit()

            logger.info(f"✅ Напоминание отправлено пользователю {user.telegram_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания пользователю {user.telegram_id}: {e}")
            return False

    @staticmethod
    async def process_reminders(bot: Bot) -> dict:
        """
        Обрабатывает все напоминания.

        Args:
            bot: Экземпляр Telegram бота

        Returns:
            Статистика отправки
        """
        inactive_users = ReminderService.get_inactive_users()

        sent = 0
        failed = 0

        for user in inactive_users:
            success = await ReminderService.send_reminder(bot, user)
            if success:
                sent += 1
            else:
                failed += 1

        logger.info(
            f"📨 Обработка напоминаний завершена: "
            f"отправлено={sent}, ошибок={failed}, всего={len(inactive_users)}"
        )

        return {
            "total": len(inactive_users),
            "sent": sent,
            "failed": failed,
        }
