"""
Endpoints для streaming AI чата через SSE.
"""

import base64
from contextlib import suppress

import httpx
from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import AIChatRequest
from bot.database import get_db
from bot.services import ChatHistoryService, UserService
from bot.services.ai_service_solid import get_ai_service
from bot.services.speech_service import get_speech_service
from bot.services.translate_service import get_translate_service
from bot.services.vision_service import VisionService
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
            try:
                logger.info(f"🎤 Stream: Обработка голосового сообщения от {telegram_id}")

                # Отправляем событие обработки аудио
                await response.write(b'event: status\ndata: {"status": "transcribing"}\n\n')

                # Убираем data:audio/...;base64, префикс
                if "base64," in audio_base64:
                    audio_base64 = audio_base64.split("base64,")[1]

                MAX_AUDIO_BASE64_SIZE = 14 * 1024 * 1024  # 14MB
                if len(audio_base64) > MAX_AUDIO_BASE64_SIZE:
                    error_msg = 'event: error\ndata: {"error": "Аудио слишком большое"}\n\n'
                    await response.write(error_msg.encode("utf-8"))
                    return response

                audio_bytes = base64.b64decode(audio_base64)

                if len(audio_bytes) > 10 * 1024 * 1024:  # 10MB
                    error_msg = 'event: error\ndata: {"error": "Аудио слишком большое"}\n\n'
                    await response.write(error_msg.encode("utf-8"))
                    return response

                speech_service = get_speech_service()
                transcribed_text = await speech_service.transcribe_voice(audio_bytes, language="ru")

                if not transcribed_text or not transcribed_text.strip():
                    error_msg = 'event: error\ndata: {"error": "Не удалось распознать речь"}\n\n'
                    await response.write(error_msg.encode("utf-8"))
                    return response

                # Определяем язык и переводим если нужно
                translate_service = get_translate_service()
                detected_lang = await translate_service.detect_language(transcribed_text)

                if (
                    detected_lang
                    and detected_lang != "ru"
                    and detected_lang in translate_service.SUPPORTED_LANGUAGES
                ):
                    lang_name = translate_service.get_language_name(detected_lang)
                    translated_text = await translate_service.translate_text(
                        transcribed_text, target_language="ru", source_language=detected_lang
                    )
                    if translated_text:
                        user_message = (
                            f"🌍 Вижу, что ты сказал на {lang_name}!\n\n"
                            f"📝 Оригинал: {transcribed_text}\n"
                            f"🇷🇺 Перевод: {translated_text}\n\n"
                            f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                        )
                    else:
                        user_message = transcribed_text
                else:
                    user_message = transcribed_text

                logger.info(f"✅ Stream: Аудио распознано: {transcribed_text[:100]}")
                await response.write(b'event: status\ndata: {"status": "transcribed"}\n\n')

            except Exception as e:
                logger.error(f"❌ Stream: Ошибка обработки аудио: {e}", exc_info=True)
                await response.write(
                    f'event: error\ndata: {{"error": "Ошибка обработки аудио: {str(e)}"}}\n\n'.encode()
                )
                return response

        # Обработка фото
        if photo_base64:
            try:
                logger.info(f"📷 Stream: Обработка фото от {telegram_id}")

                # Отправляем событие обработки фото
                await response.write(b'event: status\ndata: {"status": "analyzing_photo"}\n\n')

                # Убираем data:image/...;base64, префикс
                if "base64," in photo_base64:
                    photo_base64 = photo_base64.split("base64,")[1]

                photo_bytes = base64.b64decode(photo_base64)

                with get_db() as db:
                    user_service = UserService(db)
                    user = user_service.get_user_by_telegram_id(telegram_id)

                    if not user:
                        await response.write(b'event: error\ndata: {"error": "User not found"}\n\n')
                        return response

                    vision_service = VisionService()
                    vision_result = await vision_service.analyze_image(
                        image_data=photo_bytes,
                        user_message=message
                        or "Проанализируй это фото с заданием и реши задачу полностью",
                        user_age=user.age,
                    )

                    logger.info("✅ Stream: Фото проанализировано")
                    await response.write(b'event: status\ndata: {"status": "photo_analyzed"}\n\n')

                    # Проверяем, что анализ не является сообщением об ошибке
                    is_error_message = vision_result.analysis and (
                        "Не удалось проанализировать" in vision_result.analysis
                        or "Временная проблема с AI сервисом" in vision_result.analysis
                        or "Ошибка анализа" in vision_result.analysis
                    )

                    # КРИТИЧЕСКИ ВАЖНО: Если Vision API дал готовый ответ - сразу отправляем его!
                    if (
                        vision_result.analysis
                        and vision_result.analysis.strip()
                        and not is_error_message
                    ):
                        # Vision API уже решил задачу - отправляем ответ напрямую
                        full_response = clean_ai_response(vision_result.analysis)

                        # Отправляем ответ через streaming
                        import json as json_lib

                        chunk_data = json_lib.dumps({"chunk": full_response}, ensure_ascii=False)
                        await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                        # Сохраняем в историю
                        try:
                            from bot.services.premium_features_service import PremiumFeaturesService

                            premium_service = PremiumFeaturesService(db)
                            history_service = ChatHistoryService(db)

                            premium_service.increment_request_count(telegram_id)
                            user_msg_text = message or "📷 Фото"
                            history_service.add_message(telegram_id, user_msg_text, "user")
                            history_service.add_message(telegram_id, full_response, "ai")

                            # Геймификация
                            unlocked_achievements = []
                            try:
                                from bot.services.gamification_service import GamificationService

                                gamification_service = GamificationService(db)
                                unlocked_achievements = gamification_service.process_message(
                                    telegram_id, user_msg_text
                                )
                            except Exception as e:
                                logger.error(f"❌ Stream: Ошибка геймификации: {e}", exc_info=True)

                            db.commit()

                            # Отправляем информацию о достижениях если есть
                            if unlocked_achievements:
                                await send_achievements_event(response, unlocked_achievements)
                        except Exception as save_error:
                            logger.error(
                                f"❌ Stream: Ошибка сохранения: {save_error}", exc_info=True
                            )
                            db.rollback()

                        # Отправляем событие завершения
                        await response.write(b'event: done\ndata: {"status": "completed"}\n\n')
                        logger.info(f"✅ Stream: Фото ответ отправлен напрямую для {telegram_id}")
                        return response

                    # Если Vision API вернул ошибку - отправляем ошибку пользователю
                    if is_error_message:
                        logger.error(
                            f"❌ Stream: Vision API вернул ошибку для фото от {telegram_id}"
                        )
                        error_msg = 'event: error\ndata: {"error": "Временная проблема с AI сервисом. Попробуйте позже."}\n\n'
                        await response.write(error_msg.encode("utf-8"))
                        return response

                    # Если Vision API не дал готовый ответ - используем распознанный текст
                    if vision_result.recognized_text:
                        user_message = f"На фото написано: {vision_result.recognized_text}\n\nПомоги решить эту задачу полностью."
                    else:
                        user_message = message or "Помоги мне разобраться с этой задачей"

            except Exception as e:
                logger.error(f"❌ Stream: Ошибка обработки фото: {e}", exc_info=True)
                await response.write(
                    f'event: error\ndata: {{"error": "Ошибка обработки фото: {str(e)}"}}\n\n'.encode()
                )
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

            # Проверка Premium
            from bot.services.premium_features_service import PremiumFeaturesService

            premium_service = PremiumFeaturesService(db)
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

            # Загружаем историю
            history_limit = 50 if premium_service.is_premium_active(telegram_id) else 10
            history = history_service.get_formatted_history_for_ai(telegram_id, limit=history_limit)

            # Проверяем, была ли очистка истории (история пустая)
            is_history_cleared = len(history) == 0

            # Подсчитываем количество сообщений пользователя с последнего обращения по имени
            # Ищем последнее обращение по имени в истории (ищем в ответах AI)
            user_message_count = 0
            if user.first_name:
                # Ищем последнее обращение по имени в ответах AI (ищем имя в тексте)
                last_name_mention_index = -1
                for i, msg in enumerate(history):
                    if (
                        msg.get("role") == "assistant"
                        and user.first_name.lower() in msg.get("text", "").lower()
                    ):
                        last_name_mention_index = i
                        break

                # Считаем сообщения пользователя ПОСЛЕ последнего обращения по имени
                if last_name_mention_index >= 0:
                    # Есть обращение по имени - считаем сообщения после него
                    user_message_count = sum(
                        1
                        for msg in history[last_name_mention_index + 1 :]
                        if msg.get("role") == "user"
                    )
                else:
                    # Нет обращения по имени - считаем все сообщения пользователя
                    user_message_count = sum(1 for msg in history if msg.get("role") == "user")
            else:
                # Нет имени - считаем все сообщения пользователя
                user_message_count = sum(1 for msg in history if msg.get("role") == "user")

            # Определяем, является ли вопрос образовательным
            educational_keywords = [
                "математика",
                "алгебра",
                "геометрия",
                "арифметика",
                "русский",
                "литература",
                "сочинение",
                "диктант",
                "история",
                "география",
                "биология",
                "физика",
                "химия",
                "английский",
                "немецкий",
                "французский",
                "испанский",
                "информатика",
                "программирование",
                "задача",
                "решить",
                "решение",
                "пример",
                "уравнение",
                "урок",
                "домашнее",
                "задание",
                "дз",
                "контрольная",
                "объясни",
                "помоги",
                "как решить",
                "как сделать",
                "сколько",
                "вычисли",
                "посчитай",
                "найди",
                "таблица",
                "умножение",
                "деление",
                "сложение",
                "вычитание",
            ]

            user_message_lower = user_message.lower()
            is_educational = any(keyword in user_message_lower for keyword in educational_keywords)

            # Обновляем счетчик непредметных вопросов
            if is_educational:
                # Если вопрос образовательный - сбрасываем счетчик
                user.non_educational_questions_count = 0
            else:
                # Если непредметный - увеличиваем счетчик
                user.non_educational_questions_count += 1

            # Отправляем событие начала генерации
            await response.write(b'event: status\ndata: {"status": "generating"}\n\n')

            # Получаем AI service для streaming
            ai_service = get_ai_service()
            response_generator = ai_service.response_generator
            yandex_service = response_generator.yandex_service

            # Получаем веб-контекст
            from bot.config import settings
            from bot.services.prompt_builder import get_prompt_builder

            relevant_materials = await response_generator.knowledge_service.get_helpful_content(
                user_message, user.age
            )
            web_context = response_generator.knowledge_service.format_knowledge_for_ai(
                relevant_materials
            )

            # Используем PromptBuilder для формирования промпта
            prompt_builder = get_prompt_builder()
            enhanced_system_prompt = prompt_builder.build_system_prompt(
                user_age=user.age,
                user_name=user.first_name,
                message_count_since_name=user_message_count,
                is_history_cleared=is_history_cleared,
                chat_history=history,
                user_message=user_message,
                non_educational_questions_count=user.non_educational_questions_count,
                is_auto_greeting_sent=False,  # Определяется на фронтенде, здесь всегда False
                is_educational=is_educational,
            )

            # Добавляем веб-контекст к промпту, если он есть
            if web_context:
                enhanced_system_prompt += f"\n\n📚 Дополнительная информация:\n{web_context}"

            # Преобразуем историю в формат Yandex
            yandex_history = []
            if history:
                for msg in history[-10:]:
                    role = msg.get("role", "user")  # Используем роль напрямую
                    text = msg.get("text", "").strip()
                    if text:
                        yandex_history.append({"role": role, "text": text})

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

                # #region agent log
                import json as json_lib_debug

                debug_log_path = r"c:\Users\Vyacheslav\PandaPal\.cursor\debug.log"
                try:
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(
                            json_lib_debug.dumps(
                                {
                                    "timestamp": __import__("time").time() * 1000,
                                    "location": "miniapp_endpoints.py:1545",
                                    "message": "Детекция визуализации - начало",
                                    "data": {"user_message": user_message[:100]},
                                    "sessionId": "debug-session",
                                    "runId": "detection",
                                    "hypothesisId": "A",
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                except Exception:
                    pass
                # #endregion

                # Преобразуем сообщение в нижний регистр ОДИН РАЗ для всех проверок
                user_msg_lower = user_message.lower()

                # Расширенные паттерны для таблиц умножения (конкретные числа)
                multiplication_patterns = [
                    r"табл[иы]ц[аеы]?\s*умножени[яе]\s*на\s*(\d+)",
                    r"табл[иы]ц[аеы]?\s*умножени[яе]\s+(\d+)",
                    r"умножени[яе]\s+на\s*(\d+)",
                    r"умнож[а-я]*\s+(\d+)",
                ]

                # Функция проверки контекста: есть ли в запросе специфичные слова
                def has_specific_context(text: str) -> bool:
                    """
                    Проверяет, есть ли в запросе специфичные слова,
                    указывающие на конкретный тип таблицы/графика.

                    Args:
                        text: Текст запроса в нижнем регистре

                    Returns:
                        True если есть специфичный контекст, False если общий запрос
                    """
                    specific_keywords = [
                        # Таблицы по предметам
                        r"глагол",
                        r"падеж",
                        r"алфавит",
                        r"букв",
                        r"звук",
                        r"орфограф",
                        r"пунктуац",
                        r"морфемн",
                        r"стил\s+реч",
                        r"сопряжени[яе]",
                        r"спряжени[яе]",
                        r"времен[а]?\s+год",
                        r"месяц",
                        r"дн[ия]?\s+недел",
                        r"часов[ые]?\s+пояс",
                        r"страны?",
                        r"хронологи",
                        r"ветв[и]?\s+власт",
                        r"систем[ы]?\s+счислени",
                        r"природн[ые]?\s+зон",
                        r"растворимост",
                        r"валентност",
                        r"менделеева",
                        r"периодическая",
                        r"констант",
                        r"плотност",
                        r"теплоемкост",
                        r"сопротивлени",
                        r"неправильн",
                        r"времен[а]?\s+(?:английск|англ)",
                        # Графики с контекстом
                        r"график\s+(?:пути|путь|скорост|движени[яе])",
                        r"график\s+(?:функци[яи]|y\s*=|x\s*\*\*|sin|cos|tan|log|sqrt)",
                        r"график\s+(?:закон|ома|гука|парабол|линейн)",
                        r"график\s+(?:температур|плавлени|кристаллизац)",
                        r"график\s+(?:изотерм|изобар|изохор)",
                        r"график\s+(?:переменн[ый]?\s+ток|ac\s+current)",
                    ]
                    return any(re.search(keyword, text) for keyword in specific_keywords)

                # Общие паттерны для запросов на таблицы (без числа)
                # ВАЖНО: Эти паттерны имеют ВЫСОКИЙ ПРИОРИТЕТ - срабатывают при явных запросах
                general_table_patterns = [
                    r"состав[ьи]\s+табл[иы]ц[аеы]?",
                    r"пришли\s+табл[иы]ц[аеы]?",
                    r"покажи\s+табл[иы]ц[аеы]?",
                    r"сделай\s+табл[иы]ц[аеы]?",
                    r"нарисуй\s+табл[иы]ц[аеы]?",
                    r"построй\s+табл[иы]ц[аеы]?",
                    r"выведи\s+табл[иы]ц[аеы]?",
                    r"дай\s+табл[иы]ц[аеы]?",
                    r"нужн[аы]?\s+табл[иы]ц[аеы]?",
                    r"табл[иы]ц[аеы]?\s*(?:пришли|покажи|сделай|нарисуй|состав[ьи]|построй|дай)",
                    r"покажи\s+умножени[яе]",
                    r"табл[иы]ц[аеы]?\s*умножени[яе](?:\s+на\s+все)?",
                    r"полную\s+табл[иы]ц[аеы]?\s*умножени[яе]",
                    r"хочу\s+табл[иы]ц[аеы]?",
                ]
                # Расширенные паттерны для графиков
                # ВАЖНО: Эти паттерны имеют ВЫСОКИЙ ПРИОРИТЕТ - срабатывают при явных запросах
                general_graph_patterns = [
                    r"состав[ьи]\s+график",
                    r"пришли\s+график",
                    r"покажи\s+график",
                    r"сделай\s+график",
                    r"нарисуй\s+график",
                    r"построй\s+график",
                    r"выведи\s+график",
                    r"дай\s+график",
                    r"нужен\s+график",
                    r"хочу\s+график",
                    r"график\s+(?:покажи|нарисуй|построй|сделай|выведи)",
                ]

                # КРИТИЧНО: Сначала проверяем специфичные таблицы через detect_visualization_request
                # Это должно быть ДО проверки общих паттернов, чтобы не перехватывать специфичные запросы
                specific_visualization_image = None
                try:
                    # #region agent log
                    try:
                        with open(debug_log_path, "a", encoding="utf-8") as f:
                            f.write(
                                json_lib_debug.dumps(
                                    {
                                        "timestamp": __import__("time").time() * 1000,
                                        "location": "miniapp_endpoints.py:1611",
                                        "message": "Вызов detect_visualization_request",
                                        "data": {
                                            "user_message": user_message,
                                            "user_message_lower": user_msg_lower,
                                        },
                                        "sessionId": "debug-session",
                                        "runId": "detection",
                                        "hypothesisId": "A",
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    except Exception:
                        pass
                    # #endregion
                    specific_visualization_image = viz_service.detect_visualization_request(
                        user_message
                    )

                    # Если IntentService определил несколько таблиц умножения, игнорируем одиночную
                    # специфичную визуализацию и будем генерировать комбинированную картинку
                    try:
                        multiple_table_intent = (
                            intent.kind == "table"
                            and isinstance(intent.items, list)
                            and len([n for n in intent.items if isinstance(n, int)]) > 1
                        )
                    except Exception:
                        multiple_table_intent = False

                    if multiple_table_intent and specific_visualization_image is not None:
                        logger.info(
                            f"🔄 Stream: Игнорируем специфичную визуализацию для множественных таблиц: {intent.items}"
                        )
                        specific_visualization_image = None
                    # #region agent log
                    try:
                        with open(debug_log_path, "a", encoding="utf-8") as f:
                            f.write(
                                json_lib_debug.dumps(
                                    {
                                        "timestamp": __import__("time").time() * 1000,
                                        "location": "miniapp_endpoints.py:1635",
                                        "message": "Результат detect_visualization_request",
                                        "data": {
                                            "has_image": specific_visualization_image is not None,
                                            "image_size": len(specific_visualization_image)
                                            if specific_visualization_image
                                            else 0,
                                        },
                                        "sessionId": "debug-session",
                                        "runId": "detection",
                                        "hypothesisId": "C",
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    except Exception:
                        pass
                    # #endregion
                    if specific_visualization_image:
                        logger.info(
                            f"📊 Детектирована специфичная визуализация: '{user_message[:50]}'"
                        )
                        # #region agent log
                        try:
                            with open(debug_log_path, "a", encoding="utf-8") as f:
                                f.write(
                                    json_lib_debug.dumps(
                                        {
                                            "timestamp": __import__("time").time() * 1000,
                                            "location": "miniapp_endpoints.py:1607",
                                            "message": "Специфичная визуализация найдена",
                                            "data": {
                                                "user_message": user_message[:50],
                                                "image_size": len(specific_visualization_image),
                                            },
                                            "sessionId": "debug-session",
                                            "runId": "detection",
                                            "hypothesisId": "SPECIFIC",
                                        },
                                        ensure_ascii=False,
                                    )
                                    + "\n"
                                )
                        except Exception:
                            pass
                        # #endregion
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при детекции специфичной визуализации: {e}")

                # Проверяем конкретные таблицы умножения (с числом) - только если специфичная визуализация не найдена
                multiplication_number = None
                if not specific_visualization_image:
                    for pattern in multiplication_patterns:
                        multiplication_match = re.search(pattern, user_msg_lower)
                        if multiplication_match:
                            try:
                                multiplication_number = int(multiplication_match.group(1))
                                if 1 <= multiplication_number <= 10:
                                    # #region agent log
                                    try:
                                        with open(debug_log_path, "a", encoding="utf-8") as f:
                                            f.write(
                                                json_lib_debug.dumps(
                                                    {
                                                        "timestamp": __import__("time").time()
                                                        * 1000,
                                                        "location": "miniapp_endpoints.py:1638",
                                                        "message": "Детектирована таблица умножения с числом",
                                                        "data": {
                                                            "number": multiplication_number,
                                                            "pattern": pattern,
                                                        },
                                                        "sessionId": "debug-session",
                                                        "runId": "detection",
                                                        "hypothesisId": "A",
                                                    },
                                                    ensure_ascii=False,
                                                )
                                                + "\n"
                                            )
                                    except Exception:
                                        pass
                                    # #endregion
                                    break
                            except (ValueError, IndexError):
                                continue

                # Проверяем общие запросы на таблицы (без числа)
                # ИЗМЕНЕНО: Убрана блокировка has_specific_context - явные запросы "покажи/нарисуй" имеют приоритет
                # ВАЖНО: Только если специфичная визуализация не найдена и нет числа для умножения
                general_table_request = None
                has_context = has_specific_context(user_msg_lower)
                # #region agent log
                try:
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(
                            json_lib_debug.dumps(
                                {
                                    "timestamp": __import__("time").time() * 1000,
                                    "location": "miniapp_endpoints.py:1774",
                                    "message": "Проверка контекста запроса",
                                    "data": {
                                        "user_message": user_message[:100],
                                        "has_specific_context": has_context,
                                        "has_specific_visualization": specific_visualization_image
                                        is not None,
                                        "multiplication_number": multiplication_number,
                                    },
                                    "sessionId": "debug-session",
                                    "runId": "detection",
                                    "hypothesisId": "D",
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                except Exception:
                    pass
                # #endregion
                # ИЗМЕНЕНО: Убрана проверка has_context - явные запросы "покажи/нарисуй таблицу" должны срабатывать всегда
                if not specific_visualization_image and not multiplication_number:
                    for pattern in general_table_patterns:
                        if re.search(pattern, user_msg_lower):
                            general_table_request = True
                            logger.info(
                                f"📊 Детектирован общий запрос на таблицу: '{user_message[:50]}', pattern: {pattern}"
                            )
                            # #region agent log
                            try:
                                with open(debug_log_path, "a", encoding="utf-8") as f:
                                    f.write(
                                        json_lib_debug.dumps(
                                            {
                                                "timestamp": __import__("time").time() * 1000,
                                                "location": "miniapp_endpoints.py:1676",
                                                "message": "Детектирован общий запрос на таблицу",
                                                "data": {
                                                    "pattern": pattern,
                                                    "user_message": user_message[:100],
                                                },
                                                "sessionId": "debug-session",
                                                "runId": "detection",
                                                "hypothesisId": "B",
                                            },
                                            ensure_ascii=False,
                                        )
                                        + "\n"
                                    )
                            except Exception:
                                pass
                            # #endregion
                            break

                # Проверяем общие запросы на графики
                # ИЗМЕНЕНО: Убрана проверка has_specific_context - явные запросы "покажи/нарисуй график" должны срабатывать всегда
                general_graph_request = None
                for pattern in general_graph_patterns:
                    if re.search(pattern, user_msg_lower):
                        general_graph_request = True
                        logger.info(
                            f"📈 Детектирован общий запрос на график: '{user_message[:50]}', pattern: {pattern}"
                        )
                        # #region agent log
                        try:
                            with open(debug_log_path, "a", encoding="utf-8") as f:
                                f.write(
                                    json_lib_debug.dumps(
                                        {
                                            "timestamp": __import__("time").time() * 1000,
                                            "location": "miniapp_endpoints.py:1591",
                                            "message": "Детектирован общий запрос на график",
                                            "data": {
                                                "pattern": pattern,
                                                "user_message": user_message[:100],
                                            },
                                            "sessionId": "debug-session",
                                            "runId": "detection",
                                            "hypothesisId": "C",
                                        },
                                        ensure_ascii=False,
                                    )
                                    + "\n"
                                )
                        except Exception:
                            pass
                        # #endregion
                        break

                # Если запрос на таблицу умножения или график - собираем весь ответ, не отправляем chunks с таблицей
                will_have_visualization = (
                    multiplication_number is not None
                    or general_table_request
                    or general_graph_request
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
                        # #region agent log
                        if multiplication_text_pattern.search(
                            cleaned_chunk
                        ) or multiplication_text_pattern_no_symbol.search(cleaned_chunk):
                            logger.debug(
                                f"🚫 Stream: Chunk отфильтрован (содержит таблицу): {cleaned_chunk[:50]}"
                            )
                        # #endregion
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

                # Проверяем, нужна ли визуализация (таблица умножения, графики)
                # multiplication_number уже определен выше, если не был - проверяем в ответе AI
                visualization_image_base64 = None
                try:
                    # #region agent log
                    try:
                        with open(debug_log_path, "a", encoding="utf-8") as f:
                            f.write(
                                json_lib_debug.dumps(
                                    {
                                        "timestamp": __import__("time").time() * 1000,
                                        "location": "miniapp_endpoints.py:1820",
                                        "message": "Начало генерации визуализации",
                                        "data": {
                                            "has_specific_visualization": bool(
                                                specific_visualization_image
                                            ),
                                            "multiplication_number": multiplication_number,
                                            "general_table_request": general_table_request,
                                            "general_graph_request": general_graph_request,
                                            "full_response_length": len(full_response),
                                        },
                                        "sessionId": "debug-session",
                                        "runId": "generation",
                                        "hypothesisId": "A",
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    except Exception:
                        pass
                    # #endregion

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
                        # #region agent log
                        try:
                            with open(debug_log_path, "a", encoding="utf-8") as f:
                                f.write(
                                    json_lib_debug.dumps(
                                        {
                                            "timestamp": __import__("time").time() * 1000,
                                            "location": "miniapp_endpoints.py:1850",
                                            "message": "Специфичная визуализация использована",
                                            "data": {
                                                "user_message": user_message[:50],
                                                "image_size": len(visualization_image_base64),
                                            },
                                            "sessionId": "debug-session",
                                            "runId": "generation",
                                            "hypothesisId": "SPECIFIC",
                                        },
                                        ensure_ascii=False,
                                    )
                                    + "\n"
                                )
                        except Exception:
                            pass
                        # #endregion
                    # Если не нашли в запросе, проверяем ответ AI
                    elif not multiplication_number:
                        for pattern in multiplication_patterns:
                            multiplication_match = re.search(pattern, full_response.lower())
                            if multiplication_match:
                                try:
                                    multiplication_number = int(multiplication_match.group(1))
                                    if 1 <= multiplication_number <= 10:
                                        # #region agent log
                                        try:
                                            with open(debug_log_path, "a", encoding="utf-8") as f:
                                                f.write(
                                                    json_lib_debug.dumps(
                                                        {
                                                            "timestamp": __import__("time").time()
                                                            * 1000,
                                                            "location": "miniapp_endpoints.py:1636",
                                                            "message": "Найдено число в ответе AI",
                                                            "data": {
                                                                "number": multiplication_number
                                                            },
                                                            "sessionId": "debug-session",
                                                            "runId": "generation",
                                                            "hypothesisId": "A",
                                                        },
                                                        ensure_ascii=False,
                                                    )
                                                    + "\n"
                                                )
                                        except Exception:
                                            pass
                                        # #endregion
                                        break
                                except (ValueError, IndexError):
                                    continue

                    # Генерируем таблицу умножения используя IntentService
                    # Если intent определил несколько чисел - генерируем комбинированную картинку
                    if intent.kind == "table" and intent.items:
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
                            # #region agent log
                            try:
                                with open(debug_log_path, "a", encoding="utf-8") as f:
                                    f.write(
                                        json_lib_debug.dumps(
                                            {
                                                "timestamp": __import__("time").time() * 1000,
                                                "location": "miniapp_endpoints.py:1654",
                                                "message": "Таблица умножения сгенерирована",
                                                "data": {
                                                    "number": multiplication_number,
                                                    "image_size": len(visualization_image_base64),
                                                },
                                                "sessionId": "debug-session",
                                                "runId": "generation",
                                                "hypothesisId": "A",
                                            },
                                            ensure_ascii=False,
                                        )
                                        + "\n"
                                    )
                            except Exception:
                                pass
                            # #endregion
                    # ВАЖНО: Генерируем общую таблицу только если нет специфичной визуализации
                    elif (
                        general_table_request
                        and not visualization_image_base64
                        and not specific_visualization_image
                    ):
                        # Генерируем полную таблицу умножения (1-10)
                        # Дополнительная проверка на случай, если специфичная визуализация уже найдена
                        visualization_image = viz_service.generate_full_multiplication_table()
                        if visualization_image:
                            visualization_image_base64 = viz_service.image_to_base64(
                                visualization_image
                            )
                            logger.info("📊 Stream: Сгенерирована полная таблица умножения")
                            # #region agent log
                            try:
                                with open(debug_log_path, "a", encoding="utf-8") as f:
                                    f.write(
                                        json_lib_debug.dumps(
                                            {
                                                "timestamp": __import__("time").time() * 1000,
                                                "location": "miniapp_endpoints.py:1672",
                                                "message": "Полная таблица умножения сгенерирована",
                                                "data": {
                                                    "image_size": len(visualization_image_base64)
                                                },
                                                "sessionId": "debug-session",
                                                "runId": "generation",
                                                "hypothesisId": "B",
                                            },
                                            ensure_ascii=False,
                                        )
                                        + "\n"
                                    )
                            except Exception:
                                pass
                            # #endregion

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
                        for pattern in graph_patterns:
                            graph_match = re.search(pattern, user_msg_lower)
                            if graph_match:
                                break

                    # Генерируем графики используя IntentService
                    # Если intent определил несколько функций - генерируем комбинированную картинку
                    if intent.kind in ("graph", "both") and intent.items:
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
                        logger.info(
                            f"🔍 Stream: Проверка типа графика: general_graph={general_graph_request}, "
                            f"graph_match={bool(graph_match)}, user_msg='{user_message[:50]}'"
                        )
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
                                # #region agent log
                                try:
                                    with open(debug_log_path, "a", encoding="utf-8") as f:
                                        f.write(
                                            json_lib_debug.dumps(
                                                {
                                                    "timestamp": __import__("time").time() * 1000,
                                                    "location": "miniapp_endpoints.py:1699",
                                                    "message": "График синусоиды сгенерирован",
                                                    "data": {
                                                        "is_general_request": general_graph_request,
                                                        "image_size": len(
                                                            visualization_image_base64
                                                        ),
                                                    },
                                                    "sessionId": "debug-session",
                                                    "runId": "generation",
                                                    "hypothesisId": "C",
                                                },
                                                ensure_ascii=False,
                                            )
                                            + "\n"
                                        )
                                except Exception:
                                    pass
                                # #endregion
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
                                # #region agent log
                                try:
                                    with open(debug_log_path, "a", encoding="utf-8") as f:
                                        f.write(
                                            json_lib_debug.dumps(
                                                {
                                                    "timestamp": __import__("time").time() * 1000,
                                                    "location": "miniapp_endpoints.py:1989",
                                                    "message": "График параболы сгенерирован",
                                                    "data": {
                                                        "image_size": len(
                                                            visualization_image_base64
                                                        )
                                                    },
                                                    "sessionId": "debug-session",
                                                    "runId": "generation",
                                                    "hypothesisId": "C",
                                                },
                                                ensure_ascii=False,
                                            )
                                            + "\n"
                                        )
                                except Exception:
                                    pass
                                # #endregion
                        else:
                            expression = (
                                graph_match.group(1).strip() if graph_match.groups() else ""
                            )
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

                    # #region agent log
                    try:
                        with open(debug_log_path, "a", encoding="utf-8") as f:
                            f.write(
                                json_lib_debug.dumps(
                                    {
                                        "timestamp": __import__("time").time() * 1000,
                                        "location": "miniapp_endpoints.py:2279",
                                        "message": "Отправка изображения визуализации",
                                        "data": {
                                            "image_size": len(visualization_image_base64),
                                            "has_image": True,
                                            "has_specific": bool(specific_visualization_image),
                                            "multiplication_number": multiplication_number,
                                            "general_table": general_table_request,
                                            "general_graph": general_graph_request,
                                        },
                                        "sessionId": "debug-session",
                                        "runId": "image_send",
                                        "hypothesisId": "D",
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    except Exception:
                        pass
                    # #endregion

                    image_data = json_lib.dumps(
                        {"image": visualization_image_base64, "type": "visualization"},
                        ensure_ascii=False,
                    )
                    await response.write(f"event: image\ndata: {image_data}\n\n".encode())
                    logger.info(
                        f"📊 Stream: Изображение визуализации отправлено (размер: {len(visualization_image_base64)}, специфичная: {bool(specific_visualization_image)})"
                    )
                else:
                    # #region agent log
                    try:
                        with open(debug_log_path, "a", encoding="utf-8") as f:
                            f.write(
                                json_lib_debug.dumps(
                                    {
                                        "timestamp": __import__("time").time() * 1000,
                                        "location": "miniapp_endpoints.py:1732",
                                        "message": "Изображение НЕ отправлено - не сгенерировано",
                                        "data": {
                                            "multiplication_number": multiplication_number,
                                            "general_table": general_table_request,
                                            "general_graph": general_graph_request,
                                        },
                                        "sessionId": "debug-session",
                                        "runId": "image_send",
                                        "hypothesisId": "D",
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    except Exception:
                        pass
                    # #endregion

                # КРИТИЧНО: Если есть визуализация - даем только короткое объяснение
                # Для таблиц умножения полностью игнорируем текст от модели и формируем своё пояснение
                # Для графиков - обрезаем ответ до 1-2 предложений без воды и дублей
                if visualization_image_base64:
                    # Удаляем упоминания про "систему автоматически" и подобное
                    full_response = re.sub(
                        r"(?:систем[аеы]?\s+)?автоматически\s+сгенериру[ею]т?\s+изображени[ея]?",
                        "",
                        full_response,
                        flags=re.IGNORECASE,
                    )
                    full_response = re.sub(
                        r"покажу\s+график.*?систем[аеы]?\s+автоматически",
                        "Вот график",
                        full_response,
                        flags=re.IGNORECASE,
                    )

                    if intent.kind == "table":
                        # Формируем своё короткое объяснение для таблиц умножения
                        table_numbers = []
                        # Сначала берем числа, которые IntentService сохранил явно
                        table_numbers_attr = getattr(intent, "table_numbers", [])
                        if table_numbers_attr:
                            table_numbers = [n for n in table_numbers_attr if isinstance(n, int)]
                        elif intent.items:
                            table_numbers = [n for n in intent.items if isinstance(n, int)]
                        elif multiplication_number:
                            table_numbers = [multiplication_number]

                        if table_numbers:
                            if len(table_numbers) == 1:
                                n = table_numbers[0]
                                full_response = (
                                    f"Это таблица умножения на {n}. "
                                    "Используй её для быстрого счёта: чтобы узнать, чему равно "
                                    f"{n}×5, найди строку с числом {n} и столбец с числом 5."
                                )
                            else:
                                nums_str = ", ".join(str(n) for n in table_numbers)
                                full_response = (
                                    f"Это таблицы умножения на {nums_str}. "
                                    "Выбирай нужное число в заголовке и смотри строку и столбец, "
                                    "чтобы быстро находить результат."
                                )
                        else:
                            full_response = "Используй эту таблицу для быстрого счёта."

                    elif intent.kind == "both":
                        # Смешанный запрос: и таблица, и график.
                        # Полностью формируем собственное короткое пояснение, игнорируя текст модели.
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

                        parts.append(
                            f"Ниже {graph_description}: по горизонтали меняется число x, "
                            "а по вертикали видно, как меняется значение функции. "
                            "Посмотри, как кривая поднимается и опускается, и попробуй объяснить это своими словами."
                        )

                        full_response = " ".join(parts)

                        # #region agent log
                        try:
                            with open(debug_log_path, "a", encoding="utf-8") as f:
                                f.write(
                                    json_lib_debug.dumps(
                                        {
                                            "timestamp": __import__("time").time() * 1000,
                                            "location": "miniapp_endpoints.py:visual-mixed",
                                            "message": "Сформировано пояснение для смешанного запроса (таблица + график)",
                                            "data": {
                                                "table_numbers": table_numbers,
                                                "intent_items": intent.items,
                                                "full_response": full_response[:200],
                                            },
                                            "sessionId": "debug-session",
                                            "runId": "text_replacement",
                                            "hypothesisId": "MIX",
                                        },
                                        ensure_ascii=False,
                                    )
                                    + "\n"
                                )
                        except Exception:
                            pass
                        # #endregion

                    else:
                        # КРИТИЧНО: Удаляем дублирование таблицы умножения текстом (если модель всё же написала)
                        multiplication_duplicate_patterns = [
                            r"\d+\s*[×x*]\s*\d+\s*=\s*\d+",
                            r"\d+\s+\d+\s*=\s*\d+",
                        ]
                        for pattern in multiplication_duplicate_patterns:
                            full_response = re.sub(pattern, "", full_response, flags=re.IGNORECASE)

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
                    # #region agent log
                    try:
                        with open(debug_log_path, "a", encoding="utf-8") as f:
                            f.write(
                                json_lib_debug.dumps(
                                    {
                                        "timestamp": __import__("time").time() * 1000,
                                        "location": "miniapp_endpoints.py:1762",
                                        "message": "Текст заменен для визуализации",
                                        "data": {"new_response": full_response},
                                        "sessionId": "debug-session",
                                        "runId": "text_replacement",
                                        "hypothesisId": "C",
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    except Exception:
                        pass
                    # #endregion

                # Ограничиваем размер полного ответа
                MAX_RESPONSE_LENGTH = 4000
                full_response_for_db = full_response
                if len(full_response) > MAX_RESPONSE_LENGTH:
                    full_response = full_response[:MAX_RESPONSE_LENGTH] + "\n\n... (ответ обрезан)"

                # Сохраняем в историю
                try:
                    premium_service.increment_request_count(telegram_id)
                    history_service.add_message(telegram_id, user_message, "user")
                    history_service.add_message(telegram_id, full_response_for_db, "ai")

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
                                        safe_expr = expression.replace("x", "x")
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
                                # #region agent log
                                logger.info(
                                    f"🔍 Stream: Fallback ДО замены (multiplication_number={multiplication_number_fallback}): {cleaned_response[:200]}"
                                )
                                # #endregion

                                # Просто заменяем весь ответ на короткий, если есть визуализация
                                cleaned_response = "Вот таблица умножения."

                                # #region agent log
                                logger.info(
                                    f"✅ Stream: Fallback - текст заменен на короткий ответ (есть визуализация): {cleaned_response}"
                                )
                                # #endregion

                            # Удаляем упоминания про "систему автоматически" и подобное
                            cleaned_response = re.sub(
                                r"(?:систем[аеы]?\s+)?автоматически\s+сгенериру[ею]т?\s+изображени[ея]?",
                                "",
                                cleaned_response,
                                flags=re.IGNORECASE,
                            )
                            cleaned_response = re.sub(
                                r"покажу\s+график.*?систем[аеы]?\s+автоматически",
                                "Вот график",
                                cleaned_response,
                                flags=re.IGNORECASE,
                            )

                        # Отправляем полный ответ как один chunk
                        import json as json_lib

                        chunk_data = json_lib.dumps({"chunk": cleaned_response}, ensure_ascii=False)
                        await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                        # Сохраняем в историю
                        try:
                            premium_service.increment_request_count(telegram_id)
                            history_service.add_message(telegram_id, user_message, "user")
                            history_service.add_message(telegram_id, cleaned_response, "ai")
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
