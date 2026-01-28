"""
Вспомогательные функции для AI чата.
"""

import re


def read_file_safely(
    file_obj, max_size: int = 20 * 1024 * 1024, chunk_size: int = 64 * 1024
) -> bytes:
    """
    Потоковое чтение файла с ограничением размера.

    Читает файл по частям (chunks) вместо загрузки всего в память.
    Это критично для больших файлов (голос, аудио, изображения).

    Args:
        file_obj: Файловый объект (BytesIO или подобный) с методом read()
        max_size: Максимальный размер файла в байтах (по умолчанию 20MB)
        chunk_size: Размер чанка для чтения (по умолчанию 64KB)

    Returns:
        bytes: Содержимое файла

    Raises:
        ValueError: Если файл превышает max_size
    """
    data = b""
    total_read = 0

    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break

        data += chunk
        total_read += len(chunk)

        if total_read > max_size:
            raise ValueError(
                f"Файл слишком большой: {total_read} байт > {max_size} байт "
                f"({max_size / (1024 * 1024):.1f}MB)"
            )

    return data


def extract_user_name_from_message(user_message: str) -> tuple[str | None, bool]:
    """
    Извлечение имени пользователя из сообщения.

    Returns:
        tuple: (имя или None, является ли отказом)
    """
    cleaned_message = user_message.strip().lower()
    cleaned_message = re.sub(r"[.,!?;:]+$", "", cleaned_message)

    refusal_patterns = [
        r"не\s+хочу",
        r"не\s+скажу",
        r"не\s+буду",
        r"не\s+назову",
        r"не\s+хочу\s+называть",
        r"не\s+буду\s+называть",
        r"не\s+хочу\s+говорить",
        r"не\s+скажу\s+имя",
        r"не\s+хочу\s+сказать",
    ]
    is_refusal = any(re.search(pattern, cleaned_message) for pattern in refusal_patterns)
    if is_refusal:
        return None, True

    common_words = [
        "да",
        "нет",
        "ок",
        "окей",
        "хорошо",
        "спасибо",
        "привет",
        "пока",
        "здравствуй",
        "здравствуйте",
        "как дела",
        "что",
        "как",
        "почему",
        "где",
        "когда",
        "кто",
    ]

    cleaned_for_check = cleaned_message.split()[0] if cleaned_message.split() else cleaned_message

    is_like_name = (
        2 <= len(cleaned_for_check) <= 15
        and re.match(r"^[а-яёА-ЯЁa-zA-Z-]+$", cleaned_for_check)
        and cleaned_for_check not in common_words
        and len(cleaned_message.split()) <= 2
    )

    if is_like_name:
        return cleaned_message.split()[0].capitalize(), False

    return None, False
