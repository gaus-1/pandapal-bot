"""Тесты CONTINUE_LEARN_PATTERNS: «решать задачи» и др. считаются продолжением учёбы."""
import re

import pytest

from bot.services.panda_lazy_service import CONTINUE_LEARN_PATTERNS


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
