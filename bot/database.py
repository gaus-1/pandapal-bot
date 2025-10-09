"""
Управление подключением к базе данных PostgreSQL для PandaPal Bot.

Этот модуль предоставляет всю функциональность для работы с базой данных:
создание подключений, управление сессиями, инициализацию таблиц и сервисы
для проверки здоровья БД.

Основные компоненты:
- **SQLAlchemy Engine**: Подключение к PostgreSQL на Render.com
- **Session Factory**: Создание изолированных сессий для транзакций
- **Context Manager**: Безопасное управление жизненным циклом сессий
- **DatabaseService**: Сервис для проверки состояния подключения

Конфигурация:
- **Connection Pool**: NullPool для асинхронной работы (новое подключение на запрос)
- **SSL Mode**: Обязательный SSL для Render PostgreSQL
- **Timeout**: 10 секунд на установку подключения
- **Transactional DDL**: Поддержка миграций Alembic

Best Practices:
- Используйте get_db() как context manager для автоматического закрытия сессий
- В продакшене применяйте Alembic миграции вместо create_all()
- Проверяйте здоровье БД через DatabaseService.check_connection()
"""

from contextlib import contextmanager
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from bot.config import settings
from bot.models import Base

# Создаём engine для подключения к PostgreSQL
# NullPool для асинхронной работы (каждый запрос = новое подключение)
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,  # True для отладки SQL-запросов
    future=True,
    connect_args={
        "sslmode": "require",  # Требуем SSL для Render PostgreSQL
        "connect_timeout": 10,  # Таймаут подключения 10 секунд
    },
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """
    Инициализация базы данных
    Создаёт все таблицы, если их нет

    ВНИМАНИЕ: В production используйте Alembic миграции!
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager для получения сессии БД
    Автоматически закрывает сессию после использования

    Использование:
    ```python
    with get_db() as db:
        user = db.query(User).filter_by(telegram_id=123).first()
    ```

    Yields:
        Session: Сессия SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Автоматический commit при успехе
    except Exception as e:
        db.rollback()  # Откат при ошибке
        logger.error(f"❌ Database error: {e}")
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

        Returns:
            Session: Новая сессия SQLAlchemy
        """
        return SessionLocal()

    @staticmethod
    def check_connection() -> bool:
        """
        Проверка подключения к базе данных

        Returns:
            bool: True если подключение работает
        """
        try:
            # Логируем URL для диагностики (без пароля)
            db_url_clean = settings.database_url.replace(
                settings.database_url.split("@")[0].split("//")[1], "***:***"
            )
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
