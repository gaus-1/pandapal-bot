#!/usr/bin/env python3
"""
Скрипт для проверки и применения миграции payment_method.

Проверяет наличие полей payment_method и payment_id в таблице subscriptions.
Если полей нет - применяет миграцию.
"""

import os
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from sqlalchemy import inspect, text

from bot.database import engine


def check_payment_fields():
    """Проверяет наличие полей payment_method и payment_id."""
    try:
        inspector = inspect(engine)

        # Проверяем что таблица subscriptions существует
        tables = inspector.get_table_names()
        if "subscriptions" not in tables:
            logger.error("❌ Таблица subscriptions не найдена!")
            return False

        # Получаем колонки таблицы subscriptions
        columns = [col["name"] for col in inspector.get_columns("subscriptions")]

        has_payment_method = "payment_method" in columns
        has_payment_id = "payment_id" in columns

        logger.info(f"📊 Колонки в subscriptions: {', '.join(columns)}")

        if has_payment_method and has_payment_id:
            logger.info("✅ Поля payment_method и payment_id уже существуют")
            return True
        else:
            logger.warning("⚠️ Поля payment_method или payment_id отсутствуют!")
            logger.warning(f"   payment_method: {'✅' if has_payment_method else '❌'}")
            logger.warning(f"   payment_id: {'✅' if has_payment_id else '❌'}")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка проверки: {e}")
        return False


def apply_migration():
    """Применяет миграцию для добавления полей payment_method и payment_id."""
    try:
        with engine.connect() as conn:
            # Проверяем что поля не существуют
            inspector = inspect(engine)
            columns = [col["name"] for col in inspector.get_columns("subscriptions")]

            if "payment_method" not in columns:
                logger.info("➕ Добавляем поле payment_method...")
                conn.execute(
                    text(
                        """
                    ALTER TABLE subscriptions
                    ADD COLUMN payment_method VARCHAR(20);
                """
                    )
                )
                conn.commit()
                logger.info("✅ Поле payment_method добавлено")

            if "payment_id" not in columns:
                logger.info("➕ Добавляем поле payment_id...")
                conn.execute(
                    text(
                        """
                    ALTER TABLE subscriptions
                    ADD COLUMN payment_id VARCHAR(255);
                """
                    )
                )
                conn.commit()
                logger.info("✅ Поле payment_id добавлено")

            # Добавляем индекс
            logger.info("➕ Создаем индекс на payment_id...")
            try:
                conn.execute(
                    text(
                        """
                    CREATE INDEX IF NOT EXISTS idx_subscriptions_payment_id
                    ON subscriptions(payment_id);
                """
                    )
                )
                conn.commit()
                logger.info("✅ Индекс создан")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("ℹ️ Индекс уже существует")
                else:
                    raise

            # Добавляем constraint
            logger.info("➕ Добавляем constraint для payment_method...")
            try:
                conn.execute(
                    text(
                        """
                    ALTER TABLE subscriptions
                    ADD CONSTRAINT ck_subscriptions_payment_method
                    CHECK (payment_method IS NULL OR payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other'));
                """
                    )
                )
                conn.commit()
                logger.info("✅ Constraint добавлен")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.info("ℹ️ Constraint уже существует")
                else:
                    raise

            logger.info("✅ Миграция применена успешно!")
            return True

    except Exception as e:
        logger.error(f"❌ Ошибка применения миграции: {e}")
        return False


if __name__ == "__main__":
    logger.info("🔍 Проверка миграции payment_method...")

    if check_payment_fields():
        logger.info("✅ Все поля на месте, миграция не требуется")
        sys.exit(0)
    else:
        logger.info("🔧 Применяем миграцию...")
        if apply_migration():
            logger.info("✅ Миграция применена успешно!")
            sys.exit(0)
        else:
            logger.error("❌ Не удалось применить миграцию")
            sys.exit(1)
