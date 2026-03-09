"""
Обработка текстовых сообщений для AI чата.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.database import get_db
from bot.monitoring import log_user_activity, monitor_performance
from bot.services import ChatHistoryService, UserService
from bot.services.ai_service_solid import get_ai_service

from .helpers import (
    build_visualization_enhanced_message,
    clean_auto_generation_mentions,
    detect_and_translate_message,
    extract_user_name_from_message,
    handle_image_generation_request,
    offer_feedback_form,
    send_ai_response,
)


def register_handlers(router: Router) -> None:
    """Регистрирует handlers для текстовых сообщений."""
    router.message.register(start_ai_chat, F.text & (F.text == "💬 Общение с AI"))
    router.message.register(handle_ai_message, F.text)
    # Callback для кнопки "Показать карту"
    router.callback_query.register(handle_show_map_callback, F.data.startswith("show_map:"))


@monitor_performance
async def start_ai_chat(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Активация режима общения с AI

    Args:
        message: Сообщение от пользователя
        state: FSM состояние
    """
    await message.answer(
        text="🐼 <b>Режим общения с AI активирован!</b>\n\n"
        "Теперь просто пиши мне любые вопросы — я отвечу! 💡",
        parse_mode="HTML",
    )


async def handle_show_map_callback(callback: CallbackQuery):
    """
    Обработчик callback для кнопки "Показать карту".

    Генерирует карту и образовательное пояснение через AI.
    """
    try:
        location = callback.data.replace("show_map:", "")
        await callback.answer("Загружаю карту...")

        from bot.services.visualization_service import get_visualization_service

        viz_service = get_visualization_service()
        map_image = viz_service.generate_country_map(location)

        if map_image:
            from aiogram.types import BufferedInputFile

            photo = BufferedInputFile(map_image, filename="map.png")
            location_title = location.capitalize()

            # Генерируем образовательное пояснение через AI
            caption = await _generate_map_explanation(callback.from_user.id, location_title)

            await callback.message.answer_photo(photo=photo, caption=caption[:1024])
            if len(caption) > 1024:
                await callback.message.answer(text=caption[1024:])
            logger.info(f"🗺️ Показана карта с пояснением для: {location}")
        else:
            await callback.message.answer(
                f"К сожалению, не удалось найти карту для '{location}'. "
                "Попробуй уточнить название."
            )

    except Exception as e:
        logger.error(f"Ошибка показа карты: {e}")
        await callback.message.answer("Не удалось загрузить карту. Попробуй позже.")


async def _generate_map_explanation(telegram_id: int, location: str) -> str:
    """Генерирует образовательное пояснение к карте через AI."""
    try:
        ai_service = get_ai_service()

        # Получаем возраст пользователя для адаптации пояснения
        user_age = None
        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user(telegram_id)
            if user:
                user_age = user.age

        prompt = (
            f"Покажи карту {location}\n\n"
            f"Дай краткое образовательное пояснение к карте «{location}»: "
            "где находится объект (часть света, страна/регион), "
            "основные географические особенности (рельеф, климат, водные объекты), "
            "соседние территории, интересные факты для школьника. "
            "Опирайся на уже показанную карту: «На карте выше показан(а)…». "
            "3–5 предложений, структурированно."
        )

        response = await ai_service.generate_response(
            user_message=prompt,
            user_age=user_age,
        )
        return response if response else f"🗺️ Карта: {location}"

    except Exception as e:
        logger.warning(f"Не удалось сгенерировать пояснение к карте: {e}")
        return f"🗺️ Карта: {location}"


