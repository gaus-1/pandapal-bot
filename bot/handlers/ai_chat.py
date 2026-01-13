"""
Обработчик общения с AI для образовательного чата PandaPal.

Этот модуль реализует основную функциональность бота - диалог с AI ассистентом
PandaPalAI на базе Yandex Cloud (YandexGPT, SpeechKit, Vision). Обеспечивает
безопасное и адаптивное общение с детьми, включая поддержку различных типов контента.

Основные возможности:
- Текстовые сообщения с AI ассистентом
- Обработка изображений и их анализ
- Голосовые сообщения с распознаванием речи
- Адаптация ответов под возраст пользователя
- Многоуровневая модерация контента
- Сохранение истории чата для контекста
- Мониторинг активности

Безопасность:
- 5-уровневая система модерации
- Фильтрация запрещенных тем
- Адаптация под возраст (6-18 лет)
- Логирование всех взаимодействий
- Логирование активности

Поддерживаемые форматы:
- Текст (основной режим общения)
- Изображения (анализ и описание)
- Голосовые сообщения (распознавание речи)
- Эмодзи и специальные символы
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PhotoSize
from loguru import logger

from bot.database import get_db
from bot.monitoring import log_user_activity, monitor_performance
from bot.services import ChatHistoryService, ContentModerationService, UserService
from bot.services.ai_service_solid import get_ai_service

# Создаём роутер для AI чата
router = Router(name="ai_chat")


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


@router.message(F.text & (F.text == "💬 Общение с AI"))
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


@router.message(F.text)
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
        # Продвинутая проверка контента на безопасность
        moderation_service = ContentModerationService()

        # Сначала базовая проверка
        is_safe, reason = moderation_service.is_safe_content(user_message)

        if not is_safe:
            logger.warning(f"🚫 Заблокирован контент от {telegram_id}: {reason}")
            moderation_service.log_blocked_content(telegram_id, user_message, reason)
            log_user_activity(telegram_id, "blocked_content", False, reason)

            # Записываем метрику безопасности (базовая блокировка)
            try:
                with get_db() as db:
                    user_service = UserService(db)
                    user = user_service.get_user_by_telegram_id(telegram_id)
                    if user and user.user_type == "child":
                        from bot.services.analytics_service import AnalyticsService

                        analytics_service = AnalyticsService(db)
                        analytics_service.record_safety_metric(
                            metric_name="blocked_messages",
                            value=1.0,
                            user_telegram_id=telegram_id,
                            category="basic_moderation",
                        )
            except Exception as e:
                logger.debug(f"⚠️ Не удалось записать метрику безопасности: {e}")

            safe_response = moderation_service.get_safe_response_alternative("blocked_content")
            await message.answer(text=safe_response)
            return

        # Затем продвинутая модерация
        user_context = {
            "telegram_id": telegram_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
        }

        try:
            advanced_result = await moderation_service.advanced_moderate_content(
                user_message, user_context
            )

            # Если продвинутая модерация заблокировала контент
            if not advanced_result.is_safe:
                logger.warning(
                    f"🚫 Продвинутая модерация заблокировала контент от {telegram_id}: "
                    f"{advanced_result.reason} (уверенность: {advanced_result.confidence:.2f})"
                )

                # Логируем активность
                log_user_activity(
                    telegram_id,
                    "advanced_blocked_content",
                    False,
                    f"{advanced_result.category.value if advanced_result.category else 'unknown'}: {advanced_result.reason}",
                )

                # Записываем метрику безопасности
                try:
                    with get_db() as db:
                        from bot.services.analytics_service import AnalyticsService

                        analytics_service = AnalyticsService(db)
                        analytics_service.record_safety_metric(
                            metric_name="blocked_messages",
                            value=1.0,
                            user_telegram_id=telegram_id,
                            category=(
                                advanced_result.category.value
                                if advanced_result.category
                                else "unknown"
                            ),
                        )
                except Exception as e:
                    logger.debug(f"⚠️ Не удалось записать метрику безопасности: {e}")

                # Используем альтернативный ответ из продвинутой модерации
                response_text = (
                    advanced_result.alternative_response
                    or moderation_service.get_safe_response_alternative("blocked_content")
                )
                await message.answer(text=response_text)
                return

        except Exception as e:
            logger.error(f"❌ Ошибка продвинутой модерации: {e}")
            # Продолжаем с базовой модерацией в случае ошибки

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

            # КРИТИЧНО: Проверка Premium для неограниченных запросов
            from bot.services.premium_features_service import PremiumFeaturesService

            premium_service = PremiumFeaturesService(db)
            can_request, limit_reason = premium_service.can_make_ai_request(
                telegram_id, username=message.from_user.username
            )

            if not can_request:
                logger.warning(f"🚫 AI запрос заблокирован для user={telegram_id}: {limit_reason}")
                from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="💎 Узнать о Premium", callback_data="premium:info"
                            )
                        ]
                    ]
                )

                await message.answer(limit_reason, reply_markup=keyboard, parse_mode="HTML")
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

            logger.info(
                f"💬 Сообщение от {telegram_id} ({user.first_name}): "
                f"{user_message[:50]}... | История: {len(history)} сообщений | "
                f"Сообщений с последнего обращения: {user_message_count}"
            )

            # Показываем статус "Панда печатает..."
            await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

            # Определяем язык текста и переводим если не русский
            from bot.services.translate_service import get_translate_service

            translate_service = get_translate_service()
            detected_lang = await translate_service.detect_language(user_message)

            # Если язык определен и это не русский, но поддерживаемый язык
            if (
                detected_lang
                and detected_lang != "ru"
                and detected_lang in translate_service.SUPPORTED_LANGUAGES
            ):
                logger.info(f"🌍 Обнаружен иностранный язык: {detected_lang}")
                # Переводим текст
                translated_text = await translate_service.translate_text(
                    user_message, target_language="ru", source_language=detected_lang
                )
                if translated_text:
                    lang_name = translate_service.get_language_name(detected_lang)
                    # Формируем сообщение с переводом и объяснением
                    user_message = (
                        f"🌍 Вижу, что ты написал на {lang_name}!\n\n"
                        f"📝 Оригинал: {user_message}\n"
                        f"🇷🇺 Перевод: {translated_text}\n\n"
                        f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                    )
                    logger.info(f"✅ Текст переведен: {detected_lang} → ru")

            # Определяем Premium статус пользователя
            is_premium = premium_service.is_premium_active(telegram_id)

            # Получаем AI сервис (SOLID фасад)
            ai_service = get_ai_service()

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

            # Генерируем ответ с учётом контекста, возраста и класса
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

            # Промодерируем ответ AI на безопасность
            ai_response = moderation_service.sanitize_ai_response(ai_response)

            # Проверяем, нужна ли визуализация (таблица умножения, графики)
            visualization_image = None
            try:
                from bot.services.visualization_service import get_visualization_service

                viz_service = get_visualization_service()
                # Используем универсальный метод детекции
                visualization_image = viz_service.detect_visualization_request(user_message)

            except Exception as e:
                logger.debug(f"⚠️ Ошибка генерации визуализации: {e}")

            # Увеличиваем счетчик запросов (независимо от истории)
            premium_service.increment_request_count(telegram_id)

            # Сохраняем сообщение пользователя в историю
            history_service.add_message(
                telegram_id=telegram_id, message_text=user_message, message_type="user"
            )

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

            # Сохраняем ответ AI в историю
            history_service.add_message(
                telegram_id=telegram_id, message_text=ai_response, message_type="ai"
            )

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

            # Сохраняем количество сообщений для проверки
            message_count = user.message_count

        # Отправляем ответ пользователю (без parse_mode для избежания ошибок форматирования)
        if visualization_image:
            # Отправляем изображение вместе с текстом
            from aiogram.types import BufferedInputFile

            photo = BufferedInputFile(visualization_image, filename="visualization.png")
            await message.answer_photo(
                photo=photo,
                caption=ai_response[:1024],  # Telegram ограничение на caption
            )
            # Если текст длиннее, отправляем остаток отдельным сообщением
            if len(ai_response) > 1024:
                await message.answer(text=ai_response[1024:])
        else:
            await message.answer(
                text=ai_response,
            )

        # Предлагаем форму обратной связи после каждого 20-го сообщения
        if message_count % 20 == 0 and message_count > 0:
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

            feedback_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📝 Оставить отзыв",
                            url="https://forms.yandex.ru/cloud/695ba5a6068ff07700f0029a",
                        )
                    ]
                ]
            )

            await message.answer(
                "🎉 Спасибо за общение! Поделись мнением?\n"
                "Твой отзыв поможет улучшить PandaPal 🐼",
                reply_markup=feedback_keyboard,
            )

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        log_user_activity(telegram_id, "ai_message_error", False, str(e))

        await message.answer(
            text="Ой, что-то пошло не так. Попробуй переформулировать вопрос или напиши /start"
        )


@router.message(F.voice)
async def handle_voice(message: Message):
    """
    Обработка голосовых сообщений

    ВАЖНО: Интеграция с Yandex SpeechKit для распознавания речи.
    Стабильная версия с проверенными параметрами.

    Параметры распознавания:
    - Формат: OGG Opus (Telegram стандарт)
    - Язык: ru-RU
    - API: Yandex Cloud SpeechKit STT

    Args:
        message: Голосовое сообщение от пользователя
    """
    telegram_id = message.from_user.id

    try:
        logger.info(f"🎤 Получено голосовое сообщение от {telegram_id}")

        # Показываем что обрабатываем
        processing_msg = await message.answer("🎤 Слушаю твоё сообщение... Пожалуйста, подожди! 🐼")

        # Скачиваем голосовое сообщение
        voice_file = await message.bot.get_file(message.voice.file_id)
        voice_bytes = await message.bot.download_file(voice_file.file_path)

        # Читаем байты
        audio_data = voice_bytes.read()

        # Получаем сервис распознавания речи
        from bot.services.speech_service import get_speech_service

        speech_service = get_speech_service()

        # Распознаем речь с автоопределением языка
        recognized_text = await speech_service.transcribe_voice(
            audio_data,
            language="ru",  # Русский язык
        )

        if not recognized_text:
            await processing_msg.edit_text(
                "🎤 Не удалось распознать речь.\n" "Попробуй говорить четче или напиши текстом! 📝"
            )
            log_user_activity(telegram_id, "voice_recognition_failed", False, "SpeechKit failed")
            return

        # Удаляем сообщение "Слушаю..."
        await processing_msg.delete()

        # Определяем язык текста и переводим если не русский
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        detected_lang = await translate_service.detect_language(recognized_text)

        # Если язык определен и это не русский, но поддерживаемый язык
        if (
            detected_lang
            and detected_lang != "ru"
            and detected_lang in translate_service.SUPPORTED_LANGUAGES
        ):
            lang_name = translate_service.get_language_name(detected_lang)
            logger.info(f"🌍 Аудио: Обнаружен иностранный язык: {detected_lang}")
            # Переводим текст
            translated_text = await translate_service.translate_text(
                recognized_text, target_language="ru", source_language=detected_lang
            )
            if translated_text:
                # Показываем что было распознано и переведено
                await message.answer(
                    f'🎤 <i>Я услышал на {lang_name}:</i> "{recognized_text}"\n'
                    f'🇷🇺 <i>Перевод:</i> "{translated_text}"\n\n'
                    f"Сейчас объясню перевод и подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
                # Формируем сообщение с переводом и объяснением
                recognized_text = (
                    f"🌍 Вижу, что ты сказал на {lang_name}!\n\n"
                    f"📝 Оригинал: {recognized_text}\n"
                    f"🇷🇺 Перевод: {translated_text}\n\n"
                    f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                )
                logger.info(f"✅ Аудио переведено: {detected_lang} → ru")
            else:
                await message.answer(
                    f'🎤 <i>Я услышал:</i> "{recognized_text}"\n\n'
                    f"Сейчас подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
        else:
            # Показываем что было распознано
            await message.answer(
                f'🎤 <i>Я услышал:</i> "{recognized_text}"\n\n' f"Сейчас подумаю над ответом... 🐼",
                parse_mode="HTML",
            )

        logger.info(f"✅ Речь распознана: {recognized_text[:100]}")

        # Логируем успешную активность
        log_user_activity(telegram_id, "voice_message_sent", True)

        # Обрабатываем как обычное текстовое сообщение (передаем оригинальный message с bot)
        # Временно сохраняем текст в message для обработки
        original_text = message.text
        try:
            # Используем __dict__ для обхода frozen instance
            object.__setattr__(message, "text", recognized_text)
            await handle_ai_message(message, None)
        finally:
            # Восстанавливаем оригинальный текст
            if original_text is not None:
                object.__setattr__(message, "text", original_text)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки голосового сообщения: {e}")
        await message.answer(
            "😔 Произошла ошибка при обработке голосового сообщения.\n"
            "Попробуй написать текстом! 📝"
        )
        log_user_activity(telegram_id, "voice_processing_error", False, str(e))


@router.message(F.audio)
async def handle_audio(message: Message):
    """
    Обработка аудиофайлов (музыка, треки)

    ВАЖНО: Использует ту же логику распознавания что и голосовые сообщения.
    Yandex SpeechKit STT с параметрами (voice_file_bytes, language).

    Args:
        message: Аудиофайл от пользователя
    """
    telegram_id = message.from_user.id

    try:
        logger.info(f"🎵 Получен аудиофайл от {telegram_id}")

        # Показываем что обрабатываем
        processing_msg = await message.answer("🎵 Слушаю аудиофайл... Пожалуйста, подожди! 🐼")

        # Скачиваем аудиофайл
        audio_file = await message.bot.get_file(message.audio.file_id)
        audio_bytes = await message.bot.download_file(audio_file.file_path)

        # Читаем байты
        audio_data = audio_bytes.read()

        # Получаем сервис распознавания речи
        from bot.services.speech_service import get_speech_service

        speech_service = get_speech_service()

        # Распознаем речь
        recognized_text = await speech_service.transcribe_voice(
            audio_data,
            language="ru",
        )

        if not recognized_text:
            await processing_msg.edit_text(
                "🎵 Не удалось распознать речь из аудио.\n"
                "Попробуй голосовое сообщение или напиши текстом! 📝"
            )
            log_user_activity(telegram_id, "audio_recognition_failed", False, "SpeechKit failed")
            return

        # Удаляем сообщение "Слушаю..."
        await processing_msg.delete()

        # Определяем язык текста и переводим если не русский
        from bot.services.translate_service import get_translate_service

        translate_service = get_translate_service()
        detected_lang = await translate_service.detect_language(recognized_text)

        # Если язык определен и это не русский, но поддерживаемый язык
        if (
            detected_lang
            and detected_lang != "ru"
            and detected_lang in translate_service.SUPPORTED_LANGUAGES
        ):
            lang_name = translate_service.get_language_name(detected_lang)
            logger.info(f"🌍 Аудио: Обнаружен иностранный язык: {detected_lang}")
            # Переводим текст
            translated_text = await translate_service.translate_text(
                recognized_text, target_language="ru", source_language=detected_lang
            )
            if translated_text:
                # Показываем что было распознано и переведено
                await message.answer(
                    f'🎵 <i>Я услышал на {lang_name}:</i> "{recognized_text}"\n'
                    f'🇷🇺 <i>Перевод:</i> "{translated_text}"\n\n'
                    f"Сейчас объясню перевод и подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
                # Формируем сообщение с переводом и объяснением
                recognized_text = (
                    f"🌍 Вижу, что ты сказал на {lang_name}!\n\n"
                    f"📝 Оригинал: {recognized_text}\n"
                    f"🇷🇺 Перевод: {translated_text}\n\n"
                    f"Объясни этот перевод и помоги понять грамматику простыми словами для ребенка."
                )
                logger.info(f"✅ Аудио переведено: {detected_lang} → ru")
            else:
                await message.answer(
                    f'🎵 <i>Я услышал:</i> "{recognized_text}"\n\n'
                    f"Сейчас подумаю над ответом... 🐼",
                    parse_mode="HTML",
                )
        else:
            # Показываем что было распознано
            await message.answer(
                f'🎵 <i>Я услышал:</i> "{recognized_text}"\n\n' f"Сейчас подумаю над ответом... 🐼",
                parse_mode="HTML",
            )

        logger.info(f"✅ Речь из аудио распознана: {recognized_text[:100]}")

        # Логируем успешную активность
        log_user_activity(telegram_id, "audio_message_sent", True)

        # Обрабатываем как обычное текстовое сообщение
        original_text = message.text
        try:
            object.__setattr__(message, "text", recognized_text)
            await handle_ai_message(message, None)
        finally:
            if original_text is not None:
                object.__setattr__(message, "text", original_text)

    except Exception as e:
        logger.error(f"❌ Ошибка обработки аудиофайла: {e}")
        await message.answer(
            "😔 Произошла ошибка при обработке аудиофайла.\n" "Попробуй написать текстом! 📝"
        )
        log_user_activity(telegram_id, "audio_processing_error", False, str(e))


@router.message(F.photo)
@monitor_performance
async def handle_image(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Обработка изображений через AI Vision

    ВАЖНО: Полный цикл обработки изображений с модерацией.
    Использует Yandex Vision OCR для извлечения текста и анализа содержимого.
    Включает проверку безопасности контента на изображении.

    Args:
        message: Сообщение с изображением
        state: FSM состояние
    """
    try:
        # Получаем самое большое изображение
        photo: PhotoSize = max(message.photo, key=lambda p: p.file_size)

        # Проверяем размер изображения
        if photo.file_size > 20 * 1024 * 1024:  # 20MB лимит
            await message.answer(
                "🖼️ Изображение слишком большое! Максимум 20MB. "
                "Попробуй сжать фото и отправить снова 📏"
            )
            return

        # Показываем, что обрабатываем изображение
        processing_msg = await message.answer("🖼️ Анализирую изображение... Пожалуйста, подожди! 🐼")

        # Получаем файл изображения
        file = await message.bot.get_file(photo.file_id)
        image_data = await message.bot.download_file(file.file_path)

        # Читаем данные изображения
        image_bytes = image_data.read()

        # Получаем пользователя и его данные
        with get_db() as db:
            user_service = UserService(db)
            user = user_service.get_user_by_telegram_id(message.from_user.id)

            if not user:
                await processing_msg.edit_text("❌ Сначала зарегистрируйся командой /start")
                return

            # Получаем сервисы
            ai_service = get_ai_service()
            history_service = ChatHistoryService(db)

            # Проверяем модерацию изображения
            is_safe, reason = await ai_service.moderate_image_content(image_bytes)

            if not is_safe:
                await processing_msg.edit_text(
                    "🚫 Это изображение не подходит для детей. "
                    "Попробуй отправить что-то другое! 🐼"
                )
                log_user_activity(message.from_user.id, "image_blocked", False, reason)
                return

            # Получаем подпись к изображению (если есть)
            caption = message.caption or ""

            # Анализируем изображение с помощью AI
            ai_response = await ai_service.analyze_image(
                image_data=image_bytes,
                user_message=caption,
                user_age=user.age,
            )

            # Сохраняем в историю (синхронный метод, без await)
            history_service.add_message(
                telegram_id=message.from_user.id,
                message_text=f"[ИЗОБРАЖЕНИЕ] {caption}" if caption else "[ИЗОБРАЖЕНИЕ]",
                message_type="user",
            )

            history_service.add_message(
                telegram_id=message.from_user.id, message_text=ai_response, message_type="ai"
            )

            # Проверяем, нужна ли визуализация в ответе AI
            visualization_image = None
            try:
                from bot.services.visualization_service import get_visualization_service

                viz_service = get_visualization_service()
                # Используем универсальный метод детекции для ответа AI
                visualization_image = viz_service.detect_visualization_request(ai_response)
            except Exception as e:
                logger.debug(f"⚠️ Ошибка генерации визуализации для фото: {e}")

            # Отправляем ответ с визуализацией если есть
            if visualization_image:
                from aiogram.types import BufferedInputFile

                photo = BufferedInputFile(visualization_image, filename="visualization.png")
                await processing_msg.delete()
                await message.answer_photo(
                    photo=photo,
                    caption=ai_response[:1024],  # Telegram ограничение на caption
                )
                # Если текст длиннее, отправляем остаток отдельным сообщением
                if len(ai_response) > 1024:
                    await message.answer(text=ai_response[1024:])
            else:
                await processing_msg.edit_text(ai_response)

            log_user_activity(
                message.from_user.id, "image_analyzed", True, f"Size: {len(image_bytes)} bytes"
            )

    except Exception as e:
        logger.error(f"❌ Ошибка обработки изображения: {e}")
        await message.answer(
            "🖼️ Произошла ошибка при анализе изображения. " "Попробуй отправить другое фото! 🐼"
        )
        log_user_activity(message.from_user.id, "image_error", False, str(e))


