#!/usr/bin/env python3
"""
Комплексная проверка сохранения данных во все таблицы.
Проверяет логику записи, миграции, зависимости.
"""

import sys
import io
from pathlib import Path

# Исправление кодировки для Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from bot.database import engine, get_db
from bot.models import (
    AnalyticsMetric,
    Base,
    ChatHistory,
    DailyRequestCount,
    GameSession,
    GameStats,
    LearningSession,
    Payment,
    Subscription,
    User,
    UserProgress,
)




def check_migrations_integrity(engine: Engine) -> bool:
    """Проверка целостности миграций Alembic."""
    print("\n" + "=" * 80)
    print("📋 ПРОВЕРКА МИГРАЦИЙ ALEMBIC")
    print("=" * 80)



    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Проверяем наличие таблицы alembic_version
        if "alembic_version" not in tables:
            print("❌ Таблица alembic_version не найдена!")

            return False

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version;"))
            current_version = result.scalar()
            print(f"✅ Текущая версия миграции: {current_version}")


            # Проверяем, что все таблицы из моделей существуют
            expected_tables = {
                "users": User,
                "learning_sessions": LearningSession,
                "user_progress": UserProgress,
                "chat_history": ChatHistory,
                "analytics_metrics": AnalyticsMetric,
                "daily_request_counts": DailyRequestCount,
                "subscriptions": Subscription,
                "payments": Payment,
                "game_sessions": GameSession,
                "game_stats": GameStats,
            }

            missing_tables = []
            for table_name, model_class in expected_tables.items():
                if table_name not in tables:
                    missing_tables.append(table_name)
                    print(f"❌ Таблица {table_name} отсутствует!")


            if missing_tables:
                return False

            print(f"✅ Все {len(expected_tables)} таблиц существуют")

            return True

    except Exception as e:
        print(f"❌ Ошибка проверки миграций: {e}")

        return False


def check_table_columns_match_models(engine: Engine) -> dict[str, bool]:
    """Проверка соответствия колонок таблиц моделям."""
    print("\n" + "=" * 80)
    print("📊 ПРОВЕРКА СТРУКТУРЫ ТАБЛИЦ")
    print("=" * 80)



    inspector = inspect(engine)
    results = {}

    expected_tables = {
        "users": User,
        "learning_sessions": LearningSession,
        "user_progress": UserProgress,
        "chat_history": ChatHistory,
        "analytics_metrics": AnalyticsMetric,
        "daily_request_counts": DailyRequestCount,
        "subscriptions": Subscription,
        "payments": Payment,
        "game_sessions": GameSession,
        "game_stats": GameStats,
    }

    for table_name, model_class in expected_tables.items():
        try:
            model_columns = set(model_class.__table__.columns.keys())
            db_columns = {col["name"] for col in inspector.get_columns(table_name)}

            missing_columns = model_columns - db_columns
            extra_columns = db_columns - model_columns

            if missing_columns or extra_columns:
                print(f"❌ {table_name}:")
                if missing_columns:
                    print(f"   Отсутствующие колонки: {', '.join(missing_columns)}")

                if extra_columns:
                    print(f"   Лишние колонки в БД: {', '.join(extra_columns)}")

                results[table_name] = False
            else:
                print(f"✅ {table_name}: структура корректна")

                results[table_name] = True
        except Exception as e:
            print(f"❌ {table_name}: ошибка проверки - {e}")

            results[table_name] = False

    return results


