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
from contextlib import contextmanager
from typing import Generator

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
# Оптимизировано для высокой нагрузки (100+ одновременных пользователей)
pool_kwargs = {}
if pool_class == QueuePool:
    pool_kwargs = {
        "pool_size": 20,  # Базовое количество соединений (было: 5)
        "max_overflow": 30,  # Дополнительные соединения при нагрузке (было: 15, всего до 50)
        "pool_timeout": 60,  # Таймаут ожидания свободного соединения (было: 30)
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
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Логирование при получении соединения из пула."""
    logger.debug("🔗 Соединение получено из пула")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
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
                database_url = os.getenv("DATABASE_URL") or os.getenv("database_url")
                if database_url:
                    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
                        database_url = database_url.replace(
                            "postgresql://", "postgresql+psycopg://", 1
                        )
                    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

                logger.info("🔄 Применение миграций Alembic...")
                command.upgrade(alembic_cfg, "head")
                logger.info("✅ Миграции Alembic применены успешно")
                migration_applied = True
            except Exception as e:
                logger.warning(f"⚠️ Alembic миграция не удалась: {e}")
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
def get_db() -> Generator[Session, None, None]:
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
        try:
            db_url_clean = settings.database_url.replace(
                settings.database_url.split("@")[0].split("//")[1], "***:***"
            )
        except Exception:
            pass

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
