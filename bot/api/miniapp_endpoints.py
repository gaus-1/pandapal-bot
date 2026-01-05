"""
API endpoints для Telegram Mini App
Обеспечивает взаимодействие между React frontend и Python backend
"""

import base64

from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import (
    AIChatRequest,
    AuthRequest,
    UpdateUserRequest,
    validate_limit,
    validate_telegram_id,
)
from bot.database import get_db
from bot.models import ChatHistory
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

        # Валидация входных данных
        try:
            validated = AuthRequest(**data)
        except ValidationError as e:
            logger.warning(f"⚠️ Invalid auth request: {e.errors()}")
            return web.json_response(
                {"error": "Invalid request data", "details": e.errors()},
                status=400,
            )

        init_data = validated.initData

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
        # Используем % для логирования чтобы избежать проблем с фигурными скобками в SQL
        logger.error("❌ Ошибка аутентификации Mini App: %s", str(e), exc_info=True)
        return web.json_response({"error": f"Server error: {str(e)}"}, status=500)


async def miniapp_get_user(request: web.Request) -> web.Response:
    """
    Получить профиль пользователя.

    GET /api/miniapp/user/{telegram_id}
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

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
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        # Валидация входных данных
        data = await request.json()
        try:
            validated = UpdateUserRequest(**data)
        except ValidationError as e:
            logger.warning(f"⚠️ Invalid update user request: {e.errors()}")
            return web.json_response(
                {"error": "Invalid request data", "details": e.errors()},
                status=400,
            )

        age = validated.age
        grade = validated.grade

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
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

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
    Получить достижения пользователя с реальными данными из БД.

    GET /api/miniapp/achievements/{telegram_id}
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        with get_db() as db:
            from bot.services.gamification_service import GamificationService

            gamification_service = GamificationService(db)
            achievements_data = gamification_service.get_achievements_with_progress(telegram_id)

        # Преобразуем в формат для API
        achievements = []
        for ach in achievements_data:
            achievement_dict = {
                "id": ach["id"],
                "title": ach["title"],
                "description": ach["description"],
                "icon": ach["icon"],
                "unlocked": ach["unlocked"],
                "xp_reward": ach["xp_reward"],
                "progress": ach["progress"],
                "progress_max": ach["progress_max"],
            }
            if ach["unlocked"] and ach.get("unlock_date"):
                achievement_dict["unlock_date"] = ach["unlock_date"]
            achievements.append(achievement_dict)

        return web.json_response({"success": True, "achievements": achievements})

    except Exception as e:
        logger.error(f"❌ Ошибка получения достижений: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def miniapp_get_dashboard(request: web.Request) -> web.Response:
    """
    Получить статистику для дашборда.

    GET /api/miniapp/dashboard/{telegram_id}
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Проверяем premium для детальной аналитики
            from bot.services.premium_features_service import PremiumFeaturesService

            premium_service = PremiumFeaturesService(db)
            is_premium = premium_service.is_premium_active(telegram_id)

            # Базовая статистика (доступна всем)
            stats = {
                "total_messages": len(user.messages),
                "learning_sessions": len(user.sessions),
                "total_points": sum(p.points for p in user.progress),
                "subjects_studied": len(user.progress),
                "current_streak": 1,  # Временно hardcode
            }

            # Детальная аналитика только для Premium
            if is_premium:
                from bot.services.analytics_service import AnalyticsService

                analytics_service = AnalyticsService(db)
                stats["detailed_analytics"] = {
                    "messages_per_day": analytics_service.get_messages_per_day(telegram_id),
                    "most_active_subjects": analytics_service.get_most_active_subjects(telegram_id),
                    "learning_trends": analytics_service.get_learning_trends(telegram_id),
                }

            return web.json_response({"success": True, "stats": stats, "is_premium": is_premium})

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
    # Логируем ВСЕ запросы для отладки
    client_ip = request.remote
    logger.info(
        f"📨 Mini App AI Chat запрос от IP: {client_ip}, метод: {request.method}, путь: {request.path_qs}"
    )

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

        # Валидация входных данных
        try:
            validated = AIChatRequest(**data)
        except ValidationError as e:
            # Преобразуем ошибки валидации в сериализуемый формат
            error_details = []
            for error in e.errors():
                error_dict = {
                    "type": error.get("type", "validation_error"),
                    "loc": error.get("loc", []),
                    "msg": error.get("msg", "Validation error"),
                }
                # Преобразуем ctx если есть
                if "ctx" in error and error["ctx"]:
                    ctx = error["ctx"]
                    if isinstance(ctx, dict):
                        # Преобразуем ValueError в строку
                        if "error" in ctx:
                            ctx = {
                                k: str(v) if isinstance(v, Exception) else v for k, v in ctx.items()
                            }
                        error_dict["ctx"] = ctx
                error_details.append(error_dict)

            logger.warning(f"⚠️ Invalid AI chat request: {error_details}")
            return web.json_response(
                {"error": "Invalid request data", "details": error_details},
                status=400,
            )

        telegram_id = validated.telegram_id
        message = validated.message or ""
        photo_base64 = validated.photo_base64
        audio_base64 = validated.audio_base64

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

                # Проверяем размер base64 строки (примерно 4/3 от размера бинарных данных)
                # Лимит: 10MB аудио = ~13.3MB base64
                MAX_AUDIO_BASE64_SIZE = 14 * 1024 * 1024  # 14MB
                if len(audio_base64) > MAX_AUDIO_BASE64_SIZE:
                    logger.warning(f"⚠️ Аудио слишком большое: {len(audio_base64)} байт")
                    return web.json_response(
                        {
                            "error": "Аудио слишком большое. Максимум 10MB. Попробуй записать короче!"
                        },
                        status=413,
                    )

                audio_bytes = base64.b64decode(audio_base64)
                logger.info(f"🎤 Mini App: Декодировано {len(audio_bytes)} байт аудио")

                # Проверяем размер декодированного аудио
                MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
                if len(audio_bytes) > MAX_AUDIO_SIZE:
                    logger.warning(
                        f"⚠️ Декодированное аудио слишком большое: {len(audio_bytes)} байт"
                    )
                    return web.json_response(
                        {
                            "error": "Аудио слишком большое. Максимум 10MB. Попробуй записать короче!"
                        },
                        status=413,
                    )

                speech_service = SpeechService()
                transcribed_text = await speech_service.transcribe_voice(audio_bytes, language="ru")

                if transcribed_text and transcribed_text.strip():
                    user_message = transcribed_text
                    logger.info(f"✅ Аудио распознано: {transcribed_text[:100]}")
                else:
                    logger.warning("⚠️ Аудио не распознано или пустое")
                    # Возвращаем понятную ошибку пользователю
                    return web.json_response(
                        {
                            "error": "Не удалось распознать речь. Попробуй говорить четче или напиши текстом!",
                        },
                        status=400,
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка обработки аудио: {e}", exc_info=True)
                # Возвращаем понятную ошибку пользователю
                error_message = (
                    "Ошибка обработки аудио. Попробуй записать заново или напиши текстом!"
                )
                if "timeout" in str(e).lower() or "time" in str(e).lower():
                    error_message = "Аудио слишком длинное. Попробуй записать короче!"
                elif "format" in str(e).lower() or "decode" in str(e).lower():
                    error_message = "Неверный формат аудио. Попробуй записать заново!"
                return web.json_response({"error": error_message}, status=500)

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

            # КРИТИЧНО: Проверка Premium для неограниченных запросов
            from bot.services.premium_features_service import PremiumFeaturesService

            premium_service = PremiumFeaturesService(db)
            can_request, limit_reason = premium_service.can_make_ai_request(telegram_id)

            if not can_request:
                logger.warning(f"🚫 AI запрос заблокирован для user={telegram_id}: {limit_reason}")
                return web.json_response(
                    {
                        "error": limit_reason,
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "is_premium": False,
                    },
                    status=429,
                )

            # Для premium - больше истории для контекста
            history_limit = 50 if premium_service.is_premium_active(telegram_id) else 10

            # Загружаем историю для контекста
            history = history_service.get_formatted_history_for_ai(telegram_id, limit=history_limit)
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
            logger.info(f"💾 Начинаю сохранение в БД для telegram_id={telegram_id}")
            user_msg = None
            ai_msg = None
            unlocked_achievements = []  # Инициализируем в начале блока
            try:
                logger.info(f"💾 Сохраняю сообщение пользователя: {user_message[:50]}...")
                user_msg = history_service.add_message(telegram_id, user_message, "user")
                logger.info(f"✅ Сообщение пользователя добавлено в сессию: id={user_msg.id}")

                logger.info(f"💾 Сохраняю ответ AI: {full_response[:50]}...")
                ai_msg = history_service.add_message(telegram_id, full_response, "ai")
                logger.info(f"✅ Ответ AI добавлен в сессию: id={ai_msg.id}")

                # Обрабатываем геймификацию (XP и достижения) ПЕРЕД коммитом
                try:
                    from bot.services.gamification_service import GamificationService

                    gamification_service = GamificationService(db)
                    unlocked_achievements = gamification_service.process_message(
                        telegram_id, user_message
                    )
                    logger.info(
                        f"🎮 Геймификация обработана: разблокировано {len(unlocked_achievements)} достижений"
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки геймификации: {e}", exc_info=True)

                # ЯВНЫЙ КОММИТ перед отправкой ответа
                db.commit()
                logger.info(
                    f"✅✅✅ ТРАНЗАКЦИЯ ЗАКОММИЧЕНА: user_msg_id={user_msg.id if user_msg else None}, ai_msg_id={ai_msg.id if ai_msg else None}, telegram_id={telegram_id}"
                )

                # ПРОВЕРКА: читаем обратно из БД для подтверждения
                check_msg = db.query(ChatHistory).filter_by(id=user_msg.id).first()
                if check_msg:
                    logger.info(
                        f"✅✅✅ ПОДТВЕРЖДЕНО: сообщение {check_msg.id} существует в БД после коммита"
                    )
                else:
                    logger.error(
                        f"❌❌❌ ПРОБЛЕМА: сообщение {user_msg.id} НЕ найдено в БД после коммита!"
                    )

            except Exception as save_error:
                logger.error(
                    f"❌ КРИТИЧЕСКАЯ ОШИБКА сохранения в историю: {save_error}", exc_info=True
                )
                db.rollback()
                logger.error("❌ Транзакция откачена из-за ошибки сохранения")
                # Продолжаем работу, даже если сохранение не удалось

            # Проверяем размер JSON перед отправкой
            import json as json_lib

            response_data = {"success": True, "response": ai_response}

            # Добавляем информацию о разблокированных достижениях
            if unlocked_achievements:
                try:
                    from bot.services.gamification_service import ALL_ACHIEVEMENTS

                    achievement_info = []
                    for achievement_id in unlocked_achievements:
                        achievement = next(
                            (a for a in ALL_ACHIEVEMENTS if a.id == achievement_id), None
                        )
                        if achievement:
                            achievement_info.append(
                                {
                                    "id": achievement.id,
                                    "title": achievement.title,
                                    "description": achievement.description,
                                    "icon": achievement.icon,
                                    "xp_reward": achievement.xp_reward,
                                }
                            )
                    if achievement_info:
                        response_data["achievements_unlocked"] = achievement_info
                except Exception as e:
                    logger.error(f"❌ Ошибка формирования информации о достижениях: {e}")

            json_str = json_lib.dumps(response_data, ensure_ascii=False)
            json_size = len(json_str.encode("utf-8"))

            logger.info(f"📊 Размер JSON ответа: {json_size} байт ({len(json_str)} символов)")

            # Если JSON слишком большой, обрезаем еще больше
            if json_size > 50000:  # ~50KB лимит
                logger.warning(f"⚠️ JSON слишком большой ({json_size} байт), обрезаем ответ")
                ai_response = ai_response[:2000] + "\n\n... (ответ обрезан)"
                response_data = {"success": True, "response": ai_response}
                # Убираем достижения если JSON слишком большой
                if "achievements_unlocked" in response_data:
                    del response_data["achievements_unlocked"]

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
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        # Безопасная валидация limit
        limit = validate_limit(request.query.get("limit"), default=50, max_limit=100)

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


async def miniapp_clear_chat_history(request: web.Request) -> web.Response:
    """
    Очистить историю чата.

    DELETE /api/miniapp/chat/history/{telegram_id}
    """
    try:
        # Безопасная валидация telegram_id
        try:
            telegram_id = validate_telegram_id(request.match_info["telegram_id"])
        except ValueError as e:
            logger.warning(f"⚠️ Invalid telegram_id: {e}")
            return web.json_response({"error": str(e)}, status=400)

        with get_db() as db:
            history_service = ChatHistoryService(db)
            deleted_count = history_service.clear_history(telegram_id)
            db.commit()

            logger.info(f"🗑️ Очищена история для {telegram_id}: {deleted_count} сообщений")

            return web.json_response({"success": True, "deleted_count": deleted_count})

    except Exception as e:
        logger.error(f"❌ Ошибка очистки истории: {e}", exc_info=True)
        return web.json_response({"error": f"Internal server error: {str(e)}"}, status=500)


async def miniapp_get_subjects(request: web.Request) -> web.Response:
    """
    Получить список предметов с учетом Premium статуса.

    GET /api/miniapp/subjects?telegram_id=123
    """
    try:
        # Получаем telegram_id из query параметров (опционально)
        telegram_id = None
        telegram_id_str = request.query.get("telegram_id")
        if telegram_id_str:
            try:
                telegram_id = validate_telegram_id(telegram_id_str)
            except ValueError:
                pass  # Игнорируем невалидный ID

        # Предметы (в будущем можно вынести в БД)
        all_subjects = [
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

        # Если telegram_id указан, проверяем Premium и ограничиваем доступ
        if telegram_id:
            with get_db() as db:
                from bot.services.premium_features_service import PremiumFeaturesService

                premium_service = PremiumFeaturesService(db)
                is_premium = premium_service.is_premium_active(telegram_id)

                # Для бесплатных - только базовые предметы
                if not is_premium:
                    free_subjects_ids = ["math", "russian", "english"]
                    subjects = [s for s in all_subjects if s["id"] in free_subjects_ids]
                    # Добавляем информацию о premium для остальных
                    for subject in all_subjects:
                        if subject["id"] not in free_subjects_ids:
                            subject["premium_required"] = True
                            subject["locked"] = True
                else:
                    subjects = all_subjects
        else:
            # Если telegram_id не указан, возвращаем все предметы
            subjects = all_subjects

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
    app.router.add_delete("/api/miniapp/chat/history/{telegram_id}", miniapp_clear_chat_history)

    # Предметы
    app.router.add_get("/api/miniapp/subjects", miniapp_get_subjects)

    # Premium функции
    from bot.api.premium_features_endpoints import (
        miniapp_get_bonus_lesson_content,
        miniapp_get_bonus_lessons,
        miniapp_get_learning_plan,
        miniapp_get_premium_features_status,
    )

    app.router.add_get(
        "/api/miniapp/premium/learning-plan/{telegram_id}", miniapp_get_learning_plan
    )
    app.router.add_get(
        "/api/miniapp/premium/bonus-lessons/{telegram_id}", miniapp_get_bonus_lessons
    )
    app.router.add_get(
        "/api/miniapp/premium/bonus-lessons/{telegram_id}/{lesson_id}",
        miniapp_get_bonus_lesson_content,
    )
    app.router.add_get(
        "/api/miniapp/premium/features/{telegram_id}", miniapp_get_premium_features_status
    )

    logger.info("✅ Mini App API routes зарегистрированы")
