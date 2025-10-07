"""
Сервис алертов и уведомлений для PandaPal
Отслеживает критические события и уведомляет родителей

"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from bot.models import AnalyticsAlert, ParentalSettings, User
from bot.services.cache_service import cache_service


class AlertLevel(Enum):
    """Уровни алертов"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Типы алертов"""

    SAFETY_VIOLATION = "safety_violation"
    HIGH_BLOCKED_RATIO = "high_blocked_ratio"
    LOW_ENGAGEMENT = "low_engagement"
    LONG_INACTIVITY = "long_inactivity"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    LEARNING_PROGRESS = "learning_progress"
    SYSTEM_ERROR = "system_error"
    PARENTAL_CONTROL = "parental_control"


@dataclass
class AlertRule:
    """Правило для генерации алертов"""

    alert_type: AlertType
    alert_level: AlertLevel
    threshold: float
    condition: str
    message_template: str
    cooldown_minutes: int = 60


class AlertService:
    """
    Сервис алертов и уведомлений
    Отслеживает события и генерирует уведомления для родителей
    """

    def __init__(self, db_session: Session):
        """Инициализация сервиса алертов"""
        self.db = db_session
        self.cache_ttl = 300  # 5 минут кэширования

        # Определяем правила алертов
        self.alert_rules = self._initialize_alert_rules()

        logger.info("🚨 Сервис алертов инициализирован")

    def _initialize_alert_rules(self) -> Dict[AlertType, AlertRule]:
        """Инициализация правил алертов"""
        return {
            AlertType.SAFETY_VIOLATION: AlertRule(
                alert_type=AlertType.SAFETY_VIOLATION,
                alert_level=AlertLevel.CRITICAL,
                threshold=1.0,  # Любое нарушение безопасности
                condition="blocked_messages > 0",
                message_template="🚨 КРИТИЧНО: Ваш ребенок отправил сообщение, заблокированное системой безопасности. Содержание: {content}",
            ),
            AlertType.HIGH_BLOCKED_RATIO: AlertRule(
                alert_type=AlertType.HIGH_BLOCKED_RATIO,
                alert_level=AlertLevel.WARNING,
                threshold=0.2,  # 20% заблокированных сообщений
                condition="blocked_ratio > 0.2",
                message_template="⚠️ ВНИМАНИЕ: У вашего ребенка высокий процент заблокированных сообщений ({ratio:.1%}) за последние 24 часа",
            ),
            AlertType.LOW_ENGAGEMENT: AlertRule(
                alert_type=AlertType.LOW_ENGAGEMENT,
                alert_level=AlertLevel.INFO,
                threshold=0.3,  # Низкая вовлеченность
                condition="engagement_score < 0.3",
                message_template="📊 ИНФО: Низкая активность вашего ребенка в PandaPal. Рекомендуем поощрить использование бота",
            ),
            AlertType.LONG_INACTIVITY: AlertRule(
                alert_type=AlertType.LONG_INACTIVITY,
                alert_level=AlertLevel.WARNING,
                threshold=72.0,  # 72 часа без активности
                condition="inactivity_hours > 72",
                message_template="⏰ ВНИМАНИЕ: Ваш ребенок не использовал PandaPal более {hours} часов",
            ),
            AlertType.SUSPICIOUS_ACTIVITY: AlertRule(
                alert_type=AlertType.SUSPICIOUS_ACTIVITY,
                alert_level=AlertLevel.CRITICAL,
                threshold=10.0,  # Более 10 подозрительных действий
                condition="suspicious_actions > 10",
                message_template="🚨 КРИТИЧНО: Обнаружена подозрительная активность вашего ребенка: {details}",
            ),
            AlertType.LEARNING_PROGRESS: AlertRule(
                alert_type=AlertType.LEARNING_PROGRESS,
                alert_level=AlertLevel.INFO,
                threshold=0.8,  # Высокий прогресс
                condition="progress_score > 0.8",
                message_template="🎉 ОТЛИЧНО: Ваш ребенок показывает отличные результаты в обучении! Прогресс: {progress}",
            ),
            AlertType.SYSTEM_ERROR: AlertRule(
                alert_type=AlertType.SYSTEM_ERROR,
                alert_level=AlertLevel.WARNING,
                threshold=5.0,  # Более 5 ошибок
                condition="error_count > 5",
                message_template="⚠️ СИСТЕМА: Обнаружены технические проблемы в PandaPal. Мы работаем над их устранением",
            ),
            AlertType.PARENTAL_CONTROL: AlertRule(
                alert_type=AlertType.PARENTAL_CONTROL,
                alert_level=AlertLevel.INFO,
                threshold=1.0,  # Любое изменение настроек
                condition="settings_changed",
                message_template="⚙️ НАСТРОЙКИ: Ваши настройки родительского контроля были обновлены",
            ),
        }

    async def check_user_alerts(self, user_id: int) -> List[AnalyticsAlert]:
        """
        Проверить алерты для конкретного пользователя

        Args:
            user_id: ID пользователя

        Returns:
            List[AnalyticsAlert]: Список новых алертов
        """
        cache_key = cache_service.generate_key("user_alerts", user_id)

        # Проверяем кэш
        cached_alerts = await cache_service.get(cache_key)
        if cached_alerts:
            return cached_alerts

        new_alerts = []

        try:
            # Получаем пользователя
            user = self.db.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                return new_alerts

            # Проверяем различные типы алертов
            for alert_type, rule in self.alert_rules.items():
                alert = await self._check_alert_rule(user, rule)
                if alert:
                    new_alerts.append(alert)

            # Сохраняем в кэш
            await cache_service.set(cache_key, new_alerts, self.cache_ttl)

            logger.info(f"🔍 Проверено алертов для пользователя {user_id}: {len(new_alerts)} новых")

        except Exception as e:
            logger.error(f"❌ Ошибка проверки алертов для пользователя {user_id}: {e}")

        return new_alerts

    async def check_all_alerts(self) -> Dict[int, List[AnalyticsAlert]]:
        """
        Проверить алерты для всех пользователей

        Returns:
            Dict[int, List[AnalyticsAlert]]: Словарь с алертами по пользователям
        """
        all_alerts = {}

        try:
            # Получаем всех активных пользователей
            active_users = self.db.query(User).filter_by(is_active=True).all()

            # Проверяем алерты для каждого пользователя
            for user in active_users:
                user_alerts = await self.check_user_alerts(user.telegram_id)
                if user_alerts:
                    all_alerts[user.telegram_id] = user_alerts

            logger.info(
                f"🔍 Проверено алертов для {len(active_users)} пользователей: {sum(len(alerts) for alerts in all_alerts.values())} новых"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка проверки алертов: {e}")

        return all_alerts

    async def _check_alert_rule(self, user: User, rule: AlertRule) -> Optional[AnalyticsAlert]:
        """
        Проверить конкретное правило алерта

        Args:
            user: Пользователь
            rule: Правило алерта

        Returns:
            Optional[AnalyticsAlert]: Новый алерт или None
        """
        try:
            # Проверяем cooldown
            if await self._is_alert_in_cooldown(user.telegram_id, rule.alert_type):
                return None

            # Проверяем условие правила
            should_alert, alert_data = await self._evaluate_condition(user, rule)

            if not should_alert:
                return None

            # Создаем алерт
            alert = await self._create_alert(user, rule, alert_data)

            if alert:
                # Сохраняем в БД
                self.db.add(alert)
                self.db.commit()

                # Обновляем cooldown
                await self._update_alert_cooldown(user.telegram_id, rule.alert_type)

                logger.info(
                    f"🚨 Создан алерт {rule.alert_type.value} для пользователя {user.telegram_id}"
                )

            return alert

        except Exception as e:
            logger.error(f"❌ Ошибка проверки правила {rule.alert_type.value}: {e}")
            return None

    async def _evaluate_condition(self, user: User, rule: AlertRule) -> Tuple[bool, Dict[str, Any]]:
        """
        Оценить условие правила алерта

        Args:
            user: Пользователь
            rule: Правило алерта

        Returns:
            Tuple[bool, Dict[str, Any]]: (должен ли сработать алерт, данные алерта)
        """
        now = datetime.utcnow()
        alert_data = {}

        if rule.alert_type == AlertType.SAFETY_VIOLATION:
            # Проверяем заблокированные сообщения за последние 24 часа
            start_time = now - timedelta(hours=24)
            blocked_count = (
                self.db.query(func.count())
                .select_from(
                    self.db.query().filter(
                        and_(
                            # Здесь должен быть запрос к таблице заблокированных сообщений
                            # Пока используем заглушку
                        )
                    )
                )
                .scalar()
                or 0
            )

            should_alert = blocked_count > 0
            alert_data = {"blocked_count": blocked_count}

        elif rule.alert_type == AlertType.HIGH_BLOCKED_RATIO:
            # Проверяем соотношение заблокированных сообщений
            start_time = now - timedelta(hours=24)
            # Здесь должен быть реальный запрос к БД
            total_messages = 100  # Заглушка
            blocked_messages = 25  # Заглушка

            blocked_ratio = blocked_messages / total_messages if total_messages > 0 else 0
            should_alert = blocked_ratio > rule.threshold
            alert_data = {"blocked_ratio": blocked_ratio, "total_messages": total_messages}

        elif rule.alert_type == AlertType.LOW_ENGAGEMENT:
            # Проверяем индекс вовлеченности
            engagement_score = 0.25  # Заглушка - должно браться из аналитики
            should_alert = engagement_score < rule.threshold
            alert_data = {"engagement_score": engagement_score}

        elif rule.alert_type == AlertType.LONG_INACTIVITY:
            # Проверяем время последней активности
            last_activity = user.last_activity or user.created_at
            inactivity_hours = (now - last_activity).total_seconds() / 3600
            should_alert = inactivity_hours > rule.threshold
            alert_data = {"inactivity_hours": inactivity_hours}

        elif rule.alert_type == AlertType.SUSPICIOUS_ACTIVITY:
            # Проверяем подозрительную активность
            suspicious_actions = 0  # Заглушка
            should_alert = suspicious_actions > rule.threshold
            alert_data = {"suspicious_actions": suspicious_actions}

        elif rule.alert_type == AlertType.LEARNING_PROGRESS:
            # Проверяем прогресс обучения
            progress_score = 0.85  # Заглушка
            should_alert = progress_score > rule.threshold
            alert_data = {"progress_score": progress_score}

        elif rule.alert_type == AlertType.SYSTEM_ERROR:
            # Проверяем системные ошибки
            error_count = 0  # Заглушка
            should_alert = error_count > rule.threshold
            alert_data = {"error_count": error_count}

        elif rule.alert_type == AlertType.PARENTAL_CONTROL:
            # Проверяем изменения в настройках родительского контроля
            settings_changed = False  # Заглушка
            should_alert = settings_changed
            alert_data = {"settings_changed": settings_changed}

        else:
            should_alert = False
            alert_data = {}

        return should_alert, alert_data

    async def _create_alert(
        self, user: User, rule: AlertRule, alert_data: Dict[str, Any]
    ) -> Optional[AnalyticsAlert]:
        """
        Создать новый алерт

        Args:
            user: Пользователь
            rule: Правило алерта
            alert_data: Данные алерта

        Returns:
            Optional[AnalyticsAlert]: Новый алерт
        """
        try:
            # Формируем сообщение
            message = rule.message_template.format(**alert_data)

            # Определяем получателя уведомления
            parent_id = None
            child_id = None

            if user.user_type == "child":
                child_id = user.telegram_id
                parent_id = user.parent_telegram_id
            elif user.user_type == "parent":
                parent_id = user.telegram_id

            # Создаем алерт
            alert = AnalyticsAlert(
                alert_type=rule.alert_type.value,
                alert_level=rule.alert_level.value,
                alert_message=message,
                alert_data=alert_data,
                parent_telegram_id=parent_id,
                child_telegram_id=child_id,
                is_sent=False,
            )

            return alert

        except Exception as e:
            logger.error(f"❌ Ошибка создания алерта: {e}")
            return None

    async def send_alert_notification(self, alert: AnalyticsAlert) -> bool:
        """
        Отправить уведомление об алерте

        Args:
            alert: Алерт для отправки

        Returns:
            bool: True если уведомление отправлено
        """
        try:
            if not alert.parent_telegram_id:
                logger.warning(f"⚠️ Нет родителя для отправки алерта {alert.id}")
                return False

            # Здесь должна быть интеграция с Telegram API для отправки сообщения
            # Пока просто логируем

            logger.info(
                f"📤 Отправка уведомления родителю {alert.parent_telegram_id}: {alert.alert_message}"
            )

            # Отмечаем как отправленное
            alert.is_sent = True
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления об алерте {alert.id}: {e}")
            return False

    async def resolve_alert(self, alert_id: int, resolved_by: str) -> bool:
        """
        Разрешить алерт

        Args:
            alert_id: ID алерта
            resolved_by: Кто разрешил алерт

        Returns:
            bool: True если алерт разрешен
        """
        try:
            alert = self.db.query(AnalyticsAlert).filter_by(id=alert_id).first()
            if not alert:
                return False

            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            self.db.commit()

            logger.info(f"✅ Алерт {alert_id} разрешен пользователем {resolved_by}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка разрешения алерта {alert_id}: {e}")
            return False

    async def get_active_alerts(self, parent_id: Optional[int] = None) -> List[AnalyticsAlert]:
        """
        Получить активные алерты

        Args:
            parent_id: ID родителя (опционально)

        Returns:
            List[AnalyticsAlert]: Список активных алертов
        """
        try:
            query = self.db.query(AnalyticsAlert).filter(AnalyticsAlert.resolved_at.is_(None))

            if parent_id:
                query = query.filter_by(parent_telegram_id=parent_id)

            alerts = query.order_by(AnalyticsAlert.triggered_at.desc()).all()
            return alerts

        except Exception as e:
            logger.error(f"❌ Ошибка получения активных алертов: {e}")
            return []

    async def get_alert_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Получить статистику алертов

        Args:
            days: Количество дней для анализа

        Returns:
            Dict[str, Any]: Статистика алертов
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Общая статистика
            total_alerts = (
                self.db.query(func.count(AnalyticsAlert.id))
                .filter(AnalyticsAlert.triggered_at >= start_date)
                .scalar()
            )

            resolved_alerts = (
                self.db.query(func.count(AnalyticsAlert.id))
                .filter(
                    and_(
                        AnalyticsAlert.triggered_at >= start_date,
                        AnalyticsAlert.resolved_at.isnot(None),
                    )
                )
                .scalar()
            )

            # Статистика по типам
            alerts_by_type = (
                self.db.query(AnalyticsAlert.alert_type, func.count(AnalyticsAlert.id))
                .filter(AnalyticsAlert.triggered_at >= start_date)
                .group_by(AnalyticsAlert.alert_type)
                .all()
            )

            # Статистика по уровням
            alerts_by_level = (
                self.db.query(AnalyticsAlert.alert_level, func.count(AnalyticsAlert.id))
                .filter(AnalyticsAlert.triggered_at >= start_date)
                .group_by(AnalyticsAlert.alert_level)
                .all()
            )

            return {
                "total_alerts": total_alerts,
                "resolved_alerts": resolved_alerts,
                "unresolved_alerts": total_alerts - resolved_alerts,
                "resolution_rate": (
                    (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0
                ),
                "alerts_by_type": dict(alerts_by_type),
                "alerts_by_level": dict(alerts_by_level),
                "period_days": days,
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики алертов: {e}")
            return {}

    async def _is_alert_in_cooldown(self, user_id: int, alert_type: AlertType) -> bool:
        """
        Проверить, находится ли алерт в cooldown

        Args:
            user_id: ID пользователя
            alert_type: Тип алерта

        Returns:
            bool: True если в cooldown
        """
        try:
            rule = self.alert_rules.get(alert_type)
            if not rule:
                return False

            cooldown_time = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)

            recent_alert = (
                self.db.query(AnalyticsAlert)
                .filter(
                    and_(
                        or_(
                            AnalyticsAlert.parent_telegram_id == user_id,
                            AnalyticsAlert.child_telegram_id == user_id,
                        ),
                        AnalyticsAlert.alert_type == alert_type.value,
                        AnalyticsAlert.triggered_at >= cooldown_time,
                    )
                )
                .first()
            )

            return recent_alert is not None

        except Exception as e:
            logger.error(f"❌ Ошибка проверки cooldown: {e}")
            return False

    async def _update_alert_cooldown(self, user_id: int, alert_type: AlertType):
        """
        Обновить cooldown для алерта

        Args:
            user_id: ID пользователя
            alert_type: Тип алерта
        """
        try:
            # Cooldown обновляется автоматически при создании нового алерта
            # Здесь можно добавить дополнительную логику если нужно
            pass

        except Exception as e:
            logger.error(f"❌ Ошибка обновления cooldown: {e}")

    async def cleanup_old_alerts(self, days: int = 90):
        """
        Очистка старых алертов

        Args:
            days: Количество дней для хранения
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted_count = (
                self.db.query(AnalyticsAlert)
                .filter(
                    and_(
                        AnalyticsAlert.triggered_at < cutoff_date,
                        AnalyticsAlert.resolved_at.isnot(None),
                    )
                )
                .delete()
            )

            self.db.commit()

            logger.info(f"🧹 Удалено {deleted_count} старых алертов")

        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых алертов: {e}")
