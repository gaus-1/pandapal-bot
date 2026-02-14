"""
Обработчик streaming AI чата для Mini App (SSE).

Вынесен из bot.api.miniapp.chat_stream для уменьшения размера файла
и лучшей поддерживаемости (SOLID: SRP).
"""

import json
import re
from contextlib import suppress

import httpx
from aiohttp import web
from loguru import logger

from bot.database import get_db
from bot.services import ChatHistoryService, UserService
from bot.services.ai_service_solid import get_ai_service
from bot.services.miniapp.visualization_service import MiniappVisualizationService
from bot.services.panda_chat_reactions import get_chat_reaction
from bot.services.yandex_ai_response_generator import (
    add_random_engagement_question,
    clean_ai_response,
)

from ._history import save_and_notify
from ._media import process_media
from ._pre_checks import check_premium_and_lazy, parse_and_validate_request
from ._routing import (
    try_adult_topics,
    try_image_request,
    try_moderation,
    try_rest_offer,
    try_secret_message,
)
from ._utils import format_visualization_explanation, is_refusal_like
from ._visualization import build_visualization_explanation, generate_visualization_images

# Обратная совместимость (используются в _visualization.py и _fallback.py)
_format_visualization_explanation = format_visualization_explanation
_is_refusal_like = is_refusal_like