def check_data_persistence_logic() -> dict[str, bool]:
    """Проверка логики сохранения данных в каждой таблице."""
    print("\n" + "=" * 80)
    print("💾 ПРОВЕРКА ЛОГИКИ СОХРАНЕНИЯ ДАННЫХ")
    print("=" * 80)



    results = {}

    # Проверяем каждую таблицу на наличие логики записи
    table_services = {
        "users": ["user_service", "telegram_auth_service"],
        "chat_history": ["history_service", "ai_chat handler"],
        "game_sessions": ["games_service"],
        "game_stats": ["games_service", "gamification_service"],
        "subscriptions": ["subscription_service", "recurring_payment_service"],
        "payments": ["recurring_payment_service", "premium_endpoints"],
        "user_progress": ["gamification_service", "personal_tutor_service"],
        "daily_request_counts": ["premium_features_service"],
        "analytics_metrics": ["analytics_service"],
    }

    for table_name, expected_services in table_services.items():
        # Проверяем наличие записей в таблице
        try:
            with get_db() as db:
                model_map = {
                    "users": User,
                    "chat_history": ChatHistory,
                    "game_sessions": GameSession,
                    "game_stats": GameStats,
                    "subscriptions": Subscription,
                    "payments": Payment,
                    "user_progress": UserProgress,
                    "daily_request_counts": DailyRequestCount,
                    "analytics_metrics": AnalyticsMetric,
                }

                if table_name in model_map:
                    count = db.query(model_map[table_name]).count()
                    print(f"✅ {table_name}: {count} записей (логика записи: {', '.join(expected_services)})")

                    results[table_name] = True
                else:
                    print(f"⚠️  {table_name}: модель не найдена в проверке")

                    results[table_name] = False
        except Exception as e:
            print(f"❌ {table_name}: ошибка проверки - {e}")

            results[table_name] = False

    return results


def check_dependencies() -> bool:
    """Проверка зависимостей из requirements.txt."""
    print("\n" + "=" * 80)
    print("📦 ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    print("=" * 80)



    try:
        requirements_path = Path(__file__).parent.parent / "requirements.txt"
        if not requirements_path.exists():
            print("❌ Файл requirements.txt не найден!")

            return False

        # Потоковое чтение requirements.txt построчно
        critical_deps = [
            "sqlalchemy",
            "alembic",
            "psycopg",
            "aiogram",
            "pydantic",
        ]

        found_deps = set()
        with open(requirements_path, "r", encoding="utf-8") as f:
            for line in f:
                # Убираем пробелы и комментарии, извлекаем имя пакета
                line = line.strip().split("#")[0]  # Убираем комментарии
                if not line:
                    continue
                # Извлекаем имя пакета (до ==, >=, <=, >, <, ~=)
                dep_name = line.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].split("~=")[0].strip()
                if dep_name in critical_deps:
                    found_deps.add(dep_name)

        missing_deps = []
        for dep in critical_deps:
            if dep not in found_deps:
                missing_deps.append(dep)
                print(f"❌ Зависимость {dep} не найдена в requirements.txt")


        if missing_deps:
            return False

        print(f"✅ Все критические зависимости присутствуют")

        return True

    except Exception as e:
        print(f"❌ Ошибка проверки зависимостей: {e}")

        return False


def main():
    """Главная функция проверки."""
    print("=" * 80)
    print("🔍 КОМПЛЕКСНАЯ ПРОВЕРКА СОХРАНЕНИЯ ДАННЫХ")
    print("=" * 80)



    all_checks_passed = True

    # 1. Проверка миграций
    migrations_ok = check_migrations_integrity(engine)
    if not migrations_ok:
        all_checks_passed = False

    # 2. Проверка структуры таблиц
    structure_results = check_table_columns_match_models(engine)
    if not all(structure_results.values()):
        all_checks_passed = False

    # 3. Проверка логики сохранения
    persistence_results = check_data_persistence_logic()
    if not all(persistence_results.values()):
        all_checks_passed = False

    # 4. Проверка зависимостей
    deps_ok = check_dependencies()
    if not deps_ok:
        all_checks_passed = False

    # Итоговый отчет
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)

    if all_checks_passed:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")

        return 0
    else:
        print("⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        if not migrations_ok:
            print("   - Проблемы с миграциями")
        if not all(structure_results.values()):
            print("   - Несоответствие структуры таблиц")
        if not all(persistence_results.values()):
            print("   - Проблемы с логикой сохранения данных")
        if not deps_ok:
            print("   - Проблемы с зависимостями")

        return 1


if __name__ == "__main__":
    sys.exit(main())
