"""
API endpoints для Telegram Mini App
Обеспечивает взаимодействие между React frontend и Python backend
"""

import base64
from contextlib import suppress

import httpx
from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import (
    AIChatRequest,
    AuthRequest,
    DashboardStatsResponse,
    DetailedAnalyticsResponse,
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
from bot.services.speech_service import get_speech_service
from bot.services.translate_service import get_translate_service
from bot.services.vision_service import VisionService
from bot.services.yandex_ai_response_generator import clean_ai_response


async def _process_audio_message(
    audio_base64: str, telegram_id: int, message: str
) -> tuple[str | None, web.Response | None]:
    """
    Обработка голосового сообщения.

    Returns:
        tuple: (user_message, error_response) - если error_response не None, вернуть его
    """
    try:
        logger.info(f"🎤 Mini App: Обработка голосового сообщения от {telegram_id}")
        logger.info(f"🎤 Mini App: audio_base64 length: {len(audio_base64)}")

        if "base64," in audio_base64:
            audio_base64 = audio_base64.split("base64,")[1]
            logger.info(f"🎤 Mini App: После удаления префикса, length: {len(audio_base64)}")

        MAX_AUDIO_BASE64_SIZE = 14 * 1024 * 1024  # 14MB
        if len(audio_base64) > MAX_AUDIO_BASE64_SIZE:
            logger.warning(f"⚠️ Аудио слишком большое: {len(audio_base64)} байт")
            return None, web.json_response(
                {"error": "Аудио слишком большое. Максимум 10MB. Попробуй записать короче!"},
                status=413,
            )

        try:
            audio_bytes = base64.b64decode(audio_base64)
            logger.info(f"🎤 Mini App: Декодировано {len(audio_bytes)} байт аудио")
        except Exception as decode_error:
            logger.error(f"❌ Ошибка декодирования base64 аудио: {decode_error}")
            return None, web.json_response(
                {"error": "Неверный формат аудио. Попробуй записать заново!"},
                status=400,
            )

        MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
        if len(audio_bytes) > MAX_AUDIO_SIZE:
            logger.warning(f"⚠️ Декодированное аудио слишком большое: {len(audio_bytes)} байт")
            return None, web.json_response(
                {"error": "Аудио слишком большое. Максимум 10MB. Попробуй записать короче!"},
                status=413,
            )

        speech_service = get_speech_service()
        transcribed_text = await speech_service.transcribe_voice(audio_bytes, language="ru")

        if not transcribed_text or not transcribed_text.strip():
            logger.warning("⚠️ Аудио не распознано или пустое")
            return None, web.json_response(
                {
                    "error": "Не удалось распознать речь. Попробуй говорить четче или напиши текстом!"
                },
                status=400,
            )

        translate_service = get_translate_service()
        detected_lang = await translate_service.detect_language(transcribed_text)

        if (
            detected_lang
            and detected_lang != "ru"
            and detected_lang in translate_service.SUPPORTED_LANGUAGES
        ):
            lang_name = translate_service.get_language_name(detected_lang)
            logger.info(f"🌍 Mini App: Обнаружен иностранный язык: {detected_lang}")
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
                logger.info(f"✅ Mini App: Аудио переведено: {detected_lang} → ru")
            else:
                user_message = transcribed_text
        else:
            user_message = transcribed_text

        logger.info(f"✅ Mini App: Аудио распознано: {transcribed_text[:100]}")
        if not user_message or not user_message.strip():
            logger.warning("⚠️ user_message не установлен после распознавания аудио")
            user_message = transcribed_text if transcribed_text else message

        return user_message, None

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Ошибка SpeechKit API (HTTP {e.response.status_code}): {e}", exc_info=True)
        error_message = "Ошибка распознавания речи. Попробуй записать заново или напиши текстом!"
        if e.response.status_code == 401:
            error_message = (
                "Ошибка авторизации в сервисе распознавания речи. Обратитесь в поддержку."
            )
        elif e.response.status_code == 413:
            error_message = "Аудио слишком большое. Попробуй записать короче!"
        elif e.response.status_code == 400:
            error_message = "Неверный формат аудио. Попробуй записать заново!"
        return None, web.json_response({"error": error_message}, status=500)
    except httpx.TimeoutException as e:
        logger.error(f"❌ Таймаут распознавания речи: {e}", exc_info=True)
        return None, web.json_response(
            {"error": "Аудио слишком длинное или сервис недоступен. Попробуй записать короче!"},
            status=504,
        )
    except Exception as e:
        logger.error(f"❌ Ошибка обработки аудио: {e}", exc_info=True)
        error_message = "Ошибка обработки аудио. Попробуй записать заново или напиши текстом!"
        if "timeout" in str(e).lower() or "time" in str(e).lower():
            error_message = "Аудио слишком длинное. Попробуй записать короче!"
        elif "format" in str(e).lower() or "decode" in str(e).lower():
            error_message = "Неверный формат аудио. Попробуй записать заново!"
        elif "401" in str(e) or "unauthorized" in str(e).lower():
            error_message = (
                "Ошибка авторизации в сервисе распознавания речи. Обратитесь в поддержку."
            )
        return None, web.json_response({"error": error_message}, status=500)


def _format_achievements(unlocked_achievements: list) -> list:
    """Форматирование списка достижений для ответа."""
    try:
        from bot.services.gamification_service import ALL_ACHIEVEMENTS

        achievement_info = []
        for achievement_id in unlocked_achievements:
            achievement = next((a for a in ALL_ACHIEVEMENTS if a.id == achievement_id), None)
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
        return achievement_info
    except Exception as e:
        logger.error(f"❌ Ошибка формирования достижений: {e}")
        return []


async def _send_achievements_event(response, unlocked_achievements: list) -> None:
    """Отправка события о достижениях через SSE."""
    try:
        import json as json_lib

        achievement_info = _format_achievements(unlocked_achievements)
        if achievement_info:
            chunk_data = json_lib.dumps({"achievements": achievement_info}, ensure_ascii=False)
            await response.write(f"event: achievements\ndata: {chunk_data}\n\n".encode())
    except Exception as e:
        logger.error(f"❌ Stream: Ошибка формирования достижений: {e}")


def _extract_user_name_from_message(user_message: str) -> tuple[str | None, bool]:
    """
    Извлечение имени пользователя из сообщения.

    Returns:
        tuple: (имя или None, является ли отказом)
    """
    import re

    cleaned_message = user_message.strip().lower()
    cleaned_message = re.sub(r"[.,!?;:]+$", "", cleaned_message)

    refusal_patterns = [
        r"не\s+хочу",
        r"не\s+скажу",
        r"не\s+буду",
        r"не\s+назову",
        r"не\s+хочу\s+называть",
        r"не\s+буду\s+называть",
        r"не\s+хочу\s+говорить",
        r"не\s+скажу\s+имя",
        r"не\s+хочу\s+сказать",
    ]
    is_refusal = any(re.search(pattern, cleaned_message) for pattern in refusal_patterns)
    if is_refusal:
        return None, True

    common_words = [
        "да",
        "нет",
        "ок",
        "окей",
        "хорошо",
        "спасибо",
        "привет",
        "пока",
        "здравствуй",
        "здравствуйте",
        "как дела",
        "что",
        "как",
        "почему",
        "где",
        "когда",
        "кто",
    ]

    cleaned_for_check = cleaned_message.split()[0] if cleaned_message.split() else cleaned_message

    is_like_name = (
        2 <= len(cleaned_for_check) <= 15
        and re.match(r"^[а-яёА-ЯЁa-zA-Z-]+$", cleaned_for_check)
        and cleaned_for_check not in common_words
        and len(cleaned_message.split()) <= 2
    )

    if is_like_name:
        return cleaned_message.split()[0].capitalize(), False

    return None, False


async def _process_photo_message(
    photo_base64: str, telegram_id: int, message: str
) -> tuple[str | None, web.Response | None]:
    """
    Обработка фото сообщения.

    Returns:
        tuple: (user_message, error_response) - если error_response не None, вернуть его
    """
    try:
        logger.info(f"📷 Mini App: Обработка фото от {telegram_id}")
        logger.info(f"📷 Mini App: photo_base64 length: {len(photo_base64)}")

        if "base64," in photo_base64:
            photo_base64 = photo_base64.split("base64,")[1]
            logger.info(f"📷 Mini App: После удаления префикса, length: {len(photo_base64)}")

        photo_bytes = base64.b64decode(photo_base64)
        logger.info(f"📷 Mini App: Декодировано {len(photo_bytes)} байт изображения")

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)

            if not user:
                return None, web.json_response({"error": "User not found"}, status=404)

            vision_service = VisionService()
            logger.info(f"📷 Mini App: Вызываю analyze_image для пользователя {user.age} лет")
            vision_result = await vision_service.analyze_image(
                image_data=photo_bytes,
                user_message=message or "Проанализируй это фото с заданием и реши задачу полностью",
                user_age=user.age,
            )

            # Используем анализ напрямую, без префикса "[Фото с заданием]"
            # Vision API уже проанализировал фото и дал ответ, используем его напрямую
            if vision_result.analysis and vision_result.analysis.strip():
                user_message = vision_result.analysis
            elif vision_result.recognized_text:
                # Если есть только распознанный текст, используем его
                user_message = f"На фото написано: {vision_result.recognized_text}\n\nПомоги решить эту задачу полностью."
            else:
                user_message = message or "Помоги мне разобраться с этой задачей"

            logger.info(f"✅ Фото проанализировано: {user_message[:100]}")
            return user_message, None

    except Exception as e:
        logger.error(f"❌ Ошибка обработки фото: {e}", exc_info=True)
        return None, web.json_response({"error": f"Ошибка обработки фото: {str(e)}"}, status=500)


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
            # Оптимизация: используем SQL COUNT/SUM вместо загрузки всех объектов
            from sqlalchemy import func, select

            messages_count = (
                db.execute(
                    select(func.count(ChatHistory.id)).where(
                        ChatHistory.user_telegram_id == telegram_id
                    )
                ).scalar()
                or 0
            )

            from bot.models import LearningSession, UserProgress

            sessions_count = (
                db.execute(
                    select(func.count(LearningSession.id)).where(
                        LearningSession.user_telegram_id == telegram_id
                    )
                ).scalar()
                or 0
            )

            total_points = (
                db.execute(
                    select(func.coalesce(func.sum(UserProgress.points), 0)).where(
                        UserProgress.user_telegram_id == telegram_id
                    )
                ).scalar()
                or 0
            )

            subjects_count = (
                db.execute(
                    select(func.count(UserProgress.id)).where(
                        UserProgress.user_telegram_id == telegram_id
                    )
                ).scalar()
                or 0
            )

            # Детальная аналитика только для Premium
            detailed_analytics = None
            if is_premium:
                from bot.services.analytics_service import AnalyticsService

                analytics_service = AnalyticsService(db)
                detailed_analytics = DetailedAnalyticsResponse(
                    messages_per_day=analytics_service.get_messages_per_day(telegram_id),
                    most_active_subjects=analytics_service.get_most_active_subjects(telegram_id),
                    learning_trends=analytics_service.get_learning_trends(telegram_id),
                )

            stats = DashboardStatsResponse(
                total_messages=messages_count,
                learning_sessions=sessions_count,
                total_points=total_points,
                subjects_studied=subjects_count,
                current_streak=1,  # Временно hardcode
                detailed_analytics=detailed_analytics,
            )

            return web.json_response(
                {
                    "success": True,
                    "stats": stats.model_dump(exclude_none=True),
                    "is_premium": is_premium,
                }
            )

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
            # Логируем структуру запроса для отладки
            logger.info(
                f"📦 Получен JSON запрос: telegram_id={data.get('telegram_id')}, "
                f"has_message={bool(data.get('message'))}, "
                f"has_photo={bool(data.get('photo_base64'))}, "
                f"has_audio={bool(data.get('audio_base64'))}, "
                f"audio_length={len(data.get('audio_base64', '')) if data.get('audio_base64') else 0}"
            )
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
            user_message, error_response = await _process_audio_message(
                audio_base64, telegram_id, message
            )
            if error_response:
                return error_response

        # Обработка фото
        if photo_base64:
            user_message, error_response = await _process_photo_message(
                photo_base64, telegram_id, message
            )
            if error_response:
                return error_response

        # Если нет ни фото ни аудио - должно быть текстовое сообщение
        if not user_message or not user_message.strip():
            logger.warning(
                f"⚠️ user_message пустой после обработки: message={message}, audio={bool(audio_base64)}, photo={bool(photo_base64)}"
            )
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
            can_request, limit_reason = premium_service.can_make_ai_request(
                telegram_id, username=user.username
            )

            if not can_request:
                logger.warning(f"🚫 AI запрос заблокирован для user={telegram_id}: {limit_reason}")
                return web.json_response(
                    {
                        "error": limit_reason,
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "is_premium": False,
                        "premium_required": True,
                        "premium_message": (
                            "🐼 Ой! Ты уже использовал все бесплатные вопросы сегодня!\n\n"
                            "💎 Чтобы задавать вопросы без ограничений, перейди на Premium!\n\n"
                            "✨ С Premium ты сможешь:\n"
                            "• Задавать сколько угодно вопросов\n"
                            "• Получать помощь по всем предметам\n"
                            "• Играть в игры без ограничений"
                        ),
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

            # Генерируем ответ AI
            ai_service = get_ai_service()
            ai_response = await ai_service.generate_response(
                user_message=user_message,
                chat_history=history,
                user_age=user.age,
                user_name=user.first_name,
                is_history_cleared=is_history_cleared,
                message_count_since_name=user_message_count,
                skip_name_asking=user.skip_name_asking,
                non_educational_questions_count=user.non_educational_questions_count,
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
                # Увеличиваем счетчик запросов (независимо от истории)
                premium_service.increment_request_count(telegram_id)

                logger.info(f"💾 Сохраняю сообщение пользователя: {user_message[:50]}...")
                user_msg = history_service.add_message(telegram_id, user_message, "user")
                logger.info(f"✅ Сообщение пользователя добавлено в сессию: id={user_msg.id}")

                # Если история была очищена и пользователь, возможно, назвал имя
                if is_history_cleared and not user.first_name and not user.skip_name_asking:
                    extracted_name, is_refusal = _extract_user_name_from_message(user_message)
                    if is_refusal:
                        user.skip_name_asking = True
                        logger.info(
                            "✅ Пользователь отказался называть имя, устанавливаем флаг skip_name_asking"
                        )
                    elif extracted_name:
                        user.first_name = extracted_name
                        logger.info(f"✅ Имя пользователя обновлено: {user.first_name}")

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

                    # Используем анализ напрямую, без префикса "[Фото с заданием]"
                    # Vision API уже проанализировал фото и дал ответ, используем его напрямую
                    if vision_result.analysis and vision_result.analysis.strip():
                        user_message = vision_result.analysis
                    elif vision_result.recognized_text:
                        # Если есть только распознанный текст, используем его
                        user_message = f"На фото написано: {vision_result.recognized_text}\n\nПомоги решить эту задачу полностью."
                    else:
                        user_message = message or "Помоги мне разобраться с этой задачей"

                    logger.info("✅ Stream: Фото проанализировано")
                    await response.write(b'event: status\ndata: {"status": "photo_analyzed"}\n\n')

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

            # Получаем веб-контекст (как в обычном generate_response)
            from bot.config import settings
            from bot.config.prompts import AI_SYSTEM_PROMPT

            relevant_materials = await response_generator.knowledge_service.get_helpful_content(
                user_message, user.age
            )
            web_context = response_generator.knowledge_service.format_knowledge_for_ai(
                relevant_materials
            )

            # Формируем system prompt с учетом возраста, имени и веб-контекста
            enhanced_system_prompt = AI_SYSTEM_PROMPT

            # КРИТИЧЕСКИ ВАЖНО: Дополнительное напоминание о запрете $ и LaTeX
            enhanced_system_prompt += (
                "\n\n🚫🚫🚫 КРИТИЧЕСКОЕ НАПОМИНАНИЕ: "
                "НИКОГДА не используй символ $ (доллар) в формулах - в школе его НЕТ! "
                "НИКОГДА не используй LaTeX (\\frac, \\sqrt, \\text, \\cdot, ^, _, \\begin, \\end). "
                "НИКОГДА не используй сложные математические символы: ², ³, ∑, ∫, ∞, ≈, ≤, ≥, ∠, ° "
                "Все формулы простыми словами, как в школьных тетрадях 1-9 классов! "
                "Дроби: '1/2' или 'одна вторая', НЕ \\frac. "
                "Степени: '2 в квадрате' или '2×2', НЕ 2². "
                "Корни: 'корень из 9', НЕ \\sqrt{9}."
            )

            if user.age:
                enhanced_system_prompt += (
                    f"\n\nВажно: Адаптируй ответ под возраст пользователя ({user.age} лет)."
                )

            # Логика обращения по имени (рандомно каждые 5-10 сообщений ОТ пользователя)
            import random

            if user.first_name and user_message_count >= 5:
                # Рандомно обращаемся по имени каждые 5-10 сообщений (50% шанс)
                # Это делает обращение естественным и не навязчивым
                should_use_name = (
                    user_message_count >= 5 and user_message_count <= 10 and random.random() < 0.5
                )

                if should_use_name:
                    enhanced_system_prompt += (
                        f"\n\nВАЖНО: Обратись к пользователю по имени '{user.first_name}' в начале ответа. "
                        f"Используй имя естественно, например: '{user.first_name}, давай разберём это!' или "
                        f"'Понял, {user.first_name}! Сейчас объясню...' "
                        f"Не злоупотребляй - обращайся по имени только иногда, не в каждом ответе!"
                    )

            # Если история очищена - уточнить имя (только если пользователь не отказался И имя не сохранено в БД)
            # ВАЖНО: Имя хранится в БД (user.first_name), поэтому при очистке истории оно НЕ теряется!
            # Спрашиваем имя ТОЛЬКО если его действительно нет в БД
            if is_history_cleared and not user.first_name and not user.skip_name_asking:
                enhanced_system_prompt += (
                    "\n\n🚫🚫🚫 КРИТИЧЕСКИ ВАЖНО: История чата была очищена (пользователь очистил чат). "
                    "В начале ответа ПОПРОСИ пользователя назвать своё имя, "
                    "чтобы ты мог обращаться к нему по имени в будущем. "
                    "Например: 'Привет! Давай знакомиться! Как тебя зовут? 🐼' "
                    "или 'Привет! Меня зовут PandaPal. А как тебя зовут?'\n\n"
                    "⚠️ КРИТИЧЕСКИ ВАЖНО - ПРОВЕРКА ИМЕНИ:\n"
                    "Если пользователь написал что-то, ТЫ ДОЛЖЕН ПРОВЕРИТЬ что это действительно ИМЯ:\n"
                    "❌ НЕ является именем: 'да', 'нет', 'ок', 'хорошо', 'спасибо', 'привет', 'математика', 'задача', 'помоги', 'реши', "
                    "любые фразы длиннее 20 символов, содержит цифры или спецсимволы (кроме дефиса), обычные слова, вопросы, фразы и предложения.\n"
                    "✅ ЯВЛЯЕТСЯ именем: короткое слово 2-15 символов, только буквы (русские, латинские) и дефис, НЕ является обычным словом.\n"
                    "Примеры имен: Саша, Маша, Данил, Артём, Анастасия, Максим, Виктория.\n\n"
                    "⚠️ ЕСЛИ ПОЛЬЗОВАТЕЛЬ НАПИСАЛ ЕРУНДУ ВМЕСТО ИМЕНИ:\n"
                    "Ты ДОЛЖЕН это ПОНЯТЬ и ВЕЖЛИВО ПЕРЕСПРОСИТЬ:\n"
                    "'Хм, это не очень похоже на имя. Можешь назвать своё настоящее имя? Например: Саша, Маша, Данил и т.д. "
                    "Если не хочешь - скажи, и я больше не буду спрашивать! 😊'\n\n"
                    "Если пользователь отказывается называть имя (пишет 'не хочу', 'не скажу', 'не буду' и т.д.), "
                    "вежливо скажи что это нормально и больше не спрашивай об имени."
                )

            # Проверяем, написал ли пользователь привет
            user_message_lower = user_message.lower().strip()
            greeting_words = [
                "привет",
                "здравствуй",
                "здравствуйте",
                "добрый день",
                "добрый вечер",
                "доброе утро",
                "здарова",
                "хай",
                "hi",
                "hello",
            ]
            user_greeted = any(greeting in user_message_lower for greeting in greeting_words)

            # Проверяем, написал ли пользователь прощание
            farewell_words = [
                "пока",
                "до свидания",
                "до свиданья",
                "прощай",
                "прощайте",
                "увидимся",
                "до встречи",
                "bye",
                "goodbye",
                "see you",
            ]
            user_farewelled = any(farewell in user_message_lower for farewell in farewell_words)

            # Приветствие ТОЛЬКО если:
            # 1. История пустая (начало диалога) ИЛИ
            # 2. История была очищена ИЛИ
            # 3. Пользователь сам поздоровался (и НЕ прощается)
            should_greet = (
                (not history) or is_history_cleared or user_greeted
            ) and not user_farewelled

            if should_greet:
                enhanced_system_prompt += (
                    "\n\n👋 ПРИВЕТСТВИЕ: Пользователь поздоровался или это начало диалога. "
                    "Поприветствуй его естественно ОДИН РАЗ (можно использовать варианты приветствий из промпта). "
                    "НЕ повторяй 'Привет' в следующих ответах!"
                )
            else:
                enhanced_system_prompt += (
                    "\n\n🚫🚫🚫 КРИТИЧЕСКИ ВАЖНО: Пользователь НЕ здоровался и это НЕ начало диалога. "
                    "Пользователь задал ВОПРОС (текстом, аудио или фото) - ОТВЕЧАЙ СРАЗУ ПО ДЕЛУ!\n"
                    "❌ НЕ говори 'Привет' в начале ответа!\n"
                    "❌ НЕ говори 'Я рад помочь тебе'!\n"
                    "❌ НЕ говори 'Рад помочь'!\n"
                    "❌ НЕ говори 'С удовольствием помогу'!\n"
                    "❌ НЕ говори 'Конечно, помогу'!\n"
                    "❌ НЕ говори 'Давай разберём' в начале!\n"
                    "✅ НАЧИНАЙ ОТВЕТ СРАЗУ С РЕШЕНИЯ ЗАДАЧИ ИЛИ ОБЪЯСНЕНИЯ!\n"
                    "✅ ОТВЕТ ДОЛЖЕН БЫТЬ СТРУКТУРИРОВАННЫМ (не полотно текста)!\n"
                    "✅ В КОНЦЕ ОТВЕТА СПРОСИ: 'Понятно? Или рассказать подробнее?'"
                )

            # Прощание ТОЛЬКО если пользователь прощается
            if user_farewelled:
                enhanced_system_prompt += (
                    "\n\n👋 ПРОЩАНИЕ: Пользователь прощается. "
                    "Попрощайся с ним естественно ОДИН РАЗ: 'Пока! Удачи в учёбе! 🐼' или "
                    "'До свидания! Если будут вопросы - обращайся! 📚' или "
                    "'Пока! Желаю успехов! ✨' "
                    "НЕ говори 'Привет' в ответе на прощание! "
                    "НЕ повторяй прощание в следующих ответах!"
                )

            # Логика перенаправления на учебу после 2+ непредметных вопросов
            if user.non_educational_questions_count >= 2:
                enhanced_system_prompt += (
                    f"\n\n🚫 ВАЖНО: Пользователь задал уже {user.non_educational_questions_count} непредметных вопроса подряд. "
                    "Вежливо, но настойчиво перенаправь его на учебу. "
                    "Скажи что-то вроде: 'Интересно общаться, но давай лучше вернемся к учебе! "
                    "Есть вопросы по школьным предметам? Я помогу с математикой, русским, историей и многим другим! 📚'"
                )

            if web_context:
                enhanced_system_prompt += f"\n\nДополнительная информация:\n{web_context}"

            # Преобразуем историю в формат Yandex
            yandex_history = []
            if history:
                for msg in history[-10:]:
                    role = msg.get("role", "user")  # Используем роль напрямую
                    text = msg.get("text", "").strip()
                    if text:
                        yandex_history.append({"role": role, "text": text})

            # Отправляем chunks через streaming
            full_response = ""
            try:
                async for chunk in yandex_service.generate_text_response_stream(
                    user_message=user_message,
                    chat_history=yandex_history,
                    system_prompt=enhanced_system_prompt,
                    temperature=settings.ai_temperature,
                    max_tokens=settings.ai_max_tokens,
                ):
                    # Очищаем chunk от запрещенных символов
                    cleaned_chunk = clean_ai_response(chunk)
                    full_response += cleaned_chunk
                    # Отправляем очищенный chunk через SSE
                    import json as json_lib

                    chunk_data = json_lib.dumps({"chunk": cleaned_chunk}, ensure_ascii=False)
                    await response.write(f"event: chunk\ndata: {chunk_data}\n\n".encode())

                # Очищаем полный ответ от запрещенных символов
                full_response = clean_ai_response(full_response)

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
                        extracted_name, is_refusal = _extract_user_name_from_message(user_message)
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
                        await _send_achievements_event(response, unlocked_achievements)

                except Exception as save_error:
                    logger.error(f"❌ Stream: Ошибка сохранения: {save_error}", exc_info=True)
                    db.rollback()

                # Отправляем событие завершения
                await response.write(b'event: done\ndata: {"status": "completed"}\n\n')
                logger.info(f"✅ Stream: Streaming завершен для {telegram_id}")

            except Exception as stream_error:
                logger.error(f"❌ Stream: Ошибка streaming: {stream_error}", exc_info=True)
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


async def miniapp_log(request: web.Request) -> web.Response:
    """
    Принять логи с фронтенда для отладки.

    POST /api/miniapp/log
    Body: {
        "level": "log" | "error" | "warn" | "info",
        "message": "текст сообщения",
        "data": {...},  # опционально
        "telegram_id": 123,  # опционально
        "user_agent": "...",  # опционально
    }
    """
    try:
        # Проверяем Content-Type
        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            logger.warning(f"⚠️ Неверный Content-Type для /api/miniapp/log: {content_type}")
            return web.json_response(
                {"success": False, "error": "Invalid Content-Type"}, status=400
            )

        # Пытаемся прочитать JSON
        raw_body = None
        try:
            raw_body = await request.read()
            if not raw_body:
                logger.warning("⚠️ Пустое тело запроса в /api/miniapp/log")
                return web.json_response(
                    {"success": False, "error": "Empty request body"}, status=400
                )

            import json

            # Логируем сырые данные для отладки
            raw_body_str = raw_body.decode("utf-8")
            logger.debug(f"📊 Сырое тело запроса (первые 500 символов): {raw_body_str[:500]}")

            data = json.loads(raw_body_str)

            # Логируем распарсенные данные
            logger.debug(f"📊 Распарсенные данные: {str(data)[:500]}")
        except json.JSONDecodeError as json_err:
            logger.warning(f"⚠️ Невалидный JSON в /api/miniapp/log: {json_err}")
            return web.json_response({"success": False, "error": "Invalid JSON"}, status=400)
        except Exception as read_err:
            logger.warning(f"⚠️ Ошибка чтения тела запроса /api/miniapp/log: {read_err}")
            return web.json_response(
                {"success": False, "error": "Failed to read request body"}, status=400
            )

        # Извлекаем данные с безопасными значениями по умолчанию
        if not isinstance(data, dict):
            logger.warning(f"⚠️ Данные не являются словарем: {type(data)}")
            return web.json_response({"success": False, "error": "Invalid data format"}, status=400)

        level = data.get("level", "log")
        if level not in ("log", "error", "warn", "info", "debug"):
            level = "log"

        message = data.get("message", "")
        # Безопасно извлекаем log_data - может быть словарем или другим типом
        # ОБЕРТЫВАЕМ ВСЮ ОБРАБОТКУ В TRY-EXCEPT, чтобы избежать KeyError
        log_data = None
        try:
            log_data = data.get("data")
        except Exception as get_data_err:
            logger.debug(
                f"⚠️ Ошибка получения data из запроса: {type(get_data_err).__name__}: {get_data_err}"
            )
            log_data = None

        # Безопасная обработка log_data
        try:
            if log_data is None:
                log_data = {}
            elif isinstance(log_data, str):
                # Если это строка (например, JSON строка), пытаемся распарсить
                try:
                    import json

                    parsed = json.loads(log_data)
                    log_data = parsed if isinstance(parsed, dict) else {"value": str(parsed)[:500]}
                except Exception as parse_err:
                    # Если не JSON, просто строка
                    logger.debug(f"⚠️ Не удалось распарсить log_data как JSON: {parse_err}")
                    log_data = {"value": log_data[:500]}
            elif not isinstance(log_data, dict):
                # Если это не словарь, преобразуем в словарь с одним ключом
                try:
                    log_data = {"value": str(log_data)[:500]}  # Ограничиваем размер
                except Exception:
                    log_data = {"value": "<unserializable>"}
        except Exception as process_err:
            # Если произошла ошибка при обработке, просто создаем пустой словарь
            logger.debug(
                f"⚠️ Ошибка обработки log_data: {type(process_err).__name__}: {process_err}"
            )
            log_data = {}

        telegram_id = data.get("telegram_id")
        user_agent = data.get("user_agent", request.headers.get("User-Agent", "Unknown"))

        # Формируем лог сообщение
        log_prefix = f"📱 Frontend [{level.upper()}]"
        if telegram_id:
            log_prefix += f" user={telegram_id}"
        log_message = f"{log_prefix}: {message}"

        # Добавляем данные если есть
        if log_data:
            try:
                import json

                # ПРОСТОЕ РЕШЕНИЕ: используем json.dumps с безопасной функцией default
                # Обертываем в try-except, чтобы избежать любых KeyError
                def safe_str(obj):
                    """Безопасная функция для преобразования объектов в строку"""
                    try:
                        return str(obj)
                    except Exception:
                        return "<unserializable>"

                try:
                    # Пытаемся сериализовать через JSON
                    if isinstance(log_data, dict):
                        data_str = json.dumps(log_data, ensure_ascii=False, default=safe_str)
                    else:
                        data_str = safe_str(log_data)

                    if len(data_str) > 1000:
                        data_str = data_str[:1000] + "... (truncated)"
                    log_message += f" | data={data_str}"
                except (KeyError, TypeError, ValueError) as json_err:
                    # Если произошла ошибка при сериализации, просто пропускаем данные
                    logger.debug(
                        f"⚠️ Не удалось сериализовать log_data: {type(json_err).__name__}: {json_err}"
                    )
                    pass
                except Exception as json_err:
                    # Для любых других ошибок тоже пропускаем
                    logger.debug(
                        f"⚠️ Неожиданная ошибка при сериализации log_data: {type(json_err).__name__}: {json_err}"
                    )
                    pass
            except Exception as e:
                # Если не удалось сериализовать, просто пропускаем данные
                logger.debug(f"⚠️ Общая ошибка обработки log_data: {type(e).__name__}: {e}")
                pass

        # Логируем в зависимости от уровня
        # Обертываем логирование в try-except, чтобы избежать ошибок
        try:
            # Упрощаем логирование - убираем extra, чтобы избежать проблем
            if level == "error":
                logger.error(log_message)
            elif level == "warn":
                logger.warning(log_message)
            elif level == "info":
                logger.info(log_message)
            else:
                logger.debug(log_message)
        except Exception as log_err:
            # Если не удалось залогировать, просто логируем ошибку без форматирования
            with suppress(Exception):
                logger.debug(f"⚠️ Ошибка логирования: {type(log_err).__name__}: {str(log_err)}")

        return web.json_response({"success": True})

    except KeyError as key_err:
        # Специальная обработка KeyError - логируем детали
        error_msg = str(key_err)
        logger.error(f"❌ KeyError при приеме лога с фронтенда: {error_msg}", exc_info=True)
        # Логируем сырые данные, если они были прочитаны
        try:
            if "raw_body" in locals() and raw_body:
                logger.debug(f"📊 Сырые данные запроса (первые 500 символов): {raw_body[:500]}")
            if "data" in locals():
                logger.debug(f"📊 Распарсенные данные (первые 500 символов): {str(data)[:500]}")
        except Exception:
            pass
        # Возвращаем 200, чтобы не засорять консоль фронтенда ошибками
        return web.json_response({"success": False, "error": "Internal server error"}, status=200)
    except Exception as e:
        # Детальное логирование ошибки для отладки
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"❌ Ошибка приема лога с фронтенда: {error_type}: {error_msg}", exc_info=True)
        # Логируем сырые данные, если они были прочитаны
        try:
            if "raw_body" in locals() and raw_body:
                logger.debug(f"📊 Сырые данные запроса (первые 500 символов): {raw_body[:500]}")
        except Exception:
            pass
        # Возвращаем 200, чтобы не засорять консоль фронтенда ошибками
        return web.json_response({"success": False, "error": "Internal server error"}, status=200)


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
            with suppress(ValueError):
                telegram_id = validate_telegram_id(telegram_id_str)

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
    app.router.add_post("/api/miniapp/ai/chat-stream", miniapp_ai_chat_stream)  # Streaming endpoint
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

    # Логирование с фронтенда
    app.router.add_post("/api/miniapp/log", miniapp_log)

    logger.info("✅ Mini App API routes зарегистрированы")
