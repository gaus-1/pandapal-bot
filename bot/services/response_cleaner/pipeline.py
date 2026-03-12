"""
Главный pipeline очистки и постобработки ответов AI.

Содержит основные точки входа: `clean_ai_response` и `finalize_ai_response`.
Оркестрирует вызовы модулей deduplication, formatting и engagement.
"""

import re

from .deduplication import _remove_duplicate_long_substrings, remove_duplicate_text
from .engagement import (
    _is_farewell_message,
    _is_probably_russian_message,
    add_random_engagement_question,
)
from .formatting import (
    _ensure_list_and_bold_breaks,
    _ensure_paragraph_breaks,
    _merge_definition_split_by_dash,
    _merge_digit_only_lines,
    _strip_invisible_unicode,
    fix_glued_words,
    normalize_bold_spacing,
)


def finalize_ai_response(raw_text: str, user_message: str = "") -> str:
    """
    Единый финальный postprocess:
    - очистка формата/дубликатов
    - модерация ответа AI (защита от галлюцинаций модели)
    - вовлекающий вопрос только для RU-диалога и не в farewell-кейсах
    """
    cleaned = clean_ai_response((raw_text or "").strip())
    if not cleaned:
        return cleaned
    # Модерация ответа: блокируем запрещённый контент, который модель могла сгенерировать
    from bot.services.moderation_service import ContentModerationService

    cleaned = ContentModerationService().sanitize_ai_response(cleaned)
    if _is_farewell_message(user_message):
        return cleaned
    if not _is_probably_russian_message(user_message):
        return cleaned
    return add_random_engagement_question(cleaned)


