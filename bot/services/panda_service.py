"""
Сервис питомца-панды (тамагочи).

Логика: decay по времени, выбор состояния для отображения, feed/play/sleep.
Один питомец на пользователя. SOLID: один класс — одна ответственность.
"""

from datetime import UTC, datetime
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from bot.models import PandaPet

MIN_STAT = 5
MAX_STAT = 100
HUNGER_DECAY_PER_HOUR = 15
MOOD_DECAY_PER_2H = 10
ENERGY_DECAY_PER_HOUR = 10
FEED_MAX_PER_HOUR = 2
FEED_HUNGER_BONUS = 35
PLAY_MOOD_BONUS = 30
PLAY_ENERGY_COST = 5
SLEEP_ENERGY_FULL = 100
SLEEP_REQUIRES_FED_WITHIN_MINUTES = 30
AUTO_SLEEP_NO_PLAY_HOURS = 1
AUTO_SLEEP_NO_FED_HOURS = 1
JUST_ACTION_MINUTES = 5
VISIT_DAY_STREAK_HOURS = 20

DISPLAY_STATES = (
    "sleeping",
    "sleepy",
    "offended",
    "questioning",
    "hungry",
    "wants_bamboo",
    "full",
    "played",
    "eating",
    "excited",
    "happy",
    "bored",
    "sad",
    "no_bamboo",
    "neutral",
)

ACHIEVEMENTS_DEF = [
    {"id": "first_feed", "title": "Первое кормление", "condition": "total_fed_count >= 1"},
    {"id": "first_play", "title": "Первая игра", "condition": "total_played_count >= 1"},
    {"id": "fed_10", "title": "Заботливый хозяин", "condition": "total_fed_count >= 10"},
    {"id": "played_10", "title": "Друг панды", "condition": "total_played_count >= 10"},
    {"id": "visit_7_days", "title": "Верный друг", "condition": "consecutive_visit_days >= 7"},
    {"id": "panda_happy", "title": "Панда счастлива", "condition": "all_bars_high"},
    {"id": "early_care", "title": "Ранняя пташка", "condition": "fed_and_played_same_day"},
    {"id": "week_friend", "title": "Неделя вместе", "condition": "consecutive_visit_days >= 5"},
]


def get_or_create_pet(db: Session, telegram_id: int) -> PandaPet:
    """Получить или создать питомца для пользователя."""
    pet = db.query(PandaPet).filter(PandaPet.user_telegram_id == telegram_id).first()
    if pet is not None:
        return pet
    pet = PandaPet(
        user_telegram_id=telegram_id,
        hunger=60,
        mood=70,
        energy=50,
        achievements=[],
    )
    db.add(pet)
    db.flush()
    logger.info(f"🐼 Создан питомец для user={telegram_id}")
    return pet


def _clamp(value: int, low: int = MIN_STAT, high: int = MAX_STAT) -> int:
    return max(low, min(high, value))


def _hours_since(dt: datetime | None, now: datetime) -> float:
    if dt is None:
        return 999.0
    delta = now - dt.replace(tzinfo=dt.tzinfo or UTC)
    return delta.total_seconds() / 3600.0


def _apply_decay(pet: PandaPet, now: datetime) -> None:
    """Применить decay к голоду и настроению. Сбрасывает счётчик кормлений по новому часу."""
    hours_since_update = _hours_since(pet.updated_at, now)
    if hours_since_update <= 0:
        return

    pet.hunger = _clamp(pet.hunger - int(HUNGER_DECAY_PER_HOUR * hours_since_update))
    pet.mood = _clamp(pet.mood - int(MOOD_DECAY_PER_2H * (hours_since_update / 2)))
    pet.energy = _clamp(pet.energy - int(ENERGY_DECAY_PER_HOUR * hours_since_update))

    if pet.feed_hour_start_at is not None:
        h_since = _hours_since(pet.feed_hour_start_at, now)
        if h_since >= 1:
            pet.feed_count_since_hour_start = 0
            pet.feed_hour_start_at = now
    pet.updated_at = now


