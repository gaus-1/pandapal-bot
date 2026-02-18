"""Тесты CONTINUE_LEARN_PATTERNS, REFUSE_PLAY_PATTERNS и порогов отдыха в panda_lazy_service."""

import pytest

from bot.services.panda_lazy_service import (
    CONTINUE_LEARN_PATTERNS,
    PandaLazyService,
    REFUSE_PLAY_PATTERNS,
)


@pytest.mark.parametrize(
    "message,expected",
    [
        ("Давай решать задачи", True),
        ("решать задачи по геометрии", True),
        ("не хочу играть", True),
        ("хочу учиться", True),
        ("давай учиться", True),
        ("хочу играть", False),
        ("поиграем", False),
    ],
)
def test_continue_learn_patterns(message: str, expected: bool) -> None:
    """Сообщения про учёбу/задачи должны совпадать с CONTINUE_LEARN."""
    got = bool(CONTINUE_LEARN_PATTERNS.search(message))
    assert got == expected, f"{message!r} -> {got}, expected {expected}"


@pytest.mark.parametrize(
    "message,expected",
    [
        ("Нет", True),
        ("нет", True),
        ("Не хочу", True),
        ("не сейчас", True),
        ("потом", True),
        ("не надо", True),
        ("Не буду играть", True),
        ("да", False),
        ("давай поиграем", False),
        ("хочу играть", False),
    ],
)
def test_refuse_play_patterns(message: str, expected: bool) -> None:
    """Отказ от игры после предложения «может поиграем?» — не приглашаем в Игры."""
    got = bool(REFUSE_PLAY_PATTERNS.search(message.strip().lower()))
    assert got == expected, f"{message!r} -> {got}, expected {expected}"


def test_rest_offer_after_third_constant() -> None:
    """Третий перерыв задаётся константой REST_OFFER_AFTER_THIRD = 20."""
    assert hasattr(PandaLazyService, "REST_OFFER_AFTER_THIRD")
    assert PandaLazyService.REST_OFFER_AFTER_THIRD == 20


def test_bamboo_video_max_per_day_constant() -> None:
    """Макс. показов видео в сутки — BAMBOO_VIDEO_MAX_PER_DAY = 3."""
    assert hasattr(PandaLazyService, "BAMBOO_VIDEO_MAX_PER_DAY")
    assert PandaLazyService.BAMBOO_VIDEO_MAX_PER_DAY == 3


@pytest.mark.parametrize(
    "message,expected",
    [
        ("поешь", True),
        ("Отдохни", True),
        ("покушай", True),
        ("давай поешь", True),
        ("иди отдохни", True),
        ("съешь бамбук", True),
        ("отдохни немного", True),
        ("сделай перерыв", True),
        ("привет", False),
        ("расскажи про бамбук", False),
        ("не поешь", False),
    ],
)
def test_bamboo_eat_pattern(message: str, expected: bool) -> None:
    """Запросы «поешь»/«отдохни» совпадают с BAMBOO_EAT_PATTERN."""
    from bot.api.miniapp.stream_handlers._routing import BAMBOO_EAT_PATTERN

    got = bool(BAMBOO_EAT_PATTERN.search(message.strip()))
    assert got == expected, f"{message!r} -> {got}, expected {expected}"
