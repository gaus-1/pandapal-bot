"""Общие утилиты для stream handlers."""


def format_visualization_explanation(text: str) -> str:
    """Оставляем текст как есть — полная свобода модели."""
    return (text or "").strip()


def is_refusal_like(text: str) -> bool:
    """Проверка, похож ли текст на отказ модели обсуждать тему."""
    if not (text or "").strip():
        return False
    t = text.lower().strip()
    refusal_phrases = [
        "не могу обсуждать эту тему",
        "не могу ответить на этот вопрос",
        "поговорим о чём-нибудь ещё",
        "давайте поговорим о чём-нибудь",
        "давай лучше поговорим о чём-то",
        "лучше поговорим об учёбе",
        "давай лучше обсудим что-то",
    ]
    return any(p in t for p in refusal_phrases)
