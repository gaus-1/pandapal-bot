"""
Подпакет обработчиков для streaming-эндпоинтов Mini App.

Сейчас содержит:
- ai_chat_stream.miniapp_ai_chat_stream — основной SSE-обработчик AI чата.
"""

from .ai_chat_stream import miniapp_ai_chat_stream

__all__ = ["miniapp_ai_chat_stream"]
