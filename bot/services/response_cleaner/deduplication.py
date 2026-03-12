"""
Дедупликация повторов и артефактов стриминга AI.

Stateless-функции для удаления повторяющихся строк, абзацев,
предложений и длинных подстрок из ответов AI.
"""

import re

from .formatting import _normalize_for_dedup

# Лимит итераций для _remove_duplicate_long_substrings (защита от O(n³))
_MAX_DEDUP_ITERATIONS = 5


def _remove_duplicate_long_substrings(text: str, min_len: int = 70) -> str:
    """
    Удаляет повторяющиеся длинные подстроки (артефакт стриминга: вставка блока повторно).
    Убирает второе и последующие вхождения блока длиной min_len+ символов.
    Ограничен по итерациям для предотвращения зависания.
    """
    if not text or len(text) < min_len * 2:
        return text
    result = text
    for _iteration in range(_MAX_DEDUP_ITERATIONS):
        found = False
        for length in range(min(len(result) // 2, 200), min_len - 1, -10):
            # Проверяем только каждую 5-ю позицию для экономии (подстроки >= 70 символов)
            for i in range(0, len(result) - length, 5):
                sub = result[i : i + length]
                if sub.strip() and len(sub.strip()) >= min_len:
                    j = result.find(sub, i + 1)
                    if j != -1:
                        before = result[:j]
                        after = result[j + length :]
                        # Не склеиваем слова: если на стыке буквы — вставляем пробел
                        if before and after and before[-1].isalpha() and after[0].isalpha():
                            result = before + " " + after
                        else:
                            result = before + after
                        found = True
                        break
            if found:
                break
        if not found:
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
                            if sim > 0.75:
                                is_dup = True
                                break
                if not is_dup:
                    seen_parts.add(norm)
                    unique_parts.append(seg)
            if unique_parts:
                result = "\n\n".join(unique_parts)

        # Если всё ещё один длинный абзац — режем по маркерам списка (-, •, *, 1. 2. 3.)
        if len(result) > 300 and "\n\n" not in result:
            list_parts = re.split(r"(?=\s*[-•*]\s+|\s*\d+\.\s+)", result)
            merged = []
            buf = []
            for seg in list_parts:
                seg = seg.strip()
                if not seg:
                    continue
                if len(seg) < 30 and buf:
                    buf.append(seg)
                else:
                    if buf:
                        merged.append(" ".join(buf))
                        buf = []
                    merged.append(seg)
            if buf:
                merged.append(" ".join(buf))
            if len(merged) >= 2:
                result = "\n\n".join(merged)

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
