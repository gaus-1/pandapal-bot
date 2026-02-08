"""Fallback pipeline: не-streaming запрос при ошибке streaming."""

import asyncio
import json
import re

from aiohttp import web
from loguru import logger

from bot.services.yandex_ai_response_generator import clean_ai_response

from ._utils import format_visualization_explanation as _format_visualization_explanation
from ._utils import is_refusal_like as _is_refusal_like


async def run_fallback(
    response: web.StreamResponse,
    yandex_service,
    normalized_message: str,
    yandex_history: list,
    enhanced_system_prompt: str,
    temperature: float,
    max_tokens: int,
    model_name: str,
    user_message: str,
    telegram_id: int,
    premium_service,
    history_service,
    db,
    visualization_service,
) -> bool:
    """Fallback на не-streaming запрос. Возвращает True если успешно."""
    ai_response = await yandex_service.generate_text_response(
        user_message=normalized_message,
        chat_history=yandex_history,
        system_prompt=enhanced_system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model_name,
    )

    if not ai_response:
        raise ValueError("AI response is empty")

    cleaned_response = clean_ai_response(ai_response)

    # Визуализация в fallback
    visualization_image_base64 = None
    try:
        from bot.services.visualization_service import get_visualization_service

        viz_service = get_visualization_service()

        # Определяем, нужна ли таблица умножения
        combined_text_fallback = f"{user_message} {cleaned_response}".lower()
        multiplication_patterns_fallback = [
            r"табл[иы]ц[аеы]?\s*умножени[яе]\s*на\s*(\d+)",
            r"табл[иы]ц[аеы]?\s*умножени[яе]\s+(\d+)",
            r"умножени[яе]\s+на\s*(\d+)",
            r"умнож[а-я]*\s+(\d+)",
        ]
        general_table_patterns_fallback = [
            r"состав[ьи]\s+табл[иы]ц[аеы]?",
            r"пришли\s+табл[иы]ц[аеы]?",
            r"покажи\s+табл[иы]ц[аеы]?",
            r"сделай\s+табл[иы]ц[аеы]?",
            r"нарисуй\s+табл[иы]ц[аеы]?",
            r"построй\s+табл[иы]ц[аеы]?",
            r"выведи\s+табл[иы]ц[аеы]?",
            r"табл[иы]ц[аеы]?\s*(?:пришли|покажи|сделай|нарисуй|состав[ьи]|построй)",
            r"покажи\s+умножени[яе]",
            r"табл[иы]ц[аеы]?\s*умножени[яе](?:\s+на\s+все)?",
            r"полную\s+табл[иы]ц[аеы]?\s*умножени[яе]",
        ]
        multiplication_number_fallback = None
        for pattern in multiplication_patterns_fallback:
            multiplication_match = re.search(pattern, combined_text_fallback)
            if multiplication_match:
                try:
                    multiplication_number_fallback = int(multiplication_match.group(1))
                    if 1 <= multiplication_number_fallback <= 10:
                        break
                except (ValueError, IndexError):
                    continue

        general_table_fallback = None
        if not multiplication_number_fallback:
            for pattern in general_table_patterns_fallback:
                if re.search(pattern, combined_text_fallback):
                    general_table_fallback = True
                    break

        if multiplication_number_fallback:
            visualization_image = viz_service.generate_multiplication_table_image(
                multiplication_number_fallback
            )
            if visualization_image:
                visualization_image_base64 = viz_service.image_to_base64(visualization_image)
                logger.info(
                    f"📊 Stream: Fallback - сгенерирована таблица умножения на {multiplication_number_fallback}"
                )
        elif general_table_fallback:
            visualization_image = viz_service.generate_full_multiplication_table()
            if visualization_image:
                visualization_image_base64 = viz_service.image_to_base64(visualization_image)
                logger.info("📊 Stream: Fallback - сгенерирована полная таблица умножения")

        # Графики
        combined_text_lower = combined_text_fallback.lower()
        general_graph_fallback = any(
            re.search(pattern, combined_text_lower)
            for pattern in [
                r"состав[ьи]\s+график",
                r"пришли\s+график",
                r"покажи\s+график",
                r"сделай\s+график",
                r"нарисуй\s+график",
                r"построй\s+график",
                r"выведи\s+график",
            ]
        )

        graph_patterns = [
            r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
            r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
            r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
            r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
            r"(?:синусоид|sin|косинус|cos|тангенс|tan|экспонент|exp|логарифм|log|парабол|порабол|парабола|порабола)",
        ]
        graph_match = None
        for pattern in graph_patterns:
            graph_match = re.search(pattern, combined_text_lower)
            if graph_match:
                break

        if (general_graph_fallback or graph_match) and not visualization_image_base64:
            if re.search(r"(?:синусоид|sin)", combined_text_lower) or general_graph_fallback:
                visualization_image = viz_service.generate_function_graph("sin(x)")
                if visualization_image:
                    visualization_image_base64 = viz_service.image_to_base64(visualization_image)
                    logger.info("📈 Stream: Fallback - сгенерирован график синусоиды")
            elif re.search(r"(?:косинус|cos)", combined_text_lower):
                visualization_image = viz_service.generate_function_graph("cos(x)")
                if visualization_image:
                    visualization_image_base64 = viz_service.image_to_base64(visualization_image)
                    logger.info("📈 Stream: Fallback - сгенерирован график косинуса")
            elif re.search(r"(?:парабол)", combined_text_lower):
                visualization_image = viz_service.generate_function_graph("x**2")
                if visualization_image:
                    visualization_image_base64 = viz_service.image_to_base64(visualization_image)
                    logger.info("📈 Stream: Fallback - сгенерирован график параболы")
            else:
                expression = (
                    graph_match.group(1).strip() if graph_match and graph_match.groups() else ""
                )
                if expression and re.match(r"^[x\s+\-*/().\d\s]+$", expression):
                    safe_expr = (
                        expression.replace("²", "**2").replace("³", "**3").replace("^", "**")
                    )
                    visualization_image = viz_service.generate_function_graph(safe_expr)
                if visualization_image:
                    visualization_image_base64 = viz_service.image_to_base64(visualization_image)
                    logger.info(f"📈 Stream: Fallback - сгенерирован график функции: {expression}")

    except Exception as e:
        logger.debug(f"⚠️ Stream: Fallback - ошибка генерации визуализации: {e}")

    # Отправляем изображение если есть
    if visualization_image_base64:
        image_data = json.dumps(
            {"image": visualization_image_base64, "type": "visualization"},
            ensure_ascii=False,
        )
        await response.write(f"event: image\ndata: {image_data}\n\n".encode())
        logger.info("📊 Stream: Fallback - изображение визуализации отправлено")

        # Полноценное пояснение к таблице умножения
        if multiplication_number_fallback:
            logger.info(
                f"🔍 Stream: Fallback с визуализацией таблицы умножения (число={multiplication_number_fallback})"
            )
            cleaned_response = (
                f"Вот таблица умножения на {multiplication_number_fallback}!\n\n"
                f"Как пользоваться таблицей: найди число {multiplication_number_fallback} в левой колонке, "
                f"а второй множитель — в верхней строке. На пересечении — ответ.\n\n"
                f"Например, чтобы найти {multiplication_number_fallback} × 5, "
                f"смотри строку {multiplication_number_fallback} и столбец 5.\n\n"
                f"Таблица умножения пригодится для быстрого счёта в магазине, "
                f"при решении задач и в повседневной жизни."
            )
            logger.info("✅ Stream: Fallback - добавлено полноценное пояснение к таблице умножения")

        # Удаляем упоминания про автоматическую генерацию
        if visualization_image_base64:
            from bot.services.miniapp.intent_service import VisualizationIntent

            fallback_intent = VisualizationIntent(
                kind="table" if multiplication_number_fallback else "graph"
            )
            cleaned_response = visualization_service.postprocess_text_for_visualization(
                cleaned_response,
                fallback_intent,
                visualization_image_base64,
                multiplication_number_fallback,
            )

        cleaned_response = _format_visualization_explanation(cleaned_response)
        if visualization_image_base64 and _is_refusal_like(cleaned_response):
            cleaned_response = (
                "📐 Вот визуализация. Изучи её — по осям отложены данные. "
                "Если нужны подробности, спроси!"
            )

    # Отправляем полный ответ как один chunk
    chunk_data = json.dumps({"chunk": cleaned_response}, ensure_ascii=False)
    await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

    # Сохраняем в историю
    limit_reached = False
    try:
        limit_reached, total_requests = premium_service.increment_request_count(telegram_id)

        if limit_reached:
            asyncio.create_task(premium_service.send_limit_reached_notification_async(telegram_id))
            limit_msg_fb = premium_service.get_limit_reached_message_text()
            history_service.add_message(telegram_id, limit_msg_fb, "ai")

        history_service.add_message(telegram_id, user_message, "user")
        image_url = None
        if visualization_image_base64:
            image_url = f"data:image/png;base64,{visualization_image_base64}"
        history_service.add_message(telegram_id, cleaned_response, "ai", image_url=image_url)

        from bot.services.panda_lazy_service import PandaLazyService

        PandaLazyService(db).increment_consecutive_after_ai(telegram_id)
        db.commit()
        logger.info(f"✅ Stream: Fallback успешен, ответ сохранен для {telegram_id}")
    except Exception as save_err:
        logger.error(f"❌ Stream: Ошибка сохранения fallback ответа: {save_err}")
        db.rollback()

    # Сообщение при достижении лимита
    if limit_reached:
        limit_data_fb = json.dumps(
            {"content": premium_service.get_limit_reached_message_text()},
            ensure_ascii=False,
        )
        await response.write(f"event: message\ndata: {limit_data_fb}\n\n".encode())

    # Событие завершения
    await response.write(b'event: done\ndata: {"status": "completed"}\n\n')
    logger.info(f"✅ Stream: Fallback streaming завершен для {telegram_id}")
    return True
