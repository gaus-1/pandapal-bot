"""
API endpoints для Telegram Mini App
Обеспечивает взаимодействие между React frontend и Python backend
"""

import base64

from aiohttp import web
from loguru import logger

from bot.database import get_db
from bot.security.telegram_auth import TelegramWebAppAuth
from bot.services import (
    ChatHistoryService,
    UserService,
)
from bot.services.ai_service_solid import get_ai_service
from bot.services.speech_service import SpeechService
from bot.services.vision_service import VisionService


async def miniapp_auth(request: web.Request) -> web.Response:
    """
    Аутентификация пользователя Mini App.

    POST /api/miniapp/auth
    Body: { "initData": "..." }

    Returns:
        200: { "success": true, "user": {...} }
        400: { "error": "..." }
        403: { "error": "Invalid initData" }
    """
    try:
        data = await request.json()
        init_data = data.get("initData")

        logger.info(
            f"📡 Получен запрос аутентификации. initData length: {len(init_data) if init_data else 0}"
        )

        if not init_data:
            logger.warning("⚠️ initData отсутствует в запросе")
            return web.json_response({"error": "initData required"}, status=400)

        # Валидация данных от Telegram
        auth_validator = TelegramWebAppAuth()
        validated_data = auth_validator.validate_init_data(init_data)

        if not validated_data:
            logger.warning("⚠️ initData не прошёл валидацию")
            return web.json_response(
                {"error": "Invalid Telegram signature. Make sure app is opened via Telegram."},
                status=403,
            )

        # Извлекаем данные пользователя
        user_data = auth_validator.extract_user_data(validated_data)

        if not user_data:
            logger.error("❌ Не удалось извлечь user_data из validated_data")
            return web.json_response(
                {"error": "Failed to extract user data from initData"}, status=400
            )

        telegram_id = user_data.get("id")

        if not telegram_id:
            logger.error(f"❌ telegram_id отсутствует в user_data: {user_data}")
            return web.json_response({"error": "No user ID in initData"}, status=400)

        # Получаем или создаем пользователя
        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_or_create_user(
                telegram_id=telegram_id,
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
            )

            # Вызываем to_dict() ВНУТРИ сессии
            user_dict = user.to_dict()

        logger.info(f"✅ Пользователь {telegram_id} успешно аутентифицирован")

        # Возвращаем данные пользователя
        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка аутентификации Mini App: {e}", exc_info=True)
        return web.json_response({"error": f"Server error: {str(e)}"}, status=500)