def _compute_display_state(pet: PandaPet, now: datetime) -> str:
    """Выбор состояния для отображения по приоритету."""
    h_fed = _hours_since(pet.last_fed_at, now)
    h_played = _hours_since(pet.last_played_at, now)
    h_slept = _hours_since(pet.last_slept_at, now)
    last_visit = pet.last_visit_date
    h_visit = _hours_since(last_visit, now) if last_visit else 999.0

    just_fed = h_fed * 60 <= JUST_ACTION_MINUTES
    just_played = h_played * 60 <= JUST_ACTION_MINUTES
    auto_sleeping = (
        h_played >= AUTO_SLEEP_NO_PLAY_HOURS
        and h_fed >= AUTO_SLEEP_NO_FED_HOURS
        and pet.energy < 40
    )
    slept_recently = h_slept < 0.5

    if auto_sleeping and not just_fed:
        return "sleeping"
    if pet.energy <= 25 and not slept_recently:
        return "sleepy"
    if pet.mood <= 10 or (pet.mood <= 25 and h_visit > 24):
        return "offended"
    if h_visit > 24 and pet.mood > 25 and pet.hunger > 30:
        return "questioning"
    if pet.hunger <= 25:
        return "hungry"
    if pet.hunger <= 50 and not just_fed:
        return "wants_bamboo"
    if just_fed:
        return "full"
    if just_played:
        return "played"
    if pet.hunger <= 60 and just_fed:
        return "eating"
    if pet.hunger >= 70 and pet.mood >= 70 and pet.energy >= 50 and h_visit < 0.1:
        return "excited"
    if pet.mood >= 60 and pet.hunger >= 50:
        return "happy"
    if pet.mood <= 45:
        return "bored"
    if pet.mood <= 25 or pet.hunger <= 25:
        return "sad"
    if pet.feed_count_since_hour_start >= FEED_MAX_PER_HOUR and pet.hunger < 80:
        return "no_bamboo"
    return "neutral"


def _update_visit_streak(pet: PandaPet, now: datetime) -> None:
    """Обновить серию посещений по дням."""
    today = now.date()
    if pet.last_visit_date is None:
        pet.consecutive_visit_days = 1
        pet.last_visit_date = now
        return
    last = pet.last_visit_date.date()
    if last == today:
        return
    delta_days = (today - last).days
    if delta_days == 1:
        pet.consecutive_visit_days = (pet.consecutive_visit_days or 0) + 1
    else:
        pet.consecutive_visit_days = 1
    pet.last_visit_date = now


def _evaluate_achievements(pet: PandaPet) -> list[str]:
    """Вернуть список id достижений, которые выполнены."""
    unlocked: list[str] = []
    seen = set(pet.achievements or [])

    for ach in ACHIEVEMENTS_DEF:
        aid = ach["id"]
        if aid in seen:
            continue
        cond = ach["condition"]
        if (
            (
                cond == "total_fed_count >= 1"
                and (pet.total_fed_count or 0) >= 1
                or cond == "total_played_count >= 1"
                and (pet.total_played_count or 0) >= 1
                or cond == "total_fed_count >= 10"
                and (pet.total_fed_count or 0) >= 10
                or cond == "total_played_count >= 10"
                and (pet.total_played_count or 0) >= 10
                or cond == "consecutive_visit_days >= 7"
                and (pet.consecutive_visit_days or 0) >= 7
                or cond == "consecutive_visit_days >= 5"
                and (pet.consecutive_visit_days or 0) >= 5
            )
            or cond == "all_bars_high"
            and (pet.hunger >= 80 and pet.mood >= 80 and pet.energy >= 80)
            or (
                cond == "fed_and_played_same_day"
                and pet.last_fed_at
                and pet.last_played_at
                and pet.last_fed_at.date() == pet.last_played_at.date()
            )
        ):
            unlocked.append(aid)

    return unlocked


