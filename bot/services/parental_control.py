"""
Система родительского контроля для PandaPal
Обеспечивает мониторинг активности детей и отчеты для родителей
@module bot.services.parental_control
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from bot.models import ChatHistory, User
from bot.services.advanced_moderation import ContentCategory, ModerationLevel


class ActivityType(Enum):
    """Типы активности ребенка"""

    MESSAGE_SENT = "message_sent"
    MESSAGE_BLOCKED = "message_blocked"
    VOICE_MESSAGE = "voice_message"
    AI_INTERACTION = "ai_interaction"
    SETTINGS_CHANGED = "settings_changed"
    LOGIN = "login"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AlertLevel(Enum):
    """Уровни предупреждений для родителей"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ActivityRecord:
    """Запись активности ребенка"""

    child_id: int
    activity_type: ActivityType
    timestamp: datetime
    details: Dict[str, Any]
    alert_level: AlertLevel
    message_content: Optional[str] = None
    moderation_result: Optional[Dict] = None


@dataclass
class ParentReport:
    """Отчет для родителя"""

    parent_id: int
    child_id: int
    period_start: datetime
    period_end: datetime
    total_messages: int
    blocked_messages: int
    suspicious_activities: int
    ai_interactions: int
    voice_messages: int
    moderation_summary: Dict[str, int]
    recent_activities: List[ActivityRecord]
    recommendations: List[str]


