"""
Barrel export для всех обработчиков
Собирает все роутеры в одном месте
@module bot.handlers
"""

from bot.handlers.start import router as start_router
from bot.handlers.ai_chat import router as ai_chat_router
from bot.handlers.settings import router as settings_router

# Список всех роутеров для регистрации в main.py
routers = [
    start_router,
    settings_router,
    ai_chat_router,  # AI chat должен быть последним (ловит все текстовые сообщения)
]

__all__ = ['routers']

