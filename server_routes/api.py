"""
Регистрация API маршрутов (Mini App, Games, Premium, Auth, метрики).
"""

from aiohttp import web
from loguru import logger


def _register_api_route(
    app: web.Application, module_path: str, setup_func_name: str, route_name: str
) -> None:
    """Регистрация одного API роута."""
    try:
        module = __import__(module_path, fromlist=[setup_func_name])
        setup_func = getattr(module, setup_func_name)
        setup_func(app)
        logger.info(f"✅ {route_name} routes зарегистрированы")
    except ImportError as e:
        logger.warning(f"⚠️ Не удалось загрузить {route_name}: {e}")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при регистрации {route_name}: {e}", exc_info=True)


def setup_api_routes(app: web.Application) -> None:
    """Настройка API маршрутов."""
    route_configs = [
        ("bot.api.miniapp", "setup_miniapp_routes", "🎮 Mini App API"),
        ("bot.api.games_endpoints", "setup_games_routes", "🎮 Games API"),
        ("bot.api.premium_endpoints", "setup_premium_routes", "💰 Premium API"),
        ("bot.api.auth_endpoints", "setup_auth_routes", "🔐 Auth API"),
    ]
    for module_path, setup_func, route_name in route_configs:
        _register_api_route(app, module_path, setup_func, route_name)

    try:
        from bot.api.metrics_endpoint import add_metrics_to_web_server

        add_metrics_to_web_server(app)
        logger.info("📊 Метрики интегрированы в веб-сервер")
    except ImportError:
        logger.debug("📊 Метрики недоступны (опционально)")
