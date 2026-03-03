"""
Endpoints для обычного AI чата (без streaming).
"""

import json

from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import AIChatRequest, require_owner
from bot.database import get_db
from bot.models import ChatHistory
from bot.services import ChatHistoryService, UserService
from bot.services.ai_service_solid import get_ai_service
from bot.services.yandex_ai_response_generator import clean_ai_response

from .helpers import (
    extract_user_grade_from_message,
    extract_user_name_from_message,
    format_achievements,
    process_audio_message,
    process_photo_message,
)


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
    # Логируем ВСЕ запросы для отладки (безопасно обрабатываем mock-запросы в тестах)
    client_ip = getattr(request, "remote", None)
    method = getattr(request, "method", "UNKNOWN")
    path_qs = getattr(request, "path_qs", getattr(request, "path", ""))
    logger.info(f"📨 Mini App AI Chat запрос от IP: {client_ip}, метод: {method}, путь: {path_qs}")

    try:
        # Логируем размер запроса для отладки
        headers = getattr(request, "headers", {}) or {}
        content_length = headers.get("Content-Length")
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

        # Проверка владельца ресурса (OWASP A01)
        if error_response := require_owner(request, telegram_id):
            return error_response

        # КРИТИЧНО: Проверка лимита ДО любых платных вызовов (SpeechKit, Vision, YandexGPT)
        raw_message = validated.message or ""

        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                return web.json_response({"error": "User not found"}, status=404)
            from bot.services.premium_features_service import PremiumFeaturesService

            premium_service = PremiumFeaturesService(db)
            can_request, limit_reason = premium_service.can_make_ai_request(
                telegram_id, username=user.username
            )
            if not can_request:
                logger.warning(f"🚫 Mini App Chat: AI запрос заблокирован для user={telegram_id}")
                return web.json_response(
                    {
                        "error": limit_reason,
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "is_premium": False,
                        "premium_required": True,
                        "premium_message": limit_reason,
                    },
                    status=429,
                )

            # Проверка ленивости панды (как в Telegram-обработчике).
            # Для фидбека ("плохой/хороший ответ") не перехватываем ленивостью,
            # чтобы пользователь получил реакцию панды.
            from bot.services.panda_chat_reactions import get_chat_reaction
            from bot.services.panda_lazy_service import PandaLazyService

            if not get_chat_reaction(raw_message):
                lazy_service = PandaLazyService(db)
                is_lazy, lazy_message = lazy_service.check_and_update_lazy_state(telegram_id)
                if is_lazy and lazy_message:
                    logger.info(f"😴 Mini App: Панда 'ленива' для пользователя {telegram_id}")
                    return web.json_response({"response": lazy_message})

        message = raw_message
        photo_base64 = validated.photo_base64
        audio_base64 = validated.audio_base64

        user_message = message

        # Обработка аудио (приоритетнее фото)
        if audio_base64:
            user_message, error_response = await process_audio_message(
                audio_base64, telegram_id, message, language_code=validated.language_code
            )
            if error_response:
                return error_response

        # Обработка фото
        if photo_base64:
            photo_result, error_response = await process_photo_message(
                photo_base64, telegram_id, message
            )
            if error_response:
                return error_response

            # Проверяем, дал ли Vision API готовый ответ (маркер __READY_ANSWER__)
            if photo_result and photo_result.startswith("__READY_ANSWER__"):
                # Vision API дал готовый ответ - модерация перед показом ребёнку
                photo_analysis_result = photo_result.replace("__READY_ANSWER__", "", 1)
                user_message = message or "📷 Фото"

                from bot.services.moderation_service import ContentModerationService

                moderation_service = ContentModerationService()
                is_safe, block_reason = moderation_service.is_safe_content(photo_analysis_result)
                if not is_safe:
                    moderation_service.log_blocked_content(
                        telegram_id, photo_analysis_result, block_reason or "vision_response"
                    )
                    cleaned_response = moderation_service.get_safe_response_alternative(
                        block_reason or ""
                    )
                else:
                    cleaned_response = clean_ai_response(photo_analysis_result)

                # Сохраняем в историю и возвращаем ответ
                with get_db() as db:
                    user_service = UserService(db)
                    history_service = ChatHistoryService(db)

                    user = user_service.get_user_by_telegram_id(telegram_id)
                    if not user:
                        return web.json_response({"error": "User not found"}, status=404)

                    # Сохраняем в историю (cleaned_response уже пройден модерацией выше)
                    try:
                        from bot.services.premium_features_service import PremiumFeaturesService

                        premium_service = PremiumFeaturesService(db)
                        limit_reached, total_requests = premium_service.increment_request_count(
                            telegram_id
                        )

                        # Проактивное уведомление от панды при достижении лимита (фоновая задача)
                        if limit_reached:
                            import asyncio

                            asyncio.create_task(
                                premium_service.send_limit_reached_notification_async(telegram_id)
                            )
                            history_service.add_message(
                                telegram_id, premium_service.get_limit_reached_message_text(), "ai"
                            )
                        history_service.add_message(telegram_id, user_message, "user")
                        history_service.add_message(telegram_id, cleaned_response, "ai")
                        lazy_service = PandaLazyService(db)
                        lazy_service.increment_consecutive_after_ai(telegram_id)

                        # Геймификация
                        unlocked_achievements = []
                        try:
                            from bot.services.gamification_service import GamificationService

                            gamification_service = GamificationService(db)
                            unlocked_achievements = gamification_service.process_message(
                                telegram_id, user_message
                            )
                        except Exception as e:
                            logger.error(f"❌ Ошибка геймификации: {e}", exc_info=True)

                        # Формируем ответ (commit выполнит get_db при выходе)
                        response_data = {"success": True, "response": cleaned_response}
                        if unlocked_achievements:
                            achievement_info = format_achievements(unlocked_achievements)
                            if achievement_info:
                                response_data["achievements_unlocked"] = achievement_info

                        return web.json_response(response_data)
                    except Exception as save_error:
                        logger.error(f"❌ Ошибка сохранения: {save_error}", exc_info=True)
                        db.rollback()
                        # Все равно возвращаем ответ
                        return web.json_response({"success": True, "response": cleaned_response})
            else:
                user_message = photo_result

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

            # Проверка взрослых тем (ЖКУ, банки и т.д.) — единая точка через сервис
            from bot.services.adult_topics_service import get_adult_topics_service

            explanation = get_adult_topics_service().try_get_adult_topic_response(user_message)
            if explanation:
                limit_reached, _ = premium_service.increment_request_count(telegram_id)
                history_service.add_message(telegram_id, user_message, "user")
                history_service.add_message(telegram_id, explanation, "ai")
                if limit_reached:
                    import asyncio

                    asyncio.create_task(
                        premium_service.send_limit_reached_notification_async(telegram_id)
                    )
                    history_service.add_message(
                        telegram_id, premium_service.get_limit_reached_message_text(), "ai"
                    )
                return web.json_response({"response": explanation})

            # Предложение отдыха/игры после 10 или 20 ответов подряд
            lazy_service = PandaLazyService(db)
            from bot.services.panda_chat_reactions import get_chat_reaction

            # Фидбек пользователя (хороший/плохой ответ) не должен
            # перехватываться сценарием отдыха.
            rest_response = None
            if not get_chat_reaction(user_message):
                rest_response, _skip_ai, _show_video = lazy_service.check_rest_offer(
                    telegram_id, user_message, user.first_name
                )
            if rest_response:
                limit_reached, _ = premium_service.increment_request_count(telegram_id)
                history_service.add_message(telegram_id, user_message, "user")
                history_service.add_message(telegram_id, rest_response, "ai")
                if limit_reached:
                    import asyncio

                    asyncio.create_task(
                        premium_service.send_limit_reached_notification_async(telegram_id)
                    )
                    history_service.add_message(
                        telegram_id, premium_service.get_limit_reached_message_text(), "ai"
                    )
                return web.json_response({"response": rest_response})

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

            # Определяем, является ли вопрос образовательным (единый список — config)
            from bot.config.educational_keywords import EDUCATIONAL_KEYWORDS

            user_message_lower = user_message.lower()
            is_educational = any(keyword in user_message_lower for keyword in EDUCATIONAL_KEYWORDS)

            # Обновляем счетчик непредметных вопросов
            if is_educational:
                # Если вопрос образовательный - сбрасываем счетчик
                user.non_educational_questions_count = 0
                from bot.services.learning_session_service import LearningSessionService

                LearningSessionService(db).record_educational_question(telegram_id)
            else:
                # Если непредметный - увеличиваем счетчик
                user.non_educational_questions_count += 1

            # Определяем Premium статус пользователя
            is_premium = premium_service.is_premium_active(telegram_id)

            # Модерация: только запрещённые слова (мат). При блоке — вежливый перевод темы, не молчание.
            from bot.services.moderation_service import ContentModerationService

            moderation_service = ContentModerationService()
            is_safe, block_reason = moderation_service.is_safe_content(user_message)
            if not is_safe:
                redirect_text = moderation_service.get_safe_response_alternative(block_reason or "")
                moderation_service.log_blocked_content(
                    telegram_id, user_message, block_reason or "модерация"
                )
                return web.json_response({"response": redirect_text})

            # Предпочтение по эмодзи: парсим из сообщения и сохраняем в профиль
            from bot.services.emoji_preference import parse_emoji_preference_from_message

            emoji_pref = parse_emoji_preference_from_message(user_message)
            if emoji_pref is not None:
                user.emoji_in_chat = emoji_pref
                db.commit()

            # Генерируем ответ AI
            ai_service = get_ai_service()
            ai_response = await ai_service.generate_response(
                user_message=user_message,
                chat_history=history,
                user_age=user.age,
                user_name=user.first_name,
                user_grade=user.grade,
                is_history_cleared=is_history_cleared,
                message_count_since_name=user_message_count,
                skip_name_asking=user.skip_name_asking,
                non_educational_questions_count=user.non_educational_questions_count,
                is_premium=is_premium,
                user_gender=getattr(user, "gender", None),
                emoji_in_chat=getattr(user, "emoji_in_chat", None),
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
            limit_reached_message_text = None
            unlocked_achievements: list = []
            save_succeeded = False
            try:
                # Увеличиваем счетчик запросов (независимо от истории)
                limit_reached, total_requests = premium_service.increment_request_count(telegram_id)

                # Проактивное уведомление от панды при достижении лимита (в Telegram)
                if limit_reached:
                    import asyncio

                    asyncio.create_task(
                        premium_service.send_limit_reached_notification_async(telegram_id)
                    )
                    limit_reached_message_text = premium_service.get_limit_reached_message_text()

                logger.info(f"💾 Сохраняю сообщение пользователя: {user_message[:50]}...")
                user_msg = history_service.add_message(telegram_id, user_message, "user")
                logger.info(f"✅ Сообщение пользователя добавлено в сессию: id={user_msg.id}")

                # Если история была очищена и пользователь, возможно, назвал имя или класс
                if is_history_cleared and not user.skip_name_asking:
                    # Извлекаем имя
                    if not user.first_name:
                        extracted_name, is_refusal = extract_user_name_from_message(user_message)
                        if is_refusal:
                            user.skip_name_asking = True
                            logger.info(
                                "✅ Пользователь отказался называть имя, устанавливаем флаг skip_name_asking"
                            )
                        elif extracted_name:
                            user.first_name = extracted_name
                            logger.info(f"✅ Имя пользователя обновлено: {user.first_name}")

                    # Извлекаем класс
                    if not user.grade:
                        extracted_grade = extract_user_grade_from_message(user_message)
                        if extracted_grade:
                            user.grade = extracted_grade
                            logger.info(f"✅ Класс пользователя обновлен: {user.grade}")

                logger.info(f"💾 Сохраняю ответ AI: {full_response[:50]}...")
                ai_msg = history_service.add_message(telegram_id, full_response, "ai")
                logger.info(f"✅ Ответ AI добавлен в сессию: id={ai_msg.id}")

                lazy_service = PandaLazyService(db)
                lazy_service.increment_consecutive_after_ai(telegram_id)

                # Сообщение от панды в чат при достижении лимита (как при приветствии)
                if limit_reached and limit_reached_message_text:
                    history_service.add_message(telegram_id, limit_reached_message_text, "ai")

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

                # Commit выполнит get_db при выходе из контекста
                # ПРОВЕРКА: читаем из сессии для подтверждения перед выходом
                check_msg = db.query(ChatHistory).filter_by(id=user_msg.id).first()
                if check_msg:
                    logger.info(
                        f"✅✅✅ ПОДТВЕРЖДЕНО: сообщение {check_msg.id} существует в БД после коммита"
                    )
                else:
                    logger.error(
                        f"❌❌❌ ПРОБЛЕМА: сообщение {user_msg.id} НЕ найдено в БД после коммита!"
                    )
                save_succeeded = True

            except Exception as save_error:
                logger.error(
                    f"❌ КРИТИЧЕСКАЯ ОШИБКА сохранения в историю: {save_error}", exc_info=True
                )
                db.rollback()
                logger.error("❌ Транзакция откачена из-за ошибки сохранения")
                # Продолжаем работу, даже если сохранение не удалось

            # Проверяем размер JSON перед отправкой
            response_data = {"success": True, "response": ai_response}
            if limit_reached_message_text:
                response_data["limit_reached_message"] = limit_reached_message_text

            # Добавляем информацию о разблокированных достижениях только если сохранение прошло (не было rollback)
            if save_succeeded and unlocked_achievements:
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

            json_str = json.dumps(response_data, ensure_ascii=False)
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
