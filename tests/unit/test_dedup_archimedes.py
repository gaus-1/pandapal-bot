"""Проверка дедупликации повторяющихся абзацев и постобработки ответов."""

import pytest

from bot.services.yandex_ai_response_generator import (
    clean_ai_response,
    normalize_bold_spacing,
    remove_duplicate_text,
)


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
    assert cleaned.count("Архимедова сила — это выталкивающая сила") <= 1
    assert len(cleaned) <= len(block) * 2


@pytest.mark.unit
def test_dedup_paragraph_with_prefix():
    """Абзац с лишним префиксом («Книга Вот несколько…») удаляется как дубликат."""
    base = (
        "Вот несколько простых предложений на французском. "
        "Первое. Второе. Третье предложение для примера."
    )
    with_prefix = "Книга " + base
    text = base + "\n\n" + with_prefix
    result = remove_duplicate_text(text, min_length=15)
    assert result.count("Вот несколько простых предложений") <= 1
    assert "Книга Вот несколько" not in result or result.count("Книга") == 0


@pytest.mark.unit
def test_normalize_bold_spacing():
    """Пробелы вокруг ** вставляются для отображения жирного."""
    assert normalize_bold_spacing("слово**термин**") == "слово ** термин **"
    assert normalize_bold_spacing("уже **норм** текст") == "уже ** норм ** текст"
    assert normalize_bold_spacing("без жирного") == "без жирного"


@pytest.mark.unit
def test_clean_removes_bracket_placeholders():
    """Удаляются артефакты в скобках: [Кто такой...], [Приложить изображение...]."""
    text = "Пифагор был философом. [Кто такой Пифагор] Он жил в Древней Греции."
    cleaned = clean_ai_response(text)
    assert "[Кто такой" not in cleaned
    assert "Пифагор был" in cleaned
