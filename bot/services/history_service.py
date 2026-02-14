"""
Сервис управления историей чата пользователей.

Этот модуль предоставляет функциональность для работы с историей сообщений
пользователей, включая сохранение, получение и очистку истории чата.

Основные возможности:
- Сохранение сообщений пользователей и AI
- Получение истории чата с ограничениями
- Очистка истории по требованию пользователя
- Автоматическое управление размером истории
"""

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from bot.config import settings
from bot.models import ChatHistory


class ChatHistoryService:
    """
    Сервис управления историей чата для обеспечения памяти AI.

    Обеспечивает сохранение и получение истории сообщений для поддержания
    контекста диалога между пользователем и AI ассистентом.
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса истории чата.

        Args:
            db (Session): Сессия SQLAlchemy для работы с базой данных.
        """
        self.db = db
        self.history_limit = settings.chat_history_limit  # Лимит сообщений для контекста

    def add_message(
        self, telegram_id: int, message_text: str, message_type: str, image_url: str | None = None
    ) -> ChatHistory:
        """
        Добавить сообщение в историю.

        Args:
            telegram_id: Telegram ID пользователя
            message_text: Текст сообщения
            message_type: Тип сообщения ('user', 'ai', 'system')
            image_url: URL изображения визуализации (опционально)

        Returns:
            ChatHistory: Созданная запись

        Raises:
            ValueError: Если message_type некорректен
        """
        # Валидация типа сообщения
        if message_type not in ["user", "ai", "system"]:
            raise ValueError(f"Некорректный message_type: {message_type}")

        # Создаём новое сообщение
        message = ChatHistory(
            user_telegram_id=telegram_id,
            message_text=message_text,
            message_type=message_type,
            image_url=image_url,
        )

        try:
            self.db.add(message)
            self.db.flush()  # Получаем ID не коммитя транзакцию
            logger.info(
                f"📝 Сообщение добавлено в сессию: user={telegram_id}, type={message_type}, id={message.id}"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка добавления сообщения в сессию: {e}", exc_info=True)
            raise

        # Очищаем старые сообщения (храним только последние N)
        self._cleanup_old_messages(telegram_id)

        logger.info(
            f"✅ Сообщение готово к коммиту: user={telegram_id}, type={message_type}, id={message.id}"
        )

        return message

    def get_recent_history(self, telegram_id: int, limit: int = None) -> list[ChatHistory]:
        """
        Получить последние N сообщений пользователя.

        Используется для формирования контекста AI.

        Args:
            telegram_id: Telegram ID пользователя
            limit: Количество сообщений (по умолчанию из settings)

        Returns:
            List[ChatHistory]: Список сообщений (от старых к новым)
        """
        if limit is None:
            limit = self.history_limit

        # Выбираем последние N сообщений (при равном timestamp порядок по id — вопрос всегда перед ответом)
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.user_telegram_id == telegram_id)
            .order_by(desc(ChatHistory.timestamp), desc(ChatHistory.id))
            .limit(limit)
        )

        messages = self.db.execute(stmt).scalars().all()

        # Возвращаем в хронологическом порядке (старые → новые)
        return list(reversed(messages))

    def get_last_user_message_timestamp(self, telegram_id: int) -> datetime | None:
        """
        Время последнего сообщения пользователя (message_type == "user").

        Используется для проактивных сообщений (24ч / 7 дней без активности).

        Args:
            telegram_id: Telegram ID пользователя.

        Returns:
            datetime | None: timestamp последнего user-сообщения или None.
        """
        stmt = (
            select(ChatHistory.timestamp)
            .where(ChatHistory.user_telegram_id == telegram_id)
            .where(ChatHistory.message_type == "user")
            .order_by(desc(ChatHistory.timestamp))
            .limit(1)
        )
        row = self.db.execute(stmt).first()
        return row[0] if row else None

    def get_conversation_context(self, telegram_id: int) -> str:
        """
        Получить контекст разговора в виде строки для AI.

        Форматирует последние сообщения в читаемый вид.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            str: Форматированная история чата

        Example:
            >>> context = service.get_conversation_context(123456)
            >>> # context будет содержать:
            >>> # "User: Привет! Помоги с математикой
            >>> # AI: Привет! Конечно помогу. Что нужно решить?
            >>> # User: 2+2*2
            >>> # AI: Давай разберём по порядку..."
        """
        messages = self.get_recent_history(telegram_id)

        if not messages:
            return ""

        # Форматируем сообщения
        context_lines = []
        for msg in messages:
            role = {"user": "User", "ai": "AI", "system": "System"}.get(msg.message_type, "Unknown")

            context_lines.append(f"{role}: {msg.message_text}")

        return "\n".join(context_lines)

    def get_formatted_history_for_ai(
        self, telegram_id: int, limit: int = None
    ) -> list[dict[str, Any]]:
        """
        Получить историю в формате для YandexGPT API.

        Args:
            telegram_id: Telegram ID пользователя
            limit: Количество сообщений (по умолчанию из settings)

        Returns:
            List[Dict[str, Any]]: История в формате [{'role': 'user', 'text': '...'}, ...]
        """
        messages = self.get_recent_history(telegram_id, limit=limit)

        formatted: list[dict[str, Any]] = []
        for msg in messages:
            # Конвертируем наш message_type в формат YandexGPT
            role = "user" if msg.message_type == "user" else "assistant"

            # Форматируем в формате YandexGPT API
            formatted.append({"role": role, "text": msg.message_text})

        return formatted

    def _cleanup_old_messages(self, telegram_id: int) -> None:
        """
        Удаляет старые сообщения, оставляя только последние N.

        Вызывается автоматически при добавлении нового сообщения.

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

        # Автоудаление отключено - храним всю историю
        logger.debug(
            f"💾 История сохранена для user={telegram_id} (всего сообщений: {len(all_messages)})"
        )

    def clear_history(self, telegram_id: int) -> int:
        """
        Очистить всю историю пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            int: Количество удалённых сообщений
        """
        stmt = select(ChatHistory).where(ChatHistory.user_telegram_id == telegram_id)

        messages = self.db.execute(stmt).scalars().all()
        count = len(messages)

        for msg in messages:
            self.db.delete(msg)

        logger.info(f"🗑️ Очищена история для user={telegram_id}, удалено {count} сообщений")

        return count

    def get_message_count(self, telegram_id: int) -> int:
        """
        Получить количество сообщений в истории.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            int: Количество сообщений
        """
        stmt = select(ChatHistory).where(ChatHistory.user_telegram_id == telegram_id)

        messages = self.db.execute(stmt).scalars().all()
        return len(messages)
