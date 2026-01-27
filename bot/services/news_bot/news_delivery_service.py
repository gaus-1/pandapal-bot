"""
Сервис доставки новостей пользователям.

Ежедневная рассылка новостей с персонализацией по предпочтениям.
"""

import asyncio
from datetime import datetime, time
from typing import Any

from aiogram import Bot
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.models import User
from bot.services.news.repository import NewsRepository
from bot.services.news_bot.user_preferences_service import UserPreferencesService


class NewsDeliveryService:
    """
    Сервис доставки новостей.

    Обеспечивает ежедневную рассылку новостей пользователям
    с персонализацией по возрасту, классу и категориям.
    """

    def __init__(self, bot: Bot, db: Session):
        """
        Инициализация сервиса.

        Args:
            bot: Экземпляр Telegram бота
            db: Сессия SQLAlchemy
        """
        self.bot = bot
        self.db = db
        self.repository = NewsRepository(db)
        self.preferences_service = UserPreferencesService(db)
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Запустить сервис доставки."""
        if self._running:
            logger.warning("⚠️ NewsDeliveryService уже запущен")
            return

        self._running = True
        self._task = asyncio.create_task(self._delivery_loop())
        logger.info("✅ NewsDeliveryService запущен")

    async def stop(self) -> None:
        """Остановить сервис доставки."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:  # noqa: SIM105
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("✅ NewsDeliveryService остановлен")

    async def _delivery_loop(self) -> None:
        """Основной цикл доставки новостей."""
        while self._running:
            try:
                # Проверяем, наступило ли время рассылки (например, 9:00)
                now = datetime.now().time()
                delivery_time = time(9, 0)  # 9:00 утра

                # Если время рассылки прошло сегодня, ждем до завтра
                if now < delivery_time:
                    wait_seconds = (
                        datetime.combine(datetime.now().date(), delivery_time) - datetime.now()
                    ).total_seconds()
                else:
                    # Время рассылки прошло, ждем до завтра
                    tomorrow = datetime.now().date().replace(day=datetime.now().day + 1)
                    wait_seconds = (
                        datetime.combine(tomorrow, delivery_time) - datetime.now()
                    ).total_seconds()

                logger.info(f"⏰ Следующая рассылка через {wait_seconds / 3600:.1f} часов")
                await asyncio.sleep(wait_seconds)

                # Выполняем рассылку
                await self._send_daily_news()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле доставки: {e}")
                await asyncio.sleep(3600)  # Ждем час перед повтором

    async def _send_daily_news(self) -> None:
        """Отправить ежедневные новости всем пользователям."""
        try:
            # Получаем всех активных пользователей
            stmt = select(User).where(User.is_active == True)  # noqa: E712
            users = self.db.execute(stmt).scalars().all()

            sent_count = 0
            for user in users:
                try:
                    prefs = self.preferences_service.get_or_create_preferences(user.telegram_id)

                    # Проверяем, включена ли рассылка
                    if not prefs.get("daily_notifications", False):
                        continue

                    # Получаем персонализированные новости
                    news_list = await self._get_personalized_news(prefs)

                    if news_list:
                        # Отправляем первую новость
                        news = news_list[0]
                        await self._send_news_message(user.telegram_id, news)
                        sent_count += 1

                except Exception as e:
                    logger.warning(
                        f"⚠️ Ошибка отправки новости пользователю {user.telegram_id}: {e}"
                    )
                    continue

            logger.info(f"✅ Ежедневная рассылка завершена: отправлено {sent_count} новостей")

        except Exception as e:
            logger.error(f"❌ Ошибка ежедневной рассылки: {e}")

    async def _get_personalized_news(self, prefs: dict[str, Any]) -> list:
        """
        Получить персонализированные новости для пользователя.

        Args:
            prefs: Предпочтения пользователя

        Returns:
            List[News]: Список новостей
        """
        age = prefs.get("age")
        grade = prefs.get("grade")
        categories = prefs.get("categories", [])

        # Если выбраны категории, берем из них
        if categories:
            all_news = []
            for category in categories:
                news = self.repository.find_by_category(
                    category=category, age=age, grade=grade, limit=2
                )
                all_news.extend(news)
            return all_news[:5]  # Максимум 5 новостей

        # Иначе берем последние новости с учетом возраста/класса
        if age:
            return self.repository.find_by_age(age, limit=5)
        elif grade:
            return self.repository.find_by_grade(grade, limit=5)
        else:
            return self.repository.find_recent(limit=5)

    async def _send_news_message(self, telegram_id: int, news: Any) -> None:
        """
        Отправить новость пользователю.

        Args:
            telegram_id: Telegram ID пользователя
            news: Объект News
        """
        try:
            text = f"<b>{news.title}</b>\n\n{news.content[:500]}"

            if news.image_url:
                await self.bot.send_photo(
                    telegram_id, news.image_url, caption=text, parse_mode="HTML"
                )
            else:
                await self.bot.send_message(telegram_id, text, parse_mode="HTML")

            # Отмечаем как прочитанную
            self.preferences_service.mark_news_read(telegram_id, news.id)

        except Exception as e:
            logger.error(f"❌ Ошибка отправки новости: {e}")
