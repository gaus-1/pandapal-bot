"""
Утилита для просмотра данных в таблицах PostgreSQL и проверки активности БД.

Использование:
    python scripts/view_database.py                    # Показать статистику по всем таблицам
    python scripts/view_database.py --table users      # Показать данные из таблицы users
    python scripts/view_database.py --table chat_history --limit 10
    python scripts/view_database.py --stats            # Только статистика
    python scripts/view_database.py --activity          # Активность PostgreSQL
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Optional

# Устанавливаем UTF-8 для Windows консоли
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception as e:
        # Игнорируем ошибки конфигурации кодировки на старых системах
        pass  # noqa: S110

from sqlalchemy import func, inspect, text
from tabulate import tabulate

# Добавляем корневую директорию в путь
sys.path.insert(0, ".")

from bot.database import engine, get_db
from bot.models import (
    AnalyticsAlert,
    AnalyticsConfig,
    AnalyticsMetric,
    AnalyticsReport,
    AnalyticsTrend,
    ChatHistory,
    LearningSession,
    User,
    UserEvent,
    UserProgress,
    UserSession,
)


def get_table_stats():
    """Получить статистику по всем таблицам"""
    print("=" * 80)
    print("📊 СТАТИСТИКА ПО ТАБЛИЦАМ")
    print("=" * 80)
    print()

    with get_db() as db:
        tables = [
            ("users", User),
            ("chat_history", ChatHistory),
            ("learning_sessions", LearningSession),
            ("user_progress", UserProgress),
            ("analytics_metrics", AnalyticsMetric),
            ("user_sessions", UserSession),
            ("user_events", UserEvent),
            ("analytics_reports", AnalyticsReport),
            ("analytics_trends", AnalyticsTrend),
            ("analytics_alerts", AnalyticsAlert),
            ("analytics_config", AnalyticsConfig),
        ]

        stats_data = []
        for table_name, model in tables:
            try:
                count = db.query(func.count(model.id)).scalar() or 0
                stats_data.append([table_name, count])
            except Exception as e:
                stats_data.append([table_name, f"Ошибка: {e}"])

        print(tabulate(stats_data, headers=["Таблица", "Записей"], tablefmt="grid"))
        print()


def show_table_data(table_name: str, limit: int = 20):
    """Показать данные из таблицы"""
    print("=" * 80)
    print(f"📋 ДАННЫЕ ИЗ ТАБЛИЦЫ: {table_name}")
    print("=" * 80)
    print()

    with get_db() as db:
        table_map = {
            "users": User,
            "chat_history": ChatHistory,
            "learning_sessions": LearningSession,
            "user_progress": UserProgress,
            "analytics_metrics": AnalyticsMetric,
            "user_sessions": UserSession,
            "user_events": UserEvent,
            "analytics_reports": AnalyticsReport,
            "analytics_trends": AnalyticsTrend,
            "analytics_alerts": AnalyticsAlert,
            "analytics_config": AnalyticsConfig,
        }

        if table_name not in table_map:
            print(f"❌ Таблица '{table_name}' не найдена")
            print(f"Доступные таблицы: {', '.join(table_map.keys())}")
            return

        model = table_map[table_name]
        records = db.query(model).limit(limit).all()

        if not records:
            print(f"⚠️  В таблице '{table_name}' нет данных")
            return

        # Форматируем данные для вывода
        if table_name == "users":
            data = []
            for r in records:
                data.append(
                    [
                        r.id,
                        r.telegram_id,
                        r.first_name or "-",
                        r.username or "-",
                        r.user_type,
                        r.age or "-",
                        r.grade or "-",
                        r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "-",
                        "✅" if r.is_active else "❌",
                    ]
                )
            print(
                tabulate(
                    data,
                    headers=[
                        "ID",
                        "Telegram ID",
                        "Имя",
                        "Username",
                        "Тип",
                        "Возраст",
                        "Класс",
                        "Создан",
                        "Активен",
                    ],
                    tablefmt="grid",
                )
            )

        elif table_name == "chat_history":
            data = []
            for r in records:
                preview = (
                    r.message_text[:50] + "..." if len(r.message_text) > 50 else r.message_text
                )
                data.append(
                    [
                        r.id,
                        r.user_telegram_id,
                        r.message_type,
                        preview,
                        r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "-",
                    ]
                )
            print(
                tabulate(
                    data,
                    headers=["ID", "User ID", "Тип", "Сообщение", "Время"],
                    tablefmt="grid",
                )
            )

        elif table_name == "learning_sessions":
            data = []
            for r in records:
                data.append(
                    [
                        r.id,
                        r.user_telegram_id,
                        r.subject or "-",
                        r.topic or "-",
                        r.questions_answered,
                        r.correct_answers,
                        r.session_start.strftime("%Y-%m-%d %H:%M") if r.session_start else "-",
                        "✅" if r.is_completed else "❌",
                    ]
                )
            print(
                tabulate(
                    data,
                    headers=[
                        "ID",
                        "User ID",
                        "Предмет",
                        "Тема",
                        "Вопросов",
                        "Правильно",
                        "Начало",
                        "Завершена",
                    ],
                    tablefmt="grid",
                )
            )

        elif table_name == "analytics_metrics":
            data = []
            for r in records:
                data.append(
                    [
                        r.id,
                        r.metric_name,
                        r.metric_value,
                        r.metric_type,
                        r.period,
                        r.user_telegram_id or "-",
                        r.timestamp.strftime("%Y-%m-%d %H:%M") if r.timestamp else "-",
                    ]
                )
            print(
                tabulate(
                    data,
                    headers=["ID", "Метрика", "Значение", "Тип", "Период", "User ID", "Время"],
                    tablefmt="grid",
                )
            )

        else:
            # Общий формат для остальных таблиц
            data = []
            for r in records:
                row = []
                for col in inspect(model).columns:
                    value = getattr(r, col.name, None)
                    if isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M")
                    elif value is None:
                        value = "-"
                    elif isinstance(value, (dict, list)):
                        value = str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
                    row.append(str(value)[:50] if len(str(value)) > 50 else str(value))
                data.append(row)

            headers = [col.name for col in inspect(model).columns]
            print(tabulate(data, headers=headers, tablefmt="grid"))

        print(f"\n📊 Показано {len(records)} записей (лимит: {limit})")


def show_database_activity():
    """Показать активность PostgreSQL"""
    print("=" * 80)
    print("🔍 АКТИВНОСТЬ POSTGRESQL")
    print("=" * 80)
    print()

    with get_db() as db:
        # Размер базы данных
        try:
            result = db.execute(
                text(
                    """
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    pg_database.datname as db_name
                FROM pg_database
                WHERE datname = current_database();
            """
                )
            ).fetchone()
            if result:
                print(f"📦 Размер БД: {result[0]}")
                print(f"📝 Имя БД: {result[1]}")
                print()
        except Exception as e:
            print(f"⚠️  Не удалось получить размер БД: {e}")
            print()

        # Активные подключения
        try:
            result = db.execute(
                text(
                    """
                SELECT
                    count(*) as connections,
                    count(*) FILTER (WHERE state = 'active') as active,
                    count(*) FILTER (WHERE state = 'idle') as idle
                FROM pg_stat_activity
                WHERE datname = current_database();
            """
                )
            ).fetchone()
            if result:
                print(
                    f"🔗 Подключений: {result[0]} (активных: {result[1]}, простаивающих: {result[2]})"
                )
                print()
        except Exception as e:
            print(f"⚠️  Не удалось получить статистику подключений: {e}")
            print()

        # Размеры таблиц
        try:
            result = db.execute(
                text(
                    """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10;
            """
                )
            ).fetchall()

            if result:
                print("📊 Размеры таблиц (топ-10):")
                data = [[r[1], r[2]] for r in result]
                print(tabulate(data, headers=["Таблица", "Размер"], tablefmt="grid"))
                print()
        except Exception as e:
            print(f"⚠️  Не удалось получить размеры таблиц: {e}")
            print()

        # Последние операции
        try:
            result = db.execute(
                text(
                    """
                SELECT
                    schemaname,
                    relname as tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    last_vacuum,
                    last_autovacuum
                FROM pg_stat_user_tables
                ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
                LIMIT 10;
            """
                )
            ).fetchall()

            if result:
                print("📈 Статистика операций (топ-10):")
                data = []
                for r in result:
                    data.append(
                        [
                            r[1],
                            r[3] or 0,  # inserts
                            r[4] or 0,  # updates
                            r[5] or 0,  # deletes
                            r[6] or 0,  # live_rows
                        ]
                    )
                print(
                    tabulate(
                        data,
                        headers=["Таблица", "INSERT", "UPDATE", "DELETE", "Строк"],
                        tablefmt="grid",
                    )
                )
                print()
        except Exception as e:
            print(f"⚠️  Не удалось получить статистику операций: {e}")
            print()

        # Проверка подключения (в новой транзакции)
        try:
            # Используем новое подключение для проверки версии
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT version(), current_database(), current_user;")
                ).fetchone()
                if result:
                    print("✅ Подключение активно")
                    print(f"   PostgreSQL: {result[0].split(',')[0]}")
                    print(f"   БД: {result[1]}")
                    print(f"   Пользователь: {result[2]}")
        except Exception as e:
            print(f"⚠️  Не удалось получить версию PostgreSQL: {e}")


def show_recent_activity(hours: int = 24):
    """Показать недавнюю активность"""
    print("=" * 80)
    print(f"⏰ АКТИВНОСТЬ ЗА ПОСЛЕДНИЕ {hours} ЧАСОВ")
    print("=" * 80)
    print()

    with get_db() as db:
        since = datetime.now(UTC) - timedelta(hours=hours)

        # Новые пользователи
        new_users = db.query(User).filter(User.created_at >= since).count()
        print(f"👤 Новых пользователей: {new_users}")

        # Новые сообщения
        new_messages = db.query(ChatHistory).filter(ChatHistory.timestamp >= since).count()
        print(f"💬 Новых сообщений: {new_messages}")

        # Новые метрики
        new_metrics = db.query(AnalyticsMetric).filter(AnalyticsMetric.timestamp >= since).count()
        print(f"📊 Новых метрик: {new_metrics}")

        # Новые события
        new_events = db.query(UserEvent).filter(UserEvent.timestamp >= since).count()
        print(f"📝 Новых событий: {new_events}")

        print()


def main():
    """Главная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Просмотр данных в PostgreSQL")
    parser.add_argument("--table", type=str, help="Название таблицы для просмотра")
    parser.add_argument("--limit", type=int, default=20, help="Лимит записей (по умолчанию 20)")
    parser.add_argument("--stats", action="store_true", help="Показать только статистику")
    parser.add_argument("--activity", action="store_true", help="Показать активность PostgreSQL")
    parser.add_argument("--recent", type=int, help="Показать активность за N часов")

    args = parser.parse_args()

    try:
        if args.activity:
            show_database_activity()
        elif args.recent:
            show_recent_activity(args.recent)
        elif args.table:
            show_table_data(args.table, args.limit)
        elif args.stats:
            get_table_stats()
        else:
            # По умолчанию показываем статистику
            get_table_stats()
            print()
            show_recent_activity(24)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
