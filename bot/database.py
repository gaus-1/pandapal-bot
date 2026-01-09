"""
Управление подключением к базе данных PostgreSQL для PandaPal Bot.

Этот модуль предоставляет всю функциональность для работы с базой данных:
создание подключений, управление сессиями, инициализацию таблиц и сервисы
для проверки здоровья БД.

Основные компоненты:
- **SQLAlchemy Engine**: Подключение к PostgreSQL на Railway.app
- **Session Factory**: Создание изолированных сессий для транзакций
- **Context Manager**: Безопасное управление жизненным циклом сессий
- **DatabaseService**: Сервис для проверки состояния подключения

Конфигурация:
- **Connection Pool**: QueuePool для высокой нагрузки (переиспользование соединений)
- **SSL Mode**: Обязательный SSL для Railway PostgreSQL
- **Timeout**: 10 секунд на установку подключения
- **Pool Settings**: 5 соединений, max 20, recycle 1800s

Best Practices:
- Используйте get_db() как context manager для автоматического закрытия сессий
- В продакшене применяйте Alembic миграции вместо create_all()
- Проверяйте здоровье БД через DatabaseService.check_connection()
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
    """
    Инициализация базы данных PostgreSQL.

    Создает все таблицы, определенные в моделях SQLAlchemy,
    если они не существуют. Используется для первоначальной настройки
    или тестовой среды.

    ВНИМАНИЕ: В production используйте Alembic миграции для управления схемой БД!

    Raises:
        Exception: При ошибке создания таблиц.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise


