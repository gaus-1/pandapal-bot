"""
Сервис виртуального питомца «Моя панда» (тамагочи).

Управление состоянием панды: голод, настроение, энергия;
лимиты на кормление/игру/сон; достижения.
"""

from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.models import PandaPet, User


def _as_datetime(value: datetime | str | None) -> datetime | None:
    """Нормализация datetime из БД (SQLite может вернуть строку или naive datetime)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    return None


# Лимиты и константы (один конфиг в сервисе)
FEED_COOLDOWN_MINUTES = 30
FEED_HUNGER_DELTA = 25
PLAY_MOOD_DELTA = 20
PLAY_ENERGY_COST = 10
SLEEP_ENERGY_DELTA = 30
MIN_PLAY_INTERVAL_MINUTES = 60
MIN_SLEEP_INTERVAL_MINUTES = 120
TOILET_COOLDOWN_MINUTES = 20
CLIMB_COOLDOWN_MINUTES = 60
FALL_COOLDOWN_MINUTES = 60
ABSENCE_OFFENDED_HOURS = 24
MOOD_OFFENDED_MAX = 65
TOILET_MOOD_DELTA = 15
CLIMB_MOOD_DELTA = 10

# Деградация шкал со временем (единиц в час)
HUNGER_DECAY_PER_HOUR = 5
MOOD_DECAY_PER_HOUR = 3
ENERGY_DECAY_PER_HOUR = 2


class PandaPetService:
    """Сервис для работы с питомцем панды."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, telegram_id: int) -> PandaPet:
        """
        Получить питомца по telegram_id или создать с дефолтами.
        При создании или первом визите за день обновляет consecutive_visit_days и last_visit_date.
        """
        stmt = select(PandaPet).where(PandaPet.user_telegram_id == telegram_id)
        pet = self.db.execute(stmt).scalar_one_or_none()
        today = datetime.now(UTC).date()

        if pet:
            last_visit = _as_datetime(pet.last_visit_date)
            if last_visit is None or last_visit.date() < today:
                yesterday = today - timedelta(days=1)
                if last_visit is not None and last_visit.date() == yesterday:
                    pet.consecutive_visit_days += 1
                else:
                    pet.consecutive_visit_days = 1
                pet.last_visit_date = datetime.now(UTC)
                logger.debug(
                    "Panda visit day updated: user=%s days=%s",
                    telegram_id,
                    pet.consecutive_visit_days,
                )
            return pet

        # Проверяем, что пользователь есть в users
        user_stmt = select(User).where(User.telegram_id == telegram_id)
        if self.db.execute(user_stmt).scalar_one_or_none() is None:
            raise ValueError("User not found")

        pet = PandaPet(
            user_telegram_id=telegram_id,
            consecutive_visit_days=1,
            last_visit_date=datetime.now(UTC),
        )
        self.db.add(pet)
        self.db.flush()
        logger.info("Panda pet created: user=%s", telegram_id)
        return pet

    def _can_feed(self, pet: PandaPet, now: datetime) -> bool:
        """Можно ли кормить: прошло FEED_COOLDOWN_MINUTES с last_fed_at."""
        last = _as_datetime(pet.last_fed_at)
        if last is None:
            return True
        return (now - last).total_seconds() >= FEED_COOLDOWN_MINUTES * 60

    def _can_play(self, pet: PandaPet, now: datetime) -> bool:
        """Можно ли играть: прошло MIN_PLAY_INTERVAL_MINUTES с last_played_at."""
        last = _as_datetime(pet.last_played_at)
        if last is None:
            return True
        return (now - last).total_seconds() >= MIN_PLAY_INTERVAL_MINUTES * 60

    def _can_sleep(self, pet: PandaPet, now: datetime) -> bool:
        """Можно ли уложить спать: прошло MIN_SLEEP_INTERVAL_MINUTES с last_slept_at."""
        last = _as_datetime(pet.last_slept_at)
        if last is None:
            return True
        return (now - last).total_seconds() >= MIN_SLEEP_INTERVAL_MINUTES * 60

    def _can_toilet(self, pet: PandaPet, now: datetime) -> bool:
        """Можно ли «хочет в туалет»: прошло TOILET_COOLDOWN_MINUTES с last_toilet_at."""
        last = _as_datetime(pet.last_toilet_at)
        if last is None:
            return True
        return (now - last).total_seconds() >= TOILET_COOLDOWN_MINUTES * 60

    def _can_climb(self, pet: PandaPet, now: datetime) -> bool:
        """Можно ли «на дерево»: прошло CLIMB_COOLDOWN_MINUTES с last_climb_at."""
        last = _as_datetime(pet.last_climb_at)
        if last is None:
            return True
        return (now - last).total_seconds() >= CLIMB_COOLDOWN_MINUTES * 60

    def _can_fall(self, pet: PandaPet, now: datetime) -> bool:
        """Можно ли «упасть»: прошло FALL_COOLDOWN_MINUTES с last_fall_at."""
        last = _as_datetime(pet.last_fall_at)
        if last is None:
            return True
        return (now - last).total_seconds() >= FALL_COOLDOWN_MINUTES * 60

    def _check_achievements(self, pet: PandaPet) -> None:
        """Проверить и записать достижения питомца."""
        if pet.achievements is None:
            pet.achievements = {}
        achievements = dict(pet.achievements)
        changed = False

        if pet.total_fed_count >= 1 and "first_feed" not in achievements:
            achievements["first_feed"] = True
            changed = True
        if pet.total_played_count >= 1 and "first_play" not in achievements:
            achievements["first_play"] = True
            changed = True
        if pet.total_fed_count >= 10 and "ten_feed" not in achievements:
            achievements["ten_feed"] = True
            changed = True
        if pet.total_played_count >= 10 and "ten_play" not in achievements:
            achievements["ten_play"] = True
            changed = True
        if pet.consecutive_visit_days >= 7 and "week_visit" not in achievements:
            achievements["week_visit"] = True
            changed = True

        if changed:
            pet.achievements = achievements
            logger.debug(
                "Panda achievements updated: user=%s achievements=%s",
                pet.user_telegram_id,
                achievements,
            )

    def _apply_decay(self, pet: PandaPet, now: datetime) -> None:
        """Применить деградацию шкал на основе времени с последнего визита."""
        last_opened = _as_datetime(pet.last_opened_at)
        if last_opened is None:
            return
        hours_passed = (now - last_opened).total_seconds() / 3600
        # Минимальный порог: деградация только после 1 минуты
        if hours_passed < 1 / 60:
            return
        pet.hunger = max(0, int(pet.hunger - HUNGER_DECAY_PER_HOUR * hours_passed))
        pet.mood = max(0, int(pet.mood - MOOD_DECAY_PER_HOUR * hours_passed))
        pet.energy = max(0, int(pet.energy - ENERGY_DECAY_PER_HOUR * hours_passed))

    def get_state(self, telegram_id: int) -> dict:
        """
        Состояние панды для API: hunger, mood, energy, last_*_at,
        can_feed, can_play, can_sleep, consecutive_visit_days, achievements.
        Если пользователь не заходил в тамагочи >= 24 ч, при заходе mood понижается до offended (65).
        Шкалы деградируют со временем.
        """
        pet = self.get_or_create(telegram_id)
        now = datetime.now(UTC)

        # Деградация шкал со временем
        self._apply_decay(pet, now)

        last_opened = _as_datetime(pet.last_opened_at)
        if last_opened is not None and (now - last_opened) >= timedelta(
            hours=ABSENCE_OFFENDED_HOURS
        ):
            pet.mood = min(pet.mood, MOOD_OFFENDED_MAX)
            logger.debug(
                "Panda offended after 24h absence: user=%s mood=%s",
                telegram_id,
                pet.mood,
            )
        pet.last_opened_at = now
        self.db.flush()

        def _iso(dt: datetime | str | None) -> str | None:
            if dt is None:
                return None
            if isinstance(dt, datetime):
                return dt.isoformat()
            return str(dt)

        return {
            "hunger": pet.hunger,
            "mood": pet.mood,
            "energy": pet.energy,
            "last_fed_at": _iso(pet.last_fed_at),
            "last_played_at": _iso(pet.last_played_at),
            "last_slept_at": _iso(pet.last_slept_at),
            "last_toilet_at": _iso(pet.last_toilet_at),
            "last_climb_at": _iso(pet.last_climb_at),
            "last_fall_at": _iso(pet.last_fall_at),
            "can_feed": self._can_feed(pet, now),
            "can_play": self._can_play(pet, now),
            "can_sleep": self._can_sleep(pet, now),
            "can_toilet": self._can_toilet(pet, now),
            "can_climb": self._can_climb(pet, now),
            "can_fall": self._can_fall(pet, now),
            "consecutive_visit_days": pet.consecutive_visit_days,
            "achievements": pet.achievements or {},
        }

    def feed(self, telegram_id: int) -> dict:
        """Покормить панду. Возвращает новое состояние."""
        pet = self.get_or_create(telegram_id)
        now = datetime.now(UTC)

        if not self._can_feed(pet, now):
            raise ValueError("Кормить можно каждые 30 минут")

        # Деградация перед действием (корректный порядок с min/max capping)
        self._apply_decay(pet, now)
        pet.last_opened_at = now

        pet.hunger = min(100, pet.hunger + FEED_HUNGER_DELTA)
        pet.last_fed_at = now
        pet.total_fed_count += 1
        self._check_achievements(pet)
        self.db.flush()
        logger.debug("Panda fed: user=%s hunger=%s", telegram_id, pet.hunger)
        return self.get_state(telegram_id)

    def play(self, telegram_id: int) -> dict:
        """Играть с пандой. Возвращает новое состояние."""
        pet = self.get_or_create(telegram_id)
        now = datetime.now(UTC)

        if not self._can_play(pet, now):
            raise ValueError("Играть можно раз в час")

        self._apply_decay(pet, now)
        pet.last_opened_at = now

        pet.mood = min(100, pet.mood + PLAY_MOOD_DELTA)
        pet.energy = max(0, pet.energy - PLAY_ENERGY_COST)
        pet.last_played_at = now
        pet.total_played_count += 1
        self._check_achievements(pet)
        self.db.flush()
        logger.debug("Panda played: user=%s mood=%s", telegram_id, pet.mood)
        return self.get_state(telegram_id)

    def sleep(self, telegram_id: int) -> dict:
        """Уложить панду спать. Возвращает новое состояние."""
        pet = self.get_or_create(telegram_id)
        now = datetime.now(UTC)

        if not self._can_sleep(pet, now):
            raise ValueError("Укладывать спать можно раз в 2 часа")

        self._apply_decay(pet, now)
        pet.last_opened_at = now

        pet.energy = min(100, pet.energy + SLEEP_ENERGY_DELTA)
        pet.last_slept_at = now
        self._check_achievements(pet)
        self.db.flush()
        logger.debug("Panda slept: user=%s energy=%s", telegram_id, pet.energy)
        return self.get_state(telegram_id)

    def climb(self, telegram_id: int) -> dict:
        """Панда залезла на дерево. Кулдаун 1 час. Возвращает новое состояние."""
        pet = self.get_or_create(telegram_id)
        now = datetime.now(UTC)
        if not self._can_climb(pet, now):
            raise ValueError("На дерево можно раз в час")
        self._apply_decay(pet, now)
        pet.last_opened_at = now
        pet.mood = min(100, pet.mood + CLIMB_MOOD_DELTA)
        pet.last_climb_at = now
        self.db.flush()
        logger.debug("Panda climbed: user=%s mood=%s", telegram_id, pet.mood)
        return self.get_state(telegram_id)

    def fall_from_tree(self, telegram_id: int) -> dict:
        """Панда упала с дерева: настроение падает до «обиженной» (max 65). Кулдаун 1 час. Возвращает новое состояние."""
        pet = self.get_or_create(telegram_id)
        now = datetime.now(UTC)
        if not self._can_fall(pet, now):
            raise ValueError("Упасть можно раз в час")
        self._apply_decay(pet, now)
        pet.last_opened_at = now
        pet.mood = min(pet.mood, MOOD_OFFENDED_MAX)
        pet.last_fall_at = now
        self.db.flush()
        logger.debug("Panda fell from tree: user=%s mood=%s", telegram_id, pet.mood)
        return self.get_state(telegram_id)

    def toilet(self, telegram_id: int) -> dict:
        """Хочет в туалет: кулдаун 20 мин, поднимает настроение (довольная панда). Возвращает новое состояние."""
        pet = self.get_or_create(telegram_id)
        now = datetime.now(UTC)
        if not self._can_toilet(pet, now):
            raise ValueError("Действие доступно раз в 20 минут")
        self._apply_decay(pet, now)
        pet.last_opened_at = now
        pet.last_toilet_at = now
        pet.mood = min(100, pet.mood + TOILET_MOOD_DELTA)
        self.db.flush()
        logger.debug("Panda toilet: user=%s mood=%s", telegram_id, pet.mood)
        return self.get_state(telegram_id)
