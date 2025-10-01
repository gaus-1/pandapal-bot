"""
Сервис для работы с историей чата
Управляет памятью AI (последние 50 сообщений)
@module bot.services.history_service
"""

from typing import List, Dict
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from bot.models import ChatHistory, User
from bot.config import settings
from loguru import logger


class ChatHistoryService:
    """
    Сервис управления историей чата
    Обеспечивает память AI на заданное количество сообщений
    """
    
    def __init__(self, db: Session):
        """
        Инициализация сервиса
        
        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db
        self.history_limit = settings.chat_history_limit  # 50 сообщений
    
    def add_message(
        self, 
        telegram_id: int, 
        message_text: str, 
        message_type: str
    ) -> ChatHistory:
        """
        Добавить сообщение в историю
        
        Args:
            telegram_id: Telegram ID пользователя
            message_text: Текст сообщения
            message_type: Тип сообщения ('user', 'ai', 'system')
        
        Returns:
            ChatHistory: Созданная запись
        
        Raises:
            ValueError: Если message_type некорректен
        """
        # Валидация типа сообщения
        if message_type not in ['user', 'ai', 'system']:
            raise ValueError(f"Некорректный message_type: {message_type}")
        
        # Создаём новое сообщение
        message = ChatHistory(
            user_telegram_id=telegram_id,
            message_text=message_text,
            message_type=message_type
        )
        
        self.db.add(message)
        self.db.flush()  # Получаем ID не коммитя транзакцию
        
        # Очищаем старые сообщения (храним только последние N)
        self._cleanup_old_messages(telegram_id)
        
        logger.debug(f"📝 Добавлено сообщение: user={telegram_id}, type={message_type}")
        
        return message
    
    def get_recent_history(
        self, 
        telegram_id: int, 
        limit: int = None
    ) -> List[ChatHistory]:
        """
        Получить последние N сообщений пользователя
        Используется для формирования контекста AI
        
        Args:
            telegram_id: Telegram ID пользователя
            limit: Количество сообщений (по умолчанию из settings)
        
        Returns:
            List[ChatHistory]: Список сообщений (от старых к новым)
        """
        if limit is None:
            limit = self.history_limit
        
        # Выбираем последние N сообщений
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.user_telegram_id == telegram_id)
            .order_by(desc(ChatHistory.timestamp))
            .limit(limit)
        )
        
        messages = self.db.execute(stmt).scalars().all()
        
        # Возвращаем в хронологическом порядке (старые → новые)
        return list(reversed(messages))
    
    def get_conversation_context(self, telegram_id: int) -> str:
        """
        Получить контекст разговора в виде строки для AI
        Форматирует последние сообщения в читаемый вид
        
        Args:
            telegram_id: Telegram ID пользователя
        
        Returns:
            str: Форматированная история чата
        
        Example:
            >>> context = service.get_conversation_context(123456)
            >>> print(context)
            User: Привет! Помоги с математикой
            AI: Привет! Конечно помогу. Что нужно решить?
            User: 2+2*2
            AI: Давай разберём по порядку...
        """
        messages = self.get_recent_history(telegram_id)
        
        if not messages:
            return ""
        
        # Форматируем сообщения
        context_lines = []
        for msg in messages:
            role = {
                'user': 'User',
                'ai': 'AI',
                'system': 'System'
            }.get(msg.message_type, 'Unknown')
            
            context_lines.append(f"{role}: {msg.message_text}")
        
        return "\n".join(context_lines)
    
    def get_formatted_history_for_ai(
        self, 
        telegram_id: int
    ) -> List[Dict[str, str]]:
        """
        Получить историю в формате для Gemini API
        
        Args:
            telegram_id: Telegram ID пользователя
        
        Returns:
            List[Dict]: История в формате [{'role': 'user', 'parts': ['text']}, ...]
        """
        messages = self.get_recent_history(telegram_id)
        
        formatted = []
        for msg in messages:
            # Конвертируем наш message_type в формат Gemini
            role = 'user' if msg.message_type == 'user' else 'model'
            
            formatted.append({
                'role': role,
                'parts': [msg.message_text]
            })
        
        return formatted
    
    def _cleanup_old_messages(self, telegram_id: int) -> None:
        """
        Удаляет старые сообщения, оставляя только последние N
        Вызывается автоматически при добавлении нового сообщения
        
        Args:
            telegram_id: Telegram ID пользователя
        """
        # Подсчитываем количество сообщений
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.user_telegram_id == telegram_id)
            .order_by(desc(ChatHistory.timestamp))
        )
        
        all_messages = self.db.execute(stmt).scalars().all()
        
        # Если больше лимита — удаляем старые
        if len(all_messages) > self.history_limit:
            messages_to_delete = all_messages[self.history_limit:]
            
            for msg in messages_to_delete:
                self.db.delete(msg)
            
            logger.debug(f"🗑️ Удалено {len(messages_to_delete)} старых сообщений для user={telegram_id}")
    
    def clear_history(self, telegram_id: int) -> int:
        """
        Очистить всю историю пользователя
        
        Args:
            telegram_id: Telegram ID пользователя
        
        Returns:
            int: Количество удалённых сообщений
        """
        stmt = select(ChatHistory).where(
            ChatHistory.user_telegram_id == telegram_id
        )
        
        messages = self.db.execute(stmt).scalars().all()
        count = len(messages)
        
        for msg in messages:
            self.db.delete(msg)
        
        logger.info(f"🗑️ Очищена история для user={telegram_id}, удалено {count} сообщений")
        
        return count
    
    def get_message_count(self, telegram_id: int) -> int:
        """
        Получить количество сообщений в истории
        
        Args:
            telegram_id: Telegram ID пользователя
        
        Returns:
            int: Количество сообщений
        """
        stmt = select(ChatHistory).where(
            ChatHistory.user_telegram_id == telegram_id
        )
        
        messages = self.db.execute(stmt).scalars().all()
        return len(messages)


