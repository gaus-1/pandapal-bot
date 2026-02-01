"""
Обработчик streaming AI чата для Mini App (SSE).

Вынесен из bot.api.miniapp.chat_stream для уменьшения размера файла
и лучшей поддерживаемости (SOLID: SRP).
"""

import asyncio
import json
from contextlib import suppress

import httpx
from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.miniapp.helpers import (
    extract_user_grade_from_message,
    extract_user_name_from_message,
    send_achievements_event,
)
from bot.api.validators import AIChatRequest
from bot.database import get_db
from bot.services import ChatHistoryService, UserService
from bot.services.ai_service_solid import get_ai_service
from bot.services.miniapp.audio_service import MiniappAudioService
from bot.services.miniapp.photo_service import MiniappPhotoService
from bot.services.miniapp.visualization_service import MiniappVisualizationService
from bot.services.premium_features_service import PremiumFeaturesService
from bot.services.yandex_ai_response_generator import clean_ai_response


def _format_visualization_explanation(text: str) -> str:
    """Оставляем текст как есть — полная свобода модели."""
    return (text or "").strip()


def _is_refusal_like(text: str) -> bool:
    """Проверка, похож ли текст на отказ модели обсуждать тему."""
    if not (text or "").strip():
        return False
    t = text.lower().strip()
    refusal_phrases = [
        "не могу обсуждать эту тему",
        "не могу ответить на этот вопрос",
        "поговорим о чём-нибудь ещё",
        "давайте поговорим о чём-нибудь",
        "давай лучше поговорим о чём-то",
        "лучше поговорим об учёбе",
        "давай лучше обсудим что-то",
    ]
    return any(p in t for p in refusal_phrases)


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
    response.headers["X-Accel-Buffering"] = "no"  # Отключаем буферизацию в nginx

    try:
        await response.prepare(request)

        # Читаем данные запроса
        try:
            data = await request.json()
            logger.info(
                f"📦 Stream: получен JSON запрос: telegram_id={data.get('telegram_id')}, "
                f"has_message={bool(data.get('message'))}, "
                f"has_photo={bool(data.get('photo_base64'))}, "
                f"has_audio={bool(data.get('audio_base64'))}"
            )
        except Exception as json_error:
            err_str = str(json_error)
            logger.error(f"❌ Stream: ошибка парсинга JSON: {json_error}", exc_info=True)
            if "Content Too Large" in err_str or "too large" in err_str.lower():
                msg = '{"error": "Фото или аудио слишком большие. Уменьши размер фото или длину голосового."}'
                await response.write(f"event: error\ndata: {msg}\n\n".encode())
            else:
                await response.write(b'event: error\ndata: {"error": "Invalid JSON"}\n\n')
            return response

        # Валидация входных данных
        try:
            validated = AIChatRequest(**data)
        except ValidationError as e:
            logger.warning(f"⚠️ Stream: Invalid request: {e}")
            await response.write(b'event: error\ndata: {"error": "Invalid request data"}\n\n')
            return response

        telegram_id = validated.telegram_id
        message = validated.message or ""
        photo_base64 = validated.photo_base64
        audio_base64 = validated.audio_base64
        user_message = message

        # КРИТИЧНО: Проверка лимита ДО любых платных вызовов (SpeechKit, Vision, YandexGPT)
        with get_db() as db:
            user_service = UserService(db)
            premium_service = PremiumFeaturesService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                await response.write(b'event: error\ndata: {"error": "User not found"}\n\n')
                return response
            can_request, limit_reason = premium_service.can_make_ai_request(
                telegram_id, username=user.username
            )
            if not can_request:
                logger.warning(
                    f"🚫 Stream: AI запрос заблокирован для user={telegram_id} (до audio/photo): {limit_reason}"
                )
                err_escaped = limit_reason.replace('"', '\\"').replace("\n", " ")
                await response.write(
                    f'event: error\ndata: {{"error": "{err_escaped}", "error_code": "RATE_LIMIT_EXCEEDED"}}\n\n'.encode()
                )
                return response

            # Проверка ленивости панды (как в Telegram и обычном Mini App chat)
            from bot.services.panda_lazy_service import PandaLazyService

            lazy_service = PandaLazyService(db)
            is_lazy, lazy_message = lazy_service.check_and_update_lazy_state(telegram_id)
            if is_lazy and lazy_message:
                logger.info(f"😴 Mini App Stream: Панда 'ленива' для пользователя {telegram_id}")
                event_data = json.dumps({"content": lazy_message}, ensure_ascii=False)
                await response.write(f"event: message\ndata: {event_data}\n\n".encode())
                await response.write(b"event: done\ndata: {}\n\n")
                return response

        # Отправляем событие начала обработки
        await response.write(b'event: start\ndata: {"status": "processing"}\n\n')

        # Обработка аудио (приоритетнее фото)
        if audio_base64:
            audio_service = MiniappAudioService()
            user_message = await audio_service.process_audio(
                audio_base64, telegram_id, response, language_code=validated.language_code
            )
            if user_message is None:
                # Ошибка уже отправлена через response
                return response

        # Обработка фото
        if photo_base64:
            photo_service = MiniappPhotoService()
            user_message, is_completed = await photo_service.process_photo(
                photo_base64, telegram_id, message, response
            )
            if is_completed:
                # Ответ уже отправлен или ошибка отправлена через response
                return response

        # Если нет ни фото ни аудио - должно быть текстовое сообщение
        if not user_message or not user_message.strip():
            await response.write(
                b'event: error\ndata: {"error": "message, photo or audio required"}\n\n'
            )
            return response

        # Предложение отдыха/игры после 10 или 20 ответов подряд
        with get_db() as db_rest:
            user_rest = UserService(db_rest).get_user_by_telegram_id(telegram_id)
            if user_rest:
                from bot.services.panda_lazy_service import PandaLazyService

                lazy_service = PandaLazyService(db_rest)
                rest_response, _ = lazy_service.check_rest_offer(
                    telegram_id, user_message, user_rest.first_name
                )
                if rest_response:
                    history_service_rest = ChatHistoryService(db_rest)
                    history_service_rest.add_message(telegram_id, user_message, "user")
                    history_service_rest.add_message(telegram_id, rest_response, "ai")
                    db_rest.commit()
                    event_data = json.dumps({"content": rest_response}, ensure_ascii=False)
                    await response.write(f"event: message\ndata: {event_data}\n\n".encode())
                    await response.write(b"event: done\ndata: {}\n\n")
                    return response

        # Нормализация опечаток для маршрутизации и промпта (примеры, подробнее, температура и т.д.)
        from bot.services.typo_normalizer import normalize_common_typos

        normalized_message = normalize_common_typos(user_message)
        msg_for_routing = normalized_message

        # Правила по запрещённым темам отключены — не применяются ни в каком виде

        # Детектор запросов на генерацию изображений
        image_keywords = [
            "нарисуй",
            "нарисовать",
            "рисунок",
            "картинк",
            "изображени",
            "фото",
            "иллюстраци",
            "визуализируй",
            "покажи как выглядит",
            "сгенерируй изображение",
            "создай картинку",
        ]
        is_image_request = any(keyword in msg_for_routing.lower() for keyword in image_keywords)

        logger.debug(
            f"🎨 Stream: Проверка детектора изображений: '{msg_for_routing[:50]}', "
            f"is_image_request={is_image_request}"
        )

        if is_image_request:
            # КРИТИЧНО: Визуализация по нормализованному тексту («график темпереатуры» → график температуры)
            from bot.services.visualization_service import get_visualization_service

            viz_service = get_visualization_service()
            visualization_image, visualization_type = viz_service.detect_visualization_request(
                msg_for_routing
            )

            # Если это НЕ визуализация (не учебный запрос) - генерируем через YandexART
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
                        # Генерируем по нормализованному запросу (все слова учтены)
                        image_bytes = await art_service.generate_image(
                            prompt=msg_for_routing, style="auto", aspect_ratio="1:1"
                        )

                        if image_bytes:
                            # Конвертируем в base64
                            import base64

                            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                            image_data = json.dumps(
                                {"image": image_base64, "type": "generated_image"},
                                ensure_ascii=False,
                            )
                            await response.write(f"event: image\ndata: {image_data}\n\n".encode())

                            # Для не учебных изображений - короткое пояснение
                            caption = "Могу нарисовать что-то по школьным предметам! 📚"
                            event_data = json.dumps({"content": caption}, ensure_ascii=False)
                            await response.write(f"event: message\ndata: {event_data}\n\n".encode())
                            await response.write(b"event: done\ndata: {}\n\n")

                            logger.info(
                                f"🎨 Stream: Изображение сгенерировано для пользователя {telegram_id}"
                            )

                            # Сохраняем в историю с коротким пояснением
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
                            return response
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
                            return response

                    except Exception as e:
                        logger.error(f"❌ Stream: Ошибка генерации изображения: {e}", exc_info=True)
                        error_msg = json.dumps(
                            {"error": "Упс, что-то пошло не так с рисованием. Попробуй снова!"},
                            ensure_ascii=False,
                        )
                        await response.write(f"event: error\ndata: {error_msg}\n\n".encode())
                        return response
            else:
                logger.warning(
                    f"⚠️ Stream: YandexART недоступен (нет API ключей или роли). "
                    f"Запрос: '{user_message[:50]}'"
                )
                # Продолжаем обычную обработку текстом
                logger.info("📝 Stream: Обрабатываем запрос как обычный текст")

        # Секретный запрос для особенного человека
        # Более гибкая проверка с удалением всех пробелов и невидимых символов
        normalized_message = "".join(user_message.split())
        if normalized_message == "<>***<>" or user_message.strip() == "<>***<>":
            special_message = "Создано с любовью для Агаты ❤️❤️❤️"
            event_data = json.dumps({"content": special_message}, ensure_ascii=False)
            await response.write(f"event: message\ndata: {event_data}\n\n".encode())
            await response.write(b"event: done\ndata: {}\n\n")
            logger.info(
                f"💝 Секретное сообщение отправлено пользователю {telegram_id} (Mini App): '{user_message}'"
            )
            return response

        # Модерация: только запрещённые слова (мат). При блоке — вежливый перевод темы, не молчание.
        from bot.services.moderation_service import ContentModerationService

        moderation_service = ContentModerationService()
        is_safe, block_reason = moderation_service.is_safe_content(user_message)
        if not is_safe:
            redirect_text = moderation_service.get_safe_response_alternative(block_reason or "")
            moderation_service.log_blocked_content(
                telegram_id, user_message, block_reason or "модерация"
            )
            event_data = json.dumps({"content": redirect_text}, ensure_ascii=False)
            await response.write(f"event: message\ndata: {event_data}\n\n".encode())
            await response.write(b"event: done\ndata: {}\n\n")
            return response

        with get_db() as db:
            user_service = UserService(db)
            history_service = ChatHistoryService(db)

            user = user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                await response.write(b'event: error\ndata: {"error": "User not found"}\n\n')
                return response

            # Готовим контекст чата через отдельный сервис (SRP)
            from bot.services.miniapp.chat_context_service import MiniappChatContextService

            context_service = MiniappChatContextService(db)
            context = context_service.prepare_context(
                telegram_id=telegram_id,
                user_message=normalized_message,
                skip_premium_check=True,
            )

            # Разворачиваем контекст (берем только нужные объекты)
            yandex_history = context["yandex_history"]
            enhanced_system_prompt = context["system_prompt"]
            is_history_cleared = context["is_history_cleared"]
            premium_service = context["premium_service"]
            history_service = context["history_service"]

            # Проверка Premium (как и раньше, но через premium_service из контекста)
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

            # Отправляем событие начала генерации
            await response.write(b'event: status\ndata: {"status": "generating"}\n\n')

            # Получаем AI service для streaming
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
                enhanced_system_prompt += f"\n\n📚 Дополнительная информация:\n{web_context}\n"

            # Используем Pro модель для всех пользователей (YandexGPT 5 Pro Latest - стабильная версия)
            # Используем модель из настроек (yandexgpt/latest или yandexgpt/rc)
            model_name = settings.yandex_gpt_model
            temperature = settings.ai_temperature  # Основной параметр для всех пользователей
            max_tokens = settings.ai_max_tokens  # Основной параметр для всех пользователей
            logger.info(f"💎 Stream: Используем Pro модель для пользователя {telegram_id}")

            # Отправляем chunks через streaming
            full_response = ""
            try:
                # КРИТИЧНО: Используем IntentService для понимания ВСЕГО запроса
                import re

                from bot.services.miniapp.intent_service import get_intent_service
                from bot.services.visualization_service import get_visualization_service

                intent_service = get_intent_service()
                viz_service = get_visualization_service()

                # Парсим весь запрос пользователя
                intent = intent_service.parse_intent(normalized_message)

                # Детекция визуализаций через новый сервис
                visualization_service = MiniappVisualizationService()
                (
                    specific_visualization_image,
                    multiplication_number,
                    general_table_request,
                    general_graph_request,
                    visualization_type,
                ) = visualization_service.detect_visualization_request(normalized_message, intent)

                # УЛУЧШЕНО: Проверяем запросы на диаграмму в тексте (например, "нарисуй задачу и покажи диаграмму")
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

                # Если запрос на таблицу умножения, график или диаграмму - собираем весь ответ, не отправляем chunks с таблицей
                will_have_visualization = (
                    multiplication_number is not None
                    or general_table_request
                    or general_graph_request
                    or has_diagram_request
                    or specific_visualization_image is not None
                )
                collected_chunks = []  # Для фильтрации

                async for chunk in yandex_service.generate_text_response_stream(
                    user_message=normalized_message,
                    chat_history=yandex_history,
                    system_prompt=enhanced_system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model_name,
                ):
                    full_response += chunk
                    collected_chunks.append(chunk)

                    # Если будет визуализация — не стримим текст: покажем только image + наше пояснение
                    if not will_have_visualization:
                        import json as json_lib

                        chunk_data = json_lib.dumps({"chunk": chunk}, ensure_ascii=False)
                        await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                # Дедупликация и форматирование только по полному ответу (сохраняем ** для жирного)
                full_response = clean_ai_response(full_response)

                # Проверяем, нужна ли визуализация (таблица умножения, графики, диаграммы)
                # multiplication_number уже определен выше, если не был - проверяем в ответе AI
                visualization_image_base64 = None
                try:
                    # УЛУЧШЕНО: Если есть запрос на диаграмму, но специфичная визуализация не найдена - генерируем круговую
                    if has_diagram_request and not specific_visualization_image:
                        try:
                            demo_data = {
                                "Математика": 30,
                                "Русский": 25,
                                "Английский": 20,
                                "Физика": 15,
                                "Химия": 10,
                            }
                            diagram_image = viz_service.generate_pie_chart(demo_data, "Диаграмма")
                            if diagram_image:
                                specific_visualization_image = diagram_image
                                visualization_type = "pie"
                                logger.info(
                                    "📊 Stream: Сгенерирована круговая диаграмма по запросу"
                                )
                        except Exception as e:
                            logger.warning(f"⚠️ Stream: Ошибка генерации диаграммы: {e}")

                    # КРИТИЧНО: Если найдена специфичная визуализация - используем её
                    if specific_visualization_image:
                        try:
                            visualization_image_base64 = viz_service.image_to_base64(
                                specific_visualization_image
                            )
                            logger.info(
                                f"📊 Stream: Использована специфичная визуализация для '{user_message[:50]}' (размер base64: {len(visualization_image_base64) if visualization_image_base64 else 0})"
                            )
                        except Exception as e:
                            logger.error(
                                f"❌ Stream: Ошибка конвертации специфичной визуализации в base64: {e}"
                            )
                            visualization_image_base64 = None
                    # Если не нашли в запросе, проверяем ответ AI
                    elif not multiplication_number:
                        # Паттерны для поиска таблицы умножения в ответе AI
                        multiplication_patterns = [
                            r"табл[иы]ц[аеы]?\s*умножени[яе]\s*на\s*(\d+)",
                            r"табл[иы]ц[аеы]?\s*умножени[яе]\s+(\d+)",
                            r"умножени[яе]\s+на\s*(\d+)",
                            r"умнож[а-я]*\s+(\d+)",
                        ]
                        for pattern in multiplication_patterns:
                            multiplication_match = re.search(pattern, full_response.lower())
                            if multiplication_match:
                                try:
                                    multiplication_number = int(multiplication_match.group(1))
                                    if 1 <= multiplication_number <= 10:
                                        break
                                except (ValueError, IndexError):
                                    continue

                    # Генерируем таблицу умножения используя IntentService
                    # Если intent определил несколько чисел - генерируем комбинированную картинку
                    if intent.kind == "table" and intent.items:
                        # УЛУЧШЕНО: Устанавливаем visualization_type для правильного описания
                        if not visualization_type:
                            visualization_type = "table"
                        multiplication_numbers = [
                            item
                            for item in intent.items
                            if isinstance(item, int) and 1 <= item <= 10
                        ]
                        if multiplication_numbers:
                            if len(multiplication_numbers) > 1:
                                # Несколько таблиц в одной картинке
                                visualization_image = (
                                    viz_service.generate_multiple_multiplication_tables(
                                        multiplication_numbers
                                    )
                                )
                                logger.info(
                                    f"📊 Stream: Сгенерированы таблицы умножения на {multiplication_numbers}"
                                )
                            else:
                                # Одна таблица
                                visualization_image = (
                                    viz_service.generate_multiplication_table_image(
                                        multiplication_numbers[0]
                                    )
                                )
                                logger.info(
                                    f"📊 Stream: Сгенерирована таблица умножения на {multiplication_numbers[0]}"
                                )

                            if visualization_image:
                                visualization_image_base64 = viz_service.image_to_base64(
                                    visualization_image
                                )
                    # Старая логика для обратной совместимости (если intent не сработал)
                    elif multiplication_number:
                        # УЛУЧШЕНО: Устанавливаем visualization_type для правильного описания
                        if not visualization_type:
                            visualization_type = "table"
                        visualization_image = viz_service.generate_multiplication_table_image(
                            multiplication_number
                        )
                        if visualization_image:
                            visualization_image_base64 = viz_service.image_to_base64(
                                visualization_image
                            )
                            logger.info(
                                f"📊 Stream: Сгенерирована таблица умножения на {multiplication_number}"
                            )
                    # ВАЖНО: Генерируем общую таблицу только если нет специфичной визуализации
                    elif (
                        general_table_request
                        and not visualization_image_base64
                        and not specific_visualization_image
                    ):
                        # УЛУЧШЕНО: Устанавливаем visualization_type для правильного описания
                        if not visualization_type:
                            visualization_type = "table"
                        # Генерируем полную таблицу умножения (1-10)
                        # Дополнительная проверка на случай, если специфичная визуализация уже найдена
                        visualization_image = viz_service.generate_full_multiplication_table()
                        if visualization_image:
                            visualization_image_base64 = viz_service.image_to_base64(
                                visualization_image
                            )
                            logger.info("📊 Stream: Сгенерирована полная таблица умножения")

                    # Определяем, нужен ли график функции (расширенный паттерн)
                    if general_graph_request and not visualization_image_base64:
                        # Общий запрос на график - анализируем контекст для определения типа
                        graph_patterns = [
                            r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                            r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                            r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                            r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                            r"(?:синусоид|sin|косинус|cos|тангенс|tan|экспонент|exp|логарифм|log|парабол|порабол|парабола|порабола)",
                        ]
                        graph_match = None
                        user_msg_lower = user_message.lower()
                        for pattern in graph_patterns:
                            graph_match = re.search(pattern, user_msg_lower)
                            if graph_match:
                                break

                        # Если не нашли в запросе, проверяем в ответе AI
                        if not graph_match:
                            for pattern in graph_patterns:
                                graph_match = re.search(pattern, full_response.lower())
                                if graph_match:
                                    break

                    # Если есть график в запросе (не общий запрос)
                    if not general_graph_request and not visualization_image_base64:
                        graph_patterns = [
                            r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                            r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                            r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                            r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
                            r"(?:синусоид|sin|косинус|cos|тангенс|tan|экспонент|exp|логарифм|log|парабол|порабол|парабола|порабола)",
                        ]
                        graph_match = None
                        user_msg_lower = user_message.lower()
                        for pattern in graph_patterns:
                            graph_match = re.search(pattern, user_msg_lower)
                            if graph_match:
                                break

                    # Генерируем комбинированную визуализацию для смешанных запросов (таблица + график)
                    if intent.kind == "both":
                        # УЛУЧШЕНО: Устанавливаем visualization_type для правильного описания
                        # Для комбинированных визуализаций используем специальную обработку в блоке "both"
                        if not visualization_type:
                            visualization_type = "both"
                        # Извлекаем число для таблицы
                        table_numbers_attr = getattr(intent, "table_numbers", [])
                        table_num = None
                        if table_numbers_attr:
                            table_num = table_numbers_attr[0] if table_numbers_attr else None
                        elif intent.items:
                            table_num = next(
                                (
                                    item
                                    for item in intent.items
                                    if isinstance(item, int) and 1 <= item <= 10
                                ),
                                None,
                            )
                        elif multiplication_number:
                            table_num = multiplication_number

                        # Извлекаем выражение для графика
                        graph_functions_attr = getattr(intent, "graph_functions", None)
                        graph_expr = None
                        if graph_functions_attr:
                            graph_expr = graph_functions_attr[0] if graph_functions_attr else None
                        elif intent.items:
                            graph_expr = next(
                                (item for item in intent.items if isinstance(item, str)),
                                None,
                            )

                        # Генерируем комбинированную картинку
                        if table_num and graph_expr:
                            visualization_image = viz_service.generate_combined_table_and_graph(
                                table_num, graph_expr
                            )
                            if visualization_image:
                                visualization_image_base64 = viz_service.image_to_base64(
                                    visualization_image
                                )
                                logger.info(
                                    f"📊📈 Stream: Сгенерирована комбинированная визуализация: "
                                    f"таблица на {table_num} + график {graph_expr}"
                                )
                        else:
                            logger.warning(
                                f"⚠️ Stream: Не удалось извлечь данные для комбинированной визуализации: "
                                f"table_num={table_num}, graph_expr={graph_expr}"
                            )

                    # Генерируем графики используя IntentService (только для kind="graph")
                    elif intent.kind == "graph" and intent.items:
                        # УЛУЧШЕНО: Устанавливаем visualization_type для правильного описания
                        if not visualization_type:
                            visualization_type = "graph"
                        graph_expressions = [item for item in intent.items if isinstance(item, str)]
                        if graph_expressions:
                            if len(graph_expressions) > 1:
                                # Несколько графиков в одной картинке
                                visualization_image = viz_service.generate_multiple_function_graphs(
                                    graph_expressions
                                )
                                logger.info(
                                    f"📈 Stream: Сгенерированы графики функций: {graph_expressions}"
                                )
                            else:
                                # Один график
                                visualization_image = viz_service.generate_function_graph(
                                    graph_expressions[0]
                                )
                                logger.info(
                                    f"📈 Stream: Сгенерирован график функции: {graph_expressions[0]}"
                                )

                            if visualization_image:
                                visualization_image_base64 = viz_service.image_to_base64(
                                    visualization_image
                                )
                    # Старая логика для обратной совместимости
                    elif (general_graph_request or graph_match) and not visualization_image_base64:
                        # Если это запрос на синусоиду/косинус/параболу и т.д. без конкретной формулы
                        user_msg_lower = user_message.lower()
                        logger.info(
                            f"🔍 Stream: Проверка типа графика: general_graph={general_graph_request}, "
                            f"graph_match={bool(graph_match)}, user_msg='{user_message[:50]}'"
                        )
                        # УЛУЧШЕНО: Устанавливаем visualization_type для правильного описания
                        if not visualization_type:
                            visualization_type = "graph"
                        # ИСПРАВЛЕНО: Добавлен "синус" в паттерн для поиска слова "синуса"
                        sin_match = re.search(r"(?:синусоид|sin|синус)", user_msg_lower)
                        logger.info(
                            f"🔍 Stream: Проверка синуса: sin_match={bool(sin_match)}, "
                            f"general_graph={general_graph_request}, graph_match={bool(graph_match)}"
                        )
                        if sin_match or (general_graph_request and not graph_match):
                            # Генерируем стандартный график синуса (для общих запросов или явных запросов на синусоиду)
                            logger.info("🔍 Stream: Вход в блок генерации графика синуса")
                            visualization_image = viz_service.generate_function_graph("sin(x)")
                            logger.info(
                                f"🔍 Stream: generate_function_graph вернул: {type(visualization_image)}, "
                                f"size={len(visualization_image) if visualization_image else 0}"
                            )
                            if visualization_image:
                                visualization_image_base64 = viz_service.image_to_base64(
                                    visualization_image
                                )
                                logger.info(
                                    f"📈 Stream: Сгенерирован график синусоиды, base64 size={len(visualization_image_base64)}"
                                )
                            else:
                                logger.warning(
                                    "⚠️ Stream: generate_function_graph вернул None для sin(x)"
                                )
                        elif re.search(r"(?:косинус|cos)", user_msg_lower):
                            visualization_image = viz_service.generate_function_graph("cos(x)")
                            if visualization_image:
                                visualization_image_base64 = viz_service.image_to_base64(
                                    visualization_image
                                )
                                logger.info("📈 Stream: Сгенерирован график косинуса")
                        elif re.search(r"(?:тангенс|tan|тангенсоид)", user_msg_lower):
                            visualization_image = viz_service.generate_function_graph("tan(x)")
                            if visualization_image:
                                visualization_image_base64 = viz_service.image_to_base64(
                                    visualization_image
                                )
                                logger.info("📈 Stream: Сгенерирован график тангенса")
                        elif re.search(r"(?:парабол|порабол|парабола|порабола)", user_msg_lower):
                            # Парабола y = x^2
                            visualization_image = viz_service.generate_function_graph("x**2")
                            if visualization_image:
                                visualization_image_base64 = viz_service.image_to_base64(
                                    visualization_image
                                )
                                logger.info("📈 Stream: Сгенерирован график параболы")
                        else:
                            expression = (
                                graph_match.group(1).strip() if graph_match.groups() else ""
                            )
                            # УЛУЧШЕНО: Устанавливаем visualization_type для правильного описания
                            if not visualization_type:
                                visualization_type = "graph"
                            # Безопасные выражения для графиков (поддерживаем x^2, x**2, x², x³)
                            if expression:
                                # ИСПРАВЛЕНО: Нормализуем выражение ПЕРЕД проверкой регулярным выражением
                                # Заменяем ², ³, ^ на ** для Python
                                expression = (
                                    expression.replace("²", "**2")
                                    .replace("³", "**3")
                                    .replace("^", "**")
                                )
                                # Проверяем безопасность выражения (после нормализации)
                                if re.match(r"^[x\s+\-*/().\d\s]+$", expression):
                                    visualization_image = viz_service.generate_function_graph(
                                        expression
                                    )
                                    if visualization_image:
                                        visualization_image_base64 = viz_service.image_to_base64(
                                            visualization_image
                                        )
                                        logger.info(
                                            f"📈 Stream: Сгенерирован график функции: {expression}"
                                        )
                                    else:
                                        logger.warning(
                                            f"⚠️ Stream: Не удалось сгенерировать график для выражения: {expression}"
                                        )
                                else:
                                    logger.warning(
                                        f"⚠️ Stream: Выражение не прошло проверку безопасности: {expression}"
                                    )

                except Exception as e:
                    logger.debug(f"⚠️ Stream: Ошибка генерации визуализации: {e}")

                # Отправляем изображение если есть
                if visualization_image_base64:
                    import json as json_lib

                    image_data = json_lib.dumps(
                        {"image": visualization_image_base64, "type": "visualization"},
                        ensure_ascii=False,
                    )
                    await response.write(f"event: image\ndata: {image_data}\n\n".encode())
                    logger.info(
                        f"📊 Stream: Изображение визуализации отправлено (размер: {len(visualization_image_base64)}, специфичная: {bool(specific_visualization_image)})"
                    )

                # КРИТИЧНО: Если пользователь просил «подробно» — сохраняем текст модели (очищенный)
                user_wants_detail = (
                    "подробно" in normalized_message.lower()
                    or "подробнее" in normalized_message.lower()
                )
                if visualization_image_base64 and not user_wants_detail:
                    if intent.kind == "table":
                        # Формируем своё короткое объяснение для таблиц умножения
                        # УЛУЧШЕНО: Добавлены эмодзи и более увлекательные описания
                        import random

                        table_numbers = []
                        # Сначала берем числа, которые IntentService сохранил явно
                        table_numbers_attr = getattr(intent, "table_numbers", [])
                        if table_numbers_attr:
                            table_numbers = [n for n in table_numbers_attr if isinstance(n, int)]
                        elif intent.items:
                            table_numbers = [n for n in intent.items if isinstance(n, int)]
                        elif multiplication_number:
                            table_numbers = [multiplication_number]

                        table_jokes = [
                            "Таблица умножения - это как меню в ресторане, где все блюда (ответы) аккуратно перечислены! 🍽️",
                            "Это как бамбуковый забор, где все числа выстроены в ряд! 🎋",
                            "Таблица умножения - твой лучший друг в математике! 📊",
                        ]

                        if table_numbers:
                            if len(table_numbers) == 1:
                                n = table_numbers[0]
                                full_response = (
                                    f"📊 Это таблица умножения на {n}! "
                                    "Используй её для быстрого счёта: чтобы узнать, чему равно "
                                    f"{n}×5, найди строку с числом {n} и столбец с числом 5. "
                                    f"{random.choice(table_jokes)}"
                                )
                            else:
                                nums_str = ", ".join(str(n) for n in table_numbers)
                                full_response = (
                                    f"📊 Это таблицы умножения на {nums_str}! "
                                    "Выбирай нужное число в заголовке и смотри строку и столбец, "
                                    "чтобы быстро находить результат. "
                                    f"{random.choice(table_jokes)}"
                                )
                        else:
                            full_response = f"📋 Используй эту таблицу для быстрого счёта! {random.choice(table_jokes)}"

                    elif intent.kind == "both":
                        # Смешанный запрос: и таблица, и график.
                        # Полностью формируем собственное короткое пояснение, игнорируя текст модели.
                        logger.info(
                            f"🔍 Stream: Обработка kind='both', intent.items={intent.items}, "
                            f"table_numbers={getattr(intent, 'table_numbers', None)}, "
                            f"graph_functions={getattr(intent, 'graph_functions', None)}"
                        )
                        table_numbers: list[int] = []
                        table_numbers_attr = getattr(intent, "table_numbers", [])
                        if table_numbers_attr:
                            table_numbers = [n for n in table_numbers_attr if isinstance(n, int)]
                        elif intent.items:
                            table_numbers = [n for n in intent.items if isinstance(n, int)]
                        elif multiplication_number:
                            table_numbers = [multiplication_number]

                        # Определяем краткое описание графика (берем первую функцию-строку из graph_functions или intent.items)
                        graph_description = "график функции"
                        graph_functions_attr = getattr(intent, "graph_functions", None)
                        source_funcs = (
                            graph_functions_attr
                            if graph_functions_attr
                            else (intent.items if intent.items else [])
                        )
                        if source_funcs:
                            first_item = source_funcs[0]
                            if isinstance(first_item, str):
                                if "sin" in first_item:
                                    graph_description = "график синусоиды"
                                else:
                                    graph_description = f"график функции {first_item}"

                        parts: list[str] = []

                        if table_numbers:
                            if len(table_numbers) == 1:
                                n = table_numbers[0]
                                parts.append(
                                    f"Это таблица умножения на {n}. "
                                    f"Сначала посмотри в ней примеры с числом {n}, чтобы вспомнить умножение."
                                )
                            else:
                                nums_str = ", ".join(str(n) for n in table_numbers)
                                parts.append(
                                    f"Это таблицы умножения на {nums_str}. "
                                    "Выбирай нужное число и тренируйся находить ответы по строкам и столбцам."
                                )

                        # Описание графика (без "Ниже", так как график уже на картинке)
                        # УЛУЧШЕНО: Добавлены эмодзи и более увлекательные описания
                        import random

                        graph_jokes = [
                            "График показывает путь числа - как будто путешествие по горам! ⛰️",
                            "Кривая на графике - это как след панды в снегу! 🐾",
                            "График - это как дорога, которая показывает, куда идет число! 🛤️",
                        ]
                        if "sin" in graph_description.lower():
                            parts.append(
                                f"📈 На картинке также показан график синусоиды: "
                                "по горизонтали меняется число x, а по вертикали видно, как меняется значение функции. "
                                "Посмотри, как кривая поднимается и опускается, как волны на море! "
                                f"{random.choice(graph_jokes)}"
                            )
                        else:
                            parts.append(
                                f"📈 На картинке также показан {graph_description}: "
                                "по горизонтали меняется число x, а по вертикали видно, как меняется значение функции. "
                                "Посмотри, как кривая поднимается и опускается, и попробуй объяснить это своими словами. "
                                f"{random.choice(graph_jokes)}"
                            )

                        full_response = " ".join(parts)

                    else:
                        # Определяем тип визуализации из детектора или intent
                        if visualization_type:
                            # Используем тип из детектора (более точный)
                            pass
                        else:
                            # Fallback на intent
                            visualization_type = getattr(intent, "kind", None)
                            # УЛУЧШЕНО: Если intent.kind = "graph", устанавливаем visualization_type = "graph"
                            if visualization_type == "graph":
                                visualization_type = "graph"
                            elif visualization_type == "table":
                                visualization_type = "table"

                        # Формируем ПОДРОБНОЕ пояснение для всех типов диаграмм на основе visualization_type
                        # УЛУЧШЕНО: Добавлены эмодзи, шутки и более увлекательные описания для детей
                        if visualization_type:
                            import random

                            # Шутки для разных типов визуализаций
                            jokes = {
                                "bar": [
                                    "Высокие столбцы - это как бамбук, который я люблю! 🎋",
                                    "Столбцы растут как бамбук - чем выше, тем лучше! 🌱",
                                ],
                                "pie": [
                                    "Круговая диаграмма похожа на пиццу - каждый кусочек показывает свою долю! 🍕",
                                    "Это как разрезать торт на части - каждый кусочек важен! 🎂",
                                ],
                                "line": [
                                    "График показывает путь - как путешествие по горам, то вверх, то вниз! ⛰️",
                                    "Линия на графике - это как след панды в снегу! 🐾",
                                ],
                                "histogram": [
                                    "Гистограмма - это как лестница, где каждая ступенька показывает частоту! 📊",
                                    "Высокие столбцы - это как бамбуковые заросли, где растет больше всего! 🌿",
                                ],
                                "scatter": [
                                    "Точечная диаграмма - это как звезды на небе, каждая точка важна! ⭐",
                                    "Точки на графике - это как следы лапок на песке! 🐾",
                                ],
                                "box": [
                                    "Ящик с усами - это как коробка с сюрпризом, где внутри скрыты данные! 📦",
                                    "Это как бамбуковый контейнер - внутри все аккуратно упаковано! 🎋",
                                ],
                                "bubble": [
                                    "Пузырьковая диаграмма - это как мыльные пузыри, чем больше, тем интереснее! 🫧",
                                    "Большие пузыри - это как большие шары, которые я люблю катать! 🎈",
                                ],
                                "heatmap": [
                                    "Тепловая карта - это как погода: красное - жарко, синее - холодно! 🌡️",
                                    "Это как карта сокровищ, где темные места - самые ценные! 🗺️",
                                ],
                                "graph": [
                                    "График функции - это как дорога, которая показывает путь числа! 🛤️",
                                    "Кривая на графике - это как горная тропа, извилистая и интересная! ⛰️",
                                ],
                                "table": [
                                    "Таблица - это как бамбуковый забор, где все аккуратно выстроено в ряд! 🎋",
                                    "Это как меню в ресторане - все блюда (данные) аккуратно перечислены! 📋",
                                ],
                                "map": [
                                    "Карта - это как компас, который показывает, где что находится! 🧭",
                                    "Это как путеводитель по миру, где каждый город - это открытие! 🌍",
                                ],
                            }

                            diagram_explanations = {
                                "bar": "📊 Это столбчатая диаграмма! Она показывает сравнение разных категорий - как будто соревнование, кто выше! "
                                "По горизонтальной оси отложены категории (например, названия фруктов или месяцы), "
                                "а по вертикальной оси - значения (количество, процент и т.д.). "
                                "Чем выше столбец, тем больше значение. Используй её для сравнения данных - например, "
                                "какие фрукты самые популярные или в каком месяце больше всего дождей. "
                                "Обрати внимание на высоту столбцов - они показывают, какие значения больше, а какие меньше. "
                                "Это изучается в математике, 5-6 класс, тема 'Статистика и диаграммы'. "
                                f"{random.choice(jokes.get('bar', ['']))}",
                                "pie": "🥧 Это круговая диаграмма! Она показывает доли от целого - как будто разрезали пирог на кусочки! "
                                "Весь круг представляет 100% (целое), а каждый сектор - часть от этого целого. "
                                "Каждый сектор показывает часть от общего количества. Используй её для показа структуры данных - "
                                "например, сколько времени тратится на разные предметы или какие цвета самые популярные. "
                                "Чем больше сектор, тем больше доля от общего. "
                                "Это изучается в математике, 5-6 класс, тема 'Статистика и диаграммы'. "
                                f"{random.choice(jokes.get('pie', ['']))}",
                                "line": "📈 Это линейный график! Он показывает изменение данных во времени - как будто путешествие во времени! "
                                "По горизонтальной оси обычно откладывается время (дни, месяцы, годы), "
                                "а по вертикальной оси - измеряемая величина (температура, рост, количество и т.д.). "
                                "Линия показывает тренд - как данные растут или уменьшаются. Используй его для анализа изменений - "
                                "например, как меняется температура в течение года или рост растения. "
                                "Если линия идет вверх - данные растут, если вниз - уменьшаются. "
                                "Особые точки: пересечение с осью Y показывает начальное значение, точки перегиба - моменты изменения тренда. "
                                "Важно: если линия горизонтальная (параллельна оси X) - это значит, что значение не меняется, даже если время идет. "
                                "Например, при плавлении льда температура не растет, хотя мы продолжаем греть - вся энергия идет на превращение льда в воду! "
                                "Это изучается в математике, 5-7 класс, тема 'Графики зависимостей'. "
                                f"{random.choice(jokes.get('line', ['']))}",
                                "histogram": "📊 Это гистограмма! Она показывает распределение данных - как будто статистика по группам! "
                                "По горизонтальной оси отложены интервалы значений (диапазоны), "
                                "а по вертикальной оси - частота (сколько раз встречается значение в этом диапазоне). "
                                "Каждый столбец показывает, сколько раз встречается значение в этом диапазоне. "
                                "Используй её для анализа частоты событий - например, сколько учеников получили каждую оценку. "
                                "Высокие столбцы означают, что такие значения встречаются чаще. "
                                "Это изучается в математике, 7-9 класс, тема 'Статистика и вероятность'. "
                                f"{random.choice(jokes.get('histogram', ['']))}",
                                "scatter": "⭐ Это диаграмма рассеяния (точечная)! Она показывает связь между двумя переменными - "
                                "как будто ищешь закономерности в звездном небе! "
                                "По горизонтальной оси отложена одна переменная (например, рост), "
                                "а по вертикальной оси - другая переменная (например, вес). "
                                "Каждая точка - это одно наблюдение. "
                                "Используй её для поиска закономерностей - например, связь между ростом и весом. "
                                "Если точки выстраиваются в линию - есть связь между переменными. "
                                "Если точки разбросаны хаотично - связи нет. "
                                "Это изучается в математике, 7-9 класс, тема 'Статистика и корреляция'. "
                                f"{random.choice(jokes.get('scatter', ['']))}",
                                "box": "📦 Это ящик с усами (box plot)! Он показывает распределение данных - как будто коробка с сюрпризом! "
                                "По горизонтальной оси отложены группы для сравнения, "
                                "а по вертикальной оси - значения измеряемой величины. "
                                "Он показывает медиану, квартили и выбросы. Используй его для сравнения групп данных - "
                                "например, результаты разных классов. Центральная линия - это медиана, коробка показывает средние 50% данных. "
                                "Это изучается в математике, 7-9 класс, тема 'Статистика и анализ данных'. "
                                f"{random.choice(jokes.get('box', ['']))}",
                                "bubble": "🫧 Это пузырьковая диаграмма! Она похожа на точечную, но размер пузырька "
                                "показывает третье измерение - как будто мыльные пузыри разного размера! "
                                "По горизонтальной оси отложена одна переменная (например, население), "
                                "по вертикальной оси - другая переменная (например, ВВП), "
                                "а размер пузырька показывает третью переменную (например, площадь). "
                                "Используй её для анализа трёх переменных одновременно - например, население, площадь и ВВП стран. "
                                "Большие пузыри означают большие значения третьей переменной. "
                                "Это изучается в математике, 7-9 класс, тема 'Многомерный анализ данных'. "
                                f"{random.choice(jokes.get('bubble', ['']))}",
                                "heatmap": "🌡️ Это тепловая карта! Она показывает интенсивность значений с помощью цвета - "
                                "как будто карта погоды! "
                                "По горизонтальной оси отложены одни категории (например, дни недели), "
                                "по вертикальной оси - другие категории (например, часы дня), "
                                "а цвет ячейки показывает значение (например, количество посетителей). "
                                "Чем темнее цвет, тем больше значение. "
                                "Используй её для анализа матриц данных - например, активность по дням и часам. "
                                "Темные области показывают высокие значения, светлые - низкие. "
                                "Это изучается в математике, 7-9 класс, тема 'Статистика и визуализация данных'. "
                                f"{random.choice(jokes.get('heatmap', ['']))}",
                                "graph": "📐 Это график функции! Он показывает, как меняется значение функции "
                                "в зависимости от переменной - как будто дорога, которая показывает путь числа! "
                                "По горизонтальной оси (ось X) откладывается значение аргумента (переменной), "
                                "а по вертикальной оси (ось Y) - значение функции. "
                                "Используй его для изучения свойств функций - например, как ведет себя парабола или синусоида. "
                                "Обрати внимание на форму линии - она показывает характер изменения функции. "
                                "Особые точки: пересечение с осью Y показывает значение функции при x=0, "
                                "пересечение с осью X - нули функции, вершина (для параболы) - экстремум. "
                                "Это изучается в алгебре, 7-9 класс, тема 'Функции и их графики'. "
                                f"{random.choice(jokes.get('graph', ['']))}",
                                "table": "📋 Это таблица! Она систематизирует данные в строках и столбцах - "
                                "как будто аккуратно разложенные бамбуковые палочки! "
                                "Строки показывают отдельные объекты или записи, "
                                "а столбцы - их свойства или характеристики. "
                                "Используй её для быстрого поиска информации - например, таблица умножения или расписание. "
                                "Каждая строка - это одна запись, каждый столбец - это одно свойство. "
                                "Пересечение строки и столбца дает конкретное значение. "
                                f"{random.choice(jokes.get('table', ['']))}",
                                "map": "🗺️ Это карта! Она показывает расположение объектов на местности - "
                                "как будто путеводитель по миру! "
                                "На карте показаны географические координаты: широта (север-юг) и долгота (восток-запад). "
                                "Используй её для изучения географии и навигации - "
                                "например, где находятся страны или как добраться до места. "
                                "Обрати внимание на масштаб и условные обозначения - они помогают понять карту. "
                                "Центр карты показывает запрошенное место, границы - административные деления. "
                                "Это изучается в географии, 5-9 класс, тема 'Картография и ориентирование'. "
                                f"{random.choice(jokes.get('map', ['']))}",
                            }

                            explanation = diagram_explanations.get(visualization_type)
                            if explanation:
                                # Добавляем случайное уточнение "понятно ли?"
                                from bot.services.yandex_ai_response_generator import (
                                    add_random_engagement_question,
                                )

                                full_response = add_random_engagement_question(explanation)
                                logger.info(
                                    f"📝 Stream: Сформировано подробное пояснение для типа {visualization_type}"
                                )
                            else:
                                # Если тип неизвестен - используем общее пояснение
                                # УЛУЧШЕНО: Общее пояснение с эмодзи и шуткой
                                import random

                                from bot.services.yandex_ai_response_generator import (
                                    add_random_engagement_question,
                                )

                                general_jokes = [
                                    "Это как бамбуковый сад - все данные аккуратно организованы! 🎋",
                                    "Визуализация - это как карта сокровищ, где каждый элемент важен! 🗺️",
                                    "Изучи визуализацию внимательно - она расскажет тебе много интересного! 📊",
                                ]
                                base_text = (
                                    "📊 Это визуализация данных! Изучи её внимательно и попробуй объяснить, "
                                    f"что она показывает. {random.choice(general_jokes)}"
                                )
                                full_response = add_random_engagement_question(base_text)
                        else:
                            # КРИТИЧНО: Удаляем дублирование таблицы умножения текстом (если модель всё же написала)
                            # Но СОХРАНЯЕМ полноценное объяснение - не обрезаем до 2 предложений!
                            multiplication_duplicate_patterns = [
                                r"\d+\s*[×x*]\s*\d+\s*=\s*\d+",
                                r"\d+\s+\d+\s*=\s*\d+",
                            ]
                            for pattern in multiplication_duplicate_patterns:
                                full_response = re.sub(
                                    pattern, "", full_response, flags=re.IGNORECASE
                                )

                            # Удаляем множественные пробелы, но СОХРАНЯЕМ абзацы (двойные переносы)
                            full_response = re.sub(r"[ \t]+", " ", full_response)
                            full_response = re.sub(r"\n{3,}", "\n\n", full_response)
                            full_response = full_response.strip()

                            # НЕ обрезаем до 2 предложений!
                            # Пользователь хочет ПОЛНОЦЕННЫЕ пояснения под визуализацией

                        # Удаляем упоминания про автоматическую генерацию
                        if visualization_image_base64:
                            full_response = (
                                visualization_service.postprocess_text_for_visualization(
                                    full_response,
                                    intent,
                                    visualization_image_base64,
                                    multiplication_number,
                                )
                            )

                        full_response = _format_visualization_explanation(full_response)

                        # Если при визуализации модель отказалась — подменяем на нейтральное пояснение
                        if visualization_image_base64 and _is_refusal_like(full_response):
                            full_response = (
                                "📐 Вот визуализация. Изучи её — по осям отложены данные. "
                                "Если нужны подробности, спроси!"
                            )
                            logger.info(
                                "🔄 Stream: Текст модели — отказ; подменено на пояснение к визуализации"
                            )

                        logger.info(
                            f"✅ Stream: Полноценное пояснение к визуализации (длина: {len(full_response)}): {full_response[:100]}"
                        )

                # Ограничиваем размер полного ответа
                MAX_RESPONSE_LENGTH = 4000
                full_response_for_db = full_response
                if len(full_response) > MAX_RESPONSE_LENGTH:
                    full_response = full_response[:MAX_RESPONSE_LENGTH] + "\n\n... (ответ обрезан)"

                # Сохраняем в историю
                try:
                    limit_reached, total_requests = premium_service.increment_request_count(
                        telegram_id
                    )

                    # Проактивное уведомление от панды при достижении лимита (в чат + в Telegram)
                    if limit_reached:
                        asyncio.create_task(
                            premium_service.send_limit_reached_notification_async(telegram_id)
                        )
                        limit_msg = premium_service.get_limit_reached_message_text()
                        history_service.add_message(telegram_id, limit_msg, "ai")
                    history_service.add_message(telegram_id, user_message, "user")
                    # Формируем image_url из base64 если есть визуализация
                    image_url = None
                    if visualization_image_base64:
                        image_url = f"data:image/png;base64,{visualization_image_base64}"
                    history_service.add_message(
                        telegram_id, full_response_for_db, "ai", image_url=image_url
                    )
                    from bot.services.panda_lazy_service import PandaLazyService

                    PandaLazyService(db).increment_consecutive_after_ai(telegram_id)

                    # Если история была очищена и пользователь, возможно, назвал имя или класс
                    if is_history_cleared and not user.skip_name_asking:
                        # Извлекаем имя
                        if not user.first_name:
                            extracted_name, is_refusal = extract_user_name_from_message(
                                user_message
                            )
                            if is_refusal:
                                user.skip_name_asking = True
                                logger.info(
                                    "✅ Stream: Пользователь отказался называть имя, устанавливаем флаг skip_name_asking"
                                )
                            elif extracted_name:
                                user.first_name = extracted_name
                                logger.info(
                                    f"✅ Stream: Имя пользователя обновлено: {user.first_name}"
                                )

                        # Извлекаем класс
                        if not user.grade:
                            extracted_grade = extract_user_grade_from_message(user_message)
                            if extracted_grade:
                                user.grade = extracted_grade
                                logger.info(f"✅ Stream: Класс пользователя обновлен: {user.grade}")

                    # Геймификация
                    unlocked_achievements = []
                    try:
                        from bot.services.gamification_service import GamificationService

                        gamification_service = GamificationService(db)
                        unlocked_achievements = gamification_service.process_message(
                            telegram_id, user_message
                        )
                    except Exception as e:
                        logger.error(f"❌ Stream: Ошибка геймификации: {e}", exc_info=True)

                    db.commit()

                    # Отправляем информацию о достижениях если есть
                    if unlocked_achievements:
                        await send_achievements_event(response, unlocked_achievements)

                except Exception as save_error:
                    logger.error(f"❌ Stream: Ошибка сохранения: {save_error}", exc_info=True)
                    db.rollback()

                # Всегда отправляем финальное сообщение с очищенным (дедуплицированным) текстом:
                # при визуализации — пояснение; без неё — полный ответ (убирает повторы от модели)
                if full_response:
                    msg_data = json.dumps({"content": full_response}, ensure_ascii=False)
                    await response.write(f"event: message\ndata: {msg_data}\n\n".encode())

                # Сообщение от панды при достижении лимита (в чат, как при приветствии)
                if limit_reached:
                    limit_data = json.dumps(
                        {"content": premium_service.get_limit_reached_message_text()},
                        ensure_ascii=False,
                    )
                    await response.write(f"event: message\ndata: {limit_data}\n\n".encode())

                # Отправляем событие завершения
                await response.write(b'event: done\ndata: {"status": "completed"}\n\n')
                logger.info(f"✅ Stream: Streaming завершен для {telegram_id}")

            except (
                httpx.HTTPStatusError,
                httpx.TimeoutException,
                httpx.RequestError,
            ) as stream_error:
                # Ошибка YandexGPT API - пытаемся fallback на не-streaming запрос
                logger.warning(
                    f"⚠️ Stream: Ошибка streaming (HTTP {getattr(stream_error, 'response', None) and stream_error.response.status_code or 'unknown'}): {stream_error}"
                )
                logger.info(f"🔄 Stream: Пробуем fallback на не-streaming запрос для {telegram_id}")

                try:
                    # Fallback на не-streaming запрос
                    ai_response = await yandex_service.generate_text_response(
                        user_message=normalized_message,
                        chat_history=yandex_history,
                        system_prompt=enhanced_system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        model=model_name,
                    )

                    if ai_response:
                        # Очищаем ответ
                        cleaned_response = clean_ai_response(ai_response)

                        # Проверяем, нужна ли визуализация (fallback случай)
                        visualization_image_base64 = None
                        try:
                            import re

                            from bot.services.visualization_service import get_visualization_service

                            viz_service = get_visualization_service()

                            # Определяем, нужна ли таблица умножения (расширенные паттерны для fallback)
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
                                        multiplication_number_fallback = int(
                                            multiplication_match.group(1)
                                        )
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
                                visualization_image = (
                                    viz_service.generate_multiplication_table_image(
                                        multiplication_number_fallback
                                    )
                                )
                                if visualization_image:
                                    visualization_image_base64 = viz_service.image_to_base64(
                                        visualization_image
                                    )
                                    logger.info(
                                        f"📊 Stream: Fallback - сгенерирована таблица умножения на {multiplication_number_fallback}"
                                    )
                            elif general_table_fallback:
                                visualization_image = (
                                    viz_service.generate_full_multiplication_table()
                                )
                                if visualization_image:
                                    visualization_image_base64 = viz_service.image_to_base64(
                                        visualization_image
                                    )
                                    logger.info(
                                        "📊 Stream: Fallback - сгенерирована полная таблица умножения"
                                    )

                            # Определяем, нужен ли график функции (расширенный паттерн для fallback)
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

                            if (
                                general_graph_fallback or graph_match
                            ) and not visualization_image_base64:
                                # Если это запрос на синусоиду/косинус/параболу и т.д. без конкретной формулы
                                if (
                                    re.search(r"(?:синусоид|sin)", combined_text_lower)
                                    or general_graph_fallback
                                ):
                                    visualization_image = viz_service.generate_function_graph(
                                        "sin(x)"
                                    )
                                    if visualization_image:
                                        visualization_image_base64 = viz_service.image_to_base64(
                                            visualization_image
                                        )
                                        logger.info(
                                            "📈 Stream: Fallback - сгенерирован график синусоиды"
                                        )
                                elif re.search(r"(?:косинус|cos)", combined_text_lower):
                                    visualization_image = viz_service.generate_function_graph(
                                        "cos(x)"
                                    )
                                    if visualization_image:
                                        visualization_image_base64 = viz_service.image_to_base64(
                                            visualization_image
                                        )
                                        logger.info(
                                            "📈 Stream: Fallback - сгенерирован график косинуса"
                                        )
                                elif re.search(r"(?:парабол)", combined_text_lower):
                                    visualization_image = viz_service.generate_function_graph(
                                        "x**2"
                                    )
                                    if visualization_image:
                                        visualization_image_base64 = viz_service.image_to_base64(
                                            visualization_image
                                        )
                                        logger.info(
                                            "📈 Stream: Fallback - сгенерирован график параболы"
                                        )
                                else:
                                    expression = (
                                        graph_match.group(1).strip() if graph_match.groups() else ""
                                    )
                                    if expression and re.match(r"^[x\s+\-*/().\d\s]+$", expression):
                                        # Нормализуем выражение: заменяем ², ³, ^ на ** для Python
                                        safe_expr = (
                                            expression.replace("²", "**2")
                                            .replace("³", "**3")
                                            .replace("^", "**")
                                        )
                                        visualization_image = viz_service.generate_function_graph(
                                            safe_expr
                                        )
                                    if visualization_image:
                                        visualization_image_base64 = viz_service.image_to_base64(
                                            visualization_image
                                        )
                                        logger.info(
                                            f"📈 Stream: Fallback - сгенерирован график функции: {expression}"
                                        )

                        except Exception as e:
                            logger.debug(f"⚠️ Stream: Fallback - ошибка генерации визуализации: {e}")

                        # Отправляем изображение если есть
                        if visualization_image_base64:
                            import json as json_lib

                            image_data = json_lib.dumps(
                                {"image": visualization_image_base64, "type": "visualization"},
                                ensure_ascii=False,
                            )
                            await response.write(f"event: image\ndata: {image_data}\n\n".encode())
                            logger.info("📊 Stream: Fallback - изображение визуализации отправлено")

                            # Если есть визуализация таблицы умножения - даём полноценное пояснение
                            if multiplication_number_fallback:
                                logger.info(
                                    f"🔍 Stream: Fallback с визуализацией таблицы умножения (число={multiplication_number_fallback})"
                                )

                                # Полноценное пояснение вместо короткого ответа
                                cleaned_response = (
                                    f"Вот таблица умножения на {multiplication_number_fallback}!\n\n"
                                    f"Как пользоваться таблицей: найди число {multiplication_number_fallback} в левой колонке, "
                                    f"а второй множитель — в верхней строке. На пересечении — ответ.\n\n"
                                    f"Например, чтобы найти {multiplication_number_fallback} × 5, "
                                    f"смотри строку {multiplication_number_fallback} и столбец 5.\n\n"
                                    f"Таблица умножения пригодится для быстрого счёта в магазине, "
                                    f"при решении задач и в повседневной жизни."
                                )

                                logger.info(
                                    "✅ Stream: Fallback - добавлено полноценное пояснение к таблице умножения"
                                )

                            # Дополнительная очистка уже выполняется в clean_ai_response,
                            # здесь не дублируем специальные паттерны.

                            # Удаляем упоминания про автоматическую генерацию
                            if visualization_image_base64:
                                # В fallback случае intent может быть не определен, создаем пустой
                                from bot.services.miniapp.intent_service import VisualizationIntent

                                fallback_intent = (
                                    intent
                                    if "intent" in locals()
                                    else VisualizationIntent(
                                        kind="table" if multiplication_number_fallback else "graph"
                                    )
                                )
                                cleaned_response = (
                                    visualization_service.postprocess_text_for_visualization(
                                        cleaned_response,
                                        fallback_intent,
                                        visualization_image_base64,
                                        multiplication_number_fallback,
                                    )
                                )

                            # Делаем первые 1–2 предложения кратким жирным резюме
                            cleaned_response = _format_visualization_explanation(cleaned_response)
                            if visualization_image_base64 and _is_refusal_like(cleaned_response):
                                cleaned_response = (
                                    "📐 Вот визуализация. Изучи её — по осям отложены данные. "
                                    "Если нужны подробности, спроси!"
                                )

                        # Отправляем полный ответ как один chunk
                        import json as json_lib

                        chunk_data = json_lib.dumps({"chunk": cleaned_response}, ensure_ascii=False)
                        await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                        # Сохраняем в историю
                        try:
                            limit_reached, total_requests = premium_service.increment_request_count(
                                telegram_id
                            )

                            # Проактивное уведомление от панды при достижении лимита (в чат + в Telegram)
                            if limit_reached:
                                asyncio.create_task(
                                    premium_service.send_limit_reached_notification_async(
                                        telegram_id
                                    )
                                )
                                limit_msg_fb = premium_service.get_limit_reached_message_text()
                                history_service.add_message(telegram_id, limit_msg_fb, "ai")
                            history_service.add_message(telegram_id, user_message, "user")
                            # Формируем image_url из base64 если есть визуализация
                            image_url = None
                            if visualization_image_base64:
                                image_url = f"data:image/png;base64,{visualization_image_base64}"
                            history_service.add_message(
                                telegram_id, cleaned_response, "ai", image_url=image_url
                            )
                            from bot.services.panda_lazy_service import PandaLazyService

                            PandaLazyService(db).increment_consecutive_after_ai(telegram_id)
                            db.commit()
                            logger.info(
                                f"✅ Stream: Fallback успешен, ответ сохранен для {telegram_id}"
                            )
                        except Exception as save_err:
                            logger.error(
                                f"❌ Stream: Ошибка сохранения fallback ответа: {save_err}"
                            )
                            db.rollback()

                        # Сообщение от панды при достижении лимита (в чат)
                        if limit_reached:
                            limit_data_fb = json.dumps(
                                {"content": premium_service.get_limit_reached_message_text()},
                                ensure_ascii=False,
                            )
                            await response.write(
                                f"event: message\ndata: {limit_data_fb}\n\n".encode()
                            )

                        # Отправляем событие завершения
                        await response.write(b'event: done\ndata: {"status": "completed"}\n\n')
                        logger.info(f"✅ Stream: Fallback streaming завершен для {telegram_id}")
                    else:
                        raise ValueError("AI response is empty")

                except Exception as fallback_error:
                    # Если и fallback не помог - возвращаем ошибку пользователю
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
