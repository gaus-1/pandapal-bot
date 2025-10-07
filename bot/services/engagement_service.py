"""
Сервис вовлечения пользователей
Отправляет напоминания неактивным пользователям
"""

import asyncio
from datetime import datetime, timedelta
from typing import List

from aiogram import Bot
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.config import settings
from bot.models import User, ChatHistory


class EngagementService:
    """
    Сервис для повышения вовлеченности пользователей
    Отправляет персонализированные напоминания неактивным ученикам
    """
    
    def __init__(self, db_session: Session, bot: Bot):
        """
        Инициализация сервиса
        
        Args:
            db_session: Сессия БД
            bot: Экземпляр бота для отправки сообщений
        """
        self.db = db_session
        self.bot = bot
        self.inactive_days = 7  # Неделя
        
        logger.info("📬 Сервис вовлечения пользователей инициализирован")
    
    async def find_inactive_users(self) -> List[User]:
        """
        Находит пользователей неактивных больше недели
        
        Returns:
            List[User]: Список неактивных пользователей
        """
        cutoff_date = datetime.now() - timedelta(days=self.inactive_days)
        
        # Находим пользователей с последним сообщением старше недели
        stmt = (
            select(User)
            .join(ChatHistory, User.telegram_id == ChatHistory.user_telegram_id)
            .where(ChatHistory.timestamp < cutoff_date)
            .distinct()
        )
        
        inactive_users = self.db.execute(stmt).scalars().all()
        
        logger.info(f"📊 Найдено {len(inactive_users)} неактивных пользователей")
        
        return inactive_users
    
    async def send_engagement_message(self, user: User) -> bool:
        """
        Отправляет персонализированное напоминание пользователю
        
        Args:
            user: Пользователь для отправки
        
        Returns:
            bool: True если отправлено успешно
        """
        try:
            # Персонализированные сообщения в зависимости от профиля
            messages = self._get_engagement_messages(user)
            
            # Выбираем случайное сообщение
            import random
            message_text = random.choice(messages)
            
            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message_text,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            
            logger.info(f"📬 Отправлено напоминание пользователю {user.telegram_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания {user.telegram_id}: {e}")
            return False
    
    def _get_engagement_messages(self, user: User) -> List[str]:
        """
        Генерирует персонализированные сообщения
        
        Args:
            user: Пользователь
        
        Returns:
            List[str]: Список возможных сообщений
        """
        name = user.first_name or "друг"
        grade_info = f"ученик {user.grade} класса" if user.grade else "школьник"
        
        messages = [
            f"""
🐼 Привет, {name}!

Я скучаю по нашим беседам! 💙

Помнишь, как мы вместе решали задачки? 
У меня есть куча новых интересных тем для обсуждения!

✨ <b>Чем могу помочь сегодня?</b>
• Объяснить сложную тему из школы
• Помочь с домашкой
• Просто поболтать о науке и мире

Жду твоих вопросов! 🎓

<a href="https://pandapal.ru">🌐 Узнать больше о PandaPal</a>
""",
            f"""
👋 {name}, как дела?

Давненько не общались! Я тут подумал... 🤔

Может, у тебя накопились вопросы по учёбе? 
Или хочешь узнать что-то новое и интересное?

🐼 <b>Я всегда рад помочь!</b>
• Математика, русский, физика - что угодно!
• Объясню простым языком
• Покажу интересные примеры

Напиши мне! Буду ждать! 💪

<a href="https://pandapal.ru">Подробнее о PandaPal →</a>
""",
            f"""
🌟 {name}!

Целую неделю тебя не было... Всё хорошо? 😊

Знаешь, учёба идёт лучше, когда занимаешься регулярно!
Даже 5 минут в день с PandaPal - это уже прогресс! 📈

💡 <b>Интересные темы сегодня:</b>
• Почему небо голубое?
• Как работают компьютеры?
• Секреты математики
• И многое другое!

Давай продолжим учиться вместе! 🎓

<a href="https://pandapal.ru">Открыть PandaPal</a>
""",
        ]
        
        # Для старшеклассников более серьезный тон
        if user.grade and user.grade >= 9:
            messages.append(f"""
👋 {name}!

Прошла неделя с нашей последней беседы.

Готовишься к экзаменам? Есть сложные темы? 
Я могу помочь разобраться и объяснить материал.

📚 <b>Доступная помощь:</b>
• Подготовка к ОГЭ/ЕГЭ
• Разбор сложных тем
• Проверка решений
• Консультации по всем предметам

Буду рад снова работать вместе! 🎯

<a href="https://pandapal.ru">PandaPal - твой помощник в учёбе</a>
""")
        
        return messages
    
    async def run_engagement_campaign(self) -> dict:
        """
        Запускает кампанию вовлечения неактивных пользователей
        
        Returns:
            dict: Статистика отправки
        """
        logger.info("📬 Запуск кампании вовлечения...")
        
        # Находим неактивных пользователей
        inactive_users = await self.find_inactive_users()
        
        if not inactive_users:
            logger.info("✅ Нет неактивных пользователей")
            return {
                "total": 0,
                "sent": 0,
                "failed": 0
            }
        
        # Отправляем напоминания
        sent_count = 0
        failed_count = 0
        
        for user in inactive_users:
            success = await self.send_engagement_message(user)
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
            
            # Задержка между сообщениями (anti-spam)
            await asyncio.sleep(1)
        
        logger.info(f"✅ Кампания завершена: отправлено {sent_count}/{len(inactive_users)}")
        
        return {
            "total": len(inactive_users),
            "sent": sent_count,
            "failed": failed_count
        }

