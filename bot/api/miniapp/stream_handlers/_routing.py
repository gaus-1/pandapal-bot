"""Маршрутизация до основного стриминга: adult topics, отдых, изображения, секрет, модерация."""

import asyncio
import json
import re

from aiohttp import web
from loguru import logger

from bot.database import get_db
from bot.services import ChatHistoryService
from bot.services.premium_features_service import PremiumFeaturesService


def _build_quick_viz_caption(viz_type: str | None, user_message: str) -> str:
    """Формирует образовательную подпись для быстрой визуализации."""
    from bot.api.miniapp.stream_handlers._visualization import get_diagram_explanation

    if viz_type == "map":
        # Извлекаем название объекта из запроса
        location = _extract_location_from_message(user_message)
        if location:
            return (
                f"🗺️ На карте выше показан(а) **{location}**. "
                "Обрати внимание на масштаб и метку — они помогают понять расположение объекта. "
                "Хочешь узнать подробнее про этот регион? Спроси!"
            )
        return (
            "🗺️ Вот карта! Обрати внимание на масштаб и метку — "
            "они показывают расположение объекта. "
            "Хочешь узнать подробнее? Спроси!"
        )

    explanation = get_diagram_explanation(viz_type) if viz_type else None
    if explanation:
        return explanation

    return "Вот визуализация. Если нужны пояснения — спроси!"


