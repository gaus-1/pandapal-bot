"""Проверка дедупликации повторяющихся абзацев и постобработки ответов."""

import pytest

from bot.services.yandex_ai_response_generator import (
    clean_ai_response,
    fix_glued_words,
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
def test_dedup_numbered_list_duplicates():
    """Повторяющиеся нумерованные пункты с одинаковым содержанием удаляются."""
    text = (
        "1. Определение квадратного корня: число b, такое что b² = a.\n"
        "2. Свойства: √(a×b) = √a × √b.\n"
        "1. Определение квадратного корня: число b, такое что b² = a.\n"
        "3. Метод разложения."
    )
    result = remove_duplicate_text(text, min_length=15)
    assert result.count("Определение квадратного корня") <= 1
    assert "1." in result and "2." in result and "3." in result


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
def test_clean_formula_dedup_and_notation():
    """Дубли блоков «Формула для…» убираются; Delta t → Δt, c x m → c × m; мусор Q_Для обрезается."""
    block = (
        "Формула для расчёта количества теплоты: Q = c x m x Delta t, где: - Q — количество (Дж). "
    )
    wall = (
        "Для решения задач на температуру можно использовать несколько формул. "
        + block * 3
        + "Q_Для решения задач на"
    )
    cleaned = clean_ai_response(wall)
    assert cleaned.count("Формула для расчёта количества теплоты") <= 1
    assert "Δt" in cleaned or "Delta t" not in cleaned
    assert " × " in cleaned or " · " in cleaned
    assert "Q_Для" not in cleaned

@pytest.mark.unit
def test_clean_removes_bracket_placeholders():
    """Удаляются артефакты в скобках: [Кто такой...], [Приложить изображение...]."""
    text = "Пифагор был философом. [Кто такой Пифагор] Он жил в Древней Греции."
    cleaned = clean_ai_response(text)
    assert "[Кто такой" not in cleaned
    assert "Пифагор был" in cleaned


@pytest.mark.unit
def test_clean_fixes_glued_and_duplicate_words():
    """Склейки вершинвершина, результатеером, Рекаких и повтор «факты факты» исправляются."""
    text = (
        "Вершинвершина параболы — это точка. "
        "Некоторые факты факты о Павле I: был убит в результатеером. "
        "Рекаких условиях поток турбулентный."
    )
    cleaned = clean_ai_response(text)
    assert "вершинвершина" not in cleaned
    assert "вершина" in cleaned
    assert "факты факты" not in cleaned
    assert "результатеером" not in cleaned
    assert "результате заговора" in cleaned
    assert "Рекаких" not in cleaned
    assert "Re. При каких" in cleaned or "при каких" in cleaned


@pytest.mark.unit
def test_fix_glued_words_prefix_and_known():
    """Склейки PossPossessive, ПомоПомогает, неодушевлённыхвлённых, построени- остроения исправляются."""
    assert fix_glued_words("PossPossessive Pronouns") == "Possessive Pronouns"
    assert fix_glued_words("ПомоПомогает задавать вопросы.") == "Помогает задавать вопросы."
    assert fix_glued_words("для неодушевлённыхвлённых предметов") == "для неодушевлённых предметов"
    assert fix_glued_words("для построени- остроения вопросов") == "для построения вопросов"


@pytest.mark.unit
def test_clean_ai_response_removes_asterisks():
    """В ответе не остаётся звёздочек: *слово* и **термин** убираются."""
    text = "Личные местоимения: *I* (я), *you* (ты), **ключевой** термин."
    cleaned = clean_ai_response(text)
    assert "*" not in cleaned
    assert "I" in cleaned and "you" in cleaned
    assert "ключевой" in cleaned