@monitor_performance
async def handle_ai_message(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Обработка текстового сообщения для AI

    ВАЖНО: Этот метод является ядром взаимодействия с пользователем.
    Включает полную цепочку обработки с модерацией контента и историей чата.
    Изменения могут повлиять на безопасность и качество ответов.

    Алгоритм:
    1. Получить пользователя из БД
    2. Загрузить историю сообщений (контекст для AI)
    3. Проверить контент на безопасность (модерация)
    4. Отправить в AI с контекстом
    5. Получить ответ
    6. Промодерировать ответ AI
    7. Сохранить оба сообщения в историю
    8. Отправить ответ пользователю

    Args:
        message: Текстовое сообщение от пользователя
        state: FSM состояние
    """
    telegram_id = message.from_user.id
    user_message = message.text

    # Показываем индикатор "печатает..."
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Секретный запрос для особенного человека
        # Debug: логируем что пришло
        if "<" in user_message or ">" in user_message or "*" in user_message:
            logger.debug(
                f"🔍 Проверка секретного запроса: '{user_message}' (длина: {len(user_message.strip())})"
            )
            logger.debug(f"🔍 Байты: {user_message.strip().encode('utf-8')}")

        if user_message.strip() == "<>***<>":
            special_message = "Создано с любовью для Агаты ❤️❤️❤️"
            await message.answer(text=special_message)
            logger.info(f"💝 Секретное сообщение отправлено пользователю {telegram_id}")
            return

        # Проверка взрослых тем (ЖКУ, банки и т.д.) — единая точка через сервис
        from bot.services.adult_topics_service import get_adult_topics_service

        explanation = get_adult_topics_service().try_get_adult_topic_response(user_message)
        if explanation:
            await message.answer(text=explanation)
            logger.info(f"📚 Объяснена взрослая тема пользователю {telegram_id}")
            with get_db() as db:
                history_service = ChatHistoryService(db)
                history_service.add_message(
                    telegram_id=telegram_id,
                    message_text=user_message,
                    message_type="user",
                )
                history_service.add_message(
                    telegram_id=telegram_id,
                    message_text=explanation,
                    message_type="ai",
                )
            return

        # Детектор запросов на генерацию изображений (YandexART)
        if await handle_image_generation_request(message, user_message, state):
            return

        # Правила по запрещённым темам отключены — не применяются ни в каком виде

        # Работа с базой данных
        with get_db() as db:
            # Инициализируем сервисы
            user_service = UserService(db)
            history_service = ChatHistoryService(db)

            # Получаем пользователя
            user = user_service.get_or_create_user(
                telegram_id=telegram_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )

            # Проверка Premium-лимитов
            from bot.handlers.ai_chat.helpers import check_premium_limit
            from bot.services.premium_features_service import PremiumFeaturesService

            premium_service = PremiumFeaturesService(db)

            if not await check_premium_limit(telegram_id, message.from_user.username, message):
                return

            # Проверка ленивости панды (перед обработкой запроса)
            from bot.services.panda_lazy_service import PandaLazyService

            lazy_service = PandaLazyService(db)
            is_lazy, lazy_message = lazy_service.check_and_update_lazy_state(telegram_id)
            if is_lazy and lazy_message:
                logger.info(f"😴 Панда 'ленива' для пользователя {telegram_id}")
                await message.answer(text=lazy_message)
                return

            # Для premium - больше истории для контекста
            history_limit = 50 if premium_service.is_premium_active(telegram_id) else 10

            # Загружаем историю сообщений для контекста
            history = history_service.get_formatted_history_for_ai(telegram_id, limit=history_limit)

            # Проверяем, была ли очистка истории (история пустая)
            is_history_cleared = len(history) == 0

            # Подсчитываем количество сообщений пользователя с последнего обращения по имени
            from bot.utils.chat_utils import count_user_messages_since_name_mention

            user_message_count = count_user_messages_since_name_mention(history, user.first_name)

            logger.info(
                f"💬 Сообщение от {telegram_id} ({user.first_name}): "
                f"{user_message[:50]}... | История: {len(history)} сообщений | "
                f"Сообщений с последнего обращения: {user_message_count}"
            )

            # Модерация: только запрещённые слова (мат). При блоке — вежливый перевод темы, не молчание.
            from bot.services.moderation_service import ContentModerationService

            moderation_service = ContentModerationService()
            is_safe, block_reason = moderation_service.is_safe_content(user_message)
            if not is_safe:
                redirect_text = moderation_service.get_safe_response_alternative(block_reason or "")
                moderation_service.log_blocked_content(
                    telegram_id, user_message, block_reason or "модерация"
                )
                await message.answer(text=redirect_text)
                return

            # Предложение отдыха/игры после 10 или 20 ответов подряд; ответ «продолжаем» или «играем»
            lazy_service = PandaLazyService(db)
            rest_response, _skip_ai, _show_video = lazy_service.check_rest_offer(
                telegram_id, user_message, user.first_name or message.from_user.first_name
            )
            if rest_response:
                history_service.add_message(
                    telegram_id=telegram_id, message_text=user_message, message_type="user"
                )
                history_service.add_message(
                    telegram_id=telegram_id, message_text=rest_response, message_type="ai"
                )
                db.commit()
                await message.answer(text=rest_response)
                return

            # Показываем статус "Панда печатает..."
            await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

            # Определяем язык и переводим если не русский
            user_message, _ = await detect_and_translate_message(user_message)

            # Определяем Premium статус пользователя
            is_premium = premium_service.is_premium_active(telegram_id)

            # Проверяем, было ли отправлено автоматическое приветствие
            # Если история содержит сообщение от AI с приветствием - считаем что приветствие было отправлено
            is_auto_greeting_sent = False
            if history:
                for msg in history:
                    if msg.get("role") == "assistant":
                        msg_text = msg.get("text", "").lower()
                        if (
                            "привет" in msg_text
                            or "начнем" in msg_text
                            or "чем могу помочь" in msg_text
                        ):
                            is_auto_greeting_sent = True
                            break

            # Получаем AI сервис (SOLID фасад)
            ai_service = get_ai_service()

            # Определяем, является ли вопрос образовательным (единый список — config)
            from bot.config.educational_keywords import EDUCATIONAL_KEYWORDS

            user_message_lower = user_message.lower()
            educational_keywords = EDUCATIONAL_KEYWORDS
            is_educational = any(keyword in user_message_lower for keyword in educational_keywords)

            # Обновляем счетчик непредметных вопросов
            if is_educational:
                # Если вопрос образовательный - сбрасываем счетчик
                user.non_educational_questions_count = 0
                from bot.services.learning_session_service import LearningSessionService

                LearningSessionService(db).record_educational_question(telegram_id)
            else:
                # Если непредметный - увеличиваем счетчик
                user.non_educational_questions_count += 1

            # КРИТИЧЕСКИ ВАЖНО: Сначала проверяем визуализацию, потом генерируем ответ
            # Это нужно, чтобы AI знал, что будет визуализация, и мог сгенерировать релевантное пояснение
            visualization_image = None
            visualization_type = None
            try:
                from bot.services.visualization_service import get_visualization_service

                viz_service = get_visualization_service()
                # Используем универсальный метод детекции
                visualization_image, visualization_type = viz_service.detect_visualization_request(
                    user_message
                )

                # Определяем тип визуализации для контекста AI
                # Используем тип из детектора, если он есть, иначе определяем по контексту
                if visualization_image and not visualization_type:
                    # Если детектор не вернул тип, определяем по контексту
                    user_message_lower = user_message.lower()
                    if "табл" in user_message_lower and "умнож" in user_message_lower:
                        visualization_type = "multiplication_table"
                    elif "график" in user_message_lower:
                        visualization_type = "graph"
                    elif "табл" in user_message_lower:
                        visualization_type = "table"
                    else:
                        visualization_type = "visualization"

            except Exception as e:
                logger.debug(f"⚠️ Ошибка генерации визуализации: {e}")

            # Формируем расширенное сообщение с контекстом визуализации
            enhanced_user_message = user_message
            if visualization_image and visualization_type:
                enhanced_user_message = build_visualization_enhanced_message(
                    user_message,
                    visualization_type,
                )

            # Предпочтение по эмодзи: парсим из сообщения и сохраняем в профиль
            from bot.services.emoji_preference import parse_emoji_preference_from_message

            emoji_pref = parse_emoji_preference_from_message(user_message)
            if emoji_pref is not None:
                user.emoji_in_chat = emoji_pref
                db.commit()

            ai_response = await ai_service.generate_response(
                user_message=enhanced_user_message,
                chat_history=history,
                user_age=user.age,
                user_name=user.first_name,
                user_grade=user.grade,
                is_history_cleared=is_history_cleared,
                message_count_since_name=user_message_count,
                skip_name_asking=user.skip_name_asking,
                non_educational_questions_count=user.non_educational_questions_count,
                is_premium=is_premium,
                is_auto_greeting_sent=is_auto_greeting_sent,
                user_gender=getattr(user, "gender", None),
                emoji_in_chat=getattr(user, "emoji_in_chat", None),
            )

            # Правила по запрещённым темам отключены — ответ не фильтруем

            # Добавляем вовлекающий вопрос после визуализаций
            if visualization_image and visualization_type:
                from bot.services.yandex_ai_response_generator import (
                    add_random_engagement_question,
                )

                ai_response = add_random_engagement_question(ai_response)

            # Увеличиваем счетчик запросов (независимо от истории)
            limit_reached, total_requests = premium_service.increment_request_count(telegram_id)

            # Проактивное уведомление от панды при достижении лимита
            if limit_reached:
                try:
                    from aiogram import Bot

                    from bot.config import settings

                    bot_instance = Bot(token=settings.telegram_bot_token)
                    await premium_service.send_limit_reached_notification(telegram_id, bot_instance)
                    await bot_instance.session.close()
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки проактивного уведомления: {e}")

            # Сохраняем сообщение пользователя в историю
            history_service.add_message(
                telegram_id=telegram_id, message_text=user_message, message_type="user"
            )

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

                # Извлекаем класс
                if not user.grade:
                    from bot.api.miniapp.helpers import extract_user_grade_from_message

                    extracted_grade = extract_user_grade_from_message(user_message)
                    if extracted_grade:
                        user.grade = extracted_grade
                        logger.info(f"✅ Класс пользователя обновлен: {user.grade}")
                    logger.info(f"✅ Имя пользователя обновлено: {user.first_name}")

            # Сохраняем ответ AI в историю
            history_service.add_message(
                telegram_id=telegram_id, message_text=ai_response, message_type="ai"
            )

            # Увеличиваем счётчик ответов подряд (для предложения отдыха/игры)
            lazy_service = PandaLazyService(db)
            lazy_service.increment_consecutive_after_ai(telegram_id)

            # Обрабатываем геймификацию (XP и достижения)
            try:
                from bot.services.gamification_service import GamificationService

                gamification_service = GamificationService(db)
                unlocked_achievements = gamification_service.process_message(
                    telegram_id, user_message
                )

                # Если разблокировано новое достижение, уведомляем пользователя
                if unlocked_achievements:
                    for achievement_id in unlocked_achievements:
                        # Находим достижение по ID
                        from bot.services.gamification_service import ALL_ACHIEVEMENTS

                        achievement = next(
                            (a for a in ALL_ACHIEVEMENTS if a.id == achievement_id), None
                        )
                        if achievement:
                            await message.answer(
                                f"🏆 <b>Новое достижение!</b>\n\n"
                                f"{achievement.icon} <b>{achievement.title}</b>\n"
                                f"{achievement.description}\n\n"
                                f"+{achievement.xp_reward} XP 🎉",
                                parse_mode="HTML",
                            )
            except Exception as e:
                logger.error(f"❌ Ошибка обработки геймификации: {e}", exc_info=True)

            logger.info(f"🤖 AI ответил пользователю {telegram_id}")

            # Логируем успешную активность пользователя
            log_user_activity(telegram_id, "ai_message_sent", True)

            # Записываем метрику образования
            try:
                from bot.services.analytics_service import AnalyticsService

                analytics_service = AnalyticsService(db)
                analytics_service.record_education_metric(
                    metric_name="ai_interactions",
                    value=1.0,
                    user_telegram_id=telegram_id,
                )
            except Exception as e:
                logger.debug(f"⚠️ Не удалось записать метрику образования: {e}")

        # Удаляем упоминания про автоматическую генерацию из ответа
        if visualization_image:
            ai_response = clean_auto_generation_mentions(ai_response)

        # Отправляем ответ пользователю
        await send_ai_response(
            message, ai_response, visualization_image, visualization_type, user_message
        )

        # Предлагаем форму обратной связи (total_requests из increment_request_count)
        await offer_feedback_form(message, total_requests)

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        log_user_activity(telegram_id, "ai_message_error", False, str(e))

        await message.answer(
            text="Ой, что-то пошло не так. Попробуй переформулировать вопрос или напиши /start"
        )
