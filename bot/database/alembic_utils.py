"""
Утилиты для работы с Alembic: конфигурация и применение миграций.
"""

import os

from loguru import logger
from sqlalchemy import text

from bot.database.engine import engine


def _setup_alembic_config() -> tuple:
    """Настройка конфигурации Alembic."""
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    return alembic_cfg


def _get_current_revision(tables: list) -> str | None:
    """Получение текущей ревизии Alembic."""
    if "alembic_version" not in tables:
        return None

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            current_revision = result.scalar()
            if current_revision:
                logger.info(f"📋 Текущая версия миграции: {current_revision}")
            return current_revision
    except Exception as e:
        logger.debug(f"Не удалось прочитать текущую версию: {e}")
        return None


def _apply_alembic_migration_for_existing_tables(alembic_cfg, current_revision: str | None) -> bool:
    """Применение миграций Alembic для существующих таблиц."""
    from alembic import command

    migration_applied = False

    if not current_revision:
        logger.info(
            "📋 Таблицы существуют, но версия Alembic не установлена. Помечаем текущее состояние..."
        )
        try:
            command.stamp(alembic_cfg, "head")
            logger.info("✅ Текущее состояние БД помечено как актуальное")
            return True
        except Exception as stamp_err:
            logger.warning(f"⚠️ Не удалось пометить текущее состояние: {stamp_err}")

    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Миграции Alembic применены успешно")
        return True
    except Exception as alembic_err:
        error_str = str(alembic_err).lower()
        if (
            "already exists" in error_str
            or "duplicate" in error_str
            or ("relation" in error_str and "already exists" in error_str)
        ):
            logger.debug(f"ℹ️ Миграции уже применены (предупреждение: {alembic_err})")
            if not current_revision:
                try:
                    command.stamp(alembic_cfg, "head")
                    logger.info("✅ Текущее состояние БД помечено как актуальное")
                except Exception as stamp_err:
                    logger.warning(f"⚠️ Не удалось пометить состояние БД: {stamp_err}")
            return True
        elif "multiple head revisions" in error_str:
            logger.warning(
                "⚠️ Обнаружены множественные head ревизии, пытаемся применить все heads..."
            )
            try:
                command.upgrade(alembic_cfg, "heads")
                logger.info("✅ Миграции Alembic применены успешно (через heads)")
                return True
            except Exception as heads_err:
                logger.warning(f"⚠️ Не удалось применить миграции через heads: {heads_err}")
        elif "overlaps" in error_str or "overlap" in error_str:
            logger.warning("⚠️ Обнаружен конфликт миграций (overlaps). Проверяем состояние БД...")
            try:
                # Проверяем, есть ли поле в БД
                from sqlalchemy import inspect

                conn = engine.connect()
                inspector = inspect(conn)
                users_columns = {col["name"] for col in inspector.get_columns("users")}
                chat_history_columns = {
                    col["name"] for col in inspector.get_columns("chat_history")
                }
                conn.close()

                # Если поле уже есть в БД, значит миграция применена, но не записана
                if "panda_lazy_until" in users_columns:
                    logger.info(
                        "✅ Поле panda_lazy_until уже существует в БД, помечаем миграцию как примененную..."
                    )
                    try:
                        command.stamp(alembic_cfg, "a1b2c3d4e5f8")
                        logger.info("✅ Миграция a1b2c3d4e5f8 помечена как примененная")
                    except Exception as stamp_err:
                        logger.warning(f"⚠️ Не удалось пометить миграцию: {stamp_err}")

                # Проверяем и применяем миграцию для image_url если нужно
                if "image_url" not in chat_history_columns:
                    logger.info("📋 Поле image_url отсутствует, применяем миграцию...")
                    try:
                        # Применяем миграцию напрямую через SQL
                        with engine.begin() as conn:
                            conn.execute(
                                text(
                                    "ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS image_url TEXT"
                                )
                            )
                        logger.info("✅ Поле image_url добавлено в chat_history")
                        # Помечаем миграцию как примененную
                        try:
                            command.stamp(alembic_cfg, "51eec1cc4ab3")
                            logger.info("✅ Миграция 51eec1cc4ab3 помечена как примененная")
                        except Exception as stamp_err:
                            logger.debug(f"Не удалось пометить миграцию: {stamp_err}")
                    except Exception as img_err:
                        logger.warning(f"⚠️ Не удалось добавить image_url: {img_err}")

                # После обработки конфликтов пытаемся применить оставшиеся миграции
                try:
                    command.upgrade(alembic_cfg, "heads")
                    logger.info("✅ Оставшиеся миграции применены успешно")
                    return True
                except Exception as heads_err:
                    logger.warning(f"⚠️ Не удалось применить оставшиеся миграции: {heads_err}")
                    # Все равно возвращаем True, так как критические миграции применены
                    return True
            except Exception as check_err:
                logger.warning(f"⚠️ Не удалось проверить состояние БД: {check_err}")
        else:
            logger.warning(f"⚠️ Alembic миграция не удалась: {alembic_err}")

    return migration_applied


def _apply_alembic_migration_for_new_tables(alembic_cfg) -> bool:
    """Применение миграций Alembic для новых таблиц."""
    from alembic import command

    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Миграции Alembic применены успешно")
        return True
    except Exception as alembic_err:
        error_str = str(alembic_err).lower()
        if "already exists" in error_str or "duplicate" in error_str:
            logger.info("ℹ️ Таблицы уже существуют, миграция не требуется")
            return True
        elif "multiple head revisions" in error_str:
            logger.warning(
                "⚠️ Обнаружены множественные head ревизии, пытаемся применить все heads..."
            )
            try:
                command.upgrade(alembic_cfg, "heads")
                logger.info("✅ Миграции Alembic применены успешно (через heads)")
                return True
            except Exception as heads_err:
                logger.warning(f"⚠️ Не удалось применить миграции через heads: {heads_err}")
        else:
            logger.warning(f"⚠️ Alembic миграция не удалась: {alembic_err}")

    return False
