#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для экспорта метрик в CSV/JSON

Использование:
    python scripts/export_metrics.py --format csv --days 7
    python scripts/export_metrics.py --format json --days 30
"""

import json
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

import csv

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import Session, sessionmaker

from bot.config import settings
from bot.models import AnalyticsMetric


def get_db_session() -> Session:
    """Получить сессию БД"""
    engine = create_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def export_to_csv(db: Session, days: int, output_path: Path):
    """Экспорт метрик в CSV"""
    since = datetime.now() - timedelta(days=days)

    metrics = (
        db.query(AnalyticsMetric)
        .filter(AnalyticsMetric.timestamp >= since)
        .order_by(AnalyticsMetric.timestamp.desc())
        .all()
    )

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "metric_name",
                "metric_value",
                "metric_type",
                "period",
                "user_telegram_id",
                "tags",
                "timestamp",
            ]
        )

        for metric in metrics:
            writer.writerow(
                [
                    metric.id,
                    metric.metric_name,
                    metric.metric_value,
                    metric.metric_type,
                    metric.period,
                    metric.user_telegram_id,
                    json.dumps(metric.tags) if metric.tags else "",
                    metric.timestamp.isoformat(),
                ]
            )

    print(f"Экспортировано {len(metrics)} записей в {output_path}")


def export_to_json(db: Session, days: int, output_path: Path):
    """Экспорт метрик в JSON"""
    since = datetime.now() - timedelta(days=days)

    metrics = (
        db.query(AnalyticsMetric)
        .filter(AnalyticsMetric.timestamp >= since)
        .order_by(AnalyticsMetric.timestamp.desc())
        .all()
    )

    data = {
        "export_date": datetime.now().isoformat(),
        "period_days": days,
        "total_records": len(metrics),
        "metrics": [
            {
                "id": metric.id,
                "metric_name": metric.metric_name,
                "metric_value": metric.metric_value,
                "metric_type": metric.metric_type,
                "period": metric.period,
                "user_telegram_id": metric.user_telegram_id,
                "tags": metric.tags,
                "timestamp": metric.timestamp.isoformat(),
            }
            for metric in metrics
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Экспортировано {len(metrics)} записей в {output_path}")


def main():
    """Главная функция"""
    parser = ArgumentParser(description="Экспорт бизнес-метрик PandaPal")
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Формат экспорта",
    )
    parser.add_argument("--days", type=int, default=7, help="Количество дней для экспорта")
    parser.add_argument(
        "--output",
        type=str,
        help="Путь к файлу вывода (по умолчанию: metrics/exports/metrics_YYYYMMDD.format)",
    )

    args = parser.parse_args()

    # Определяем путь вывода
    if args.output:
        output_path = Path(args.output)
    else:
        metrics_dir = root_dir / "metrics" / "exports"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        ext = args.format
        output_path = metrics_dir / f"metrics_{date_str}.{ext}"

    try:
        db = get_db_session()

        if args.format == "csv":
            export_to_csv(db, args.days, output_path)
        else:
            export_to_json(db, args.days, output_path)

        db.close()

    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
