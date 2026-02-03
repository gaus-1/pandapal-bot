"""
Генератор ответов AI для Yandex Cloud (YandexGPT).

Использует Yandex Cloud AI сервисы (YandexGPT Lite, SpeechKit STT, Vision OCR).
Соблюдает архитектуру SOLID.
"""

import random
import re
from abc import ABC, abstractmethod

from loguru import logger

from bot.config import settings
from bot.services.knowledge_service import get_knowledge_service
from bot.services.prompt_builder import get_prompt_builder
from bot.services.rag import ContextCompressor
from bot.services.yandex_cloud_service import get_yandex_cloud_service


def add_random_engagement_question(response: str) -> str:
    """
    Добавляет случайный вопрос для вовлечения в конец ответа.

    КРИТИЧЕСКИ ВАЖНО: Вопрос ВСЕГДА должен быть отделен пустой строкой от основного текста.

    Args:
        response: Исходный ответ AI

    Returns:
        str: Ответ с добавленным случайным вопросом (отделенным пустой строкой)
    """
    if not response or not response.strip():
        return response

    # Варианты вопросов для вовлечения
    engagement_questions = [
        "Понятно? Могу объяснить подробнее?",
        "Объяснить подробнее?",
        "Спроси меня ещё что-нибудь, мне нравится с тобой общаться!",
        "Хочешь, объясню подробнее...",
        "Есть вопросы посложнее?",
    ]

    # Проверяем, нет ли уже вопроса в конце ответа (более строгая проверка)
    response_lower = response.lower().strip()
    question_indicators = [
        "понятно?",
        "объяснить подробнее",
        "спроси меня",
        "есть вопросы",
        "хочешь, объясню",
        "рассказать подробнее",
        "подробнее?",
    ]

    # Проверяем последние 150 символов на наличие вопроса (более широкая проверка)
    last_part = response_lower[-150:] if len(response_lower) > 150 else response_lower
    has_existing_question = any(indicator in last_part for indicator in question_indicators)

    if has_existing_question:
        # Если вопрос уже есть, просто убеждаемся что он отделен пустой строкой
        response_stripped = response.strip()
        if not response_stripped.endswith("\n\n") and "\n\n" not in response_stripped[-50:]:
            # Добавляем пустую строку перед последним предложением если её нет
            lines = response_stripped.split("\n")
            if len(lines) > 1 and lines[-1].strip():
                # Если последняя строка не пустая, добавляем пустую строку
                return "\n".join(lines[:-1]) + "\n\n" + lines[-1]
        return response

    # Добавляем случайный вопрос
    random_question = random.choice(engagement_questions)

    # ВСЕГДА отделяем вопрос пустой строкой от основного текста
    response_stripped = response.strip()

    # Убираем лишние переносы строк в конце
    while response_stripped.endswith("\n"):
        response_stripped = response_stripped.rstrip("\n")

    # Добавляем вопрос с пустой строкой перед ним
    return f"{response_stripped}\n\n{random_question}"


def _normalize_for_dedup(s: str) -> str:
    """Нормализация для сравнения: убираем ** и лишние пробелы, чтобы дубли не различались из-за форматирования."""
    if not s:
        return ""
    s = re.sub(r"\*\*", "", s.lower().strip())
    return re.sub(r"\s+", " ", s)


