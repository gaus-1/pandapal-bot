"""
API endpoints для работы с геолокацией Mini App.
"""

from aiohttp import web
from loguru import logger

from bot.config import settings
from bot.database import get_db
from bot.services import UserService


async def miniapp_share_location(request: web.Request) -> web.Response:
    """
    Получить и сохранить геолокацию ребенка, отправить уведомление родителю.

    POST /api/miniapp/location/share
    Body: {
        "telegram_id": 123,
        "latitude": 55.7558,
        "longitude": 37.6173,
        "accuracy": 10,
        "timestamp": "2025-01-02T10:00:00Z"
    }
    """
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        accuracy = data.get("accuracy")
        timestamp = data.get("timestamp")

        if not telegram_id or not latitude or not longitude:
            return web.json_response(
                {"error": "telegram_id, latitude, and longitude required"}, status=400
            )

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Получаем родителя
            parent_telegram_id = user.parent_telegram_id

            if not parent_telegram_id:
                logger.warning(f"User {telegram_id} не имеет привязанного родителя")
                return web.json_response(
                    {
                        "success": True,
                        "message": "Location saved but no parent to notify",
                    }
                )

            # Отправляем уведомление родителю через Telegram Bot API
            bot = request.app["bot"]  # Получаем bot из app context

            location_text = (
                f"📍 **Местоположение ребенка**\n\n"
                f"👤 Ребенок: {user.first_name or 'Без имени'}\n"
                f"🗺️ Координаты: {latitude:.6f}, {longitude:.6f}\n"
            )

            if accuracy:
                location_text += f"🎯 Точность: ±{round(accuracy)}м\n"

            location_text += (
                f"🕐 Время: {timestamp}\n\n"
                f"🔗 [Открыть на карте](https://www.google.com/maps?q={latitude},{longitude})"
            )

            try:
                # Отправляем точку на карте
                await bot.send_location(
                    chat_id=parent_telegram_id,
                    latitude=latitude,
                    longitude=longitude,
                )

                # Отправляем текст с подробностями
                await bot.send_message(
                    chat_id=parent_telegram_id,
                    text=location_text,
                    parse_mode="Markdown",
                )

                logger.info(
                    f"✅ Местоположение ребенка {telegram_id} отправлено родителю {parent_telegram_id}"
                )

                return web.json_response(
                    {
                        "success": True,
                        "message": "Location shared with parent",
                    }
                )

            except Exception as send_error:
                logger.error(
                    f"❌ Ошибка отправки местоположения родителю: {send_error}",
                    exc_info=True,
                )
                return web.json_response(
                    {
                        "success": False,
                        "error": "Failed to send location to parent",
                    },
                    status=500,
                )

    except Exception as e:
        logger.error(f"❌ Ошибка обработки геолокации: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


def setup_location_routes(app: web.Application) -> None:
    """
    Регистрация роутов Location в aiohttp приложении.

    Args:
        app: aiohttp приложение
    """
    app.router.add_post("/api/miniapp/location/share", miniapp_share_location)
    logger.info("✅ Mini App Location API routes зарегистрированы")
