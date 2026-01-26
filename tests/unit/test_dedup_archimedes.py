"""Проверка дедупликации повторяющихся абзацев (Archimedes-style)."""

import pytest

from bot.services.yandex_ai_response_generator import clean_ai_response


@pytest.mark.unit
def test_dedup_repeated_paragraphs():
    """Повторяющиеся абзацы удаляются (как в примере с Архимедовой силой)."""
    block = (
        "Архимедова сила — это выталкивающая сила, которая действует на тело, "
        "погружённое в жидкость или газ. Она возникает из-за разности давления. "
        "На Луне ускорение свободного падения меньше. "
        "Проводя опыты, можно сделать заключения: 1. Величина силы будет меньше. "
        "2. Отношение силы к весу тела изменится."
    )
    text = block + "\n\n" + block + "\n\n" + block
    cleaned = clean_ai_response(text)
    # Должен остаться один блок
    assert cleaned.count("Архимедова сила — это выталкивающая сила") <= 1
    assert len(cleaned) <= len(block) * 2  # не больше двух блоков