def _extract_location_from_message(text: str) -> str | None:
    """Извлекает название локации из пользовательского запроса."""
    text_lower = text.lower().strip()
    patterns = [
        r"карт[аеыу]\s+(.+?)(?:\s*$)",
        r"покажи\s+на\s+карте\s+(.+?)(?:\s*$)",
        r"покажи\s+карт[аеыу]\s+(.+?)(?:\s*$)",
        r"(?:покажи|нарисуй|выведи)\s+(.+?)\s+на\s+карте",
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            loc = match.group(1).strip()
            loc = re.sub(r"\s*(?:пожалуйста|плиз|плз|пож)\s*$", "", loc).strip()
            if 2 <= len(loc) <= 60:
                # "реки волга" -> "Реки Волга"
                return " ".join(w.capitalize() for w in loc.split())
    return None


async def try_adult_topics(
    user_message: str, telegram_id: int, response: web.StreamResponse
) -> bool:
    """Проверка взрослых тем. Возвращает True если обработано."""
    from bot.services.adult_topics_service import get_adult_topics_service

    explanation = get_adult_topics_service().try_get_adult_topic_response(user_message)
    if not explanation:
        return False

    with get_db() as db_at:
        hist = ChatHistoryService(db_at)
        prem = PremiumFeaturesService(db_at)
        limit_reached, _ = prem.increment_request_count(telegram_id)
        hist.add_message(telegram_id, user_message, "user")
        hist.add_message(telegram_id, explanation, "ai")
        if limit_reached:
            hist.add_message(telegram_id, prem.get_limit_reached_message_text(), "ai")
            asyncio.create_task(prem.send_limit_reached_notification_async(telegram_id))
        db_at.commit()

    event_data = json.dumps({"content": explanation}, ensure_ascii=False)
    await response.write(f"event: message\ndata: {event_data}\n\n".encode())
    await response.write(b"event: done\ndata: {}\n\n")
    return True


async def try_rest_offer(user_message: str, telegram_id: int, response: web.StreamResponse) -> bool:
    """Предложение отдыха после длинной сессии. Возвращает True если обработано."""
    with get_db() as db_rest:
        from bot.services import UserService

        user_rest = UserService(db_rest).get_user_by_telegram_id(telegram_id)
        if not user_rest:
            return False

        from bot.services.panda_lazy_service import PandaLazyService

        lazy_service = PandaLazyService(db_rest)
        rest_response, _ = lazy_service.check_rest_offer(
            telegram_id, user_message, user_rest.first_name
        )
        if not rest_response:
            return False

        history_service_rest = ChatHistoryService(db_rest)
        prem_rest = PremiumFeaturesService(db_rest)
        limit_reached_rest, _ = prem_rest.increment_request_count(telegram_id)
        history_service_rest.add_message(telegram_id, user_message, "user")
        history_service_rest.add_message(telegram_id, rest_response, "ai")
        if limit_reached_rest:
            history_service_rest.add_message(
                telegram_id, prem_rest.get_limit_reached_message_text(), "ai"
            )
            asyncio.create_task(prem_rest.send_limit_reached_notification_async(telegram_id))
        db_rest.commit()

    event_data = json.dumps({"content": rest_response}, ensure_ascii=False)
    await response.write(f"event: message\ndata: {event_data}\n\n".encode())
    await response.write(b"event: done\ndata: {}\n\n")
    return True


def _extract_location_from_history(telegram_id: int) -> str | None:
    """Извлекает название локации из последних сообщений (для follow-up 'покажи на карте')."""
    with get_db() as db:
        history = ChatHistoryService(db).get_chat_history(telegram_id, limit=6)

    geo_patterns = [
        r"где\s+(?:находится|расположен[аоы]?)\s+(.+?)(?:\?|\s*$)",
        r"расскажи\s+(?:про|о|об)\s+(.+?)(?:\?|\s*$)",
        r"что\s+(?:такое|за\s+страна|за\s+город)\s+(.+?)(?:\?|\s*$)",
        r"^([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁа-яё]+){0,3})$",
    ]
    for msg in history:
        if msg.get("role") != "user":
            continue
        text = msg.get("content", "").strip()
        for pattern in geo_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                loc = match.group(1).strip()
                loc = re.sub(r"\s*(?:пожалуйста|плиз|плз)\s*$", "", loc).strip()
                if 2 <= len(loc) <= 60:
                    return loc
    return None


async def try_image_request(
    msg_for_routing: str, user_message: str, telegram_id: int, response: web.StreamResponse
) -> bool:
    """Обработка запросов на генерацию изображений. Возвращает True если обработано."""
    image_keywords = [
        "нарисуй",
        "нарисовать",
        "рисунок",
        "картинк",
        "изображени",
        "фото",
        "иллюстраци",
        "покажи как выглядит",
        "сгенерируй изображение",
        "создай картинку",
    ]
    # Исключаем карты и визуализации — они обрабатываются отдельно
    map_exclusions = ["карт", "на карте", "график", "таблиц", "диаграмм", "схем"]
    msg_lower = msg_for_routing.lower()
    is_image_request = any(keyword in msg_lower for keyword in image_keywords) and not any(
        excl in msg_lower for excl in map_exclusions
    )

    logger.debug(
        f"🎨 Stream: Проверка детектора изображений: '{msg_for_routing[:50]}', "
        f"is_image_request={is_image_request}"
    )

    if not is_image_request:
        return False

    # КРИТИЧНО: Визуализация по нормализованному тексту
    from bot.services.visualization_service import get_visualization_service

    viz_service = get_visualization_service()
    visualization_image, visualization_type = viz_service.detect_visualization_request(
        msg_for_routing
    )

    # Follow-up: "покажи на карте" без локации — ищем в истории чата
    if not visualization_image and re.search(r"покажи\s+на\s+карте", msg_lower):
        location = _extract_location_from_history(telegram_id)
        if location:
            logger.info(f"🗺️ Контекст из истории: '{location}' для '{msg_for_routing[:40]}'")
            enriched = f"покажи на карте {location}"
            visualization_image, visualization_type = viz_service.detect_visualization_request(
                enriched
            )

    # Учебная визуализация (карта, график, таблица и т.д.)
    if visualization_image:
        import base64 as b64

        image_base64 = b64.b64encode(visualization_image).decode("utf-8")
        event_payload: dict = {
            "image": image_base64,
            "type": visualization_type or "visualization",
        }

        # Для карт передаём координаты — фронтенд покажет интерактивную карту
        if visualization_type == "map":
            map_coords = viz_service.get_last_map_coordinates()
            if map_coords:
                event_payload["mapData"] = map_coords

        image_data = json.dumps(event_payload, ensure_ascii=False)
        await response.write(f"event: image\ndata: {image_data}\n\n".encode())
        caption = _build_quick_viz_caption(visualization_type, user_message)
        event_data = json.dumps({"content": caption}, ensure_ascii=False)
        await response.write(f"event: message\ndata: {event_data}\n\n".encode())
        await response.write(b"event: done\ndata: {}\n\n")
        with get_db() as db:
            hist = ChatHistoryService(db)
            hist.add_message(
                telegram_id=telegram_id, message_text=user_message, message_type="user"
            )
            hist.add_message(
                telegram_id=telegram_id,
                message_text=caption,
                message_type="ai",
                image_url=f"data:image/png;base64,{image_base64}",
            )
            from bot.services.panda_lazy_service import PandaLazyService

            PandaLazyService(db).increment_consecutive_after_ai(telegram_id)
            db.commit()
        return True

    # Не визуализация - генерируем через YandexART
    if not visualization_image:
        from bot.services.yandex_art_service import get_yandex_art_service

        art_service = get_yandex_art_service()
        is_available = art_service.is_available()

        logger.info(
            f"🎨 Stream: Запрос на генерацию изображения (не учебный) от {telegram_id}: "
            f"'{msg_for_routing[:50]}', art_service.is_available={is_available}"
        )

        if is_available:
            try:
                image_bytes = await art_service.generate_image(
                    prompt=msg_for_routing, style="auto", aspect_ratio="1:1"
                )

                if image_bytes:
                    import base64

                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                    image_data = json.dumps(
                        {"image": image_base64, "type": "generated_image"},
                        ensure_ascii=False,
                    )
                    await response.write(f"event: image\ndata: {image_data}\n\n".encode())

                    caption = "Могу нарисовать что-то по школьным предметам! 📚"
                    event_data = json.dumps({"content": caption}, ensure_ascii=False)
                    await response.write(f"event: message\ndata: {event_data}\n\n".encode())
                    await response.write(b"event: done\ndata: {}\n\n")

                    logger.info(
                        f"🎨 Stream: Изображение сгенерировано для пользователя {telegram_id}"
                    )

                    with get_db() as db:
                        history_service = ChatHistoryService(db)
                        history_service.add_message(
                            telegram_id=telegram_id,
                            message_text=user_message,
                            message_type="user",
                        )
                        image_url = f"data:image/jpeg;base64,{image_base64}"
                        history_service.add_message(
                            telegram_id=telegram_id,
                            message_text=caption,
                            message_type="ai",
                            image_url=image_url,
                        )
                        from bot.services.panda_lazy_service import PandaLazyService

                        PandaLazyService(db).increment_consecutive_after_ai(telegram_id)
                        db.commit()
                    return True
                else:
                    logger.warning(
                        f"⚠️ Stream: Не удалось сгенерировать изображение для {telegram_id}"
                    )
                    error_msg = json.dumps(
                        {
                            "error": "Не получилось нарисовать картинку. Попробуй переформулировать запрос!"
                        },
                        ensure_ascii=False,
                    )
                    await response.write(f"event: error\ndata: {error_msg}\n\n".encode())
                    return True

            except Exception as e:
                logger.error(f"❌ Stream: Ошибка генерации изображения: {e}", exc_info=True)
                error_msg = json.dumps(
                    {"error": "Упс, что-то пошло не так с рисованием. Попробуй снова!"},
                    ensure_ascii=False,
                )
                await response.write(f"event: error\ndata: {error_msg}\n\n".encode())
                return True
    else:
        logger.warning(
            f"⚠️ Stream: YandexART недоступен (нет API ключей или роли). "
            f"Запрос: '{user_message[:50]}'"
        )
        logger.info("📝 Stream: Обрабатываем запрос как обычный текст")

    return False


async def try_secret_message(
    user_message: str, telegram_id: int, response: web.StreamResponse
) -> bool:
    """Секретное сообщение. Возвращает True если обработано."""
    normalized = "".join(user_message.split())
    if normalized != "<>***<>" and user_message.strip() != "<>***<>":
        return False

    special_message = "Создано с любовью для Агаты ❤️❤️❤️"
    event_data = json.dumps({"content": special_message}, ensure_ascii=False)
    await response.write(f"event: message\ndata: {event_data}\n\n".encode())
    await response.write(b"event: done\ndata: {}\n\n")
    logger.info(
        f"💝 Секретное сообщение отправлено пользователю {telegram_id} (Mini App): '{user_message}'"
    )
    return True


async def try_moderation(user_message: str, telegram_id: int, response: web.StreamResponse) -> bool:
    """Модерация контента. Возвращает True если заблокировано."""
    from bot.services.moderation_service import ContentModerationService

    moderation_service = ContentModerationService()
    is_safe, block_reason = moderation_service.is_safe_content(user_message)
    if is_safe:
        return False

    redirect_text = moderation_service.get_safe_response_alternative(block_reason or "")
    moderation_service.log_blocked_content(telegram_id, user_message, block_reason or "модерация")
    event_data = json.dumps({"content": redirect_text}, ensure_ascii=False)
    await response.write(f"event: message\ndata: {event_data}\n\n".encode())
    await response.write(b"event: done\ndata: {}\n\n")
    return True
