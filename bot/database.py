"""
Управление подключением к базе данных PostgreSQL.

Предоставляет подключения, управление сессиями, инициализацию таблиц
и проверку здоровья БД.
"""

import os
from collections.abc import Generator
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from bot.config import settings
from bot.models import Base

# Определяем тип пула в зависимости от окружения
# SQLite не поддерживает QueuePool, PostgreSQL - поддерживает
is_sqlite = settings.database_url.startswith("sqlite")

# Настройки подключения
connect_args = {}
pool_class = NullPool  # По умолчанию NullPool для SQLite

if not is_sqlite:
    # PostgreSQL: используем QueuePool для высокой нагрузки
    # Определяем режим SSL: для localhost - prefer, для Railway/Render - require
    db_url = settings.database_url
    is_localhost = "localhost" in db_url or "127.0.0.1" in db_url
    ssl_mode = "prefer" if is_localhost else "require"

    connect_args = {
        "sslmode": ssl_mode,  # prefer для localhost, require для Railway/Render
        "connect_timeout": 10,  # Таймаут подключения 10 секунд
    }
    pool_class = QueuePool

# Параметры пула соединений для PostgreSQL
# Оптимизировано для очень высокой нагрузки (1000+ одновременных запросов)
pool_kwargs = {}
if pool_class == QueuePool:
    pool_kwargs = {
        "pool_size": 100,  # Базовое количество соединений (увеличено с 50 для 1000+ запросов)
        "max_overflow": 200,  # Дополнительные соединения при нагрузке (всего до 300)
        "pool_timeout": 180,  # Таймаут ожидания свободного соединения (увеличено с 120)
        "pool_recycle": 1800,  # Пересоздание соединений каждые 30 минут
        "pool_pre_ping": True,  # Проверка соединения перед использованием
    }

engine = create_engine(
    settings.database_url,
    poolclass=pool_class,
    echo=False,  # True для отладки SQL-запросов
    future=True,
    connect_args=connect_args,
    **pool_kwargs,
)


# Event listener для логирования проблем с пулом
@event.listens_for(engine, "checkout")
def receive_checkout(_dbapi_connection, _connection_record, _connection_proxy):  # noqa: ARG001
    """Логирование при получении соединения из пула."""
    logger.debug("🔗 Соединение получено из пула")


@event.listens_for(engine, "checkin")
def receive_checkin(_dbapi_connection, _connection_record):  # noqa: ARG001
    """Логирование при возврате соединения в пул."""
    logger.debug("🔙 Соединение возвращено в пул")


# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Инициализация базы данных (создание таблиц)."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise


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
                        except Exception:
                            pass
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
    """Применение SQL миграции как fallback."""
    from pathlib import Path

    logger.info("🔄 Пробуем применить SQL скрипт напрямую...")
    try:
        project_root = Path(__file__).parent.parent
        sql_file = project_root / "sql" / "03_add_premium_subscriptions.sql"
        if not sql_file.exists():
            logger.warning(f"⚠️ SQL файл не найден: {sql_file}")
            return False

        with engine.connect() as conn:
            sql_content = sql_file.read_text(encoding="utf-8")
            for statement in sql_content.split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    try:
                        conn.execute(text(statement))
                    except Exception as sql_err:
                        if "already exists" not in str(sql_err).lower():
                            logger.warning(f"⚠️ SQL ошибка (игнорируем): {sql_err}")
            conn.commit()
        logger.info("✅ SQL миграция применена успешно")
        return True
    except Exception as sql_err:
        logger.error(f"❌ Не удалось применить SQL миграцию: {sql_err}")
        return False


async def init_database() -> None:
    """Инициализация базы данных с проверкой подключения."""
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
                from alembic import command

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


@contextmanager
def get_db() -> Generator[Session]:
    """Контекстный менеджер для получения сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Автоматический commit при успехе
    except Exception as e:
        db.rollback()  # Откат при ошибке
        # Используем безопасное логирование чтобы избежать проблем с фигурными скобками в SQL
        error_msg = str(e).replace("{", "{{").replace("}", "}}")
        logger.error(f"❌ Database error: {error_msg}")
        raise
    finally:
        db.close()  # Всегда закрываем сессию


class DatabaseService:
    """Сервис для работы с базой данных."""

    @staticmethod
    def get_db_session() -> Session:
        """
        Получить новую сессию БД.

        Deprecated: используйте get_db() context manager.
        """
        import warnings

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
        from contextlib import suppress

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
