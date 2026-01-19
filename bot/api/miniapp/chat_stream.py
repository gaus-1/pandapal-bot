"""
Endpoints для streaming AI чата через SSE.

Фактическая реализация вынесена в подмодуль
`bot.api.miniapp.stream_handlers.ai_chat_stream` для уменьшения размера файла
и лучшей поддерживаемости.
"""

from .stream_handlers.ai_chat_stream import miniapp_ai_chat_stream

__all__ = ["miniapp_ai_chat_stream"]
