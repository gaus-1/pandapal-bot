"""
Endpoints для обычного AI чата (без streaming).
"""

import json

from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from bot.api.validators import AIChatRequest
from bot.database import get_db
from bot.models import ChatHistory
from bot.services import ChatHistoryService, UserService
from bot.services.ai_service_solid import get_ai_service
from bot.services.yandex_ai_response_generator import clean_ai_response

from .helpers import (
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
            user_message, error_response = await process_audio_message(
                audio_base64, telegram_id, message
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
                # Vision API дал готовый ответ - возвращаем его сразу
                photo_analysis_result = photo_result.replace("__READY_ANSWER__", "", 1)
                user_message = message or "📷 Фото"

                # Сохраняем в историю и возвращаем ответ
                with get_db() as db:
                    user_service = UserService(db)
                    history_service = ChatHistoryService(db)

                    user = user_service.get_user_by_telegram_id(telegram_id)
                    if not user:
                        return web.json_response({"error": "User not found"}, status=404)

                    # Очищаем ответ от запрещенных символов
                    cleaned_response = clean_ai_response(photo_analysis_result)

                    # Сохраняем в историю
                    try:
                        from bot.services.premium_features_service import PremiumFeaturesService

                        premium_service = PremiumFeaturesService(db)
                        premium_service.increment_request_count(telegram_id)
                        history_service.add_message(telegram_id, user_message, "user")
                        history_service.add_message(telegram_id, cleaned_response, "ai")

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

                        db.commit()

                        # Формируем ответ
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

            # Определяем Premium статус пользователя
            is_premium = premium_service.is_premium_active(telegram_id)

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
                is_premium=is_premium,
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
                    extracted_name, is_refusal = extract_user_name_from_message(user_message)
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
