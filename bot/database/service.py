"""
DatabaseService — сервис для проверки подключения и получения сессий.
"""

import warnings
from contextlib import suppress

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from bot.config import settings
from bot.database.engine import SessionLocal, engine


class DatabaseService:
    """Сервис для работы с базой данных."""

    @staticmethod
    def get_db_session() -> Session:
        """
        Получить новую сессию БД.

        Deprecated: используйте get_db() context manager.
        """
        warnings.warn(
            "DatabaseService.get_db_session() устарел. "
            "Используйте get_db() context manager для безопасной работы с БД.",
            DeprecationWarning,
            stacklevel=2,
        )
        return SessionLocal()

    @staticmethod
    def check_connection() -> bool:
        """Проверка подключения к базе данных."""
        # Логируем URL для диагностики (без пароля)
        db_url_clean = "***:***@***"

        with suppress(Exception):
            db_url_clean = settings.database_url.replace(
                settings.database_url.split("@")[0].split("//")[1], "***:***"
            )

        try:
            logger.info(f"🔍 Подключение к БД: {db_url_clean}")

            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info(f"✅ Тест запроса успешен: {result.fetchone()}")
            logger.info("✅ Подключение к БД активно")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            logger.error(f"❌ URL БД (без пароля): {db_url_clean}")
            return False
