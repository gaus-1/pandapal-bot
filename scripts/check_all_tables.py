"""
Скрипт для проверки всех таблиц в базе данных.

Проверяет:
1. Все ли таблицы из models.py созданы в БД
2. Соответствие структуры таблиц моделям
3. Использование таблиц в сервисах
"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from bot.database import engine
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


def get_expected_tables() -> dict[str, type]:
    """Получить список ожидаемых таблиц из моделей."""
    return {
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


def check_tables_exist(engine: Engine) -> dict[str, bool]:
    """Проверить наличие всех таблиц в БД."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    expected_tables = get_expected_tables()
    results = {}

    print("=" * 80)
    print("ПРОВЕРКА НАЛИЧИЯ ТАБЛИЦ")
    print("=" * 80)

    for table_name, model_class in expected_tables.items():
        exists = table_name in existing_tables
        results[table_name] = exists
        status = "[OK]" if exists else "[MISSING]"
        print(f"{status} {table_name:30} ({model_class.__name__})")

    missing_tables = [t for t, exists in results.items() if not exists]
    if missing_tables:
        print(f"\n[WARNING] Отсутствующие таблицы: {', '.join(missing_tables)}")
    else:
        print("\n[OK] Все таблицы на месте!")

    return results


def check_table_structure(engine: Engine, table_name: str, model_class: type) -> bool:
    """Проверить структуру таблицы."""
    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return False

    # Получаем колонки из модели
    model_columns = set(model_class.__table__.columns.keys())

    # Получаем колонки из БД
    db_columns = {col["name"] for col in inspector.get_columns(table_name)}

    missing_columns = model_columns - db_columns
    extra_columns = db_columns - model_columns

    if missing_columns or extra_columns:
        print(f"\n  [WARNING] {table_name}:")
        if missing_columns:
            print(f"     Отсутствующие колонки: {', '.join(missing_columns)}")
        if extra_columns:
            print(f"     Лишние колонки в БД: {', '.join(extra_columns)}")
        return False

    return True


def check_all_structures(engine: Engine) -> dict[str, bool]:
    """Проверить структуру всех таблиц."""
    expected_tables = get_expected_tables()
    results = {}

    print("\n" + "=" * 80)
    print("ПРОВЕРКА СТРУКТУРЫ ТАБЛИЦ")
    print("=" * 80)

    for table_name, model_class in expected_tables.items():
        is_valid = check_table_structure(engine, table_name, model_class)
        results[table_name] = is_valid
        status = "[OK]" if is_valid else "[WARNING]"
        print(f"{status} {table_name:30} структура {'корректна' if is_valid else 'НЕ совпадает'}")

    invalid_tables = [t for t, is_valid in results.items() if not is_valid]
    if invalid_tables:
        print(f"\n[WARNING] Таблицы с несовпадением структуры: {', '.join(invalid_tables)}")
    else:
        print("\n[OK] Все структуры таблиц корректны!")

    return results


def check_table_usage() -> dict[str, list[str]]:
    """Проверить использование таблиц в сервисах."""
    import os
    import re

    services_dir = project_root / "bot" / "services"
    usage = {table: [] for table in get_expected_tables().keys()}

    print("\n" + "=" * 80)
    print("ПРОВЕРКА ИСПОЛЬЗОВАНИЯ ТАБЛИЦ В СЕРВИСАХ")
    print("=" * 80)

    for service_file in services_dir.glob("*.py"):
        if service_file.name.startswith("__"):
            continue

        try:
            content = service_file.read_text(encoding="utf-8")

            for table_name in usage.keys():
                # Ищем импорты моделей и использование в коде
                model_name = get_expected_tables()[table_name].__name__

                # Проверяем импорт
                if f"from bot.models import" in content and model_name in content:
                    # Проверяем использование
                    if re.search(rf"\b{model_name}\b", content):
                        usage[table_name].append(service_file.stem)
        except Exception as e:
            print(f"⚠️  Ошибка при проверке {service_file.name}: {e}")

    for table_name, services in usage.items():
        if services:
            print(f"[OK] {table_name:30} используется в: {', '.join(sorted(set(services)))}")
        else:
            print(f"[WARNING] {table_name:30} НЕ используется в сервисах")

    return usage


def check_table_data_counts(engine: Engine) -> dict[str, int]:
    """Проверить количество записей в каждой таблице."""
    expected_tables = get_expected_tables()
    counts = {}

    print("\n" + "=" * 80)
    print("ПРОВЕРКА КОЛИЧЕСТВА ДАННЫХ В ТАБЛИЦАХ")
    print("=" * 80)

    for table_name in expected_tables.keys():
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                count = result.scalar()
                conn.commit()  # Коммитим каждую транзакцию отдельно
                counts[table_name] = count

                status = "[OK]" if count > 0 else "[EMPTY]"
                print(f"{status} {table_name:30} записей: {count}")
        except Exception as e:
            counts[table_name] = -1
            print(f"[ERROR] {table_name:30} ошибка: {e}")

    empty_tables = [t for t, count in counts.items() if count == 0]
    if empty_tables:
        print(f"\n[WARNING] Пустые таблицы (возможно, это нормально): {', '.join(empty_tables)}")

    return counts


def main():
    """Главная функция проверки."""
    import io
    import sys

    # Устанавливаем UTF-8 для вывода
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("ПРОВЕРКА ВСЕХ ТАБЛИЦ БАЗЫ ДАННЫХ\n")

    try:
        # 1. Проверка наличия таблиц
        existence_results = check_tables_exist(engine)

        # 2. Проверка структуры
        structure_results = check_all_structures(engine)

        # 3. Проверка использования
        usage_results = check_table_usage()

        # 4. Проверка данных
        data_counts = check_table_data_counts(engine)

        # Итоговый отчет
        print("\n" + "=" * 80)
        print("ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 80)

        all_exist = all(existence_results.values())
        all_valid = all(structure_results.values())

        if all_exist and all_valid:
            print("[OK] Все проверки пройдены успешно!")
            print(f"   - Все {len(existence_results)} таблиц существуют")
            print(f"   - Все структуры таблиц корректны")
            print(
                f"   - Использование в сервисах: {sum(1 for v in usage_results.values() if v)}/{len(usage_results)}"
            )
            print(
                f"   - Таблицы с данными: {sum(1 for v in data_counts.values() if v > 0)}/{len(data_counts)}"
            )
        else:
            print("[WARNING] Обнаружены проблемы:")
            if not all_exist:
                missing = [t for t, exists in existence_results.items() if not exists]
                print(f"   - Отсутствующие таблицы: {', '.join(missing)}")
            if not all_valid:
                invalid = [t for t, valid in structure_results.items() if not valid]
                print(f"   - Таблицы с неверной структурой: {', '.join(invalid)}")

            return 1

        return 0

    except Exception as e:
        print(f"\n[ERROR] КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
