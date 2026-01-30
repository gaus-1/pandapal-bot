"""
Регистрация роутов веб-сервера PandaPal.

Вынесено из web_server.py: health, API, static, middleware.
"""

from server_routes.api import setup_api_routes
from server_routes.health import setup_health_routes
from server_routes.middleware import setup_middleware
from server_routes.static import setup_frontend_static

__all__ = [
    "setup_api_routes",
    "setup_health_routes",
    "setup_frontend_static",
    "setup_middleware",
]
