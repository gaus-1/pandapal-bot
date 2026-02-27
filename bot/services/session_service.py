"""
Сервис управления сессиями с поддержкой Redis.

Поддерживает:
- Redis (Upstash, Redis Cloud) для production
- In-memory fallback для разработки
- Автоматическое TTL для сессий
- Миграция между хранилищами
"""

import json
import secrets
from datetime import UTC, datetime, timedelta

from loguru import logger

from bot.config import settings

# Константы
SESSION_TTL_DAYS = 30  # Время жизни сессии в днях
AUTH_EXPIRY_HOURS = 24  # Время действия авторизации Telegram

# Попытка импорта Redis
try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️ redis package не установлен, используется in-memory хранилище")


class SessionData:
    """Структура данных сессии."""

    def __init__(
        self,
        telegram_id: int,
        user_data: dict,
        expires_at: datetime,
    ):
        """
        Инициализация данных сессии.

        Args:
            telegram_id: ID пользователя в Telegram
            user_data: Данные пользователя
            expires_at: Дата истечения сессии
        """
        self.telegram_id = telegram_id
        self.user_data = user_data
        self.expires_at = expires_at

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "telegram_id": self.telegram_id,
            "user_data": self.user_data,
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        """Десериализация из словаря."""
        return cls(
            telegram_id=data["telegram_id"],
            user_data=data["user_data"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )


class SessionService:
    """
    Универсальный сервис управления сессиями.

    Автоматически выбирает между Redis и in-memory хранилищем.
    """

    def __init__(self):
        """
        Инициализация сервиса сессий.

        Автоматически подключается к Redis если доступен,
        иначе использует in-memory хранилище.
        """
        logger.info("🔄 Инициализация SessionService...")

        self._redis_client: aioredis.Redis | None = None
        self._use_redis = False
        self._memory_sessions: dict[str, SessionData] = {}

        # Конфигурация
        self.session_ttl_days = SESSION_TTL_DAYS
        self.redis_key_prefix = "session:"

        # Диагностика
        logger.info(f"📋 REDIS_AVAILABLE: {REDIS_AVAILABLE}")
        logger.info(
            f"📋 settings.redis_url: {'настроен' if hasattr(settings, 'redis_url') and settings.redis_url else 'не настроен'}"
        )

        # Подключение к Redis
        if REDIS_AVAILABLE and hasattr(settings, "redis_url") and settings.redis_url:
            logger.info("🔄 Попытка подключения к Redis...")
            self._init_redis()
        else:
            reasons = []
            if not REDIS_AVAILABLE:
                reasons.append("redis пакет не установлен")
            if not hasattr(settings, "redis_url"):
                reasons.append("redis_url отсутствует в settings")
            elif not settings.redis_url:
                reasons.append("REDIS_URL не задан в переменных окружения")

            logger.warning(
                f"🔧 Сессии хранятся в памяти (Redis не настроен: {', '.join(reasons)}). "
                "Добавьте REDIS_URL в переменные окружения для персистентности."
            )

    def _init_redis(self):
        """Инициализация подключения к Redis."""
        try:
            redis_url = settings.redis_url

            # Проверка формата URL
            if not redis_url.startswith(("rediss://", "redis://")):
                raise ValueError(
                    f"REDIS_URL должен начинаться с rediss:// или redis://. "
                    f"Получено: {redis_url[:30]}..."
                )

            # Для Upstash проверяем наличие default: в URL
            if "upstash.io" in redis_url and "default:" not in redis_url:
                logger.warning(
                    "⚠️ Upstash URL должен содержать 'default:' в формате: "
                    "rediss://default:TOKEN@host:6379"
                )

            # Маскируем токен в логах
            url_for_log = redis_url
            if "@" in redis_url:
                parts = redis_url.split("@")
                if ":" in parts[0]:
                    protocol_user = parts[0].split("://")[1] if "://" in parts[0] else parts[0]
                    if ":" in protocol_user:
                        user, token = protocol_user.split(":", 1)
                        masked_token = token[:8] + "..." if len(token) > 8 else "***"
                        url_for_log = redis_url.replace(token, masked_token)

            logger.info(f"🔄 Подключение к Redis: {url_for_log[:60]}...")

            self._redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=10,
            )

            self._use_redis = True
            logger.info("✅ Redis клиент создан (подключение произойдет при первом запросе)")
            logger.info(f"📊 Сессии будут храниться в Redis с TTL={self.session_ttl_days} дней")

        except Exception as e:
            logger.error(f"❌ Ошибка создания Redis клиента: {e}", exc_info=True)
            logger.warning("⚠️ Fallback на in-memory хранилище сессий")
            self._redis_client = None
            self._use_redis = False

    async def create_session(self, telegram_id: int, user_data: dict) -> str:
        """
        Создать новую сессию для пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            user_data: Данные пользователя (dict)

        Returns:
            str: Session token
        """
        # Генерируем безопасный токен
        session_token = secrets.token_urlsafe(32)

        # Создаём данные сессии
        expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=self.session_ttl_days)
        session_data = SessionData(
            telegram_id=telegram_id, user_data=user_data, expires_at=expires_at
        )

        # Сохраняем в хранилище
        if self._use_redis and self._redis_client:
            await self._save_to_redis(session_token, session_data)
        else:
            self._save_to_memory(session_token, session_data)

        logger.info(f"✅ Создана сессия для пользователя {telegram_id}")

        return session_token

    async def get_session(self, session_token: str) -> SessionData | None:
        """
        Получить данные сессии по токену.

        Args:
            session_token: Токен сессии

        Returns:
            SessionData или None если не найдена/истекла
        """
        if self._use_redis and self._redis_client:
            return await self._get_from_redis(session_token)
        else:
            return self._get_from_memory(session_token)

    async def delete_session(self, session_token: str) -> bool:
        """
        Удалить сессию (logout).

        Args:
            session_token: Токен сессии

        Returns:
            bool: True если удалено успешно
        """
        if self._use_redis and self._redis_client:
            return await self._delete_from_redis(session_token)
        else:
            return self._delete_from_memory(session_token)

    async def refresh_session(self, session_token: str) -> bool:
        """
        Обновить TTL сессии (продлить на 30 дней).

        Args:
            session_token: Токен сессии

        Returns:
            bool: True если обновлено успешно
        """
        session = await self.get_session(session_token)
        if not session:
            return False

        # Обновляем expires_at
        session.expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
            days=self.session_ttl_days
        )

        # Сохраняем обратно
        if self._use_redis and self._redis_client:
            await self._save_to_redis(session_token, session)
        else:
            self._save_to_memory(session_token, session)

        logger.debug(f"🔄 Сессия продлена на {self.session_ttl_days} дней")
        return True

    # Redis методы

    async def _save_to_redis(self, token: str, session_data: SessionData):
        """Сохранить сессию в Redis."""
        try:
            key = f"{self.redis_key_prefix}{token}"
            value = json.dumps(session_data.to_dict())
            ttl_seconds = self.session_ttl_days * 24 * 3600

            await self._redis_client.setex(name=key, time=ttl_seconds, value=value)

            logger.debug(f"💾 Сессия сохранена в Redis: {key}")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сессии в Redis: {e}")
            # Fallback на memory
            self._save_to_memory(token, session_data)

    async def _get_from_redis(self, token: str) -> SessionData | None:
        """Получить сессию из Redis."""
        try:
            key = f"{self.redis_key_prefix}{token}"
            value = await self._redis_client.get(key)

            if not value:
                return None

            data = json.loads(value)
            session = SessionData.from_dict(data)

            # Проверяем срок действия
            if datetime.now(UTC).replace(tzinfo=None) > session.expires_at:
                await self._delete_from_redis(token)
                return None

            return session

        except Exception as e:
            logger.error(f"❌ Ошибка получения сессии из Redis: {e}")
            return None

    async def _delete_from_redis(self, token: str) -> bool:
        """Удалить сессию из Redis."""
        try:
            key = f"{self.redis_key_prefix}{token}"
            result = await self._redis_client.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"❌ Ошибка удаления сессии из Redis: {e}")
            return False

    # In-memory методы

    def _save_to_memory(self, token: str, session_data: SessionData):
        """Сохранить сессию в память."""
        self._memory_sessions[token] = session_data
        logger.debug(f"💾 Сессия сохранена в память: {token[:10]}...")

        # Очищаем старые сессии
        self._cleanup_memory()

    def _get_from_memory(self, token: str) -> SessionData | None:
        """Получить сессию из памяти."""
        session = self._memory_sessions.get(token)

        if not session:
            return None

        # Проверяем срок действия
        if datetime.now(UTC).replace(tzinfo=None) > session.expires_at:
            self._delete_from_memory(token)
            return None

        return session

    def _delete_from_memory(self, token: str) -> bool:
        """Удалить сессию из памяти."""
        if token in self._memory_sessions:
            del self._memory_sessions[token]
            return True
        return False

    def _cleanup_memory(self):
        """Очистка истекших сессий из памяти."""
        now = datetime.now(UTC).replace(tzinfo=None)
        expired_tokens = [
            token for token, session in self._memory_sessions.items() if now > session.expires_at
        ]

        for token in expired_tokens:
            del self._memory_sessions[token]

        if expired_tokens:
            logger.debug(f"🧹 Очищено {len(expired_tokens)} истёкших сессий из памяти")

    # Статистика

    async def get_stats(self) -> dict:
        """Получить статистику по сессиям."""
        if self._use_redis and self._redis_client:
            try:
                keys = await self._redis_client.keys(f"{self.redis_key_prefix}*")
                return {
                    "storage": "redis",
                    "total_sessions": len(keys),
                    "redis_connected": True,
                }
            except Exception as e:
                logger.error(f"❌ Ошибка получения статистики из Redis: {e}")
                return {"storage": "redis", "error": str(e), "redis_connected": False}
        else:
            # Очищаем перед подсчетом
            self._cleanup_memory()
            return {
                "storage": "memory",
                "total_sessions": len(self._memory_sessions),
                "redis_connected": False,
            }

    async def close(self):
        """Закрыть соединения (cleanup)."""
        if self._redis_client:
            try:
                await self._redis_client.close()
                logger.info("👋 Redis соединение закрыто")
            except Exception as e:
                logger.error(f"❌ Ошибка закрытия Redis: {e}")


# Глобальный экземпляр сервиса сессий
_session_service: SessionService | None = None


def get_session_service() -> SessionService:
    """
    Получить глобальный экземпляр сервиса сессий.

    Returns:
        SessionService: Singleton экземпляр
    """
    global _session_service

    if _session_service is None:
        _session_service = SessionService()

    return _session_service
