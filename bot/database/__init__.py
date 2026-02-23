"""
Управление подключением к базе данных PostgreSQL.

Предоставляет подключения, управление сессиями, инициализацию таблиц
и проверку здоровья БД.

Пакет разделён на модули по ответственности:
- engine — движок, пул, фабрика сессий, get_db(), init_db()
- alembic_utils — настройка и применение Alembic-миграций
- sql_migrations — SQL-миграции (premium, payments)
- service — DatabaseService (проверка подключения)
"""

import os

from loguru import logger

# Re-export: обратная совместимость с `from bot.database import ...`
from bot.database.engine import SessionLocal, engine, get_db, init_db  # noqa: F401
from bot.database.service import DatabaseService  # noqa: F401
from bot.models import Base  # noqa: F401

__all__ = [
    "Base",
    "DatabaseService",
    "SessionLocal",
    "engine",
    "get_db",
    "init_database",
    "init_db",
]


async def init_database() -> None:
    """Инициализация базы данных с проверкой подключения и миграциями."""
    from bot.database.alembic_utils import (
        _apply_alembic_migration_for_existing_tables,
        _apply_alembic_migration_for_new_tables,
        _get_current_revision,
        _setup_alembic_config,
    )
    from bot.database.sql_migrations import (
        _apply_fallback_sql_migration,
        _apply_payment_migration,
        _apply_payments_table_migration,
        _apply_premium_migration,
        _check_payment_migration_needed,
        _check_premium_migration_needed,
    )

    try:
        if DatabaseService.check_connection():
            logger.info("✅ База данных подключена и готова к работе")
        else:
            logger.warning("⚠️ Проблема с подключением к базе данных")

        auto_migrate = os.getenv("AUTO_MIGRATE", "false").lower() == "true"
        if not auto_migrate:
            return

        migration_applied = False
        try:
            alembic_cfg = _setup_alembic_config()
            from sqlalchemy import inspect

            inspector = inspect(engine)
            tables = inspector.get_table_names()

            if "users" in tables and "chat_history" in tables:
                logger.info("📊 Таблицы уже существуют, проверяем только новые миграции...")
                current_revision = _get_current_revision(tables)
                migration_applied = _apply_alembic_migration_for_existing_tables(
                    alembic_cfg, current_revision
                )
            else:
                migration_applied = _apply_alembic_migration_for_new_tables(alembic_cfg)

            if _check_premium_migration_needed(inspector, tables):
                migration_applied = _apply_premium_migration()
            elif not migration_applied:
                import logging

                from alembic import command

                for _name in ("alembic.runtime.migration", "alembic.runtime.migrations"):
                    logging.getLogger(_name).setLevel(logging.WARNING)
                logger.info("🔄 Применение миграций Alembic...")
                try:
                    command.upgrade(alembic_cfg, "head")
                    logger.info("✅ Миграции Alembic применены успешно")
                    migration_applied = True
                except Exception as alembic_err:
                    logger.warning(f"⚠️ Alembic миграция не удалась: {alembic_err}")

            needs_payment_migration, columns = _check_payment_migration_needed(inspector, tables)
            if needs_payment_migration:
                _apply_payment_migration(columns)

            if "payments" not in tables:
                logger.info("📋 Обнаружено: таблица payments отсутствует")
                _apply_payments_table_migration()

        except Exception as e:
            logger.warning(f"⚠️ Ошибка при проверке миграций: {e}")
            migration_applied = _apply_fallback_sql_migration()

        if not migration_applied:
            logger.warning("⚠️ Миграции не применены. Примените вручную: alembic upgrade head")
    except Exception as e:
        logger.error("❌ Ошибка инициализации БД: %s", str(e))
        raise
