"""
Endpoints для streaming AI чата через SSE.
"""

import json
from contextlib import suppress

import httpx
from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import AIChatRequest
from bot.database import get_db
from bot.services import ChatHistoryService, UserService
from bot.services.ai_service_solid import get_ai_service
from bot.services.miniapp_audio_service import MiniappAudioService
from bot.services.miniapp_photo_service import MiniappPhotoService
from bot.services.miniapp_visualization_service import MiniappVisualizationService
from bot.services.yandex_ai_response_generator import clean_ai_response

from .helpers import extract_user_name_from_message, send_achievements_event


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
            logger.error(f"❌ Stream: ошибка парсинга JSON: {json_error}", exc_info=True)
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

        # Отправляем событие начала обработки
        await response.write(b'event: start\ndata: {"status": "processing"}\n\n')

        # Обработка аудио (приоритетнее фото)
        if audio_base64:
            audio_service = MiniappAudioService()
            user_message = await audio_service.process_audio(audio_base64, telegram_id, response)
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

        with get_db() as db:
            user_service = UserService(db)
            history_service = ChatHistoryService(db)

            user = user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                await response.write(b'event: error\ndata: {"error": "User not found"}\n\n')
                return response

            # Готовим контекст чата через отдельный сервис (SRP)
            from bot.services.miniapp_chat_context_service import MiniappChatContextService

            context_service = MiniappChatContextService(db)
            context = context_service.prepare_context(
                telegram_id=telegram_id,
                user_message=user_message,
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

            # Проверка на провокационные вопросы о запрещенных темах
            from bot.monitoring import log_user_activity
            from bot.services.moderation_service import ContentModerationService

            moderation_service = ContentModerationService()
            if moderation_service.is_provocative_question(user_message):
                logger.warning(
                    f"🚫 Stream: Провокационный вопрос от {telegram_id}: {user_message[:50]}..."
                )
                log_user_activity(
                    telegram_id, "provocative_question", False, "question_about_forbidden_topics"
                )

                # Вежливо перенаправляем на учебу
                safe_response = (
                    "Я помогаю с учебой и школьными предметами! 📚\n\n"
                    "Могу помочь с:\n"
                    "• Математикой (задачи, примеры, формулы)\n"
                    "• Русским языком (правила, орфография, грамматика)\n"
                    "• Историей (даты, события, эпохи)\n"
                    "• Географией (страны, карты, природные зоны)\n"
                    "• Физикой, химией, биологией\n"
                    "• Литературой и иностранными языками\n\n"
                    "Задай вопрос по любому школьному предмету! 🐼"
                )
                await send_achievements_event(response, telegram_id, "message_sent")
                await response.write(
                    f'event: message\ndata: {{"text": {json.dumps(safe_response, ensure_ascii=False)}}}\n\n'.encode()
                )
                await response.write(b"event: done\ndata: {}\n\n")
                return response

            # Отправляем событие начала генерации
            await response.write(b'event: status\ndata: {"status": "generating"}\n\n')

            # Получаем AI service для streaming
            ai_service = get_ai_service()
            response_generator = ai_service.response_generator
            yandex_service = response_generator.yandex_service

            # Получаем веб-контекст
            from bot.config import settings

            relevant_materials = await response_generator.knowledge_service.get_helpful_content(
                user_message, user.age
            )
            web_context = response_generator.knowledge_service.format_knowledge_for_ai(
                relevant_materials
            )

            # Добавляем веб-контекст к промпту, если он есть
            if web_context:
                enhanced_system_prompt += f"\n\n📚 Дополнительная информация:\n{web_context}"

            # Используем Pro модель для всех пользователей (YandexGPT 5 Pro Latest - стабильная версия)
            # Формат yandexgpt/latest - как в примере из Yandex Cloud Console
            model_name = "yandexgpt/latest"
            temperature = settings.ai_temperature  # Основной параметр для всех пользователей
            max_tokens = settings.ai_max_tokens  # Основной параметр для всех пользователей
            logger.info(f"💎 Stream: Используем Pro модель для пользователя {telegram_id}")

            # Отправляем chunks через streaming
            full_response = ""
            try:
                # КРИТИЧНО: Используем IntentService для понимания ВСЕГО запроса
                import re

                from bot.services.miniapp_intent_service import get_intent_service
                from bot.services.visualization_service import get_visualization_service

                intent_service = get_intent_service()
                viz_service = get_visualization_service()

                # Парсим весь запрос пользователя
                intent = intent_service.parse_intent(user_message)

                # Детекция визуализаций через новый сервис
                visualization_service = MiniappVisualizationService()
                (
                    specific_visualization_image,
                    multiplication_number,
                    general_table_request,
                    general_graph_request,
                    visualization_type,
                ) = visualization_service.detect_visualization_request(user_message, intent)

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
                        re.search(pattern, user_message.lower()) for pattern in diagram_patterns
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
                    user_message=user_message,
                    chat_history=yandex_history,
                    system_prompt=enhanced_system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model_name,
                ):
                    # Очищаем chunk от запрещенных символов
                    cleaned_chunk = clean_ai_response(chunk)
                    full_response += cleaned_chunk
                    collected_chunks.append(cleaned_chunk)

                    # Если будет визуализация - НЕ отправляем chunks с таблицей умножения
                    if will_have_visualization:
                        # Проверяем, содержит ли chunk таблицу умножения (оба паттерна!)
                        multiplication_text_pattern = re.compile(
                            r"\d+\s*[×x*]\s*\d+\s*=\s*\d+", re.IGNORECASE
                        )
                        # КРИТИЧНО: паттерн БЕЗ символа умножения - именно такой формат приходит от AI
                        multiplication_text_pattern_no_symbol = re.compile(
                            r"\d+\s+\d+\s*=\s*\d+", re.IGNORECASE
                        )
                        if not multiplication_text_pattern.search(
                            cleaned_chunk
                        ) and not multiplication_text_pattern_no_symbol.search(cleaned_chunk):
                            # Отправляем только chunks без таблицы умножения
                            import json as json_lib

                            chunk_data = json_lib.dumps(
                                {"chunk": cleaned_chunk}, ensure_ascii=False
                            )
                            await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())
                    else:
                        # Обычная отправка всех chunks
                        import json as json_lib

                        chunk_data = json_lib.dumps({"chunk": cleaned_chunk}, ensure_ascii=False)
                        await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                # Очищаем полный ответ от запрещенных символов
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

                # КРИТИЧНО: Если есть визуализация - даем только короткое объяснение
                # Для таблиц умножения полностью игнорируем текст от модели и формируем своё пояснение
                # Для графиков - обрезаем ответ до 1-2 предложений без воды и дублей
                if visualization_image_base64:
                    # Удаляем упоминания про "систему автоматически" и подобное
                    patterns_to_remove = [
                        r"(?:систем[аеы]?\s+)?автоматически\s+сгенериру[ею]т?\s+(?:изображени[ея]?|диаграмм[аеыу]?|график[и]?|таблиц[аеыу]?|карт[аеыу]?)",
                        r"систем[аеы]?\s+сгенериру[ею]т?\s+(?:изображени[ея]?|диаграмм[аеыу]?|график[и]?|таблиц[аеыу]?|карт[аеыу]?)\s+автоматически",
                        r"покажу\s+(?:график|диаграмм[аеыу]?|таблиц[аеыу]?|карт[аеыу]?).*?систем[аеы]?\s+автоматически",
                        r"систем[аеы]?\s+уже\s+сгенерировал[аи]?\s+(?:изображени[ея]?|диаграмм[аеыу]?|график[и]?|таблиц[аеыу]?|карт[аеыу]?)",
                        r"систем[аеы]?\s+автоматически\s+добавит",
                    ]
                    for pattern in patterns_to_remove:
                        full_response = re.sub(pattern, "", full_response, flags=re.IGNORECASE)

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
                            multiplication_duplicate_patterns = [
                                r"\d+\s*[×x*]\s*\d+\s*=\s*\d+",
                                r"\d+\s+\d+\s*=\s*\d+",
                            ]
                            for pattern in multiplication_duplicate_patterns:
                                full_response = re.sub(
                                    pattern, "", full_response, flags=re.IGNORECASE
                                )

                            # Удаляем множественные пробелы и пустые строки
                            full_response = re.sub(r"\s+", " ", full_response)
                            full_response = re.sub(r"\n\s*\n", "\n", full_response)

                            # Если ответ слишком длинный (больше 2 предложений) - обрезаем до первых 2
                            sentences = re.split(r"[.!?]+\s+", full_response.strip())
                            if len(sentences) > 2:
                                meaningful_sentences = [
                                    s.strip()
                                    for s in sentences[:2]
                                    if s.strip() and len(s.strip()) > 10
                                ]
                                if meaningful_sentences:
                                    full_response = ". ".join(meaningful_sentences)
                                    if not full_response.endswith((".", "!", "?")):
                                        full_response += "."
                                else:
                                    full_response = ". ".join(sentences[:2])
                                    if not full_response.endswith((".", "!", "?")):
                                        full_response += "."

                        logger.info(
                            f"✅ Stream: Текст обрезан до короткого объяснения (есть визуализация): {full_response[:100]}"
                        )

                # Ограничиваем размер полного ответа
                MAX_RESPONSE_LENGTH = 4000
                full_response_for_db = full_response
                if len(full_response) > MAX_RESPONSE_LENGTH:
                    full_response = full_response[:MAX_RESPONSE_LENGTH] + "\n\n... (ответ обрезан)"

                # Сохраняем в историю
                try:
                    premium_service.increment_request_count(telegram_id)
                    history_service.add_message(telegram_id, user_message, "user")
                    # Формируем image_url из base64 если есть визуализация
                    image_url = None
                    if visualization_image_base64:
                        image_url = f"data:image/png;base64,{visualization_image_base64}"
                    history_service.add_message(
                        telegram_id, full_response_for_db, "ai", image_url=image_url
                    )

                    # Если история была очищена и пользователь, возможно, назвал имя
                    if is_history_cleared and not user.first_name and not user.skip_name_asking:
                        extracted_name, is_refusal = extract_user_name_from_message(user_message)
                        if is_refusal:
                            user.skip_name_asking = True
                            logger.info(
                                "✅ Stream: Пользователь отказался называть имя, устанавливаем флаг skip_name_asking"
                            )
                        elif extracted_name:
                            user.first_name = extracted_name
                            logger.info(f"✅ Stream: Имя пользователя обновлено: {user.first_name}")

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
                        user_message=user_message,
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

                            # Если есть визуализация - заменяем весь текст на короткий ответ
                            # Не пытаемся удалять фрагменты - это ломает ответ!
                            if multiplication_number_fallback:
                                logger.info(
                                    f"🔍 Stream: Fallback ДО замены (multiplication_number={multiplication_number_fallback}): {cleaned_response[:200]}"
                                )

                                # Просто заменяем весь ответ на короткий, если есть визуализация
                                cleaned_response = "Вот таблица умножения."

                                logger.info(
                                    f"✅ Stream: Fallback - текст заменен на короткий ответ (есть визуализация): {cleaned_response}"
                                )

                            # Удаляем упоминания про "систему автоматически" и подобное
                            patterns_to_remove = [
                                r"(?:систем[аеы]?\s+)?автоматически\s+сгенериру[ею]т?\s+(?:изображени[ея]?|диаграмм[аеыу]?|график[и]?|таблиц[аеыу]?|карт[аеыу]?)",
                                r"систем[аеы]?\s+сгенериру[ею]т?\s+(?:изображени[ея]?|диаграмм[аеыу]?|график[и]?|таблиц[аеыу]?|карт[аеыу]?)\s+автоматически",
                                r"покажу\s+(?:график|диаграмм[аеыу]?|таблиц[аеыу]?|карт[аеыу]?).*?систем[аеы]?\s+автоматически",
                                r"систем[аеы]?\s+уже\s+сгенерировал[аи]?\s+(?:изображени[ея]?|диаграмм[аеыу]?|график[и]?|таблиц[аеыу]?|карт[аеыу]?)",
                                r"систем[аеы]?\s+автоматически\s+добавит",
                            ]
                            for pattern in patterns_to_remove:
                                cleaned_response = re.sub(
                                    pattern, "", cleaned_response, flags=re.IGNORECASE
                                )

                        # Отправляем полный ответ как один chunk
                        import json as json_lib

                        chunk_data = json_lib.dumps({"chunk": cleaned_response}, ensure_ascii=False)
                        await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                        # Сохраняем в историю
                        try:
                            premium_service.increment_request_count(telegram_id)
                            history_service.add_message(telegram_id, user_message, "user")
                            # Формируем image_url из base64 если есть визуализация
                            image_url = None
                            if visualization_image_base64:
                                image_url = f"data:image/png;base64,{visualization_image_base64}"
                            history_service.add_message(
                                telegram_id, cleaned_response, "ai", image_url=image_url
                            )
                            db.commit()
                            logger.info(
                                f"✅ Stream: Fallback успешен, ответ сохранен для {telegram_id}"
                            )
                        except Exception as save_err:
                            logger.error(
                                f"❌ Stream: Ошибка сохранения fallback ответа: {save_err}"
                            )
                            db.rollback()

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