def _remove_duplicate_long_substrings(text: str, min_len: int = 70) -> str:
    """
    Удаляет повторяющиеся длинные подстроки (артефакт стриминга: вставка блока повторно).
    Убирает второе и последующие вхождения блока длиной min_len+ символов.
    """
    if not text or len(text) < min_len * 2:
        return text
    result = text
    changed = True
    while changed:
        changed = False
        for length in range(min(len(result) // 2, 200), min_len - 1, -10):
            for i in range(len(result) - length):
                sub = result[i : i + length]
                if sub.strip() and len(sub.strip()) >= min_len:
                    j = result.find(sub, i + 1)
                    if j != -1:
                        result = result[:j] + result[j + length :]
                        changed = True
                        break
            if changed:
                break
    return result


def remove_duplicate_text(text: str, min_length: int = 20) -> str:
    """
    Удаляет повторяющиеся фрагменты текста (дубликаты).
    Агрессивная версия для полного удаления всех повторений.

    Args:
        text: Исходный текст
        min_length: Минимальная длина фрагмента для проверки на дубликат

    Returns:
        str: Текст без повторяющихся фрагментов
    """
    if not text or len(text) < min_length * 2:
        return text

    # Шаг 1: Проверяем, не повторяется ли весь текст целиком несколько раз
    text_len = len(text)
    if text_len > min_length * 3:
        # Разбиваем на 3 части и проверяем
        part_size = text_len // 3
        parts = [text[i : i + part_size] for i in range(0, text_len, part_size)]
        if len(parts) >= 2:
            normalized_parts = [re.sub(r"\s+", " ", p.lower().strip()) for p in parts[:3]]
            # Если все части одинаковые - оставляем только первую
            if len(normalized_parts) >= 2 and all(
                p == normalized_parts[0] for p in normalized_parts[1:] if len(p) >= min_length
            ):
                return parts[0].strip()

    # Шаг 2: Разбиваем на строки (по переносам)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    if len(lines) < 2 and len(text) <= 300:
        return text

    # Шаг 3: Удаляем дубликаты строк
    # НО сохраняем markdown заголовки и маркеры списков!
    seen_lines = set()
    unique_lines = []

    def _content_for_dedup(s: str) -> str:
        """Содержимое строки без номера/маркера списка — для дедупликации."""
        t = s.strip()
        if re.match(r"^\d+\.\s*", t):
            t = re.sub(r"^\d+\.\s*", "", t)
        if t.startswith("- ") or t.startswith("* ") or t.startswith("• "):
            t = t[2:].strip()
        return _normalize_for_dedup(t)

    for line in lines:
        # Заголовки (#) не дедуплицируем по содержимому
        if line.strip().startswith("#"):
            unique_lines.append(line)
            continue

        # Нормализуем для сравнения: для списков (1., -, *) — по содержимому без маркера
        normalized = _content_for_dedup(line)

        # Проверяем дубликаты по содержимому (ловим повторы «1. Определение…» / «1. Определение…»)
        if len(normalized) >= min_length:
            if normalized not in seen_lines:
                seen_lines.add(normalized)
                unique_lines.append(line)
        else:
            if line not in unique_lines:
                unique_lines.append(line)

    result = "\n".join(unique_lines)

    # Шаг 4: Проверяем повторяющиеся блоки (несколько строк подряд)
    if len(unique_lines) >= 4:
        # Ищем блоки из 2-5 строк, которые повторяются
        seen_blocks = set()
        final_lines = []
        i = 0

        while i < len(unique_lines):
            # Проверяем блоки разной длины
            found_duplicate = False
            for block_len in range(5, 1, -1):  # От 5 до 2 строк
                if i + block_len > len(unique_lines):
                    continue

                block = "\n".join(unique_lines[i : i + block_len])
                normalized_block = _normalize_for_dedup(block)

                if len(normalized_block) >= min_length * 2:
                    if normalized_block in seen_blocks:
                        # Пропускаем весь блок
                        i += block_len
                        found_duplicate = True
                        break
                    else:
                        seen_blocks.add(normalized_block)

            if not found_duplicate:
                final_lines.append(unique_lines[i])
                i += 1

        result = "\n".join(final_lines)

    # Шаг 4.5: Один длинный абзац без переносов (типично «формулы») — режем по границам блоков и дедуплицируем
    if len(result) > 300 and "\n\n" not in result:
        parts = re.split(
            r"(?=Формула для|Для решения задач|Вот некоторые из них|где:)",
            result,
            flags=re.IGNORECASE,
        )
        if len(parts) >= 2:
            seen_parts = set()
            unique_parts = []
            for seg in parts:
                seg = seg.strip()
                if not seg or len(seg) < 50:
                    if seg:
                        unique_parts.append(seg)
                    continue
                norm = _normalize_for_dedup(seg)
                if len(norm) < 80:
                    unique_parts.append(seg)
                    continue
                is_dup = norm in seen_parts
                if not is_dup:
                    for seen in seen_parts:
                        if len(seen) < 80:
                            continue
                        w_new = set(norm.split())
                        w_seen = set(seen.split())
                        if w_new and w_seen:
                            sim = len(w_new & w_seen) / max(len(w_new), len(w_seen))
                            if sim > 0.55:
                                is_dup = True
                                break
                if not is_dup:
                    seen_parts.add(norm)
                    unique_parts.append(seg)
            if unique_parts:
                result = "\n\n".join(unique_parts)

    # Шаг 5: Удаляем повторяющиеся абзацы (похожесть 50%, подстрока, блок с префиксом)
    raw_paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
    if len(raw_paragraphs) == 1 and "\n" in result:
        paragraphs = [p.strip() for p in result.split("\n") if len(p.strip()) > 30]
    else:
        paragraphs = raw_paragraphs
    if len(paragraphs) >= 2:
        seen_paragraphs = set()
        unique_paragraphs = []
        normalized_list = [_normalize_for_dedup(p) for p in paragraphs]
        min_para_len = 25

        for idx, paragraph in enumerate(paragraphs):
            normalized_para = normalized_list[idx]
            words_new = set(normalized_para.split())
            is_duplicate = False
            for seen_para in seen_paragraphs:
                words_seen = set(seen_para.split())
                if len(words_new) > 0 and len(words_seen) > 0:
                    common = len(words_new & words_seen)
                    similarity = common / max(len(words_new), len(words_seen))
                    # Длинные почти одинаковые абзацы (повтор вводной фразы списка и т.п.)
                    long_both = min(len(words_new), len(words_seen)) > 20
                    if similarity > 0.50 or (long_both and similarity > 0.80):
                        is_duplicate = True
                        break
                if (
                    len(normalized_para) >= min_para_len
                    and len(seen_para) >= min_para_len
                    and (normalized_para in seen_para or seen_para in normalized_para)
                ):
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_paragraphs.add(normalized_para)
                unique_paragraphs.append(paragraph)

        # Абзацы с лишним префиксом (1–4 слова): «Книга Вот несколько…» — удаляем дубликат
        if len(unique_paragraphs) >= 2:
            norm_unique = [_normalize_for_dedup(p) for p in unique_paragraphs]
            to_remove = set()
            for j in range(len(unique_paragraphs)):
                wj = norm_unique[j].split()
                for i in range(len(unique_paragraphs)):
                    if i == j or i in to_remove or j in to_remove:
                        continue
                    wi = norm_unique[i].split()
                    if len(wi) < 10:
                        continue
                    for prefix_len in range(1, min(5, len(wj))):
                        if wj[prefix_len:] == wi:
                            to_remove.add(j)
                            break
            unique_paragraphs = [p for k, p in enumerate(unique_paragraphs) if k not in to_remove]
        result = "\n\n".join(unique_paragraphs)

    # Шаг 6: Удаляем повторяющиеся предложения (включая похожие по словам >70%)
    sentences = re.split(r"([.!?]\s+)", result)
    if len(sentences) >= 4:
        seen_normalized = set()
        unique_sentences = []
        sent_min_len = 40

        i = 0
        while i < len(sentences) - 1:
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            normalized_sent = _normalize_for_dedup(sentence)
            if len(normalized_sent) < sent_min_len:
                unique_sentences.append(sentence)
                i += 2
                continue
            is_dup = normalized_sent in seen_normalized
            if not is_dup:
                for seen in seen_normalized:
                    if len(seen) < sent_min_len:
                        continue
                    w_new = set(normalized_sent.split())
                    w_seen = set(seen.split())
                    if w_new and w_seen:
                        sim = len(w_new & w_seen) / max(len(w_new), len(w_seen))
                        if sim > 0.7:
                            is_dup = True
                            break
            if not is_dup:
                seen_normalized.add(normalized_sent)
                unique_sentences.append(sentence)
            i += 2

        result = "".join(unique_sentences)

    # Шаг 7: СОХРАНЯЕМ markdown форматирование для структуры ответов!
    # НЕ преобразуем и НЕ удаляем:
    # - ### заголовки (фронтенд умеет их рендерить)
    # - **жирный** (фронтенд умеет)
    # - *курсив* (фронтенд умеет)
    # - списки с "-" или "*" (фронтенд умеет)
    # - нумерованные списки "1. 2. 3." (фронтенд умеет)
    #
    # Фронтенд (AIChat.tsx) уже имеет полноценный парсинг markdown!

    # Шаг 8: Финальная агрессивная дедупликация - удаляем точные повторы
    # Разбиваем по всем возможным разделителям и удаляем последовательные дубликаты
    final_chunks = re.split(r"(\n\n|\n|\.  |\.(?=\s+[А-ЯA-Z]))", result)
    deduplicated_chunks = []
    prev_chunk_normalized = None

    for chunk in final_chunks:
        if not chunk or chunk in ("\n", "\n\n", ".  "):
            deduplicated_chunks.append(chunk)
            continue

        chunk_normalized = _normalize_for_dedup(chunk)
        # Пропускаем только если это дубликат предыдущего (с учётом **)
        if chunk_normalized and chunk_normalized != prev_chunk_normalized:
            deduplicated_chunks.append(chunk)
            prev_chunk_normalized = chunk_normalized
        elif not chunk_normalized:
            deduplicated_chunks.append(chunk)

    result = "".join(deduplicated_chunks)

    return result.strip() if result.strip() else text.strip()


def normalize_bold_spacing(text: str) -> str:
    """Вставляет пробел перед и после ** между буквами: слово**термин** → слово **термин**."""
    if not text or "**" not in text:
        return text
    text = re.sub(r"(\w)\*\*", r"\1 **", text)
    text = re.sub(r"\*\*(\w)", r"** \1", text)
    return text


def fix_glued_words(text: str) -> str:
    """
    Исправляет склеенные слова: УПривет, шеПривет, вершинвершина, Рекаких и т.п.
    """
    if not text or len(text) < 4:
        return text
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
    ]
    for pattern, replacement in glued_fixes:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    # Повтор слова подряд без пробела (вершинвершина уже выше; общий случай для 3+ букв)
    text = re.sub(r"\b(\w{3,})\1\b", r"\1", text)
    # Общий паттерн: одна буква/слог + заглавное слово (Привет, Презент, Это) → пробел + слово
    text = re.sub(r"([а-яёa-z])([А-ЯЁA-Z][а-яёa-z]{2,})", r"\1 \2", text)
    return text


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

    # Исправляем склеенные слова в начале
    text = fix_glued_words(text)

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

    # Артефакты модели: "2dot 6" → "2·6", "х } = -2" → "х = -2"
    text = re.sub(r"(\d+)dot\s+(\d+)", r"\1·\2", text, flags=re.IGNORECASE)
    text = re.sub(r"(\w)\s*\}\s*=\s*", r"\1 = ", text)

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

    # Степень в формулах: ^2 ^3 ^4 ^5 → ² ³ ⁴ ⁵ (типографский стиль)
    text = re.sub(r"(\w)\^2\b", r"\1²", text)
    text = re.sub(r"(\w)\^3\b", r"\1³", text)
    text = re.sub(r"(\w)\^4\b", r"\1⁴", text)
    text = re.sub(r"(\w)\^5\b", r"\1⁵", text)

    # Обрезка мусора в конце: склеенные «Q_Для решения…», «t_Для…» — убираем до конца строки
    text = re.sub(r"\s+[A-Za-z]_[А-Яа-яё]\S*(?:\s+\S+)*\s*$", "", text)

    # Убираем знак доллара (ограничители формул в Telegram/Markdown)
    text = text.replace("$", "")

    # Сохраняем ** (markdown жирный) — фронтенд рендерит жирный текст для лучшего восприятия

    # Заменяем LaTeX команды на типографский стиль (как в промпте: √, не sqrt())
    text = re.sub(r"\\sqrt\s*\{([^}]*)\}", r"√(\1)", text)
    # \vec{v} → v (векторная величина в формулах)
    text = re.sub(r"\\vec\s*\{([^}]*)\}", r"\1", text, flags=re.IGNORECASE)
    # \nabla → ∇, \partial → ∂ (символы для физики/математики)
    text = re.sub(r"\\nabla\b", "∇", text, flags=re.IGNORECASE)
    text = re.sub(r"\\partial\b", "∂", text, flags=re.IGNORECASE)
    # Остальные LaTeX команды
    latex_to_text = {
        r"\\log": "log",
        r"\\ln": "ln",
        r"\\sin": "sin",
        r"\\cos": "cos",
        r"\\tan": "tan",
        r"\\cot": "cot",
        r"\\sqrt": "√",
        r"\\sum": "sum",
        r"\\int": "integral",
        r"\\lim": "lim",
        r"\\infty": "infinity",
        r"\\alpha": "alpha",
        r"\\beta": "beta",
        r"\\gamma": "gamma",
        r"\\pi": "pi",
        r"\\times": "×",
        r"\\cdot": "×",
        r"\\div": "÷",
        r"\\pm": "+-",
        r"\\leq": "<=",
        r"\\geq": ">=",
        r"\\neq": "!=",
        r"\\approx": "~",
    }
    for latex, replacement in latex_to_text.items():
        text = re.sub(latex, replacement, text, flags=re.IGNORECASE)

    # Убираем оставшиеся LaTeX окружения и скобки
    latex_patterns = [
        r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}",  # Окружения
        r"\\frac\{([^}]+)\}\{([^}]+)\}",  # \frac{a}{b} → (a)/(b)
        r"\\\[",  # \[
        r"\\\]",  # \]
        r"\\\{",  # \{
        r"\\\}",  # \}
        r"\\\(",  # \(
        r"\\\)",  # \)
    ]
    # Специальная обработка дробей
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", text)
    # Удаляем оставшиеся LaTeX конструкции
    for pattern in latex_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    # Удаляем неизвестные LaTeX команды (но сохраняем подчеркивания после них)
    text = re.sub(r"\\([a-zA-Z]+)(?=_)", r"\1", text)  # \log_a → log_a
    text = re.sub(r"\\([a-zA-Z]+)", r"\1", text)  # \unknown → unknown

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

    # Убираем только символы, которые ломают отображение или не поддерживаются
    # НЕ удаляем: × • (буллеты, умножение); ² ³ ∑ ∫ ∞ ∠ ° (формулы — см. prompts.py ЗАПИСЬ ФОРМУЛ)
    complex_math_chars = []
    for char in complex_math_chars:
        text = text.replace(char, "")

    # Очищаем лишние пробелы (но сохраняем абзацы - двойные переносы строк)
    text = re.sub(r"[ \t]+", " ", text)  # Множественные пробелы в одну строку
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Множественные переносы строк в два
    text = text.strip()

    return text


