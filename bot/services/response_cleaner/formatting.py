"""
Форматирование и нормализация текста ответов AI.

Stateless-функции для: нормализации bold-форматирования, удаления
невидимых Unicode-символов, исправления склеенных слов, работы со
строками-цифрами, маркерами списков и абзацами.
"""

import re


def _normalize_for_dedup(s: str) -> str:
    """Нормализация для сравнения: убираем ** и лишние пробелы, чтобы дубли не различались из-за форматирования."""
    if not s:
        return ""
    s = re.sub(r"\*\*", "", s.lower().strip())
    return re.sub(r"\s+", " ", s)


def normalize_bold_spacing(text: str) -> str:
    """Вставляет пробел перед и после ** между буквами: слово**термин** → слово **термин**."""
    if not text or "**" not in text:
        return text
    text = re.sub(r"(\w)\*\*", r"\1 **", text)
    text = re.sub(r"\*\*(\w)", r"** \1", text)
    return text


def _strip_invisible_unicode(text: str) -> str:
    """Удаляет невидимые Unicode-символы, которые ломают regex-дедупликацию."""
    # LINE SEPARATOR / PARAGRAPH SEPARATOR → обычные переносы (не удаляем!)
    text = text.replace("\u2028", "\n").replace("\u2029", "\n\n")
    # Zero-width chars, soft hyphen, BOM, invisible formatting
    return re.sub(r"[\u200b\u200c\u200d\u200e\u200f\u00ad\ufeff\u2060\u202a-\u202e]", "", text)


def fix_glued_words(text: str) -> str:
    """
    Исправляет склеенные слова и артефакты модели: УПривет, PossPossessive, ПомоПомогает и т.п.
    """
    if not text or len(text) < 4:
        return text
    # Невидимые Unicode-символы ломают word boundary — убираем первым делом
    text = _strip_invisible_unicode(text)
    # Известные склейки (артефакты модели)
    glued_fixes = [
        (r"\bУПривет\b", "Привет"),
        (r"\bшеПривет\b", "Привет"),
        (r"\bУПрезент\b", "Презент"),
        (r"\bиПрезент\b", "и Презент"),
        (r"\bшеЭто\b", "Это"),
        (r"вершинвершина", "вершина"),
        (r"результатеером", "результате заговора"),
        (r"Рекаких\b", "Re. При каких"),
        (r"\bPossPossessive\b", "Possessive"),
        (r"\bПомоПомогает\b", "Помогает"),
        (r"неодушевлённыхвлённых", "неодушевлённых"),
        (r"построени-\s*остроения", "построения"),
    ]
    for pattern, replacement in glued_fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    # Повтор слова подряд без пробела (вершинвершина уже выше; общий случай для 3+ букв)
    text = re.sub(r"\b(\w{3,})\1\b", r"\1", text)
    # Префикс + то же слово полностью (PossPossessive → Possessive, ПомоПомогает → Помогает)
    text = re.sub(r"\b(\w{2,})(\1\w+)\b", r"\2", text)
    # Общий паттерн: одна буква/слог + заглавное слово (Привет, Презент, Это) → пробел + слово
    text = re.sub(r"([а-яёa-z])([А-ЯЁA-Z][а-яёa-z]{2,})", r"\1 \2", text)
    return text


def _is_digit_only_line(line: str) -> bool:
    """
    Строка считается «только цифры», если после нормализации это цифры и опционально [.)] в конце.
    Не считаем нумерованный пункт вида «1. Текст» или «1) Текст».
    """
    stripped = line.strip().replace("\r", "")
    if not stripped:
        return False
    # Только цифры и пробелы, или цифры + одна точка/скобка в конце (артефакт модели: 1. 8. 3.)
    return bool(re.match(r"^\s*\d+[.)]?\s*$", stripped))


