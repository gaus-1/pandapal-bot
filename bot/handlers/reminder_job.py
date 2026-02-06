"""
Handler для периодической отправки напоминаний.

Запускается по расписанию (например, через APScheduler или cron).
"""

from aiogram import Bot
from loguru import logger

from bot.services.reminder_service import ReminderService


async def send_reminders_job(bot: Bot):
    """
    Задача для отправки напоминаний неактивным пользователям.

    Запускается периодически (рекомендуется 1 раз в день).

    Args:
        bot: Экземпляр Telegram бота
    """
    logger.info("🔔 Запуск задачи отправки напоминаний")

    try:
        stats = await ReminderService.process_reminders(bot)
        panda_stats = await ReminderService.process_panda_reminders(bot)

        logger.info(
            "✅ Задача напоминаний завершена: "
            "неактивные всего=%s отправлено=%s ошибок=%s | "
            "панда всего=%s отправлено=%s ошибок=%s",
            stats["total"],
            stats["sent"],
            stats["failed"],
            panda_stats["total"],
            panda_stats["sent"],
            panda_stats["failed"],
        )

        return {**stats, "panda": panda_stats}

    except Exception as e:
        logger.error(f"❌ Ошибка выполнения задачи напоминаний: {e}")
        return {"total": 0, "sent": 0, "failed": 0, "error": str(e)}