async def miniapp_ai_chat_stream(request: web.Request) -> web.StreamResponse:
    """
    Отправить сообщение AI и получить streaming ответ через SSE.

    POST /api/miniapp/ai/chat-stream
    Body: {
        "telegram_id": 123,
        "message": "...",
        "photo_base64": "data:image/jpeg;base64,...", # опционально
        "audio_base64": "data:audio/webm;base64,..." # опционально
    }

    Returns:
        SSE stream с chunks ответа AI
    """
    client_ip = request.remote
    logger.info(
        f"📨 Mini App AI Chat Stream запрос от IP: {client_ip}, метод: {request.method}, путь: {request.path_qs}"
    )

    # Создаем SSE response
    response = web.StreamResponse()
    response.headers["Content-Type"] = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"

    try:
        await response.prepare(request)

        # Парсинг и валидация запроса
        parsed = await parse_and_validate_request(request, response)
        if parsed is None:
            return response

        telegram_id = parsed["telegram_id"]
        message = parsed["message"]
        photo_base64 = parsed["photo_base64"]
        audio_base64 = parsed["audio_base64"]
        language_code = parsed["language_code"]

        # Проверка лимитов и ленивости
        if not await check_premium_and_lazy(telegram_id, response):
            return response

        # Событие начала обработки
        await response.write(b'event: start\ndata: {"status": "processing"}\n\n')

        # Обработка медиа
        user_message = await process_media(
            audio_base64, photo_base64, telegram_id, message, response, language_code
        )
        if user_message is None:
            return response

        # Маршрутизация: adult topics, отдых, изображения, секрет, модерация
        if await try_adult_topics(user_message, telegram_id, response):
            return response

        if await try_rest_offer(user_message, telegram_id, response):
            return response

        # Нормализация опечаток
        from bot.services.typo_normalizer import normalize_common_typos

        normalized_message = normalize_common_typos(user_message)
        msg_for_routing = normalized_message

        if await try_image_request(msg_for_routing, user_message, telegram_id, response):
            return response

        if await try_secret_message(user_message, telegram_id, response):
            return response

        if await try_moderation(user_message, telegram_id, response):
            return response

        # Основной pipeline: streaming AI ответ + визуализации
        with get_db() as db:
            user_service = UserService(db)
            history_service = ChatHistoryService(db)

            user = user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                await response.write(b'event: error\ndata: {"error": "User not found"}\n\n')
                return response

            # Контекст чата
            from bot.services.miniapp.chat_context_service import MiniappChatContextService

            context_service = MiniappChatContextService(db)
            context = context_service.prepare_context(
                telegram_id=telegram_id,
                user_message=normalized_message,
                skip_premium_check=True,
            )

            yandex_history = context["yandex_history"]
            enhanced_system_prompt = context["system_prompt"]
            is_history_cleared = context["is_history_cleared"]
            is_educational = context.get("is_educational", False)
            premium_service = context["premium_service"]
            history_service = context["history_service"]

            # Проверка Premium
            can_request, limit_reason = premium_service.can_make_ai_request(
                telegram_id, username=user.username
            )
            if not can_request:
                logger.warning(
                    f"🚫 Stream: AI запрос заблокирован для user={telegram_id}: {limit_reason}"
                )
                await response.write(
                    f'event: error\ndata: {{"error": "{limit_reason}", "error_code": "RATE_LIMIT_EXCEEDED"}}\n\n'.encode()
                )
                return response

            await response.write(b'event: status\ndata: {"status": "generating"}\n\n')

            # AI service + knowledge search
            ai_service = get_ai_service()
            response_generator = ai_service.response_generator
            yandex_service = response_generator.yandex_service

            from bot.config import settings
            from bot.services.rag import ContextCompressor

            relevant_materials = await response_generator.knowledge_service.enhanced_search(
                user_question=normalized_message,
                user_age=user.age,
                top_k=3,
                use_wikipedia=response_generator._should_use_wikipedia(normalized_message),
            )
            web_context = response_generator.knowledge_service.format_knowledge_for_ai(
                relevant_materials
            )
            if web_context:
                compressor = ContextCompressor()
                web_context = compressor.compress(
                    context=web_context, question=normalized_message, max_sentences=7
                )
            if web_context:
                from bot.config.prompts import RAG_FORMAT_REMINDER

                enhanced_system_prompt += (
                    f"\n\n📚 Дополнительная информация:\n{web_context}\n\n{RAG_FORMAT_REMINDER}\n\n"
                )
            from bot.config.prompts import STRUCTURE_REMINDER_ALWAYS

            enhanced_system_prompt += f"\n\n{STRUCTURE_REMINDER_ALWAYS}\n\n"

            model_name = settings.yandex_gpt_model
            temperature = settings.ai_temperature
            max_tokens = settings.ai_max_tokens
            logger.info(f"💎 Stream: Используем Pro модель для пользователя {telegram_id}")

            # Streaming + визуализации
            full_response = ""
            limit_reached = False
            try:
                from bot.services.miniapp.intent_service import get_intent_service
                from bot.services.visualization_service import get_visualization_service

                intent_service = get_intent_service()
                viz_service = get_visualization_service()

                intent = intent_service.parse_intent(normalized_message)

                # Детекция визуализаций
                visualization_service = MiniappVisualizationService()
                (
                    specific_visualization_image,
                    multiplication_number,
                    general_table_request,
                    general_graph_request,
                    visualization_type,
                ) = visualization_service.detect_visualization_request(normalized_message, intent)

                # Проверяем запросы на диаграмму
                has_diagram_request = False
                if not specific_visualization_image:
                    diagram_patterns = [
                        r"покажи\s+диаграмм",
                        r"нарисуй\s+диаграмм",
                        r"создай\s+диаграмм",
                        r"построй\s+диаграмм",
                        r"выведи\s+диаграмм",
                        r"покажи\s+к\s+ней\s+диаграмм",
                        r"покажи\s+к\s+задаче\s+диаграмм",
                        r"покажи\s+к\s+ней\s+круговую",
                    ]
                    has_diagram_request = any(
                        re.search(pattern, normalized_message.lower())
                        for pattern in diagram_patterns
                    )

                will_have_visualization = (
                    multiplication_number is not None
                    or general_table_request
                    or general_graph_request
                    or has_diagram_request
                    or specific_visualization_image is not None
                )
                chunk_count = 0

                async for chunk in yandex_service.generate_text_response_stream(
                    user_message=normalized_message,
                    chat_history=yandex_history,
                    system_prompt=enhanced_system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model_name,
                ):
                    chunk_count += 1

                    # YandexGPT streaming возвращает кумулятивный текст:
                    # каждый chunk содержит ВЕСЬ сгенерированный текст на данный момент.
                    # Используем последний chunk как полный ответ (не +=).
                    is_cumulative = (
                        chunk_count > 1 and full_response and chunk.startswith(full_response[:50])
                    )
                    if is_cumulative:
                        full_response = chunk
                    else:
                        full_response += chunk

                    if chunk_count <= 3:
                        logger.debug(
                            f"🔍 Stream chunk #{chunk_count}: cumulative={is_cumulative}, "
                            f"len={len(chunk)}, preview={repr(chunk[:80])}"
                        )

                    if not will_have_visualization:
                        chunk_data = json.dumps({"chunk": chunk}, ensure_ascii=False)
                        await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                full_response = clean_ai_response(full_response)
                full_response = add_random_engagement_question(full_response)

                # Генерация визуализаций
                visualization_image_base64, visualization_type, multiplication_number = (
                    generate_visualization_images(
                        full_response=full_response,
                        user_message=user_message,
                        intent=intent,
                        specific_visualization_image=specific_visualization_image,
                        multiplication_number=multiplication_number,
                        general_table_request=general_table_request,
                        general_graph_request=general_graph_request,
                        has_diagram_request=has_diagram_request,
                        visualization_type=visualization_type,
                        viz_service=viz_service,
                    )
                )

                # Отправляем изображение если есть
                if visualization_image_base64:
                    event_payload: dict = {
                        "image": visualization_image_base64,
                        "type": visualization_type or "visualization",
                    }
                    # Для карт передаём координаты — фронтенд покажет InteractiveMap
                    if visualization_type == "map":
                        map_coords = viz_service.get_last_map_coordinates()
                        if map_coords:
                            event_payload["mapData"] = map_coords
                    image_data = json.dumps(event_payload, ensure_ascii=False)
                    await response.write(f"event: image\ndata: {image_data}\n\n".encode())
                    logger.info(
                        f"📊 Stream: Изображение визуализации отправлено "
                        f"(размер: {len(visualization_image_base64)}, специфичная: {bool(specific_visualization_image)})"
                    )

                # Построение пояснения к визуализации
                full_response = build_visualization_explanation(
                    full_response=full_response,
                    visualization_image_base64=visualization_image_base64,
                    normalized_message=normalized_message,
                    intent=intent,
                    visualization_type=visualization_type,
                    multiplication_number=multiplication_number,
                    visualization_service=visualization_service,
                )

                # Ограничиваем размер ответа
                MAX_RESPONSE_LENGTH = 8000
                full_response_for_db = full_response
                if len(full_response) > MAX_RESPONSE_LENGTH:
                    full_response = full_response[:MAX_RESPONSE_LENGTH] + "\n\n... (ответ обрезан)"

                # Сохраняем в историю
                limit_reached, total_requests = await save_and_notify(
                    db=db,
                    premium_service=premium_service,
                    history_service=history_service,
                    telegram_id=telegram_id,
                    user_message=user_message,
                    full_response_for_db=full_response_for_db,
                    visualization_image_base64=visualization_image_base64,
                    is_educational=is_educational,
                    is_history_cleared=is_history_cleared,
                    user=user,
                    response=response,
                )

                # Финальный контент (очищенный + вовлечение) — одним событием, без подмены «другая версия»
                if full_response:
                    final_payload = {"content": full_response}
                    panda_reaction = get_chat_reaction(normalized_message)
                    if panda_reaction is not None:
                        final_payload["pandaReaction"] = panda_reaction
                    final_data = json.dumps(final_payload, ensure_ascii=False)
                    await response.write(f"event: final\ndata: {final_data}\n\n".encode())

                # Сообщение при достижении лимита
                if limit_reached:
                    limit_data = json.dumps(
                        {"content": premium_service.get_limit_reached_message_text()},
                        ensure_ascii=False,
                    )
                    await response.write(f"event: message\ndata: {limit_data}\n\n".encode())

                await response.write(b'event: done\ndata: {"status": "completed"}\n\n')
                logger.info(f"✅ Stream: Streaming завершен для {telegram_id}")

            except (
                httpx.HTTPStatusError,
                httpx.TimeoutException,
                httpx.RequestError,
            ) as stream_error:
                logger.warning(
                    f"⚠️ Stream: Ошибка streaming (HTTP {getattr(stream_error, 'response', None) and stream_error.response.status_code or 'unknown'}): {stream_error}"
                )
                logger.info(f"🔄 Stream: Пробуем fallback на не-streaming запрос для {telegram_id}")

                try:
                    from ._fallback import run_fallback

                    await run_fallback(
                        response=response,
                        yandex_service=yandex_service,
                        normalized_message=normalized_message,
                        yandex_history=yandex_history,
                        enhanced_system_prompt=enhanced_system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        model_name=model_name,
                        user_message=user_message,
                        telegram_id=telegram_id,
                        premium_service=premium_service,
                        history_service=history_service,
                        db=db,
                        visualization_service=visualization_service,
                    )
                except Exception as fallback_error:
                    logger.error(
                        f"❌ Stream: Fallback также не удался: {fallback_error}", exc_info=True
                    )
                    error_msg = 'event: error\ndata: {"error": "Временная проблема с AI сервисом. Попробуйте позже."}\n\n'
                    await response.write(error_msg.encode("utf-8"))
                    return response

            except Exception as stream_error:
                logger.error(
                    f"❌ Stream: Неожиданная ошибка streaming: {stream_error}", exc_info=True
                )
                error_msg = 'event: error\ndata: {"error": "Ошибка генерации ответа"}\n\n'
                await response.write(error_msg.encode("utf-8"))
                return response

    except Exception as e:
        logger.error(f"❌ Stream: Критическая ошибка: {e}", exc_info=True)
        try:
            error_msg = 'event: error\ndata: {"error": "Внутренняя ошибка сервера"}\n\n'
            await response.write(error_msg.encode("utf-8"))
        except Exception:
            pass
    finally:
        with suppress(Exception):
            await response.write_eof()

    return response