def get_state(db: Session, telegram_id: int) -> dict[str, Any]:
    """
    Текущее состояние панды: шкалы, display_state, достижения, флаги действий.

    Пересчитывает decay и визит-стрик, обновляет достижения.
    """
    now = datetime.now(UTC)
    pet = get_or_create_pet(db, telegram_id)
    _apply_decay(pet, now)
    _update_visit_streak(pet, now)

    new_achievements = _evaluate_achievements(pet)
    if new_achievements:
        current = list(pet.achievements or [])
        for aid in new_achievements:
            if aid not in current:
                current.append(aid)
        pet.achievements = current

    db.flush()

    can_feed = True
    if pet.feed_hour_start_at is not None:
        h = _hours_since(pet.feed_hour_start_at, now)
        if h < 1 and (pet.feed_count_since_hour_start or 0) >= FEED_MAX_PER_HOUR:
            can_feed = False

    need_feed_for_sleep = (
        _hours_since(pet.last_fed_at, now) * 60 > SLEEP_REQUIRES_FED_WITHIN_MINUTES
    )

    display_state = _compute_display_state(pet, now)
    achievements_list = [
        {"id": a["id"], "title": a["title"]}
        for a in ACHIEVEMENTS_DEF
        if a["id"] in (pet.achievements or [])
    ]

    return {
        "hunger": pet.hunger,
        "mood": pet.mood,
        "energy": pet.energy,
        "display_state": display_state,
        "achievements": achievements_list,
        "can_feed": can_feed,
        "can_play": True,
        "sleep_need_feed_first": need_feed_for_sleep,
        "total_fed_count": pet.total_fed_count or 0,
        "total_played_count": pet.total_played_count or 0,
        "consecutive_visit_days": pet.consecutive_visit_days or 0,
    }


def feed(db: Session, telegram_id: int) -> dict[str, Any]:
    """Покормить панду. Не чаще 2 раз в час."""
    now = datetime.now(UTC)
    pet = get_or_create_pet(db, telegram_id)
    _apply_decay(pet, now)

    if pet.feed_hour_start_at is None:
        pet.feed_hour_start_at = now
    h_since = _hours_since(pet.feed_hour_start_at, now)
    if h_since >= 1:
        pet.feed_count_since_hour_start = 0
        pet.feed_hour_start_at = now
        h_since = 0

    if pet.feed_count_since_hour_start >= FEED_MAX_PER_HOUR:
        return {
            "success": False,
            "message": "no_bamboo",
            "state": get_state(db, telegram_id),
        }

    pet.feed_count_since_hour_start = pet.feed_count_since_hour_start + 1
    pet.last_fed_at = now
    pet.hunger = _clamp((pet.hunger or 0) + FEED_HUNGER_BONUS)
    pet.energy = _clamp((pet.energy or 0) + 15)
    pet.total_fed_count = (pet.total_fed_count or 0) + 1
    pet.updated_at = now
    db.flush()

    return {"success": True, "message": "full", "state": get_state(db, telegram_id)}


def play(db: Session, telegram_id: int) -> dict[str, Any]:
    """Поиграть с пандой."""
    now = datetime.now(UTC)
    pet = get_or_create_pet(db, telegram_id)
    _apply_decay(pet, now)

    pet.last_played_at = now
    pet.mood = _clamp((pet.mood or 0) + PLAY_MOOD_BONUS)
    pet.energy = _clamp((pet.energy or 0) - PLAY_ENERGY_COST)
    pet.total_played_count = (pet.total_played_count or 0) + 1
    pet.updated_at = now
    db.flush()

    return {"success": True, "message": "played", "state": get_state(db, telegram_id)}


def put_to_sleep(db: Session, telegram_id: int) -> dict[str, Any]:
    """Уложить спать. Панда согласна только после еды."""
    now = datetime.now(UTC)
    pet = get_or_create_pet(db, telegram_id)
    _apply_decay(pet, now)

    need_feed = _hours_since(pet.last_fed_at, now) * 60 > SLEEP_REQUIRES_FED_WITHIN_MINUTES
    if need_feed:
        return {
            "success": False,
            "need_feed_first": True,
            "message": "wants_bamboo",
            "state": get_state(db, telegram_id),
        }

    pet.last_slept_at = now
    pet.energy = SLEEP_ENERGY_FULL
    pet.updated_at = now
    db.flush()

    return {"success": True, "message": "sleeping", "state": get_state(db, telegram_id)}


def get_users_with_sad_or_hungry_panda(db: Session) -> list[int]:
    """Список user_telegram_id, у которых панда грустная или голодная (для напоминаний)."""
    threshold = 35
    now = datetime.now(UTC)
    pets = db.query(PandaPet).all()
    result = []
    for pet in pets:
        _apply_decay(pet, now)
        if (pet.hunger or 0) <= threshold or (pet.mood or 0) <= threshold:
            result.append(pet.user_telegram_id)
    return result
