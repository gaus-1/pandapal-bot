"""Тест страховки от сплошного текста: _ensure_paragraph_breaks, _merge_digit_only_lines, clean_ai_response."""

import pytest

from bot.services.yandex_ai_response_generator import (
    _ensure_paragraph_breaks,
    _merge_digit_only_lines,
    clean_ai_response,
)


def test_ensure_paragraph_breaks_adds_newlines_for_long_wall():
    """Длинный текст (>=300 символов) без \\n\\n получает разбивку по предложениям."""
    # Порог 300 символов — иначе _ensure_paragraph_breaks не срабатывает
    wall = (
        "Газ — это одно из четырёх основных агрегатных состояний вещества, которое характеризуется "
        "очень слабыми связями между частицами. Основные характеристики газа: частицы движутся "
        "свободно и хаотично. Газ заполняет весь доступный объём. Идеальный газ — теоретическая "
        "модель, в которой пренебрегают размерами частиц. Реальный газ учитывает взаимодействия. "
        "Давление и температура связаны уравнением состояния."
    )
    assert len(wall) >= 300
    out = _ensure_paragraph_breaks(wall)
    assert "\n\n" in out
    paragraphs = [p.strip() for p in out.split("\n\n") if p.strip()]
    assert len(paragraphs) >= 2


def test_ensure_paragraph_breaks_does_nothing_if_already_has_paragraphs():
    """Текст с абзацами не трогаем."""
    text = "Первый абзац.\n\nВторой абзац."
    assert _ensure_paragraph_breaks(text) == text


def test_ensure_paragraph_breaks_short_text_unchanged():
    """Короткий текст без \\n\\n не меняем."""
    short = "Краткий ответ."
    assert _ensure_paragraph_breaks(short) == short


def test_merge_digit_only_lines_merges_column_of_digits():
    """Строки из одних цифр (1\\n8\\n3) склеиваются в одно число 183."""
    text = "Годы жизни: 1799 —\n1\n8\n3\n7\nВклад в литературу:"
    out = _merge_digit_only_lines(text)
    assert "1\n8\n3\n7" not in out
    assert "1837" in out
    assert "Годы жизни:" in out and "Вклад в литературу:" in out


def test_merge_digit_only_lines_keeps_normal_lines_unchanged():
    """Обычные строки и нумерованные пункты (1. текст) не трогаем."""
    text = "Первый пункт.\n1. Один\n2. Два"
    assert _merge_digit_only_lines(text) == text


def test_merge_digit_only_lines_merges_digit_with_dot_artifact():
    """Артефакт модели 1.\\n8.\\n3. (год) склеивается в 183."""
    text = "Годы жизни: 1799 —\n1.\n8.\n3.\n7\nВклад в литературу:"
    out = _merge_digit_only_lines(text)
    assert "1.\n8.\n3.\n7" not in out
    assert "1837" in out


def test_merge_digit_only_lines_handles_crlf():
    """Строки с \\r не ломают склейку."""
    text = "Даты:\n1\r\n8\r\n3\n7\nТекст"
    out = _merge_digit_only_lines(text)
    assert "1837" in out


def test_clean_ai_response_long_wall_gets_paragraphs():
    """clean_ai_response в конце вызывает _ensure_paragraph_breaks — длинное полотно получает \\n\\n."""
    # Строка заметно длиннее 400 символов, чтобы после любых внутренних замен осталось >= 400
    wall = (
        "Газ — одно из агрегатных состояний вещества. Частицы движутся хаотично в пространстве. "
        "Газ заполняет весь объём сосуда. Идеальный газ — модель без взаимодействий. "
        "Реальный газ учитывает притяжение и отталкивание. Уравнение Клапейрона-Менделеева связывает "
        "давление, объём и температуру. Молярная масса входит в расчёты. Константа R универсальна. "
        "При нормальных условиях один моль газа занимает около 22.4 литра. "
        "Изопроцессы — изотерма, изобара, изохора. Закон Бойля-Мариотта и Гей-Люссака."
    )
    assert len(wall) >= 450
    cleaned = clean_ai_response(wall)
    # Страховка срабатывает при длине >= 300 символов
    assert "\n\n" in cleaned, f"expected paragraph breaks in cleaned ({len(cleaned)} chars)"


def test_clean_ai_response_list_and_bold_breaks():
    """clean_ai_response разбивает длинную строку по маркерам списка (-) и после жирного (**)."""
    long_line = (
        "Основные принципы: - Чем больше масса, тем сильнее притяжение. "
        "- Чем больше расстояние, тем слабее сила. "
        "**Как работает формула:** F = G·(m₁·m₂)/r². Это закон Ньютона."
    )
    assert len(long_line) >= 130
    cleaned = clean_ai_response(long_line)
    # Должны появиться переносы (между пунктами или после **)
    assert "\n" in cleaned
    lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]
    assert len(lines) >= 2, "ожидалась разбивка на несколько строк"


def test_clean_ai_response_degree_symbol():
    """Градусы: 30^circ, 30\\circ, текст 30^circ заменяются на 30°."""
    text = "Упростить sin² 30^circ + cos² 30^circ. Решение: sin² 30^circ + cos² 30^circ = 1."
    cleaned = clean_ai_response(text)
    assert "circ" not in cleaned or "°" in cleaned
    assert "30°" in cleaned


def test_clean_ai_response_duplicate_numbering():
    """Сдвоенная нумерация «5. 6. Текст» заменяется на «6. Текст»."""
    text = "Формулы:\n5. 6. Сумма кубов: a³ + b³ = (a + b)(a² - ab + b²)."
    cleaned = clean_ai_response(text)
    assert "5. 6." not in cleaned
    assert "6." in cleaned
