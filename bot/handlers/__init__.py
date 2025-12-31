"""
Barrel export для всех обработчиков
Собирает все роутеры в одном месте

"""

from bot.handlers.achievements import router as achievements_router
from bot.handlers.admin_commands import router as admin_commands_router
from bot.handlers.ai_chat import router as ai_chat_router
from bot.handlers.emergency import router as emergency_router
from bot.handlers.location import router as location_router
from bot.handlers.menu import router as menu_router
from bot.handlers.parent_dashboard import router as parent_dashboard_router
from bot.handlers.parental_control import router as parental_control_router
from bot.handlers.settings import router as settings_router
from bot.handlers.start import router as start_router

# Список всех роутеров для регистрации в main.py
routers = [
    admin_commands_router,  # Административные команды (высший приоритет)
    start_router,
    emergency_router,  # Экстренные номера (важно для детей)
    menu_router,  # Обработка кнопок меню
    achievements_router,  # Система достижений
    location_router,  # Геолокация для безопасности
    settings_router,
    parental_control_router,  # Родительский контроль
    parent_dashboard_router,  # Дашборд для родителей
    ai_chat_router,  # AI chat должен быть последним (ловит все текстовые сообщения)
]

__all__ = ["routers"]