class IModerator(ABC):
    """
    Интерфейс для модерации контента.

    Следует принципу Interface Segregation (ISP).
    """

    @abstractmethod
    def moderate(self, text: str) -> tuple[bool, str]:
        """
        Проверить текст на соответствие правилам модерации.

        Args:
            text: Текст для проверки.

        Returns:
            tuple[bool, str]: (is_safe, reason)
        """
        pass


class IContextBuilder(ABC):
    """
    Интерфейс для построения контекста для AI.

    Следует принципу Interface Segregation (ISP).
    """

    @abstractmethod
    def build(
        self, user_message: str, chat_history: list[dict] = None, user_age: int | None = None
    ) -> str:
        """
        Построить контекст для генерации ответа AI.

        Args:
            user_message: Текущее сообщение пользователя.
            chat_history: История предыдущих сообщений.
            user_age: Возраст пользователя для адаптации ответа.

        Returns:
            str: Сформированный контекст для AI модели.
        """
        pass


class YandexAIResponseGenerator:
    """
    Генератор ответов AI через Yandex Cloud (YandexGPT).

    Единственная ответственность - генерация ответов AI.
    Модерация и контекст делегируются через Dependency Injection (SOLID).
    """

    def __init__(
        self,
        moderator: IModerator,
        context_builder: IContextBuilder,
        knowledge_service=None,  # type: ignore
        yandex_service=None,  # type: ignore
    ):
        """
        Инициализация генератора ответов.

        Args:
            moderator: Сервис модерации контента.
            context_builder: Сервис построения контекста.
            knowledge_service: Опционально - сервис знаний (для DI).
                Если None, используется глобальный синглтон.
            yandex_service: Опционально - Yandex Cloud сервис (для DI).
                Если None, используется глобальный синглтон.
        """
        self.moderator = moderator
        self.context_builder = context_builder

        # Dependency Injection: используем переданные сервисы или глобальные синглтоны
        # Это позволяет тестировать с моками и улучшает соблюдение DIP
        self.knowledge_service = (
            knowledge_service if knowledge_service is not None else get_knowledge_service()
        )
        self.yandex_service = (
            yandex_service if yandex_service is not None else get_yandex_cloud_service()
        )

        logger.info("✅ Yandex AI Response Generator инициализирован")

    def _should_use_wikipedia(self, user_message: str) -> bool:
        """
        Определить, нужно ли использовать проверенные данные для этого вопроса.

        КРИТИЧЕСКИ ВАЖНО: Wikipedia должна использоваться для ВСЕХ образовательных вопросов!
        Исключения только для чисто вычислительных задач.

        Args:
            user_message: Сообщение пользователя.

        Returns:
            bool: True если стоит использовать проверенные данные.
        """
        message_lower = user_message.lower().strip()

        # Исключаем ТОЛЬКО чисто математические/вычислительные запросы
        # Для всех остальных используем Wikipedia!
        exclude_patterns = [
            r"^\d+\s*[\+\-\*\/×÷]\s*\d+",  # Чистые вычисления: "5 + 3", "7 × 8"
            r"^сколько будет\s+\d+",  # "Сколько будет 5+3"
            r"^реши\s+\d+",  # "Реши 5+3"
            r"^посчитай\s+\d+",  # "Посчитай 5+3"
            r"^вычисли\s+\d+",  # "Вычисли 5+3"
            r"покажи\s+таблицу\s+умножения",  # Таблица умножения - визуализация
            r"нарисуй\s+график",  # Графики - визуализация
            r"построй\s+график",  # Графики
            r"покажи\s+график",  # Графики
            r"привет",  # Приветствия
            r"^как\s+(?:тебя|твоя)\s+(?:зовут|имя)",  # Вопросы о боте
        ]

        # Для ВСЕХ остальных запросов используем Wikipedia (кроме исключений)
        # - "что такое фотосинтез" - да
        # - "кто такой Пушкин" - да
        # - "почему небо голубое" - да
        # - "какая столица Франции" - да
        # - "расскажи про ВОВ" - да
        # - "где находится Китай" - да
        # - "в каком году была война" - да
        # - любые образовательные вопросы - да!
        return all(not re.search(pattern, message_lower) for pattern in exclude_patterns)

    async def generate_response(
        self,
        user_message: str,
        chat_history: list[dict] = None,
        user_age: int | None = None,
        user_name: str | None = None,
        user_grade: int | None = None,
        is_history_cleared: bool = False,
        message_count_since_name: int = 0,
        skip_name_asking: bool = False,  # noqa: ARG002
        non_educational_questions_count: int = 0,
        is_premium: bool = False,  # noqa: ARG002
        is_auto_greeting_sent: bool = False,
        user_gender: str | None = None,
    ) -> str:
        """
        Генерировать ответ AI на сообщение пользователя.

        Использует Pro модель для всех пользователей.
        Лимиты запросов управляются через premium_features_service.

        Args:
            user_message: Сообщение пользователя.
            chat_history: История предыдущих сообщений.
            user_age: Возраст пользователя для адаптации.
            user_name: Имя пользователя для обращения.
            is_history_cleared: Флаг очистки истории.
            message_count_since_name: Количество сообщений с последнего обращения по имени.
            skip_name_asking: Пропустить запрос имени (не используется в текущей реализации).
            non_educational_questions_count: Количество непредметных вопросов подряд.
            is_premium: Premium статус (не используется, оставлено для обратной совместимости)
            is_auto_greeting_sent: Флаг, что автоматическое приветствие уже было отправлено

        Returns:
            str: Сгенерированный ответ AI.
        """
        try:
            # Правила по запрещённым темам отключены — модерация не применяется

            # RAG: enhanced_search подтягивает Wikipedia при пустой базе (use_wikipedia)
            relevant_materials = await self.knowledge_service.enhanced_search(
                user_question=user_message,
                user_age=user_age,
                top_k=3,
                use_wikipedia=self._should_use_wikipedia(user_message),
            )
            web_context = self.knowledge_service.format_knowledge_for_ai(relevant_materials)

            if web_context:
                compressor = ContextCompressor()
                web_context = compressor.compress(
                    context=web_context,
                    question=user_message,
                    max_sentences=7,
                )

            # Преобразуем историю в формат Yandex Cloud
            yandex_history = []
            if chat_history:
                for msg in chat_history[-10:]:  # Последние 10 сообщений
                    role = msg.get("role", "user")  # Используем роль напрямую из истории
                    text = msg.get("text", "").strip()
                    if text:  # Только непустые сообщения
                        yandex_history.append({"role": role, "text": text})

            # Используем PromptBuilder для формирования промпта
            prompt_builder = get_prompt_builder()
            # Если is_auto_greeting_sent не передан, проверяем историю
            if not is_auto_greeting_sent and chat_history:
                for msg in chat_history:
                    if msg.get("role") == "assistant":
                        msg_text = msg.get("text", "").lower()
                        if (
                            "привет" in msg_text
                            or "начнем" in msg_text
                            or "чем могу помочь" in msg_text
                        ):
                            is_auto_greeting_sent = True
                            break

            enhanced_system_prompt = prompt_builder.build_system_prompt(
                user_message=user_message,
                user_name=user_name,
                chat_history=chat_history,
                is_history_cleared=is_history_cleared,
                message_count_since_name=message_count_since_name,
                non_educational_questions_count=non_educational_questions_count,
                user_age=user_age,
                user_grade=user_grade,
                is_auto_greeting_sent=is_auto_greeting_sent,
                user_gender=user_gender,
            )

            if web_context:
                enhanced_system_prompt += f"\n\n📚 Дополнительная информация:\n{web_context}\n\n"

            # Используем Pro модель для всех пользователей (YandexGPT Pro Latest - стабильная версия)
            # Формат yandexgpt-pro/latest - Pro версия YandexGPT
            model_name = settings.yandex_gpt_model
            temperature = settings.ai_temperature  # Основной параметр для всех пользователей
            max_tokens = settings.ai_max_tokens  # Основной параметр для всех пользователей

            # Генерация ответа через Yandex Cloud
            logger.info("📤 Отправка запроса в YandexGPT Pro...")
            response = await self.yandex_service.generate_text_response(
                user_message=user_message,  # Передаем чистое сообщение пользователя
                chat_history=yandex_history,
                system_prompt=enhanced_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_name,
            )

            if response:
                # Очищаем ответ от запрещенных символов и LaTeX
                cleaned_response = clean_ai_response(response.strip())
                # Добавляем случайный вопрос для вовлечения
                final_response = add_random_engagement_question(cleaned_response)
                return final_response
            else:
                return "Извините, не смог сгенерировать ответ. Попробуйте переформулировать вопрос."

        except Exception as e:
            logger.error(f"❌ Ошибка генерации AI (Yandex): {e}")
            return "Ой, что-то пошло не так. Попробуйте переформулировать вопрос."

    def get_model_info(self) -> dict[str, str]:
        """
        Получить информацию о текущей модели AI.

        Returns:
            Dict[str, str]: Информация о модели Yandex Cloud.
        """
        return {
            "provider": "Yandex Cloud",
            "model": settings.yandex_gpt_model,
            "temperature": str(settings.ai_temperature),
            "max_tokens": str(settings.ai_max_tokens),
            "public_name": "PandaPalAI (powered by YandexGPT)",
        }

    async def analyze_image(
        self,
        image_data: bytes,
        user_message: str | None = None,
        user_age: int | None = None,  # noqa: ARG002
    ) -> str:
        """
        Анализировать изображение через Yandex Vision + YandexGPT.

        Args:
            image_data: Данные изображения в байтах.
            user_message: Сопровождающий текст пользователя.
            user_age: Возраст пользователя для адаптации.

        Returns:
            str: Образовательный ответ на основе анализа изображения.
        """
        try:
            logger.info("📷 Анализ изображения через Yandex Vision + GPT...")

            # Анализируем изображение через Yandex Vision + GPT
            analysis_result = await self.yandex_service.analyze_image_with_text(
                image_data=image_data, user_question=user_message
            )

            if not analysis_result.get("has_text") and not analysis_result.get("analysis"):
                return (
                    "📷 Я не смог распознать текст на изображении.\n\n"
                    "Попробуй сфотографировать задание более четко! 📝"
                )

            # Формируем образовательный ответ
            response_parts = []

            if analysis_result.get("recognized_text"):
                response_parts.append(
                    f"📝 <b>Текст на изображении:</b>\n{analysis_result['recognized_text']}\n"
                )

            if analysis_result.get("analysis"):
                # Очищаем ответ от дубликатов и форматируем
                cleaned_analysis = clean_ai_response(analysis_result["analysis"])
                response_parts.append(f"🎓 <b>Разбор задания:</b>\n{cleaned_analysis}")

            result = "\n".join(response_parts)
            # Финальная очистка всего ответа
            cleaned_result = clean_ai_response(result)
            # Добавляем случайный вопрос для вовлечения
            return add_random_engagement_question(cleaned_result)

        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения (Yandex): {e}")
            return "😔 Извини, у меня возникли проблемы с анализом изображения. Попробуй ещё раз!"

    async def moderate_image_content(self, image_data: bytes) -> tuple[bool, str]:  # noqa: ARG002
        """
        Проверить изображение на безопасность.

        Args:
            image_data: Данные изображения в байтах.

        Returns:
            tuple[bool, str]: (is_safe, reason)
        """
        # Правила по запрещённым темам отключены — не применяются
        return True, "OK"
