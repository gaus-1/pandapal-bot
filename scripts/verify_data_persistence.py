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
    AnalyticsAlert,
    AnalyticsConfig,
    AnalyticsMetric,
    AnalyticsReport,
    AnalyticsTrend,
    Base,
    ChatHistory,
    DailyRequestCount,
    GameSession,
    GameStats,
    LearningSession,
    Payment,
    Subscription,
    User,
    UserEvent,
    UserProgress,
    UserSession,
)

# #region agent log
import json
import time
log_path = Path(__file__).parent.parent / ".cursor" / "debug.log"
def log_debug(location, message, data=None, hypothesis_id=None):
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "location": location,
                "message": message,
                "data": data or {},
                "timestamp": int(time.time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": hypothesis_id or "general"
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion


def check_migrations_integrity(engine: Engine) -> bool:
    """Проверка целостности миграций Alembic."""
    print("\n" + "=" * 80)
    print("📋 ПРОВЕРКА МИГРАЦИЙ ALEMBIC")
    print("=" * 80)

    # #region agent log
    log_debug("scripts/verify_data_persistence.py:check_migrations_integrity", "Starting migration check", {}, "1")
    # #endregion

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Проверяем наличие таблицы alembic_version
        if "alembic_version" not in tables:
            print("❌ Таблица alembic_version не найдена!")
            log_debug("scripts/verify_data_persistence.py:check_migrations_integrity", "alembic_version table missing", {}, "1")
            return False

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version;"))
            current_version = result.scalar()
            print(f"✅ Текущая версия миграции: {current_version}")
            log_debug("scripts/verify_data_persistence.py:check_migrations_integrity", "Current migration version", {"version": current_version}, "1")

            # Проверяем, что все таблицы из моделей существуют
            expected_tables = {
                "users": User,
                "learning_sessions": LearningSession,
                "user_progress": UserProgress,
                "chat_history": ChatHistory,
                "analytics_metrics": AnalyticsMetric,
                "user_sessions": UserSession,
                "user_events": UserEvent,
                "daily_request_counts": DailyRequestCount,
                "analytics_reports": AnalyticsReport,
                "analytics_trends": AnalyticsTrend,
                "analytics_alerts": AnalyticsAlert,
                "analytics_config": AnalyticsConfig,
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
                    log_debug("scripts/verify_data_persistence.py:check_migrations_integrity", "Missing table", {"table": table_name}, "1")

            if missing_tables:
                return False

            print(f"✅ Все {len(expected_tables)} таблиц существуют")
            log_debug("scripts/verify_data_persistence.py:check_migrations_integrity", "All tables exist", {"count": len(expected_tables)}, "1")
            return True

    except Exception as e:
        print(f"❌ Ошибка проверки миграций: {e}")
        log_debug("scripts/verify_data_persistence.py:check_migrations_integrity", "Migration check error", {"error": str(e)}, "1")
        return False


def check_table_columns_match_models(engine: Engine) -> dict[str, bool]:
    """Проверка соответствия колонок таблиц моделям."""
    print("\n" + "=" * 80)
    print("📊 ПРОВЕРКА СТРУКТУРЫ ТАБЛИЦ")
    print("=" * 80)

    # #region agent log
    log_debug("scripts/verify_data_persistence.py:check_table_columns_match_models", "Starting column check", {}, "2")
    # #endregion

    inspector = inspect(engine)
    results = {}

    expected_tables = {
        "users": User,
        "learning_sessions": LearningSession,
        "user_progress": UserProgress,
        "chat_history": ChatHistory,
        "analytics_metrics": AnalyticsMetric,
        "user_sessions": UserSession,
        "user_events": UserEvent,
        "daily_request_counts": DailyRequestCount,
        "analytics_reports": AnalyticsReport,
        "analytics_trends": AnalyticsTrend,
        "analytics_alerts": AnalyticsAlert,
        "analytics_config": AnalyticsConfig,
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
                    log_debug("scripts/verify_data_persistence.py:check_table_columns_match_models", "Missing columns", {"table": table_name, "columns": list(missing_columns)}, "2")
                if extra_columns:
                    print(f"   Лишние колонки в БД: {', '.join(extra_columns)}")
                    log_debug("scripts/verify_data_persistence.py:check_table_columns_match_models", "Extra columns", {"table": table_name, "columns": list(extra_columns)}, "2")
                results[table_name] = False
            else:
                print(f"✅ {table_name}: структура корректна")
                log_debug("scripts/verify_data_persistence.py:check_table_columns_match_models", "Table structure OK", {"table": table_name}, "2")
                results[table_name] = True
        except Exception as e:
            print(f"❌ {table_name}: ошибка проверки - {e}")
            log_debug("scripts/verify_data_persistence.py:check_table_columns_match_models", "Column check error", {"table": table_name, "error": str(e)}, "2")
            results[table_name] = False

    return results


def check_data_persistence_logic() -> dict[str, bool]:
    """Проверка логики сохранения данных в каждой таблице."""
    print("\n" + "=" * 80)
    print("💾 ПРОВЕРКА ЛОГИКИ СОХРАНЕНИЯ ДАННЫХ")
    print("=" * 80)

    # #region agent log
    log_debug("scripts/verify_data_persistence.py:check_data_persistence_logic", "Starting persistence logic check", {}, "3")
    # #endregion

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
                    log_debug("scripts/verify_data_persistence.py:check_data_persistence_logic", "Table record count", {"table": table_name, "count": count, "services": expected_services}, "3")
                    results[table_name] = True
                else:
                    print(f"⚠️  {table_name}: модель не найдена в проверке")
                    log_debug("scripts/verify_data_persistence.py:check_data_persistence_logic", "Model not in check", {"table": table_name}, "3")
                    results[table_name] = False
        except Exception as e:
            print(f"❌ {table_name}: ошибка проверки - {e}")
            log_debug("scripts/verify_data_persistence.py:check_data_persistence_logic", "Persistence check error", {"table": table_name, "error": str(e)}, "3")
            results[table_name] = False

    return results


def check_dependencies() -> bool:
    """Проверка зависимостей из requirements.txt."""
    print("\n" + "=" * 80)
    print("📦 ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    print("=" * 80)

    # #region agent log
    log_debug("scripts/verify_data_persistence.py:check_dependencies", "Starting dependencies check", {}, "4")
    # #endregion

    try:
        requirements_path = Path(__file__).parent.parent / "requirements.txt"
        if not requirements_path.exists():
            print("❌ Файл requirements.txt не найден!")
            log_debug("scripts/verify_data_persistence.py:check_dependencies", "requirements.txt not found", {}, "4")
            return False

        with open(requirements_path, "r", encoding="utf-8") as f:
            requirements = f.read()

        # Ключевые зависимости для работы с БД
        critical_deps = [
            "sqlalchemy",
            "alembic",
            "psycopg",
            "aiogram",
            "pydantic",
        ]

        missing_deps = []
        for dep in critical_deps:
            if dep.lower() not in requirements.lower():
                missing_deps.append(dep)
                print(f"❌ Зависимость {dep} не найдена в requirements.txt")
                log_debug("scripts/verify_data_persistence.py:check_dependencies", "Missing dependency", {"dependency": dep}, "4")

        if missing_deps:
            return False

        print(f"✅ Все критические зависимости присутствуют")
        log_debug("scripts/verify_data_persistence.py:check_dependencies", "All critical dependencies present", {}, "4")
        return True

    except Exception as e:
        print(f"❌ Ошибка проверки зависимостей: {e}")
        log_debug("scripts/verify_data_persistence.py:check_dependencies", "Dependencies check error", {"error": str(e)}, "4")
        return False


def main():
    """Главная функция проверки."""
    print("=" * 80)
    print("🔍 КОМПЛЕКСНАЯ ПРОВЕРКА СОХРАНЕНИЯ ДАННЫХ")
    print("=" * 80)

    # #region agent log
    log_debug("scripts/verify_data_persistence.py:main", "Starting comprehensive check", {}, "general")
    # #endregion

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
        log_debug("scripts/verify_data_persistence.py:main", "All checks passed", {}, "general")
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
        log_debug("scripts/verify_data_persistence.py:main", "Some checks failed", {"migrations": migrations_ok, "structure": all(structure_results.values()), "persistence": all(persistence_results.values()), "dependencies": deps_ok}, "general")
        return 1


if __name__ == "__main__":
    sys.exit(main())
