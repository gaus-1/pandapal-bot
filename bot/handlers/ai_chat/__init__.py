"""
AI Chat handlers - модульная структура.

Разбит на подмодули:
- text: текстовые сообщения
- voice: голосовые и аудио сообщения
- image: изображения
- document: документы
- helpers: вспомогательные функции
"""

from aiogram import Router

from . import document, image, text, voice

# Создаём роутер для AI чата
router = Router(name="ai_chat")

# Регистрируем handlers на router
text.register_handlers(router)
voice.register_handlers(router)
image.register_handlers(router)
document.register_handlers(router)

__all__ = ["router"]