def _merge_digit_only_lines(text: str) -> str:
    """
    Склеивает строки из одних цифр (артефакт модели: год 1837 как 1\\n8\\n3\\n7) в одну строку.
    Убирает «цифры в столбик» в ответах. Учитывает варианты 1\\n8\\n3 и 1.\\n8.\\n3.
    """
    if not text or "\n" not in text:
        return text
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _is_digit_only_line(line):
            digit_lines = [line]
            j = i + 1
            while j < len(lines) and _is_digit_only_line(lines[j]):
                digit_lines.append(lines[j])
                j += 1
            # Из каждой строки оставляем только цифры (убираем пробелы, точку, скобку)
            merged = "".join(re.sub(r"\D", "", ln) for ln in digit_lines)
            if merged:
                result.append(merged)
            i = j
        else:
            result.append(line)
            i += 1
    return "\n".join(result)


def _ensure_list_and_bold_breaks(text: str, line_threshold: int = 130) -> str:
    """
    В длинных строках вставляет переносы перед маркерами списка и после закрывающего **,
    чтобы списки и подзаголовки не сливались в сплошной текст.
    """
    if not text or len(text) < line_threshold:
        return text
    lines = text.split("\n")
    result_lines = []
    for line in lines:
        if len(line) <= line_threshold:
            result_lines.append(line)
            continue
        # Перед маркерами списка (с пробелом после) вставляем перенос
        line = re.sub(r"\s+(-\s+)", r"\n\1", line, count=0)
        line = re.sub(r"\s+(•\s+)", r"\n\1", line, count=0)
        # * как маркер списка только когда не часть ** (жирное)
        line = re.sub(r"(?<!\*)\s+\*\s+(?!\*)", "\n* ", line, count=0)
        # После полной фразы жирным **...**, если следом буква/цифра — перенос (подзаголовок)
        line = re.sub(r"(\*\*[^*]*\*\*)(\s*)([A-Za-zА-Яа-я0-9])", r"\1\n\n\2\3", line, count=0)
        result_lines.append(line)
    return "\n".join(result_lines)


def _merge_definition_split_by_dash(text: str) -> str:
    """
    Склеивает случаи, когда определение вида «**Термин** — это ...»
    разорвалось на два пункта списка:

    - **Термин**
    - — это величина, которая ...

    Объединяет их в один корректный пункт:

    - **Термин** — это величина, которая ...
    """
    if not text or "**" not in text:
        return text

    lines = text.split("\n")
    result_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Ищем строку-пункт со строгим жирным термином: "- **Термин**"
        if stripped.startswith("- **") and stripped.endswith("**") and i + 1 < len(lines):
            next_line = lines[i + 1]
            next_stripped = next_line.lstrip()

            # Следующая строка — ещё один пункт или просто строка, начинающаяся с тире
            if next_stripped.startswith("- —") or next_stripped.startswith("—"):
                # Убираем второй маркер списка, но оставляем само определение
                tail = next_stripped.lstrip("-").lstrip()
                merged = f"{line.rstrip()} {tail}"
                result_lines.append(merged)
                i += 2
                continue

        result_lines.append(line)
        i += 1

    return "\n".join(result_lines)


# Порог длины текста без абзацев, при котором включается страховка разбивки (символов)
_PARAGRAPH_BREAK_MIN_LENGTH = 250


def _ensure_paragraph_breaks(
    text: str, min_length: int | None = None, sentences_per_para: int = 2
) -> str:
    """
    Если текст длинный и без абзацев (нет \\\\n\\\\n) — вставить разбивку по предложениям.
    Страховка от «полотна» текста от модели.
    """
    if min_length is None:
        min_length = _PARAGRAPH_BREAK_MIN_LENGTH
    if not text or "\n\n" in text or len(text) < min_length:
        return text
    # Разбиваем по границам предложений (. ! ? с последующим пробелом)
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 15]
    if len(parts) < 2:
        return text
    paragraphs = []
    for i in range(0, len(parts), sentences_per_para):
        chunk = parts[i : i + sentences_per_para]
        paragraphs.append(" ".join(chunk))
    return "\n\n".join(paragraphs)
