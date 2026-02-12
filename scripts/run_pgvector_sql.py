#!/usr/bin/env python3
"""
Выполнить SQL для создания pgvector-таблиц.

Требует: PostgreSQL с pgvector (Docker: pgvector/pgvector:pg17, Railway: pgvector template).
Запуск: python scripts/run_pgvector_sql.py
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


def main():
    url = os.getenv("DATABASE_URL")
    if not url or "sqlite" in url.lower():
        print("DATABASE_URL не задан или SQLite. Нужен PostgreSQL с pgvector.")
        return 1

    if "postgresql://" in url and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    sql_path = Path(__file__).parent.parent / "sql" / "07_add_pgvector_tables.sql"
    if not sql_path.exists():
        print(f"Файл не найден: {sql_path}")
        return 1

    sql = sql_path.read_text(encoding="utf-8")

    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            for stmt in sql.split(";"):
                stmt = stmt.strip()
                if stmt and not stmt.startswith("--"):
                    conn.execute(text(stmt + ";"))
            conn.commit()
        print("Таблицы pgvector созданы.")
        return 0
    except Exception as e:
        err = str(e).lower()
        if "extension" in err and "not available" in err:
            print("pgvector не установлен. Используйте Docker (pgvector/pgvector:pg17) или Railway с pgvector.")
        else:
            print(f"Ошибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
