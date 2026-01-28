#!/usr/bin/env python3
"""
Скрипт для проверки подключения к Railway PostgreSQL и списка таблиц.
Использует данные из переменных окружения Railway.
"""

import os
import sys
import io
from pathlib import Path

# Исправление кодировки для Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Данные из Railway
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "XFYmPwXJOGgAkbMGCclEHXMEWEAYKonP"
POSTGRES_DB = "railway"
# Railway обычно предоставляет DATABASE_URL напрямую, но если нет - используем стандартные значения
# Попробуем получить из DATABASE_URL или используем переменные окружения
DATABASE_URL_ENV = os.getenv("DATABASE_URL", "")
if DATABASE_URL_ENV and "railway" in DATABASE_URL_ENV.lower():
    # Парсим DATABASE_URL если он есть
    import re
    match = re.search(r"@([^:]+):(\d+)/", DATABASE_URL_ENV)
    if match:
        POSTGRES_HOST = match.group(1)
        POSTGRES_PORT = match.group(2)
    else:
        POSTGRES_HOST = os.getenv("POSTGRES_HOST", "containers-us-west-146.railway.app")
        POSTGRES_PORT = os.getenv("POSTGRES_PORT", "6543")
else:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "containers-us-west-146.railway.app")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "6543")

# Формируем DATABASE_URL (используем psycopg v3)
DATABASE_URL = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO",
)


def check_railway_database():
    """Проверка подключения к Railway PostgreSQL и списка таблиц."""
    print("\n" + "=" * 80)
    print("🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К RAILWAY POSTGRESQL")
    print("=" * 80 + "\n")

    print(f"📊 Host: {POSTGRES_HOST}")
    print(f"📊 Port: {POSTGRES_PORT}")
    print(f"📊 Database: {POSTGRES_DB}")
    print(f"📊 User: {POSTGRES_USER}")
    print(f"📊 DATABASE_URL: postgresql://{POSTGRES_USER}:***@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}\n")

    try:
        # Создаем подключение
        engine = create_engine(
            DATABASE_URL,
            connect_args={
                "sslmode": "require",
                "connect_timeout": 10,
            },
            pool_pre_ping=True,
        )

        # Проверяем подключение
        print("🔌 Попытка подключения...")
        with engine.connect() as conn:
            # Проверяем версию PostgreSQL
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Подключение успешно!")
            print(f"📊 PostgreSQL версия: {version.split(',')[0]}\n")

            # Получаем список всех таблиц
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            print(f"📋 НАЙДЕНО ТАБЛИЦ: {len(tables)}\n")

            if tables:
                print("=" * 80)
                print("📊 СПИСОК ТАБЛИЦ:")
                print("=" * 80)
                for i, table_name in enumerate(sorted(tables), 1):
                    # Получаем количество строк в таблице
                    try:
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
                        row_count = count_result.scalar()
                        print(f"{i:3d}. {table_name:50s} | Строк: {row_count:>8,}")
                    except Exception as e:
                        print(f"{i:3d}. {table_name:50s} | Ошибка подсчета: {e}")

                print("\n" + "=" * 80)
                print("📊 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ТАБЛИЦАХ:")
                print("=" * 80 + "\n")

                for table_name in sorted(tables):
                    print(f"\n📋 Таблица: {table_name}")
                    print("-" * 80)
                    columns = inspector.get_columns(table_name)
                    print(f"Колонок: {len(columns)}")
                    for col in columns:
                        nullable = "NULL" if col.get("nullable") else "NOT NULL"
                        default = f" DEFAULT {col.get('default')}" if col.get("default") else ""
                        print(f"  • {col['name']:30s} {str(col['type']):30s} {nullable}{default}")

                    # Показываем индексы
                    indexes = inspector.get_indexes(table_name)
                    if indexes:
                        print(f"\nИндексы ({len(indexes)}):")
                        for idx in indexes:
                            cols = ", ".join(idx["column_names"])
                            unique = "UNIQUE" if idx.get("unique") else ""
                            print(f"  • {idx['name']:30s} {unique} ({cols})")

            else:
                print("❌ ТАБЛИЦЫ НЕ НАЙДЕНЫ!")
                print("\n⚠️  База данных пуста. Возможно:")
                print("   1. Миграции Alembic не были применены")
                print("   2. База данных была пересоздана")
                print("   3. Неправильные учетные данные")

            # Проверяем схему alembic_version
            print("\n" + "=" * 80)
            print("📊 ПРОВЕРКА MIGRATIONS (alembic_version):")
            print("=" * 80)
            try:
                if "alembic_version" in tables:
                    result = conn.execute(text("SELECT version_num FROM alembic_version;"))
                    version_num = result.scalar()
                    print(f"✅ Текущая версия миграции: {version_num}")
                else:
                    print("❌ Таблица alembic_version не найдена - миграции не применены!")
            except Exception as e:
                print(f"⚠️  Ошибка проверки миграций: {e}")

    except SQLAlchemyError as e:
        print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
        print("\nВозможные причины:")
        print("  1. Неправильные учетные данные")
        print("  2. Хост недоступен")
        print("  3. Проблемы с SSL")
        print("  4. Firewall блокирует подключение")
        return False
    except Exception as e:
        print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 80 + "\n")
    return True


if __name__ == "__main__":
    check_railway_database()