async def init_database() -> None:
    """
    Асинхронная инициализация базы данных PostgreSQL.

    Проверяет подключение к базе данных и валидирует её состояние.
    Опционально применяет миграции Alembic при старте (если AUTO_MIGRATE=true).

    Raises:
        Exception: При ошибке подключения или проверки БД.
    """
    try:
        # Проверяем подключение к БД
        if DatabaseService.check_connection():
            logger.info("✅ База данных подключена и готова к работе")
        else:
            logger.warning("⚠️ Проблема с подключением к базе данных")

        # Опционально применяем миграции при старте
        auto_migrate = os.getenv("AUTO_MIGRATE", "false").lower() == "true"
        if auto_migrate:
            migration_applied = False
            try:
                from alembic import command
                from alembic.config import Config

                alembic_cfg = Config("alembic.ini")
                # Переопределяем URL из переменной окружения
                database_url = os.getenv("DATABASE_URL")
                if database_url:
                    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
                        database_url = database_url.replace(
                            "postgresql://", "postgresql+psycopg://", 1
                        )
                    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

                # Проверяем текущее состояние БД перед миграцией
                from sqlalchemy import inspect, text

                inspector = inspect(engine)
                tables = inspector.get_table_names()

                # Если таблицы уже существуют, проверяем состояние Alembic
                if "users" in tables and "chat_history" in tables:
                    logger.info("📊 Таблицы уже существуют, проверяем только новые миграции...")
                    # Проверяем таблицу alembic_version
                    alembic_version_exists = "alembic_version" in tables
                    current_revision = None

                    if alembic_version_exists:
                        try:
                            with engine.connect() as conn:
                                result = conn.execute(
                                    text("SELECT version_num FROM alembic_version LIMIT 1")
                                )
                                current_revision = result.scalar()
                                if current_revision:
                                    logger.info(f"📋 Текущая версия миграции: {current_revision}")
                        except Exception as e:
                            logger.debug(f"Не удалось прочитать текущую версию: {e}")

                    # Если таблицы есть, но версия Alembic не установлена - помечаем текущее состояние
                    if not current_revision:
                        logger.info(
                            "📋 Таблицы существуют, но версия Alembic не установлена. Помечаем текущее состояние..."
                        )
                        try:
                            command.stamp(alembic_cfg, "head")
                            logger.info("✅ Текущее состояние БД помечено как актуальное")
                            migration_applied = True
                        except Exception as stamp_err:
                            logger.warning(f"⚠️ Не удалось пометить текущее состояние: {stamp_err}")
                            # Продолжаем попытку upgrade

                    # Пытаемся применить только новые миграции
                    if not migration_applied:
                        try:
                            command.upgrade(alembic_cfg, "head")
                            migration_applied = True
                            logger.info("✅ Миграции Alembic применены успешно")
                        except Exception as alembic_err:
                            # Если ошибка связана с существующими таблицами - это нормально
                            error_str = str(alembic_err).lower()
                            if (
                                "already exists" in error_str
                                or "duplicate" in error_str
                                or ("relation" in error_str and "already exists" in error_str)
                            ):
                                logger.debug(
                                    f"ℹ️ Миграции уже применены (предупреждение: {alembic_err})"
                                )
                                # Если версия не была установлена, пытаемся установить её сейчас
                                if not current_revision:
                                    try:
                                        command.stamp(alembic_cfg, "head")
                                        logger.info(
                                            "✅ Текущее состояние БД помечено как актуальное"
                                        )
                                    except Exception:
                                        pass
                                migration_applied = True
                            elif "multiple head revisions" in error_str:
                                # Если есть множественные head ревизии, пытаемся применить все heads
                                logger.warning(
                                    "⚠️ Обнаружены множественные head ревизии, пытаемся применить все heads..."
                                )
                                try:
                                    command.upgrade(alembic_cfg, "heads")
                                    migration_applied = True
                                    logger.info(
                                        "✅ Миграции Alembic применены успешно (через heads)"
                                    )
                                except Exception as heads_err:
                                    logger.warning(
                                        f"⚠️ Не удалось применить миграции через heads: {heads_err}"
                                    )
                            else:
                                logger.warning(f"⚠️ Alembic миграция не удалась: {alembic_err}")
                else:
                    # Применяем все миграции с нуля
                    try:
                        command.upgrade(alembic_cfg, "head")
                        migration_applied = True
                        logger.info("✅ Миграции Alembic применены успешно")
                    except Exception as alembic_err:
                        error_str = str(alembic_err).lower()
                        if "already exists" in error_str or "duplicate" in error_str:
                            logger.info("ℹ️ Таблицы уже существуют, миграция не требуется")
                            migration_applied = True
                        elif "multiple head revisions" in error_str:
                            # Если есть множественные head ревизии, пытаемся применить все heads
                            logger.warning(
                                "⚠️ Обнаружены множественные head ревизии, пытаемся применить все heads..."
                            )
                            try:
                                command.upgrade(alembic_cfg, "heads")
                                migration_applied = True
                                logger.info("✅ Миграции Alembic применены успешно (через heads)")
                            except Exception as heads_err:
                                logger.warning(
                                    f"⚠️ Не удалось применить миграции через heads: {heads_err}"
                                )
                        else:
                            logger.warning(f"⚠️ Alembic миграция не удалась: {alembic_err}")

                # Проверяем, нужна ли миграция premium
                needs_premium_migration = False

                # Проверяем наличие premium_until в users
                if "users" in tables:
                    columns = [col["name"] for col in inspector.get_columns("users")]
                    if "premium_until" not in columns:
                        needs_premium_migration = True
                        logger.info("📋 Обнаружено: колонка premium_until отсутствует")

                # Проверяем наличие таблицы subscriptions
                if "subscriptions" not in tables:
                    needs_premium_migration = True
                    logger.info("📋 Обнаружено: таблица subscriptions отсутствует")

                if needs_premium_migration:
                    # Применяем SQL скрипт напрямую (надежнее чем Alembic для существующей БД)
                    logger.info("🔄 Применение миграции premium через SQL...")
                    try:
                        # Выполняем команды в правильном порядке
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
                                                CHECK (plan_id IN ('week', 'month', 'year'))
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
                        migration_applied = True
                    except Exception as sql_err:
                        logger.error(f"❌ Не удалось применить SQL миграцию: {sql_err}")
                else:
                    # Premium миграция не нужна, пробуем Alembic для других миграций
                    logger.info("🔄 Применение миграций Alembic...")
                    try:
                        command.upgrade(alembic_cfg, "head")
                        logger.info("✅ Миграции Alembic применены успешно")
                        migration_applied = True
                    except Exception as alembic_err:
                        logger.warning(f"⚠️ Alembic миграция не удалась: {alembic_err}")
                        migration_applied = False

                # Проверяем, нужна ли миграция payment_method
                needs_payment_migration = False
                if "subscriptions" in tables:
                    columns = [col["name"] for col in inspector.get_columns("subscriptions")]
                    if "payment_method" not in columns or "payment_id" not in columns:
                        needs_payment_migration = True
                        logger.info(
                            "📋 Обнаружено: колонки payment_method или payment_id отсутствуют"
                        )

                if needs_payment_migration:
                    logger.info("🔄 Применение миграции payment_method через SQL...")
                    try:
                        with engine.begin() as conn:
                            # Добавляем payment_method
                            if "payment_method" not in columns:
                                conn.execute(
                                    text(
                                        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20)"
                                    )
                                )
                                logger.info("✅ Колонка payment_method добавлена")

                            # Добавляем payment_id
                            if "payment_id" not in columns:
                                conn.execute(
                                    text(
                                        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS payment_id VARCHAR(255)"
                                    )
                                )
                                logger.info("✅ Колонка payment_id добавлена")

                            # Создаем индекс
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

                            # Добавляем constraint
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
                                logger.info(
                                    "✅ Constraint ck_subscriptions_payment_method добавлен"
                                )
                            except Exception as e:
                                if (
                                    "already exists" not in str(e).lower()
                                    and "duplicate" not in str(e).lower()
                                ):
                                    logger.warning(f"⚠️ Ошибка создания constraint: {e}")

                        logger.info("✅ Миграция payment_method применена")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка применения миграции payment_method: {e}")

                # Проверяем, нужна ли миграция payments таблицы
                needs_payments_table = False
                if "payments" not in tables:
                    needs_payments_table = True
                    logger.info("📋 Обнаружено: таблица payments отсутствует")

                if needs_payments_table:
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
                                            CHECK (plan_id IN ('week', 'month', 'year')),
                                        CONSTRAINT ck_payments_status
                                            CHECK (status IN ('pending', 'succeeded', 'cancelled', 'failed'))
                                    )
                                    """
                                )
                            )
                            logger.info("✅ Таблица payments создана")

                            # Создаем индексы
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

            except Exception as e:
                logger.warning(f"⚠️ Ошибка при проверке миграций: {e}")
                logger.info("🔄 Пробуем применить SQL скрипт напрямую...")

                # Fallback: применяем SQL скрипт напрямую
                try:
                    from pathlib import Path

                    from sqlalchemy import text

                    # Путь относительно корня проекта
                    project_root = Path(__file__).parent.parent
                    sql_file = project_root / "sql" / "03_add_premium_subscriptions.sql"
                    if sql_file.exists():
                        with engine.connect() as conn:
                            sql_content = sql_file.read_text(encoding="utf-8")
                            # Выполняем SQL построчно для лучшей обработки ошибок
                            for statement in sql_content.split(";"):
                                statement = statement.strip()
                                if statement and not statement.startswith("--"):
                                    try:
                                        conn.execute(text(statement))
                                    except Exception as sql_err:
                                        # Игнорируем ошибки "already exists" - это нормально
                                        if "already exists" not in str(sql_err).lower():
                                            logger.warning(f"⚠️ SQL ошибка (игнорируем): {sql_err}")
                            conn.commit()
                        logger.info("✅ SQL миграция применена успешно")
                        migration_applied = True
                    else:
                        logger.warning(f"⚠️ SQL файл не найден: {sql_file}")
                except Exception as sql_err:
                    logger.error(f"❌ Не удалось применить SQL миграцию: {sql_err}")

            if not migration_applied:
                logger.warning("⚠️ Миграции не применены. Примените вручную: alembic upgrade head")
    except Exception as e:
        logger.error("❌ Ошибка инициализации БД: %s", str(e))
        raise


@contextmanager
def get_db() -> Generator[Session]:
    """
    Контекстный менеджер для получения сессии базы данных.

    Автоматически создает сессию БД и гарантирует её корректное закрытие
    после завершения работы. Обеспечивает безопасное управление транзакциями
    и предотвращает утечки соединений.

    Yields:
        Session: Сессия SQLAlchemy для работы с базой данных.

    Example:
        >>> with get_db() as db:
        ...     user = db.query(User).filter_by(telegram_id=123).first()
        ...     user.name = "Новое имя"
        ...     db.commit()  # Автоматически откатится при ошибке
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Автоматический commit при успехе
    except Exception as e:
        db.rollback()  # Откат при ошибке
        # Используем % для логирования чтобы избежать проблем с фигурными скобками в SQL
        logger.error("❌ Database error: %s", str(e))
        raise
    finally:
        db.close()  # Всегда закрываем сессию


class DatabaseService:
    """
    Сервис для работы с базой данных
    Предоставляет высокоуровневые методы
    """

    @staticmethod
    def get_db_session() -> Session:
        """
        Получить новую сессию БД
        НЕ ЗАБУДЬТЕ закрыть сессию после использования!

        .. deprecated:: 2025-01
           Используйте `get_db()` context manager вместо этого метода.
           Это обеспечивает автоматическое закрытие сессии и обработку ошибок.

        Returns:
            Session: Новая сессия SQLAlchemy
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
        """
        Проверка подключения к базе данных

        Returns:
            bool: True если подключение работает
        """
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