async def miniapp_get_user(request: web.Request) -> web.Response:
    """
    Получить профиль пользователя.

    GET /api/miniapp/user/{telegram_id}
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            user_dict = user.to_dict()

        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения пользователя: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_update_user(request: web.Request) -> web.Response:
    """
    Обновить профиль пользователя.

    PATCH /api/miniapp/user/{telegram_id}
    Body: { "age": 10, "grade": 4 }
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])
        data = await request.json()

        age = data.get("age")
        grade = data.get("grade")

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.update_user_profile(telegram_id=telegram_id, age=age, grade=grade)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            user_dict = user.to_dict()

        return web.json_response(
            {
                "success": True,
                "user": user_dict,
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка обновления пользователя: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_progress(request: web.Request) -> web.Response:
    """
    Получить прогресс обучения пользователя.

    GET /api/miniapp/progress/{telegram_id}
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Получаем прогресс из БД ВНУТРИ сессии
            progress_items = [p.to_dict() for p in user.progress]

        return web.json_response({"success": True, "progress": progress_items})

    except Exception as e:
        logger.error(f"❌ Ошибка получения прогресса: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_achievements(request: web.Request) -> web.Response:
    """
    Получить достижения пользователя.

    GET /api/miniapp/achievements/{telegram_id}
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])

        # Временные данные (в будущем из БД)
        achievements = [
            {
                "id": "1",
                "title": "Первые шаги",
                "description": "Отправь первое сообщение боту",
                "icon": "🌟",
                "unlocked": True,
                "unlock_date": "2025-01-01T00:00:00Z",
            },
            {
                "id": "2",
                "title": "Знаток математики",
                "description": "Реши 10 задач по математике",
                "icon": "🧮",
                "unlocked": False,
            },
            {
                "id": "3",
                "title": "Полиглот",
                "description": "Изучи 3 языка",
                "icon": "🗣️",
                "unlocked": False,
            },
        ]

        return web.json_response({"success": True, "achievements": achievements})

    except Exception as e:
        logger.error(f"❌ Ошибка получения достижений: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_dashboard(request: web.Request) -> web.Response:
    """
    Получить статистику для дашборда.

    GET /api/miniapp/dashboard/{telegram_id}
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Собираем статистику
            stats = {
                "total_messages": len(user.messages),
                "learning_sessions": len(user.sessions),
                "total_points": sum(p.points for p in user.progress),
                "subjects_studied": len(user.progress),
                "current_streak": 1,  # Временно hardcode
            }

            return web.json_response({"success": True, "stats": stats})

    except Exception as e:
        logger.error(f"❌ Ошибка получения дашборда: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_ai_chat(request: web.Request) -> web.Response:
    """
    Отправить сообщение AI и получить ответ.

    POST /api/miniapp/ai/chat
    Body: {
        "telegram_id": 123,
        "message": "...",
        "photo_base64": "data:image/jpeg;base64,...", # опционально
        "audio_base64": "data:audio/webm;base64,..." # опционально
    }
    """
    try:
        # Логируем размер запроса для отладки
        content_length = request.headers.get("Content-Length")
        if content_length:
            logger.info(f"📊 Размер входящего запроса: {content_length} байт")

        try:
            data = await request.json()
        except Exception as json_error:
            logger.error(f"❌ Ошибка парсинга JSON: {json_error}", exc_info=True)
            # Если ошибка "Content Too Large", это значит запрос слишком большой
            if "Content Too Large" in str(json_error) or "too large" in str(json_error).lower():
                return web.json_response(
                    {"error": "Запрос слишком большой. Попробуй уменьшить размер фото или аудио."},
                    status=413,
                )
            raise

        telegram_id = data.get("telegram_id")
        message = data.get("message", "")
        photo_base64 = data.get("photo_base64")
        audio_base64 = data.get("audio_base64")

        if not telegram_id:
            return web.json_response({"error": "telegram_id required"}, status=400)

        user_message = message

        # Обработка аудио (приоритетнее фото)
        if audio_base64:
            try:
                logger.info(f"🎤 Mini App: Обработка голосового сообщения от {telegram_id}")
                logger.info(f"🎤 Mini App: audio_base64 length: {len(audio_base64)}")
                # Убираем data:audio/...;base64, префикс
                if "base64," in audio_base64:
                    audio_base64 = audio_base64.split("base64,")[1]
                    logger.info(
                        f"🎤 Mini App: После удаления префикса, length: {len(audio_base64)}"
                    )

                audio_bytes = base64.b64decode(audio_base64)
                logger.info(f"🎤 Mini App: Декодировано {len(audio_bytes)} байт аудио")

                speech_service = SpeechService()
                transcribed_text = await speech_service.transcribe_voice(audio_bytes, language="ru")

                if transcribed_text:
                    user_message = transcribed_text
                    logger.info(f"✅ Аудио распознано: {transcribed_text[:100]}")
                else:
                    logger.warning("⚠️ Аудио не распознано - возвращаем ошибку")
                    return web.json_response(
                        {"error": "Не удалось распознать аудио. Попробуй еще раз!"},
                        status=400,
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка обработки аудио: {e}", exc_info=True)
                return web.json_response({"error": f"Ошибка обработки аудио: {str(e)}"}, status=500)

        # Обработка фото
        if photo_base64:
            try:
                logger.info(f"📷 Mini App: Обработка фото от {telegram_id}")
                logger.info(f"📷 Mini App: photo_base64 length: {len(photo_base64)}")
                # Убираем data:image/...;base64, префикс
                if "base64," in photo_base64:
                    photo_base64 = photo_base64.split("base64,")[1]
                    logger.info(
                        f"📷 Mini App: После удаления префикса, length: {len(photo_base64)}"
                    )

                photo_bytes = base64.b64decode(photo_base64)
                logger.info(f"📷 Mini App: Декодировано {len(photo_bytes)} байт изображения")

                with get_db() as db:
                    user_service = UserService(db)
                    user = user_service.get_user_by_telegram_id(telegram_id)

                    if not user:
                        return web.json_response({"error": "User not found"}, status=404)

                    vision_service = VisionService()
                    logger.info(
                        f"📷 Mini App: Вызываю analyze_image для пользователя {user.age} лет"
                    )
                    vision_result = await vision_service.analyze_image(
                        image_data=photo_bytes,
                        user_message=message or "Помоги мне разобраться с этой задачей",
                        user_age=user.age,
                    )

                    user_message = f"[Фото с заданием]\n{vision_result.analysis}"
                    logger.info(f"✅ Фото проанализировано: {user_message[:100]}")
            except Exception as e:
                logger.error(f"❌ Ошибка обработки фото: {e}", exc_info=True)
                return web.json_response({"error": f"Ошибка обработки фото: {str(e)}"}, status=500)

        # Если нет ни фото ни аудио - должно быть текстовое сообщение
        if not user_message.strip():
            return web.json_response({"error": "message, photo or audio required"}, status=400)

        with get_db() as db:
            user_service = UserService(db)
            history_service = ChatHistoryService(db)

            user = user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Загружаем историю для контекста (ограничиваем размер)
            history = history_service.get_formatted_history_for_ai(
                telegram_id, limit=10
            )  # Уменьшили до 10
            history_size = sum(len(str(msg)) for msg in history)
            logger.info(
                f"📊 Размер истории чата: {history_size} символов, сообщений: {len(history)}"
            )

            # Генерируем ответ AI
            ai_service = get_ai_service()
            ai_response = await ai_service.generate_response(
                user_message=user_message, chat_history=history, user_age=user.age
            )
            logger.info(f"📊 Размер ответа AI: {len(ai_response)} символов")

            # Ограничиваем размер ответа ДО сохранения в историю
            # Максимальный размер ответа: ~4000 символов (безопасный лимит для JSON)
            MAX_RESPONSE_LENGTH = 4000
            full_response = ai_response
            if len(ai_response) > MAX_RESPONSE_LENGTH:
                logger.warning(
                    f"⚠️ Ответ AI слишком длинный ({len(ai_response)} символов), обрезаем до {MAX_RESPONSE_LENGTH}"
                )
                ai_response = (
                    ai_response[:MAX_RESPONSE_LENGTH]
                    + "\n\n... (ответ обрезан, продолжение в следующем сообщении)"
                )

            # Сохраняем в историю (полный ответ для контекста, но отправляем обрезанный)
            history_service.add_message(telegram_id, user_message, "user")
            history_service.add_message(telegram_id, full_response, "ai")  # Сохраняем полный ответ

            # Проверяем размер JSON перед отправкой
            import json as json_lib

            response_data = {"success": True, "response": ai_response}
            json_str = json_lib.dumps(response_data, ensure_ascii=False)
            json_size = len(json_str.encode("utf-8"))

            logger.info(f"📊 Размер JSON ответа: {json_size} байт ({len(json_str)} символов)")

            # Если JSON слишком большой, обрезаем еще больше
            if json_size > 50000:  # ~50KB лимит
                logger.warning(f"⚠️ JSON слишком большой ({json_size} байт), обрезаем ответ")
                ai_response = ai_response[:2000] + "\n\n... (ответ обрезан)"
                response_data = {"success": True, "response": ai_response}

            return web.json_response(response_data)

    except Exception as e:
        logger.error(f"❌ Ошибка AI чата: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def miniapp_get_chat_history(request: web.Request) -> web.Response:
    """
    Получить историю чата.

    GET /api/miniapp/chat/history/{telegram_id}?limit=50
    """
    try:
        telegram_id = int(request.match_info["telegram_id"])
        limit = int(request.query.get("limit", "50"))

        with get_db() as db:
            history_service = ChatHistoryService(db)
            messages = history_service.get_recent_history(telegram_id, limit=limit)

            history = [
                {
                    "role": "user" if msg.message_type == "user" else "ai",
                    "content": msg.message_text,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in messages
            ]

            return web.json_response({"success": True, "history": history})

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def miniapp_get_subjects(request: web.Request) -> web.Response:
    """
    Получить список предметов.

    GET /api/miniapp/subjects
    """
    try:
        # Предметы (в будущем можно вынести в БД)
        subjects = [
            {
                "id": "math",
                "name": "Математика",
                "icon": "🧮",
                "description": "Арифметика, алгебра, геометрия",
                "grade_range": [1, 11],
            },
            {
                "id": "russian",
                "name": "Русский язык",
                "icon": "📝",
                "description": "Грамматика, орфография, пунктуация",
                "grade_range": [1, 11],
            },
            {
                "id": "english",
                "name": "Английский язык",
                "icon": "🇬🇧",
                "description": "Vocabulary, grammar, conversation",
                "grade_range": [1, 11],
            },
            {
                "id": "physics",
                "name": "Физика",
                "icon": "⚡",
                "description": "Механика, оптика, электричество",
                "grade_range": [7, 11],
            },
            {
                "id": "chemistry",
                "name": "Химия",
                "icon": "⚗️",
                "description": "Неорганика, органика, реакции",
                "grade_range": [8, 11],
            },
            {
                "id": "biology",
                "name": "Биология",
                "icon": "🧬",
                "description": "Ботаника, зоология, анатомия",
                "grade_range": [5, 11],
            },
            {
                "id": "geography",
                "name": "География",
                "icon": "🌍",
                "description": "Страны, континенты, природа",
                "grade_range": [5, 11],
            },
            {
                "id": "history",
                "name": "История",
                "icon": "📚",
                "description": "Древний мир, средние века, новое время",
                "grade_range": [5, 11],
            },
        ]

        return web.json_response({"success": True, "subjects": subjects})

    except Exception as e:
        logger.error(f"❌ Ошибка получения предметов: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


def setup_miniapp_routes(app: web.Application) -> None:
    """
    Регистрация роутов Mini App в aiohttp приложении.

    Args:
        app: aiohttp приложение
    """
    # Аутентификация
    app.router.add_post("/api/miniapp/auth", miniapp_auth)

    # Пользователь
    app.router.add_get("/api/miniapp/user/{telegram_id}", miniapp_get_user)
    app.router.add_patch("/api/miniapp/user/{telegram_id}", miniapp_update_user)

    # Прогресс и достижения
    app.router.add_get("/api/miniapp/progress/{telegram_id}", miniapp_get_progress)
    app.router.add_get("/api/miniapp/achievements/{telegram_id}", miniapp_get_achievements)
    app.router.add_get("/api/miniapp/dashboard/{telegram_id}", miniapp_get_dashboard)

    # AI чат
    app.router.add_post("/api/miniapp/ai/chat", miniapp_ai_chat)
    app.router.add_get("/api/miniapp/chat/history/{telegram_id}", miniapp_get_chat_history)

    # Предметы
    app.router.add_get("/api/miniapp/subjects", miniapp_get_subjects)

    logger.info("✅ Mini App API routes зарегистрированы")
