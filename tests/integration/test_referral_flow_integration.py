"""
Интеграционный тест полного пути реферальной программы.

Проверяет: реферер в whitelist -> пользователь с ref -> оплата -> referral_payouts ->
отчёт за месяц (1–30). Использует реальную БД (sqlite или PostgreSQL из env).
"""

import calendar
import os
import tempfile
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from bot.config import settings
from bot.models import Base, ReferralPayout, Referrer, User
from bot.services.referral_service import resolve_referrer_telegram_id
from bot.services.user_service import UserService


@pytest.fixture(scope="function")
def real_db_session():
    """Сессия БД (sqlite для изоляции, или PostgreSQL из env)."""
    db_url = os.getenv("DATABASE_URL") or os.getenv("database_url")
    use_sqlite = not (db_url and "postgresql" in db_url)
    if use_sqlite:
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
    else:
        if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        engine = create_engine(db_url, echo=False)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()
    if use_sqlite:
        os.close(db_fd)
        os.unlink(db_path)


def test_referral_full_path(real_db_session):
    """Полный путь: referrer -> user с ref -> payout -> отчёт за месяц."""
    db = real_db_session

    # 1. Реферер в whitelist (get or create — в реальной БД уже есть из миграции)
    existing = db.execute(select(Referrer).where(Referrer.telegram_id == 729414271)).scalar_one_or_none()
    if not existing:
        ref = Referrer(telegram_id=729414271, comment="Преподаватель")
        db.add(ref)
        db.commit()

    # 2. resolve_referrer_telegram_id возвращает id
    assert resolve_referrer_telegram_id(db, "ref_729414271") == 729414271

    # 3. Пользователь создаётся с referrer_telegram_id (уникальный id для изоляции)
    test_telegram_id = 999888777
    user_service = UserService(db)
    user = user_service.get_or_create_user(
        telegram_id=test_telegram_id,
        username="pupil_test",
        first_name="Pupil",
        last_name="One",
        referrer_telegram_id=729414271,
    )
    db.commit()
    assert user.referrer_telegram_id == 729414271

    # 4. Запись в referral_payouts (как при payment.succeeded)
    tz = timezone.utc
    now = datetime.now(tz)
    payment_id = f"test_referral_{uuid.uuid4().hex[:16]}"
    payout = ReferralPayout(
        referrer_telegram_id=729414271,
        user_telegram_id=test_telegram_id,
        payment_id=payment_id,
        amount_rub=float(settings.referral_payout_rub),
        paid_at=now,
    )
    db.add(payout)
    db.commit()

    # 5. Отчёт за месяц: по рефереру 729414271 одна оплата, сумма = referral_payout_rub
    year, month = now.year, now.month
    _, last_day = calendar.monthrange(year, month)
    stmt = (
        select(
            ReferralPayout.referrer_telegram_id,
            func.count(ReferralPayout.id).label("count"),
            func.sum(ReferralPayout.amount_rub).label("total_rub"),
        )
        .where(
            ReferralPayout.paid_at >= datetime(year, month, 1, tzinfo=tz),
            ReferralPayout.paid_at
            <= datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=tz),
        )
        .group_by(ReferralPayout.referrer_telegram_id)
    )
    row = db.execute(stmt).one()
    assert row.referrer_telegram_id == 729414271
    assert row.count >= 1
    assert float(row.total_rub) >= float(settings.referral_payout_rub)
