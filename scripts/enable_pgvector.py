#!/usr/bin/env python3
"""
Включить pgvector в PostgreSQL.

Запустить до alembic upgrade, если расширение ещё не установлено.
Использует DATABASE_URL из .env.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError


def main():
    url = os.getenv("DATABASE_URL")
    if not url or "sqlite" in url.lower():
        print("DATABASE_URL не задан или это SQLite. pgvector нужен только для PostgreSQL.")
        return 0

    if "postgresql://" in url and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        print("pgvector включён.")
        return 0
    except (ProgrammingError, Exception) as e:
        err = str(e).lower()
        if "extension" in err and ("not available" in err or "could not open" in err):
            print(
                "Ошибка: pgvector не установлен в PostgreSQL.\n"
                "Локально: docker-compose up -d postgres (image: pgvector/pgvector:pg17),\n"
                "  затем: set DATABASE_URL=postgresql://pandapal_user:pandapal_password@localhost:5432/pandapal\n"
                "Railway: разверните PostgreSQL с pgvector: railway.com/deploy/postgres-with-pgvector-engine"
            )
        else:
            print(f"Ошибка: {e}")
        return 1
    except OperationalError as e:
        print(f"Ошибка подключения: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
