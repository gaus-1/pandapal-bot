"""
Скрипт проверки подключения к базе данных PostgreSQL
Запустите для диагностики подключения к БД
"""

import os
import sys
from pathlib import Path

from sqlalchemy import inspect, text

from bot.config import settings
from bot.database import DatabaseService, engine

# Устанавливаем UTF-8 для Windows консоли
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")

# Добавляем корень проекта в PATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_database_connection():
    """Проверка подключения к базе данных"""
    print("=" * 80)
    print("🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ PANDAPAL")
    print("=" * 80)
    print()

    # 1. Проверка настроек
    print("📋 Настройки подключения:")
    print("-" * 80)

    # Безопасно показываем URL (скрываем пароль)
    db_url = settings.database_url
    if "@" in db_url:
        url_parts = db_url.split("@")
        credentials = url_parts[0].split("//")[1]
        safe_url = db_url.replace(credentials, "***:***")
    else:
        safe_url = db_url

    print(f"DATABASE_URL: {safe_url}")
    print(f"Тип БД: {'PostgreSQL' if db_url.startswith('postgres') else 'SQLite'}")
    print()

    # 2. Проверка подключения
    print("🔌 Тестирование подключения...")
    print("-" * 80)

    try:
        if DatabaseService.check_connection():
            print("✅ Подключение к БД успешно!")
        else:
            print("❌ Не удалось подключиться к БД")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

    print()

    # 3. Проверка таблиц
    print("📊 Проверка структуры базы данных...")
    print("-" * 80)

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"Найдено таблиц: {len(tables)}")
        print()

        if not tables:
            print("⚠️  Таблицы не найдены! Запустите миграции:")
            print("   alembic upgrade head")
            print("   или примените SQL скрипт: sql/02_create_tables.sql")
            return False

        # Ожидаемые таблицы
        expected_tables = [
            "users",
            "chat_history",
            "learning_sessions",
            "user_progress",
            "analytics_metrics",
            "user_sessions",
            "user_events",
            "analytics_reports",
        ]

        print("Таблицы:")
        for table in sorted(tables):
            status = "✅" if table in expected_tables else "ℹ️"

            # Получаем количество записей
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  {status} {table:<25} ({count} записей)")
            except Exception as e:
                print(f"  {status} {table:<25} (ошибка подсчета)")

        print()

        # Проверка отсутствующих таблиц
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print(f"⚠️  Отсутствующие таблицы: {', '.join(missing_tables)}")
            print("   Запустите: alembic upgrade head")
        else:
            print("✅ Все основные таблицы на месте!")

    except Exception as e:
        print(f"❌ Ошибка проверки структуры БД: {e}")
        return False

    print()

    # 4. Проверка индексов
    print("📑 Индексы (выборочно)...")
    print("-" * 80)

    try:
        if "chat_history" in tables:
            indexes = inspector.get_indexes("chat_history")
            print(f"Индексов в chat_history: {len(indexes)}")
            for idx in indexes[:3]:  # Показываем первые 3
                print(f"  • {idx['name']}")

        if "users" in tables:
            indexes = inspector.get_indexes("users")
            print(f"Индексов в users: {len(indexes)}")

    except Exception as e:
        print(f"⚠️  Не удалось получить информацию об индексах: {e}")

    print()

    # 5. Проверка Foreign Keys
    print("🔗 Foreign Keys (выборочно)...")
    print("-" * 80)

    try:
        if "chat_history" in tables:
            fks = inspector.get_foreign_keys("chat_history")
            print(f"Foreign Keys в chat_history: {len(fks)}")
            for fk in fks:
                print(
                    f"  • {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}"
                )

    except Exception as e:
        print(f"⚠️  Не удалось получить информацию о Foreign Keys: {e}")

    print()
    print("=" * 80)
    print("✅ ПРОВЕРКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = check_database_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
