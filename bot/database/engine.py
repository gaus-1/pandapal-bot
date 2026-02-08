"""
Создание движка SQLAlchemy, пула соединений, фабрики сессий.

Предоставляет engine, SessionLocal, get_db() и init_db().
"""

from collections.abc import Generator
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import create_engine, event
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
