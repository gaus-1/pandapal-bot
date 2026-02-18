"""
Alembic environment configuration.

This module configures Alembic for database migrations.
It loads environment variables and sets up the database connection.
"""

import os
from pathlib import Path

from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context  # type: ignore[attr-defined]

# Загружаем .env из корня проекта; override=True — приоритет над уже заданным DATABASE_URL в окружении
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env", override=True)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with environment variable
database_url = os.getenv("DATABASE_URL") or os.getenv("database_url")
if database_url:
    # Нормализуем DATABASE_URL: заставляем использовать psycopg v3
    # Это необходимо для совместимости с SQLAlchemy 2.0+
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from bot.models import Base  # noqa: E402

target_metadata = Base.metadata


def _compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    """Считать эквивалентными представления типов БД (PostgreSQL) и метаданных (SQLAlchemy)."""
    from sqlalchemy import (
        Boolean,
        DateTime,
        Float,
        Integer,
        BigInteger,
        JSON,
        String,
        Text,
    )
    from sqlalchemy.dialects.postgresql import (
        BOOLEAN,
        DATE,
        DOUBLE_PRECISION,
        JSONB,
        TIMESTAMP,
    )
    t1 = type(inspected_type).__name__
    t2 = type(metadata_type).__name__
    # Эквиваленты целых
    if isinstance(inspected_type, (Integer, BigInteger)) and isinstance(
        metadata_type, (Integer, BigInteger)
    ):
        return False
    # JSON/JSONB
    if isinstance(inspected_type, (JSONB, JSON)) and isinstance(metadata_type, (JSONB, JSON)):
        return False
    # Строки: VARCHAR(n) <-> String(n)
    if t1 in ("VARCHAR", "String") and t2 in ("VARCHAR", "String"):
        return False
    # TEXT <-> Text()
    if (t1 in ("TEXT", "Text") or isinstance(inspected_type, Text)) and (
        t2 in ("TEXT", "Text") or isinstance(metadata_type, Text)
    ):
        return False
    # TIMESTAMP(timezone=True) <-> DateTime(timezone=True)
    if isinstance(inspected_type, (TIMESTAMP, DateTime)) and isinstance(
        metadata_type, (TIMESTAMP, DateTime)
    ):
        return False
    if isinstance(inspected_type, DATE) and isinstance(metadata_type, DateTime):
        return False
    # BOOLEAN <-> Boolean()
    if isinstance(inspected_type, (BOOLEAN, Boolean)) and isinstance(
        metadata_type, (BOOLEAN, Boolean)
    ):
        return False
    # DOUBLE_PRECISION <-> Float()
    if isinstance(inspected_type, (DOUBLE_PRECISION, Float)) and isinstance(
        metadata_type, (DOUBLE_PRECISION, Float)
    ):
        return False
    return True


def _compare_server_default(
    context,
    inspected_column,
    metadata_column,
    inspected_default,
    metadata_default,
    rendered_metadata_default,
):
    """Считать одинаковыми логически эквивалентные server_default (например 'true' и True)."""
    if inspected_default is None and metadata_default is None:
        return False
    if inspected_default is None or metadata_default is None:
        return None
    a = str(inspected_default).strip().lower()
    b = str(metadata_default).strip().lower()
    if a == b:
        return False
    if a in ("true", "false") and b in ("true", "false"):
        return False
    return None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=_compare_type,
        compare_server_default=_compare_server_default,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=_compare_type,
            compare_server_default=_compare_server_default,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
