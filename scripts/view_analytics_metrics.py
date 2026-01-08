#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для просмотра бизнес-метрик из таблицы analytics_metrics

Использование:
    python scripts/view_analytics_metrics.py
    python scripts/view_analytics_metrics.py --type safety
    python scripts/view_analytics_metrics.py --days 7
"""

import os
import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta
from pathlib import Path

# Устанавливаем UTF-8 для вывода (для Windows)
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Добавляем корневую папку в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import Session, sessionmaker

from bot.config import settings
from bot.models import AnalyticsMetric


def get_db_session() -> Session:
    """Получить сессию БД"""
    engine = create_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def show_safety_metrics(db: Session, days: int = 7):
    """Показать метрики безопасности"""
    since = datetime.now() - timedelta(days=days)

    # Заблокированные сообщения (все типы блокировок)
    blocked = (
        db.query(func.sum(AnalyticsMetric.metric_value))
        .filter(
            AnalyticsMetric.metric_type == "safety",
            AnalyticsMetric.metric_name.in_(["blocked_messages", "blocked_advanced_content"]),
            AnalyticsMetric.timestamp >= since,
        )
        .scalar()
        or 0
    )

    # По категориям (используем PostgreSQL JSONB синтаксис)
    categories_result = db.execute(
        text(
            """
            SELECT
                tags->>'category' as category,
                SUM(metric_value) as count
            FROM analytics_metrics
            WHERE metric_type = :metric_type
              AND (metric_name = 'blocked_messages' OR metric_name = 'blocked_advanced_content')
              AND timestamp >= :since
            GROUP BY tags->>'category'
        """
        ),
        {
            "metric_type": "safety",
            "since": since,
        },
    )
    categories = [(row.category, float(row.count)) for row in categories_result]

    print("\nMETRIKI BEZOPASNOSTI")
    print("=" * 60)
    print(f"Заблокированных сообщений за {days} дней: {int(blocked)}")
    if categories:
        print("\nПо категориям:")
        for cat, count in categories:
            if cat:
                print(f"  • {cat}: {int(count)}")


def show_education_metrics(db: Session, days: int = 7):
    """Показать метрики образования"""
    since = datetime.now() - timedelta(days=days)

    # AI взаимодействия
    ai_interactions = (
        db.query(func.sum(AnalyticsMetric.metric_value))
        .filter(
            AnalyticsMetric.metric_type == "education",
            AnalyticsMetric.metric_name == "ai_interactions",
            AnalyticsMetric.timestamp >= since,
        )
        .scalar()
        or 0
    )

    # Уникальных детей с активностью
    active_children = (
        db.query(func.count(func.distinct(AnalyticsMetric.user_telegram_id)))
        .filter(
            AnalyticsMetric.metric_type == "education",
            AnalyticsMetric.metric_name == "ai_interactions",
            AnalyticsMetric.timestamp >= since,
        )
        .scalar()
        or 0
    )

    print("\nMETRIKI OBRAZOVANIYA")
    print("=" * 60)
    print(f"AI взаимодействий за {days} дней: {int(ai_interactions)}")
    print(f"Активных детей: {active_children}")
    if active_children > 0:
        avg = ai_interactions / active_children
        print(f"Среднее взаимодействий на ребенка: {avg:.1f}")


def show_parent_metrics(db: Session, days: int = 7):
    """Показать метрики родительского контроля"""
    since = datetime.now() - timedelta(days=days)

    # Просмотры дашборда
    dashboard_views = (
        db.query(func.sum(AnalyticsMetric.metric_value))
        .filter(
            AnalyticsMetric.metric_type == "parent",
            AnalyticsMetric.metric_name == "dashboard_views",
            AnalyticsMetric.timestamp >= since,
        )
        .scalar()
        or 0
    )

    # Уникальных родителей
    active_parents = (
        db.query(func.count(func.distinct(AnalyticsMetric.user_telegram_id)))
        .filter(
            AnalyticsMetric.metric_type == "parent",
            AnalyticsMetric.metric_name == "dashboard_views",
            AnalyticsMetric.timestamp >= since,
        )
        .scalar()
        or 0
    )

    print("\nMETRIKI RODITELEY")
    print("=" * 60)
    print(f"Просмотров дашборда за {days} дней: {int(dashboard_views)}")
    print(f"Активных родителей: {active_parents}")


def show_all_metrics(db: Session, days: int = 7):
    """Показать все метрики"""
    since = datetime.now() - timedelta(days=days)

    # Общая статистика
    total_metrics = (
        db.query(func.count(AnalyticsMetric.id)).filter(AnalyticsMetric.timestamp >= since).scalar()
        or 0
    )

    print("\nOBSHCHAYA STATISTIKA METRIK")
    print("=" * 60)
    print(f"Всего записей за {days} дней: {total_metrics}")

    # По типам
    by_type = (
        db.query(
            AnalyticsMetric.metric_type,
            func.count(AnalyticsMetric.id).label("count"),
        )
        .filter(AnalyticsMetric.timestamp >= since)
        .group_by(AnalyticsMetric.metric_type)
        .all()
    )

    if by_type:
        print("\nПо типам:")
        for metric_type, count in by_type:
            print(f"  • {metric_type}: {count}")

    # Показываем детали по типам
    show_safety_metrics(db, days)
    show_education_metrics(db, days)
    show_parent_metrics(db, days)


def main():
    """Главная функция"""
    parser = ArgumentParser(description="Просмотр бизнес-метрик PandaPal")
    parser.add_argument(
        "--type",
        choices=["safety", "education", "parent", "all"],
        default="all",
        help="Тип метрик для отображения",
    )
    parser.add_argument("--days", type=int, default=7, help="Количество дней для анализа")

    args = parser.parse_args()

    print("=" * 60)
    print("PROSMOTR BIZNES-METRIK PANDAPAL")
    print("=" * 60)
    print(f"Период: последние {args.days} дней")
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        db = get_db_session()

        if args.type == "safety":
            show_safety_metrics(db, args.days)
        elif args.type == "education":
            show_education_metrics(db, args.days)
        elif args.type == "parent":
            show_parent_metrics(db, args.days)
        else:
            show_all_metrics(db, args.days)

        print("\n" + "=" * 60)
        print("Gotovo")

        db.close()

    except Exception as e:
        print(f"\nOshibka: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
