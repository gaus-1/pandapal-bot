"""
Сервис реферальной программы.

Проверка валидности реферера, парсинг ref-параметра.
Один источник правды для логики реферальных ссылок (Single Responsibility).
"""

import re

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.models import Referrer

REF_PATTERN = re.compile(r"^ref_(\d+)$")


def parse_referrer_from_ref(ref: str | None) -> int | None:
    """
    Извлечь telegram_id реферера из строки ref (например ref_729414271).

    Returns:
        telegram_id реферера или None, если формат неверный.
    """
    if not ref or not ref.strip():
        return None
    ref = ref.strip()
    match = REF_PATTERN.fullmatch(ref)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def is_referrer(db: Session, telegram_id: int) -> bool:
    """Проверить, что telegram_id есть в whitelist рефереров."""
    stmt = select(Referrer).where(Referrer.telegram_id == telegram_id)
    return db.execute(stmt).scalar_one_or_none() is not None


def resolve_referrer_telegram_id(db: Session, ref: str | None) -> int | None:
    """
    Парсинг ref и проверка, что реферер в whitelist.

    Returns:
        telegram_id реферера или None.
    """
    referrer_id = parse_referrer_from_ref(ref)
    if referrer_id is None:
        return None
    if not is_referrer(db, referrer_id):
        logger.warning("Referrer telegram_id=%s not in whitelist", referrer_id)
        return None
    return referrer_id