@router.message(F.document)
@monitor_performance
async def handle_document(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Обработка документов (PDF, Word и т.д.)

    Args:
        message: Сообщение с документом
        state: FSM состояние
    """
    try:
        # Проверяем тип документа
        document = message.document

        # Поддерживаемые форматы
        supported_formats = {
            "application/pdf": "PDF",
            "application/msword": "Word",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
            "text/plain": "Текстовый файл",
        }

        file_type = supported_formats.get(document.mime_type, "Неизвестный формат")

        # Проверяем размер файла (максимум 20MB)
        if document.file_size > 20 * 1024 * 1024:
            await message.answer(
                "📄 Файл слишком большой! Максимум 20MB. "
                "Попробуй сжать документ или скопировать текст 📏"
            )
            return

        # Показываем информацию о файле
        await message.answer(
            f"📄 Получен документ: {document.file_name}\n"
            f"Тип: {file_type}\n"
            f"Размер: {document.file_size / 1024:.1f} KB\n\n"
            "Для полноценной обработки документов нужно больше времени на разработку. "
            "Пока лучше скопируй текст задачи и отправь текстом — я помогу! 📝"
        )

        # Логируем попытку отправки документа
        log_user_activity(
            message.from_user.id,
            "document_upload",
            True,
            f"Type: {file_type}, Size: {document.file_size}",
        )

    except Exception as e:
        logger.error(f"❌ Ошибка обработки документа: {e}")
        await message.answer(
            "📄 Произошла ошибка при обработке документа. " "Попробуй отправить текст задачи! 📝"
        )
        log_user_activity(message.from_user.id, "document_error", False, str(e))