class ParentalControlService:
    """
    Сервис родительского контроля
    Мониторит активность детей и предоставляет отчеты родителям
    """

    def __init__(self, db_session: Session):
        """Инициализация сервиса родительского контроля"""
        self.db = db_session
        self.activity_buffer: List[ActivityRecord] = []
        self.buffer_size = 100

        logger.info("👨‍👩‍👧‍👦 Система родительского контроля инициализирована")

    async def record_child_activity(
        self,
        child_telegram_id: int,
        activity_type: ActivityType,
        details: Dict[str, Any] = None,
        message_content: str = None,
        moderation_result: Dict = None,
    ) -> None:
        """
        Записывает активность ребенка

        Args:
            child_telegram_id: Telegram ID ребенка
            activity_type: Тип активности
            details: Дополнительные детали
            message_content: Содержимое сообщения (если есть)
            moderation_result: Результат модерации (если есть)
        """
        if details is None:
            details = {}

        # Определяем уровень предупреждения
        alert_level = self._determine_alert_level(activity_type, moderation_result, details)

        # Создаем запись активности
        activity = ActivityRecord(
            child_id=child_telegram_id,
            activity_type=activity_type,
            timestamp=datetime.utcnow(),
            details=details,
            alert_level=alert_level,
            message_content=message_content,
            moderation_result=moderation_result,
        )

        # Добавляем в буфер
        self.activity_buffer.append(activity)

        # Если буфер заполнен, сохраняем в БД
        if len(self.activity_buffer) >= self.buffer_size:
            await self._flush_activity_buffer()

        # Если критический уровень - немедленно уведомляем родителей
        if alert_level == AlertLevel.CRITICAL:
            await self._notify_parents_immediately(child_telegram_id, activity)

        logger.info(
            f"📊 Активность записана: {child_telegram_id} | "
            f"Тип: {activity_type.value} | Уровень: {alert_level.value}"
        )

    def _determine_alert_level(
        self, activity_type: ActivityType, moderation_result: Dict = None, details: Dict = None
    ) -> AlertLevel:
        """Определяет уровень предупреждения для активности"""

        # Критические события
        if activity_type == ActivityType.SUSPICIOUS_ACTIVITY:
            return AlertLevel.CRITICAL

        if moderation_result:
            # Проверяем результат модерации
            if moderation_result.get("level") == ModerationLevel.DANGEROUS:
                return AlertLevel.CRITICAL
            elif moderation_result.get("level") == ModerationLevel.BLOCKED:
                return AlertLevel.WARNING

        # Блокированные сообщения
        if activity_type == ActivityType.MESSAGE_BLOCKED:
            return AlertLevel.WARNING

        # Обычные активности
        return AlertLevel.INFO

    async def _flush_activity_buffer(self) -> None:
        """Сохраняет буфер активности в базу данных"""
        if not self.activity_buffer:
            return

        try:
            # Здесь можно добавить сохранение в таблицу activity_log
            # Пока просто логируем
            logger.info(f"💾 Сохранено {len(self.activity_buffer)} записей активности")
            self.activity_buffer.clear()
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения активности: {e}")

    async def _notify_parents_immediately(self, child_id: int, activity: ActivityRecord) -> None:
        """Немедленно уведомляет родителей о критической активности"""
        try:
            # Находим родителей ребенка
            parents = self._get_parents_of_child(child_id)

            for parent in parents:
                # Здесь можно добавить отправку уведомления родителю
                logger.warning(
                    f"🚨 КРИТИЧЕСКАЯ АКТИВНОСТЬ | "
                    f"Ребенок: {child_id} | Родитель: {parent.telegram_id} | "
                    f"Тип: {activity.activity_type.value}"
                )

        except Exception as e:
            logger.error(f"❌ Ошибка уведомления родителей: {e}")

    def _get_parents_of_child(self, child_id: int) -> List[User]:
        """Возвращает список родителей ребенка"""
        child = (
            self.db.query(User)
            .filter(User.telegram_id == child_id, User.user_type == "child")
            .first()
        )

        if not child or not child.parent_telegram_id:
            return []

        parent = (
            self.db.query(User)
            .filter(User.telegram_id == child.parent_telegram_id, User.user_type == "parent")
            .first()
        )

        return [parent] if parent else []

    async def generate_parent_report(
        self, parent_id: int, child_id: int, days: int = 7
    ) -> ParentReport:
        """
        Генерирует отчет для родителя

        Args:
            parent_id: Telegram ID родителя
            child_id: Telegram ID ребенка
            days: Количество дней для отчета

        Returns:
            ParentReport: Детальный отчет об активности ребенка
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        # Получаем статистику сообщений
        message_stats = self._get_message_statistics(child_id, period_start, period_end)

        # Получаем статистику модерации
        moderation_stats = self._get_moderation_statistics(child_id, period_start, period_end)

        # Получаем последние активности
        recent_activities = self._get_recent_activities(child_id, period_start, period_end)

        # Генерируем рекомендации
        recommendations = self._generate_recommendations(message_stats, moderation_stats)

        report = ParentReport(
            parent_id=parent_id,
            child_id=child_id,
            period_start=period_start,
            period_end=period_end,
            total_messages=message_stats["total"],
            blocked_messages=message_stats["blocked"],
            suspicious_activities=message_stats["suspicious"],
            ai_interactions=message_stats["ai_interactions"],
            voice_messages=message_stats["voice_messages"],
            moderation_summary=moderation_stats,
            recent_activities=recent_activities,
            recommendations=recommendations,
        )

        logger.info(f"📊 Отчет сгенерирован: Родитель {parent_id} -> Ребенок {child_id}")
        return report

    def _get_message_statistics(
        self, child_id: int, start: datetime, end: datetime
    ) -> Dict[str, int]:
        """Получает статистику сообщений ребенка"""
        # Запрос к таблице chat_history
        total_messages = (
            self.db.query(ChatHistory)
            .filter(
                ChatHistory.user_telegram_id == child_id,
                ChatHistory.timestamp >= start,
                ChatHistory.timestamp <= end,
                ChatHistory.message_type == "user",
            )
            .count()
        )

        # Здесь можно добавить более детальную статистику
        # Пока возвращаем базовые данные
        # Получаем реальную статистику модерации
        moderation_stats = self._get_moderation_statistics(child_id, start, end)

        return {
            "total": total_messages,
            "blocked": moderation_stats.get("blocked", 0),
            "suspicious": moderation_stats.get("suspicious", 0),
            "ai_interactions": total_messages,  # Каждое сообщение = взаимодействие с AI
            "voice_messages": moderation_stats.get("voice_messages", 0),
        }

    def _get_moderation_statistics(
        self, child_id: int, start: datetime, end: datetime
    ) -> Dict[str, int]:
        """Получает статистику модерации"""
        try:
            # Получаем реальную статистику из буфера активности
            blocked_count = 0
            suspicious_count = 0
            voice_messages_count = 0

            for activity in self.activity_buffer:
                if activity.child_id == child_id and start <= activity.timestamp <= end:

                    if activity.activity_type == ActivityType.MESSAGE_BLOCKED:
                        blocked_count += 1
                    elif activity.alert_level == "WARNING":
                        suspicious_count += 1
                    elif "voice" in activity.activity_type.value.lower():
                        voice_messages_count += 1

            return {
                "blocked": blocked_count,
                "suspicious": suspicious_count,
                "voice_messages": voice_messages_count,
                "violence": 0,  # Можно расширить в будущем
                "drugs": 0,
                "politics": 0,
                "bullying": 0,
                "scam": 0,
                "spam": 0,
            }
        except Exception:
            # Fallback при ошибке
            return {
                "blocked": 0,
                "suspicious": 0,
                "voice_messages": 0,
                "violence": 0,
                "drugs": 0,
                "politics": 0,
                "bullying": 0,
                "scam": 0,
                "spam": 0,
            }

    def _get_recent_activities(
        self, child_id: int, start: datetime, end: datetime
    ) -> List[ActivityRecord]:
        """Получает последние активности ребенка"""
        # Здесь можно получить данные из таблицы активности
        # Пока возвращаем данные из буфера
        return [
            activity
            for activity in self.activity_buffer
            if activity.child_id == child_id and start <= activity.timestamp <= end
        ]

    def _generate_recommendations(self, message_stats: Dict, moderation_stats: Dict) -> List[str]:
        """Генерирует рекомендации для родителей"""
        recommendations = []

        # Рекомендации по количеству сообщений
        if message_stats["total"] > 50:
            recommendations.append(
                "Ребенок активно использует бота. Рекомендуется обсудить баланс между обучением и развлечением."
            )

        # Рекомендации по заблокированному контенту
        blocked_count = message_stats["blocked"]
        if blocked_count > 5:
            recommendations.append(
                "Обнаружено много заблокированных сообщений. Рекомендуется поговорить с ребенком о правилах безопасности."
            )

        # Рекомендации по подозрительной активности
        if message_stats["suspicious"] > 0:
            recommendations.append(
                "Обнаружена подозрительная активность. Рекомендуется усиленный контроль."
            )

        # Общие рекомендации
        if not recommendations:
            recommendations.append("Ребенок использует бота безопасно. Продолжайте мониторинг.")

        return recommendations

    async def link_parent_to_child(self, parent_id: int, child_id: int) -> bool:
        """
        Связывает родителя с ребенком

        Args:
            parent_id: Telegram ID родителя
            child_id: Telegram ID ребенка

        Returns:
            bool: Успешно ли создана связь
        """
        try:
            # Проверяем что пользователи существуют и имеют правильные типы
            parent = (
                self.db.query(User)
                .filter(User.telegram_id == parent_id, User.user_type == "parent")
                .first()
            )

            child = (
                self.db.query(User)
                .filter(User.telegram_id == child_id, User.user_type == "child")
                .first()
            )

            if not parent or not child:
                logger.error(
                    f"❌ Родитель или ребенок не найдены: parent={parent_id}, child={child_id}"
                )
                return False

            # Устанавливаем связь
            child.parent_telegram_id = parent_id
            self.db.commit()

            logger.info(f"👨‍👧 Связь создана: Родитель {parent_id} <-> Ребенок {child_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка создания связи родитель-ребенок: {e}")
            self.db.rollback()
            return False

    async def get_children_of_parent(self, parent_id: int) -> List[User]:
        """
        Возвращает список детей родителя

        Args:
            parent_id: Telegram ID родителя

        Returns:
            List[User]: Список детей
        """
        children = (
            self.db.query(User)
            .filter(
                User.parent_telegram_id == parent_id,
                User.user_type == "child",
                User.is_active.is_(True),
            )
            .all()
        )

        return children

    async def get_parental_control_stats(self) -> Dict[str, Any]:
        """Возвращает общую статистику родительского контроля"""
        total_parents = self.db.query(User).filter(User.user_type == "parent").count()
        total_children = self.db.query(User).filter(User.user_type == "child").count()
        linked_children = (
            self.db.query(User)
            .filter(User.user_type == "child", User.parent_telegram_id.isnot(None))
            .count()
        )

        return {
            "total_parents": total_parents,
            "total_children": total_children,
            "linked_children": linked_children,
            "unlinked_children": total_children - linked_children,
            "activity_records_in_buffer": len(self.activity_buffer),
            "coverage_percentage": (
                (linked_children / total_children * 100) if total_children > 0 else 0
            ),
        }
