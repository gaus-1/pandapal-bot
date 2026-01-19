"""
Сервис приоритетной поддержки для Premium пользователей.

Обеспечивает приоритетную обработку запросов поддержки для Premium пользователей.
"""

from datetime import datetime
from enum import Enum

from loguru import logger
from sqlalchemy.orm import Session

from bot.services.premium_features_service import PremiumFeaturesService


class SupportPriority(Enum):
    """Приоритеты поддержки."""

    FREE = "free"  # Бесплатные пользователи
    PREMIUM = "premium"  # Premium пользователи
    VIP = "vip"  # VIP пользователи (годовая подписка)


class SupportRequest:
    """Запрос в поддержку."""

    def __init__(  # noqa: D107
        self,
        telegram_id: int,
        message: str,
        priority: SupportPriority,
        created_at: datetime,
    ):
        self.telegram_id = telegram_id
        self.message = message
        self.priority = priority
        self.created_at = created_at


class PrioritySupportService:
    """
    Сервис приоритетной поддержки.

    Обеспечивает приоритетную обработку запросов для Premium пользователей.
    """

    def __init__(self, db: Session):
        """
        Инициализация сервиса.

        Args:
            db: Сессия SQLAlchemy
        """
        self.db = db
        self.premium_service = PremiumFeaturesService(db)
        # В памяти очередь поддержки (в production можно использовать Redis)
        self._support_queue: list[SupportRequest] = []

    def get_support_priority(self, telegram_id: int) -> SupportPriority:
        """
        Получить приоритет поддержки для пользователя.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            SupportPriority: Приоритет поддержки
        """
        if not self.premium_service.is_premium_active(telegram_id):
            return SupportPriority.FREE

        plan = self.premium_service.get_premium_plan(telegram_id)
        if plan == "year":
            return SupportPriority.VIP

        return SupportPriority.PREMIUM

    def add_support_request(self, telegram_id: int, message: str) -> SupportRequest:
        """
        Добавить запрос в поддержку.

        Args:
            telegram_id: Telegram ID пользователя
            message: Сообщение в поддержку

        Returns:
            SupportRequest: Созданный запрос
        """
        priority = self.get_support_priority(telegram_id)
        request = SupportRequest(
            telegram_id=telegram_id,
            message=message,
            priority=priority,
            created_at=datetime.utcnow(),
        )

        # Добавляем в очередь с учетом приоритета
        # VIP и Premium в начало, FREE в конец
        if priority == SupportPriority.VIP:
            self._support_queue.insert(0, request)
        elif priority == SupportPriority.PREMIUM:
            # Вставляем после VIP, но перед FREE
            vip_count = sum(1 for r in self._support_queue if r.priority == SupportPriority.VIP)
            self._support_queue.insert(vip_count, request)
        else:
            self._support_queue.append(request)

        logger.info(
            f"📞 Запрос в поддержку добавлен: user={telegram_id}, "
            f"priority={priority.value}, queue_position={self._get_queue_position(telegram_id)}"
        )

        return request

    def get_next_support_request(self) -> SupportRequest | None:
        """
        Получить следующий запрос из очереди (с учетом приоритета).

        Returns:
            Optional[SupportRequest]: Следующий запрос или None
        """
        if not self._support_queue:
            return None

        return self._support_queue.pop(0)

    def _get_queue_position(self, telegram_id: int) -> int:
        """Получить позицию в очереди."""
        for i, request in enumerate(self._support_queue):
            if request.telegram_id == telegram_id:
                return i + 1
        return len(self._support_queue) + 1

    def get_queue_info(self, telegram_id: int) -> dict:
        """
        Получить информацию о позиции в очереди.

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict: Информация о позиции
        """
        priority = self.get_support_priority(telegram_id)
        position = self._get_queue_position(telegram_id)

        # Подсчитываем запросы с более высоким приоритетом
        higher_priority_count = sum(
            1 for r in self._support_queue if r.priority.value < priority.value
        )

        return {
            "priority": priority.value,
            "queue_position": position,
            "higher_priority_requests": higher_priority_count,
            "estimated_wait_time": self._estimate_wait_time(priority, position),
        }

    def _estimate_wait_time(self, priority: SupportPriority, position: int) -> int:
        """Оценить время ожидания в минутах."""
        if priority == SupportPriority.VIP:
            return max(0, (position - 1) * 2)  # 2 минуты на запрос
        elif priority == SupportPriority.PREMIUM:
            return max(0, (position - 1) * 5)  # 5 минут на запрос
        else:
            return max(0, (position - 1) * 15)  # 15 минут на запрос
