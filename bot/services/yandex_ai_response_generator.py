import re


def clean_ai_response(text: str) -> str:
    """
    Очищает ответ AI от LaTeX и сложных математических символов.
    Сохраняет сравнения (>, <) и знаки препинания.
    """
    if not text:
        return text

    # Убираем знак доллара (ограничители формул в Telegram/Markdown)
    text = text.replace("$", "")

    # Убираем специфичные LaTeX команды (включая скобки)
    latex_patterns = [
        r"\\frac\{[^}]+\}\{[^}]+\}",  # \frac{}{}
        r"\\sqrt\[[^\]]+\]\{[^}]+\}",  # \sqrt[n]{}
        r"\\sqrt\{[^}]+\}",  # \sqrt{}
        r"\\[a-zA-Z]+\{[^}]*\}",  # \command{}
        r"\\[a-zA-Z]+",  # \command
        r"\\[\\\]\{\}\(\)",  # Пробелы и спецсимволы escape
        r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}",  # Окружения
    ]
    for pattern in latex_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Убираем математические символы верхних индексов и спецзнаков
    # (Оставляем знаки препинания и базовые операторы + - =)
    complex_math_chars = [
        "²",
        "³",
        "∑",
        "∫",
        "∞",
        "∠",
        "°",
        "•",
        "×",
    ]  # × можно заменить на x, но лучше оставить
    for char in complex_math_chars:
        text = text.replace(char, "")

    # Очищаем лишние пробелы (но оставляем обычные)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text
