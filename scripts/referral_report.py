#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Месячный отчёт по реферальной программе (1–30/31 число).

Показывает по каждому рефереру: количество оплат и сумма к выплате за месяц.
Итоговая сумма по всем реферерам. Выплату рефереру вы производите вручную.

Использование:
    python scripts/referral_report.py
    python scripts/referral_report.py --year 2026 --month 2
"""

import calendar
import os
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from bot.config import settings
from bot.models import ReferralPayout, Referrer


def get_db_session() -> Session:
    """Сессия БД (использует DATABASE_URL из env)."""
    url = os.getenv("DATABASE_URL") or os.getenv("database_url") or settings.database_url
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def run_report(year: int, month: int) -> None:
    """Отчёт за календарный месяц (1–30/31)."""
    _, last_day = calendar.monthrange(year, month)
    tz = timezone.utc
    start = datetime(year, month, 1, tzinfo=tz)
    end = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=tz)

    db = get_db_session()
    try:
        # По каждому рефереру: количество оплат и сумма
        stmt = (
            select(
                ReferralPayout.referrer_telegram_id,
                func.count(ReferralPayout.id).label("count"),
                func.sum(ReferralPayout.amount_rub).label("total_rub"),
            )
            .where(
                ReferralPayout.paid_at >= start,
                ReferralPayout.paid_at <= end,
            )
            .group_by(ReferralPayout.referrer_telegram_id)
            .order_by(ReferralPayout.referrer_telegram_id)
        )
        rows = db.execute(stmt).all()

        # Рефереры из whitelist (для комментария)
        referrers = {r.telegram_id: r.comment for r in db.execute(select(Referrer)).scalars().all()}

        print(f"\n=== Реферальный отчёт за {month:02d}.{year} (1–{last_day} число) ===\n")
        if not rows:
            print("Нет оплат по реферальным ссылкам за этот период.\n")
            return

        grand_count = 0
        grand_sum = 0.0
        for referrer_id, count, total_rub in rows:
            total_rub = float(total_rub or 0)
            grand_count += count
            grand_sum += total_rub
            comment = referrers.get(referrer_id) or ""
            print(f"  Реферер {referrer_id}  {comment}")
            print(f"    Оплат: {count}, к выплате: {total_rub:.2f} RUB")
            print()

        print("---")
        print(f"  Всего оплат: {grand_count}, общая сумма к выплате: {grand_sum:.2f} RUB\n")
    finally:
        db.close()


def main() -> None:
    parser = ArgumentParser(description="Месячный отчёт по реферальной программе (1–30/31)")
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year,
        help="Год (по умолчанию текущий)",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=datetime.now().month,
        help="Месяц (по умолчанию текущий)",
    )
    args = parser.parse_args()
    if not (1 <= args.month <= 12):
        print("Месяц должен быть от 1 до 12")
        sys.exit(1)
    run_report(args.year, args.month)


if __name__ == "__main__":
    main()