def clean_ai_response(text: str) -> str:
    """
    Очищает ответ AI от LaTeX, сложных математических символов и повторяющихся фрагментов.
    Сохраняет сравнения (>, <) и знаки препинания.
    Исправляет форматирование таблицы умножения.
    Удаляет дублирующиеся первые слова более агрессивно.
    Исправляет склеенные слова (УПривет, иПрезент).
    """
    if not text:
        return text

    # Невидимые Unicode-символы от модели ломают regex — убираем сразу
    text = _strip_invisible_unicode(text)

    # Исправляем склеенные слова в начале
    text = fix_glued_words(text)

    # Склеиваем строки из одних цифр (1\n8\n3 → 183), убираем «цифры в столбик»
    text = _merge_digit_only_lines(text)

    # Разбивка длинных строк по маркерам списка и после жирного (до дедупликации и финальной нормализации)
    text = _ensure_list_and_bold_breaks(text)

    # Склеиваем случаи, когда определение «**Термин** — это ...» разорвалось на два пункта списка
    text = _merge_definition_split_by_dash(text)

    # Удаляем вставки в квадратных скобках (артефакты модели)
    text = re.sub(r"\[Приложить изображение[^\]]*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[Дай[^\]]*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[(?:Кто такой|Что такое|Кто такая)[^\]]*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[[^\]]{15,}\]", "", text)  # длинные скобки — инструкции/заголовки

    # Удаляем повторяющиеся длинные блоки (стриминг иногда вставляет блок дважды)
    text = _remove_duplicate_long_substrings(text, min_len=70)

    # LaTeX в формулах → типографский стиль: убираем \quad, \text{}, \left/\right
    text = re.sub(r"\\quad\s*", " ", text)
    text = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\left\s*\(\s*", "(", text)
    text = re.sub(r"\s*\\right\s*\)", ")", text)
    text = re.sub(r"\\left\s*\[\s*", "[", text)
    text = re.sub(r"\s*\\right\s*\]", "]", text)
    # Без слэша: left( / right) → ( / )
    text = re.sub(r"\bleft\s*\(\s*", "(", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*right\s*\)", ")", text, flags=re.IGNORECASE)

    # Умножение в формулах: G. и F. между буквами/скобками → G·, F· (не точка как умножение)
    text = re.sub(r"(\bG)\.(\s*)(?=[\(\w])", r"\1·\2", text)
    text = re.sub(r"(\bF)\.(\s*)(?=[\(\w])", r"\1·\2", text)

    # Пробелы вокруг ** для корректного отображения жирного
    text = normalize_bold_spacing(text)

    # Дублированная первая буква в начале предложения (ВВ каком -> В каком)
    text = re.sub(r"(^|[\n.]\s*)([А-Яа-яA-Za-z])\2(\s)", r"\1\2\3", text)

    # Повтор одного и того же слова подряд (факты факты → факты)
    text = re.sub(r"\b(\w{4,})\s+\1\b", r"\1", text)

    # УЛУЧШЕННАЯ ПРОВЕРКА: Удаляем дублирующиеся первые слова
    # Проверяем первые 1-5 слов на дублирование
    words = text.split()
    if len(words) >= 2:
        # Шаг 1: Проверяем, не дублируется ли первое слово целиком
        first_word = words[0].strip()
        # Убираем знаки препинания для сравнения
        first_word_clean = re.sub(r"[^\w]", "", first_word.lower())

        # Проверяем, не дублируется ли первое слово в составе (например, "ЖивуЖиву")
        if len(first_word_clean) >= 4 and len(first_word_clean) % 2 == 0:
            half_len = len(first_word_clean) // 2
            first_half = first_word_clean[:half_len]
            second_half = first_word_clean[half_len:]
            if first_half == second_half:
                # Удаляем дубликат внутри слова
                text = first_word[:half_len] + " " + " ".join(words[1:])
                words = text.split()

        # Шаг 2: Проверяем, не дублируется ли первое слово целиком во втором слове
        if len(words) >= 2:
            second_word_clean = re.sub(r"[^\w]", "", words[1].lower())
            if first_word_clean == second_word_clean:
                # Удаляем дубликат второго слова
                text = " ".join([words[0]] + words[2:])
                words = text.split()

        # Шаг 3: Проверяем дублирование первых 2-5 слов (более агрессивно)
        for word_count in range(5, 1, -1):  # От 5 до 2 слов
            if len(words) >= word_count * 2:
                first_block = " ".join(words[:word_count]).lower()
                # Убираем знаки препинания для сравнения
                first_block_clean = re.sub(r"[^\w\s]", "", first_block)
                next_block_clean = re.sub(
                    r"[^\w\s]", "", " ".join(words[word_count : word_count * 2]).lower()
                )

                if first_block_clean == next_block_clean:
                    # Удаляем дубликат блока
                    text = " ".join(words[:word_count] + words[word_count * 2 :])
                    words = text.split()
                    break

        # Шаг 4: Проверяем повторение первого слова в разных формах
        # Например: "Живу" → "Живу, живу" или "живу Живу"
        if len(words) >= 2:
            first_word_lower = words[0].lower().strip()
            second_word_lower = words[1].lower().strip()
            # Убираем знаки препинания
            first_clean = re.sub(r"[^\w]", "", first_word_lower)
            second_clean = re.sub(r"[^\w]", "", second_word_lower)

            if first_clean == second_clean and first_clean:
                # Удаляем дубликат
                text = " ".join([words[0]] + words[2:])
                words = text.split()

    # Удаляем дубликаты (минимальная длина 15 для ловли повторов типа «Привет! To be — это глагол...»)
    text = remove_duplicate_text(text, min_length=15)

    # Удаляем подряд идущие одинаковые абзацы (точное совпадение после нормализации)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2:
        unique_ordered = [paragraphs[0]]
        for i in range(1, len(paragraphs)):
            prev_norm = re.sub(r"\s+", " ", unique_ordered[-1].lower().strip())
            curr_norm = re.sub(r"\s+", " ", paragraphs[i].lower().strip())
            if curr_norm != prev_norm or len(curr_norm) < 20:
                unique_ordered.append(paragraphs[i])
        text = "\n\n".join(unique_ordered)

    # Фиксим артефакт: знак конца предложения + длинное тире после него (". — текст") → ". текст"
    # Учитываем возможную кавычку/ёлочку сразу после знака (.\\" — ...).\
    text = re.sub(r"([.!?][\"»]?)\s+—\s+", r"\1 ", text)

    # Схлопываем лишние пробелы (не трогаем переводы строк)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Убираем двойной маркер списка: "- - Текст", "• - Текст", "– - Текст", "— - Текст" → "- Текст"
    text = re.sub(r"(^|\n)\s*[-–—•]\s+[-–—]\s+", r"\1- ", text)

    # Артефакты модели: "2dot 6" → "2·6"
    text = re.sub(r"(\d+)dot\s+(\d+)", r"\1·\2", text, flags=re.IGNORECASE)

    # Исправляем форматирование таблицы умножения
    # Паттерн 1: "1. 3 1 = 3" → "1. 3 × 1 = 3" (нумерованные списки - сначала обрабатываем их)
    text = re.sub(r"(\d+\.\s+)(\d+)\s+(\d+)\s*=\s*(\d+)", r"\1\2 × \3 = \4", text)
    # Паттерн 2: "3 1 = 3" → "3 × 1 = 3" (обычные выражения, но не если перед первым числом есть точка)
    text = re.sub(r"(?<!\d\.\s)(?<!\d\.)(\d+)\s+(\d+)\s*=\s*(\d+)", r"\1 × \2 = \3", text)
    # Паттерн 3: "3*3=9" → "3 × 3 = 9"
    text = re.sub(r"(\d+)\*(\d+)\s*=\s*(\d+)", r"\1 × \2 = \3", text)

    # Физика: Delta t / Delta T → Δt / ΔT; в формулах буква x как умножение → ·
    text = re.sub(r"\bDelta\s+t\b", "Δt", text, flags=re.IGNORECASE)
    text = re.sub(r"\bDelta\s+T\b", "ΔT", text)
    # Операнд x операнд (число или идентификатор типа log_a, b, c) → ·
    text = re.sub(
        r"(\b\d+\b|\b[a-zA-Z_][a-zA-Z0-9_]*\b)\s+x\s+(\b\d+\b|\b[a-zA-Z_][a-zA-Z0-9_]*\b)",
        r"\1 · \2",
        text,
    )

    # ФАЗА 1: Убираем $ и LaTeX-артефакты
    text = text.replace("$", "")
    text = text.replace("{,}", ",")  # LaTeX числовая запятая: 9{,}8 → 9,8

    # ФАЗА 2: LaTeX конструкции → типографский стиль
    # Порядок важен: сначала внутренние (\text, \sqrt), потом внешние (\frac)
    text = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\sqrt\s*\{([^}]*)\}", r"√(\1)", text)
    text = re.sub(r"\\vec\s*\{([^}]*)\}", r"\1→", text, flags=re.IGNORECASE)
    text = re.sub(r"\\overline\s*\{([^}]*)\}", r"\1", text)
    # Градусы: \circ, ^\circ, ^{\circ} → ° (до общего сноса LaTeX)
    text = re.sub(r"\^\\circ\b", "°", text)
    text = re.sub(r"\^\{?\\circ\}?", "°", text)
    text = re.sub(r"\\circ\b", "°", text)
    # Текстовый артефакт "circ" после числа (модель иногда выдаёт 30^circ)
    text = re.sub(r"(\d+)\s*\^?\s*circ\b", r"\1°", text, flags=re.IGNORECASE)
    # Дроби (после очистки вложенных конструкций)
    text = re.sub(r"\\frac\s*\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", text)
    text = re.sub(r"\bfrac\s*\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", text)

    # ФАЗА 3: LaTeX команды → Unicode
    _latex_unicode = {
        r"\\nabla": "∇",
        r"\\partial": "∂",
        r"\\alpha": "α",
        r"\\beta": "β",
        r"\\gamma": "γ",
        r"\\delta": "δ",
        r"\\epsilon": "ε",
        r"\\zeta": "ζ",
        r"\\eta": "η",
        r"\\theta": "θ",
        r"\\lambda": "λ",
        r"\\mu": "μ",
        r"\\nu": "ν",
        r"\\xi": "ξ",
        r"\\rho": "ρ",
        r"\\sigma": "σ",
        r"\\tau": "τ",
        r"\\phi": "φ",
        r"\\omega": "ω",
        r"\\Omega": "Ω",
        r"\\Delta": "Δ",
        r"\\Sigma": "Σ",
        r"\\pi": "π",
        r"\\Pi": "Π",
        r"\\times": "×",
        r"\\cdot": "·",
        r"\\div": "÷",
        r"\\pm": "±",
        r"\\mp": "∓",
        r"\\leq": "≤",
        r"\\geq": "≥",
        r"\\neq": "≠",
        r"\\approx": "≈",
        r"\\infty": "∞",
        r"\\sum": "∑",
        r"\\int": "∫",
        r"\\prod": "∏",
        r"\\forall": "∀",
        r"\\exists": "∃",
        r"\\in": "∈",
        r"\\log": "log",
        r"\\ln": "ln",
        r"\\lg": "lg",
        r"\\sin": "sin",
        r"\\cos": "cos",
        r"\\tan": "tan",
        r"\\cot": "cot",
        r"\\arcsin": "arcsin",
        r"\\arccos": "arccos",
        r"\\arctan": "arctan",
        r"\\lim": "lim",
        r"\\sqrt": "√",
    }
    for latex, replacement in _latex_unicode.items():
        text = re.sub(latex, replacement, text, flags=re.IGNORECASE)

    # LaTeX пробелы: \, \; \: \! → обычный пробел
    text = re.sub(r"\\[,;:!]", " ", text)
    # LaTeX окружения
    text = re.sub(r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}", "", text, flags=re.DOTALL)
    # Экранирование скобок: \[ \] \{ \} \( \)
    text = re.sub(r"\\([\[\]{}()])", r"\1", text)
    # Остаточные \quad, \left, \right
    text = re.sub(r"\\(?:quad|qquad|hspace|vspace)\s*(?:\{[^}]*\})?", " ", text)
    text = re.sub(r"\\(?:left|right)\s*([|()\[\]])", r"\1", text)
    # Неизвестные LaTeX команды (сохраняем подчёркивания)
    text = re.sub(r"\\([a-zA-Z]+)(?=_)", r"\1", text)
    text = re.sub(r"\\([a-zA-Z]+)", r"\1", text)

    # ФАЗА 4: Superscripts/subscripts (ПОСЛЕ полной очистки LaTeX)
    _superscript_map = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "n": "ⁿ",
        "m": "ᵐ",
        "i": "ⁱ",
        "k": "ᵏ",
        "x": "ˣ",
        "+": "⁺",
        "-": "⁻",
        "(": "⁽",
        ")": "⁾",
    }

    def _to_superscript(m: re.Match) -> str:
        base = m.group(1)
        exp = m.group(2)
        return base + "".join(_superscript_map.get(c, c) for c in exp)

    text = re.sub(r"([\w)])\^\{([^}]+)\}", _to_superscript, text)
    text = re.sub(r"([\w)])\^(\d+)\b", _to_superscript, text)
    text = re.sub(r"([\w)])\^([a-zA-Z])\b", _to_superscript, text)

    _subscript_map = {
        "0": "₀",
        "1": "₁",
        "2": "₂",
        "3": "₃",
        "4": "₄",
        "5": "₅",
        "6": "₆",
        "7": "₇",
        "8": "₈",
        "9": "₉",
        "a": "ₐ",
        "e": "ₑ",
        "i": "ᵢ",
        "n": "ₙ",
        "m": "ₘ",
        "o": "ₒ",
        "p": "ₚ",
        "r": "ᵣ",
        "s": "ₛ",
        "t": "ₜ",
        "x": "ₓ",
        "k": "ₖ",
        "+": "₊",
        "-": "₋",
    }

    def _to_subscript(m: re.Match) -> str:
        base = m.group(1)
        sub = m.group(2)
        return base + "".join(_subscript_map.get(c, c) for c in sub)

    # _{выражение} — x_{общ} → xобщ (кириллица не в subscript map → остаётся текстом)
    text = re.sub(r"(\w)_\{([^}]+)\}", _to_subscript, text)
    # _буквы/цифры (одна или несколько) — a_1 → a₁, log_2 → log₂, C_nk → Cₙₖ
    text = re.sub(r"(\w)_([a-z0-9]+)\b", _to_subscript, text)

    # Обрезка мусора в конце
    text = re.sub(r"\s+[A-Za-z]_[А-Яа-яё]\S*(?:\s+\S+)*\s*$", "", text)

    # Артефакт: одиночные } перед = (после Phase 4 все _{} уже обработаны)
    text = re.sub(r"(\w)\s*\}\s*=\s*", r"\1 = ", text)
    # Удаляем оставшиеся одиночные { и }
    text = re.sub(r"(?<!\*)\{(?!\*)", "", text)
    text = re.sub(r"(?<!\*)\}(?!\*)", "", text)

    # Маркер списка «* пункт» → «- пункт» (НЕ трогаем **bold**)
    text = re.sub(r"(?m)^\s*\*\s+", "- ", text)
    # Сдвоенная нумерация «5. 6. Текст» или «5. 6.» → «6. Текст» / «6. » (оставляем второй номер)
    text = re.sub(r"(?m)^\s*\d+\.\s+(\d+)\.\s*", r"\1. ", text)
    # Одиночные *italic* → без звёздочек (но сохраняем **bold**)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)

    # Удаляем формулировки про «визуализацию/график/таблицу, которые будут показаны автоматически».
    # Важно: делаем это централизованно, чтобы такие фразы не проскакивали
    # ни в одном ответе (для любых предметов и типов запросов).
    auto_system_patterns = [
        # «визуализация будет показана автоматически»
        r"[Вв]изуализаци[яию]\s+.{0,30}?\s*(?:будет|появится|покажется)\s+автоматическ[а-яё]*\.?",
        r"[Вв]изуализаци[яию]\s+.{0,30}?\s*сгенерируется\s+автоматическ[а-яё]*\.?",
        # «график будет показан/появится автоматически»
        r"[Гг]рафик\s+.{0,30}?\s*(?:будет\s+показан|появится|сгенерируется)\s+автоматическ[а-яё]*\.?",
        # «таблица будет показана/сгенерируется»
        r"[Тт]аблиц[аеы]\s+.{0,30}?\s*(?:будет\s+показан[аы]?|появится|сгенерируется)\s+автоматическ[а-яё]*\.?",
        # «диаграмма/схема/карта будет показана»
        r"(?:[Дд]иаграмм[аы]|[Сс]хем[аы]|[Кк]арт[аы])\s+.{0,30}?\s*(?:будет\s+показан[аы]?|появится|сгенерируется)\s+автоматическ[а-яё]*\.?",
        # «система автоматически сгенерирует/нарисует/покажет ...»
        r"(?:систем[аеы]?\s+)?автоматическ[а-яё]+\s+сгенериру[ею]т?\s+[^.!?\n]+",
        r"(?:систем[аеы]?\s+)?автоматическ[а-яё]+\s+нарису[ею]т?\s+[^.!?\n]+",
        r"(?:систем[аеы]?\s+)?автоматическ[а-яё]+\s+покаж[еtu][тм]?\s+[^.!?\n]+",
        # «система уже сгенерировала / система автоматически добавит ...»
        r"систем[аеы]?\s+уже\s+сгенерировал[аи]?\s+[^.!?\n]+",
        r"систем[аеы]?\s+сгенериру[ею]т?\s+[^.!?\n]+автоматическ[а-яё]+\s*[^.!?\n]*",
        r"систем[аеы]?\s+автоматическ[а-яё]+\s+добавит\s+[^.!?\n]+",
        # Общее: «система автоматически ...» без уточнения, что именно
        r"систем[аеы]?\s+автоматическ[а-яё]+[^.!?\n]*",
        # Англоязычные формулировки на всякий случай
        r"system\s+will\s+automatically[^.!?\n]*",
        # Упрощенные паттерны для частых случаев
        r"будет\s+показан[аоы]?\s+автоматически\.?",
        r"появится\s+автоматически\.?",
        r"сгенерируется\s+автоматически\.?",
    ]
    for pattern in auto_system_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # НЕ удаляем: × • (буллеты, умножение); ² ³ ∑ ∫ ∞ ∠ ° (формулы — см. prompts.py ЗАПИСЬ ФОРМУЛ)

    # Очищаем лишние пробелы (но сохраняем абзацы - двойные переносы строк)
    text = re.sub(r"[ \t]+", " ", text)  # Множественные пробелы в одну строку
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Множественные переносы строк в два
    text = text.strip()

    # Страховка: длинный сплошной текст без абзацев — разбиваем по предложениям (каждые 2)
    text = _ensure_paragraph_breaks(text)

    # Убираем «пустые» пункты списков, которые состоят только из маркера и тире/ничего
    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()

        # Пустая строка — это разделитель абзацев, его сохраняем
        if stripped == "":
            cleaned_lines.append(line)
            continue

        # Строки вида "-", "•", "—" считаем артефактами модели и пропускаем
        if stripped in {"-", "•", "—"}:
            continue

        # Строки вида "- -", "- —", "-   " — тоже артефакты, пропускаем
        if stripped.startswith("- "):
            rest = stripped[2:].strip()
            if rest in {"", "-", "—"}:
                continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    return text
