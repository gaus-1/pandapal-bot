"""
SQL-миграции: premium, payment, payments table.

Применяются как fallback, когда Alembic не может обработать изменения.
"""

from loguru import logger
from sqlalchemy import text

from bot.database.engine import engine


def _check_premium_migration_needed(inspector, tables: list) -> bool:
    """Проверка необходимости миграции premium."""
    if "users" in tables:
        columns = [col["name"] for col in inspector.get_columns("users")]
        if "premium_until" not in columns:
            logger.info("📋 Обнаружено: колонка premium_until отсутствует")
            return True

    if "subscriptions" not in tables:
        logger.info("📋 Обнаружено: таблица subscriptions отсутствует")
        return True

    return False


def _apply_premium_migration() -> bool:
    """Применение миграции premium."""
    logger.info("🔄 Применение миграции premium через SQL...")
    try:
        # 1. Добавляем колонку premium_until
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS premium_until TIMESTAMP WITH TIME ZONE"
                    )
                )
            logger.info("✅ Колонка premium_until добавлена")
        except Exception as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"⚠️ Ошибка добавления колонки: {e}")

        # 2. Создаем таблицу subscriptions
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS subscriptions (
                            id SERIAL PRIMARY KEY,
                            user_telegram_id BIGINT NOT NULL,
                            plan_id VARCHAR(20) NOT NULL,
                            starts_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            is_active BOOLEAN NOT NULL DEFAULT true,
                            transaction_id VARCHAR(255),
                            invoice_payload VARCHAR(255),
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT fk_subscriptions_user
                                FOREIGN KEY (user_telegram_id)
                                REFERENCES users(telegram_id)
                                ON DELETE CASCADE,
                            CONSTRAINT ck_subscriptions_plan_id
                                CHECK (plan_id IN ('month', 'year'))
                        )
                        """
                    )
                )
            logger.info("✅ Таблица subscriptions создана")
        except Exception as e:
            if "already exists" not in str(e).lower():
                logger.warning(f"⚠️ Ошибка создания таблицы: {e}")

        # 3. Создаем индексы
        indexes = [
            (
                "idx_subscriptions_user_active",
                "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_active ON subscriptions(user_telegram_id, is_active)",
            ),
            (
                "idx_subscriptions_expires",
                "CREATE INDEX IF NOT EXISTS idx_subscriptions_expires ON subscriptions(expires_at)",
            ),
        ]
        for idx_name, idx_sql in indexes:
            try:
                with engine.begin() as conn:
                    conn.execute(text(idx_sql))
                logger.info(f"✅ Индекс {idx_name} создан")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"⚠️ Ошибка создания индекса {idx_name}: {e}")

        logger.info("✅ SQL миграция premium применена успешно")
        return True
    except Exception as sql_err:
        logger.error(f"❌ Не удалось применить SQL миграцию: {sql_err}")
        return False


def _check_payment_migration_needed(inspector, tables: list) -> tuple[bool, list]:
    """Проверка необходимости миграции payment_method."""
    if "subscriptions" not in tables:
        return False, []

    columns = [col["name"] for col in inspector.get_columns("subscriptions")]
    if "payment_method" not in columns or "payment_id" not in columns:
        logger.info("📋 Обнаружено: колонки payment_method или payment_id отсутствуют")
        return True, columns

    return False, columns


def _apply_payment_migration(columns: list) -> None:
    """Применение миграции payment_method."""
    logger.info("🔄 Применение миграции payment_method через SQL...")
    try:
        with engine.begin() as conn:
            if "payment_method" not in columns:
                conn.execute(
                    text(
                        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20)"
                    )
                )
                logger.info("✅ Колонка payment_method добавлена")

            if "payment_id" not in columns:
                conn.execute(
                    text(
                        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS payment_id VARCHAR(255)"
                    )
                )
                logger.info("✅ Колонка payment_id добавлена")

            try:
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_subscriptions_payment_id ON subscriptions(payment_id)"
                    )
                )
                logger.info("✅ Индекс idx_subscriptions_payment_id создан")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"⚠️ Ошибка создания индекса: {e}")

            try:
                conn.execute(
                    text(
                        """
                        ALTER TABLE subscriptions
                        ADD CONSTRAINT ck_subscriptions_payment_method
                        CHECK (payment_method IS NULL OR payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other'))
                        """
                    )
                )
                logger.info("✅ Constraint ck_subscriptions_payment_method добавлен")
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    logger.warning(f"⚠️ Ошибка создания constraint: {e}")

        logger.info("✅ Миграция payment_method применена")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка применения миграции payment_method: {e}")


def _apply_payments_table_migration() -> None:
    """Применение миграции таблицы payments."""
    logger.info("🔄 Применение миграции payments через SQL...")
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS payments (
                        id SERIAL PRIMARY KEY,
                        payment_id VARCHAR(255) NOT NULL UNIQUE,
                        user_telegram_id BIGINT NOT NULL,
                        subscription_id INTEGER,
                        payment_method VARCHAR(20) NOT NULL,
                        plan_id VARCHAR(20) NOT NULL,
                        amount FLOAT NOT NULL,
                        currency VARCHAR(10) NOT NULL DEFAULT 'RUB',
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        payment_metadata JSONB,
                        webhook_data JSONB,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        paid_at TIMESTAMP WITH TIME ZONE,
                        CONSTRAINT fk_payments_user
                            FOREIGN KEY (user_telegram_id)
                            REFERENCES users(telegram_id)
                            ON DELETE CASCADE,
                        CONSTRAINT fk_payments_subscription
                            FOREIGN KEY (subscription_id)
                            REFERENCES subscriptions(id)
                            ON DELETE SET NULL,
                        CONSTRAINT ck_payments_payment_method
                            CHECK (payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other')),
                        CONSTRAINT ck_payments_plan_id
                            CHECK (plan_id IN ('month', 'year')),
                        CONSTRAINT ck_payments_status
                            CHECK (status IN ('pending', 'succeeded', 'cancelled', 'failed'))
                    )
                    """
                )
            )
            logger.info("✅ Таблица payments создана")

            indexes = [
                (
                    "idx_payments_payment_id",
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id)",
                ),
                (
                    "idx_payments_user_telegram_id",
                    "CREATE INDEX IF NOT EXISTS idx_payments_user_telegram_id ON payments(user_telegram_id)",
                ),
                (
                    "idx_payments_subscription_id",
                    "CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments(subscription_id)",
                ),
                (
                    "idx_payments_status",
                    "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
                ),
                (
                    "idx_payments_user_status",
                    "CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_telegram_id, status)",
                ),
                (
                    "idx_payments_created",
                    "CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at)",
                ),
                (
                    "idx_payments_paid",
                    "CREATE INDEX IF NOT EXISTS idx_payments_paid ON payments(paid_at)",
                ),
            ]
            for idx_name, idx_sql in indexes:
                try:
                    conn.execute(text(idx_sql))
                    logger.info(f"✅ Индекс {idx_name} создан")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.warning(f"⚠️ Ошибка создания индекса {idx_name}: {e}")

        logger.info("✅ Миграция payments применена")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка применения миграции payments: {e}")


def _apply_fallback_sql_migration() -> bool:
    """
    Fallback при ошибке миграций: схема управляется только через Alembic.

    Не читаем sql/ — единый источник правды: alembic/versions.
    """
    logger.warning(
        "⚠️ Миграции через Alembic не применились. "
        "Схема БД управляется только Alembic. Выполните вручную: alembic upgrade head"
    )
    return False
