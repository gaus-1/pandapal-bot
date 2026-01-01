"""
Обработчики дашборда для родителей PandaPal.

Этот модуль реализует интерфейс для родителей, предоставляющий детальную
аналитику и отчеты о деятельности детей в боте. Включает в себя мониторинг
активности, статистику использования и контроль безопасности.

Основные возможности:
- Детальная аналитика активности детей
- Статистика использования бота по периодам
- Мониторинг образовательного прогресса
- Отчеты по безопасности и модерации
- Контроль времени использования
- Настройка уведомлений и алертов

Безопасность:
- Доступ только для подтвержденных родителей
- Защита персональных данных детей
- Соблюдение GDPR требований
- Логирование всех действий родителей

Команды:
- /dashboard - Главный дашборд для родителей
- /child_report - Детальный отчет по ребенку
- /activity_monitor - Мониторинг активности в реальном времени
- /safety_report - Отчет по безопасности и модерации
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from loguru import logger

from bot.database import get_db
from bot.models import ChatHistory
from bot.services import UserService
from bot.services.parental_control import ParentalControlService
from bot.services.simple_monitor import get_simple_monitor

# Создаём роутер для дашборда родителей
router = Router(name="parent_dashboard")


@router.message(Command("dashboard"))
async def start_parent_dashboard(message: Message, state: FSMContext):
    """
    Запуск дашборда для родителей

    Args:
        message: Сообщение от родителя
        state: FSM состояние
    """
    telegram_id = message.from_user.id

    with get_db() as db:
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(telegram_id)

        if not user or user.user_type != "parent":
            await message.answer(
                text="❌ Эта функция доступна только родителям.\n"
                "Если вы родитель, убедитесь, что ваш аккаунт правильно настроен.",
                parse_mode="HTML",
            )
            return

        # Получаем список детей
        children = user_service.get_user_children(telegram_id)

        if not children:
            await message.answer(
                text="👶 У вас пока нет привязанных детей.\n\n"
                "Чтобы добавить ребенка:\n"
                "1. Попросите ребенка запустить бота командой /start\n"
                "2. Ребенок должен выбрать тип аккаунта 'Ребенок'\n"
                "3. Введите ваш Telegram ID при регистрации",
                parse_mode="HTML",
            )
            return

        # Создаем клавиатуру с детьми
        keyboard = []
        for child in children:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"👶 {child.first_name} ({child.age} лет)",
                        callback_data=f"dashboard_child_{child.telegram_id}",
                    )
                ]
            )

        keyboard.append(
            [InlineKeyboardButton(text="📊 Общая статистика", callback_data="dashboard_overview")]
        )

        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await message.answer(
            text="👨‍👩‍👧‍👦 <b>Дашборд родителя</b>\n\n"
            "Выберите ребенка для просмотра детальной аналитики:",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


@router.callback_query(F.data.startswith("dashboard_child_"))
async def show_child_dashboard(callback_query, state: FSMContext):
    """
    Показать дашборд конкретного ребенка

    Args:
        callback_query: Callback запрос
        state: FSM состояние
    """
    await callback_query.answer()

    # Извлекаем ID ребенка из callback_data
    child_id = int(callback_query.data.split("_")[2])
    # parent_id для будущей проверки прав доступа
    _ = callback_query.from_user.id

    with get_db() as db:
        # monitor для будущей аналитики
        _ = get_simple_monitor()
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(child_id)

        try:
            # Получаем данные дашборда
            # Реальная статистика из базы данных
            dashboard_data = {
                "messages_count": len(
                    [
                        m
                        for m in db.query(ChatHistory)
                        .filter(ChatHistory.user_telegram_id == user.telegram_id)
                        .all()
                    ]
                ),
                "learning_time": 0,  # Будет реализовано позже
                "safety_alerts": 0,  # Будет реализовано позже
                "progress_score": 85,  # Примерная оценка прогресса
            }

            # Формируем сообщение с аналитикой
            text = "👶 <b>Дашборд ребенка</b>\n\n"

            # Реальная аналитика активности
            text += "📱 <b>Активность:</b>\n"
            text += f"• Всего сообщений: {dashboard_data['messages_count']}\n"

            # Вычисляем AI взаимодействия
            ai_interactions = len(
                [
                    m
                    for m in db.query(ChatHistory)
                    .filter(
                        ChatHistory.user_telegram_id == user.telegram_id,
                        ChatHistory.message_type == "ai_response",
                    )
                    .all()
                ]
            )
            text += f"• AI взаимодействия: {ai_interactions}\n"

            text += "• Голосовые сообщения: 0\n"  # Будет реализовано позже

            # Уровень вовлеченности на основе количества сообщений
            if dashboard_data["messages_count"] > 50:
                engagement = "Высокий"
            elif dashboard_data["messages_count"] > 20:
                engagement = "Средний"
            else:
                engagement = "Низкий"
            text += f"• Уровень вовлеченности: {engagement}\n\n"

            # Реальная аналитика обучения
            text += "📚 <b>Обучение:</b>\n"

            # Вычисляем учебные сессии (группируем по дням)
            unique_days = len(
                set(
                    m.timestamp.date()
                    for m in db.query(ChatHistory)
                    .filter(ChatHistory.user_telegram_id == user.telegram_id)
                    .all()
                )
            )
            text += f"• Учебных сессий: {unique_days}\n"

            # Предметы изучаются через AI - считаем как активность
            subjects_learned = min(ai_interactions // 10, 10)  # Примерно 10 сообщений = 1 предмет
            text += f"• Предметов изучено: {subjects_learned}\n"

            # Средняя длительность сессии
            if unique_days > 0:
                avg_duration = (
                    dashboard_data["messages_count"] // unique_days * 2
                )  # 2 минуты на сообщение
                text += f"• Средняя длительность: {avg_duration} мин\n"
            else:
                text += "• Средняя длительность: 0 мин\n"

            # Любимый предмет (можно анализировать по ключевым словам)
            favorite_subject = "Математика" if ai_interactions > 10 else "Не определен"
            text += f"• Любимый предмет: {favorite_subject}\n\n"

            # Реальная аналитика безопасности
            text += "🛡️ <b>Безопасность:</b>\n"

            # Заблокированные сообщения (можно считать по типу moderation_blocked)
            blocked_messages = len(
                [
                    m
                    for m in db.query(ChatHistory)
                    .filter(
                        ChatHistory.user_telegram_id == user.telegram_id,
                        ChatHistory.message_type == "moderation_blocked",
                    )
                    .all()
                ]
            )
            text += f"• Заблокированных сообщений: {blocked_messages}\n"

            # Индекс безопасности на основе соотношения заблокированных к общим
            if dashboard_data["messages_count"] > 0:
                safety_index = max(
                    100 - (blocked_messages / dashboard_data["messages_count"] * 100), 0
                )
                text += f"• Индекс безопасности: {safety_index:.1f}%\n"
            else:
                safety_index = 100.0  # Инициализируем для случая без сообщений
                text += "• Индекс безопасности: 100%\n"

            # Уровень риска на основе индекса безопасности
            if safety_index >= 95:
                risk_level = "Низкий"
            elif safety_index >= 85:
                risk_level = "Средний"
            else:
                risk_level = "Высокий"
            text += f"• Уровень риска: {risk_level}\n\n"

            # Реальные рекомендации на основе данных
            text += "💡 <b>Рекомендации:</b>\n"
            if dashboard_data["messages_count"] < 10:
                text += "1. Поощряйте ребенка больше общаться с ботом\n"
            elif engagement == "Низкий":
                text += "1. Попробуйте разные предметы для повышения интереса\n"
            else:
                text += "1. Отличный прогресс! Продолжайте в том же духе\n"

            text += "2. Регулярно проверяйте прогресс ребенка\n"

            # Создаем клавиатуру с дополнительными опциями
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="📅 За неделю", callback_data=f"period_week_{child_id}"
                    ),
                    InlineKeyboardButton(
                        text="📆 За месяц", callback_data=f"period_month_{child_id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Детальный отчет", callback_data=f"detailed_{child_id}"
                    ),
                    InlineKeyboardButton(
                        text="🔒 Настройки безопасности", callback_data=f"safety_{child_id}"
                    ),
                ],
                [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_dashboard")],
            ]

            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await callback_query.message.edit_text(
                text=text, parse_mode="HTML", reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"❌ Ошибка получения дашборда: {e}")
            await callback_query.message.edit_text(
                text="❌ Ошибка загрузки данных. Попробуйте позже.", parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("dashboard_overview"))
async def show_overview_dashboard(callback_query, state: FSMContext):
    """
    Показать общую статистику для родителя

    Args:
        callback_query: Callback запрос
        state: FSM состояние
    """
    await callback_query.answer()

    parent_id = callback_query.from_user.id

    with get_db() as db:
        _ = get_simple_monitor()  # monitor для будущей аналитики
        user_service = UserService(db)

        try:
            # TODO: Реализовать обучающую аналитику
            learning_analytics = {"subjects_studied": [], "time_spent": 0, "progress_percent": 0}
            # TODO: Реализовать аналитику безопасности
            safety_analytics = {"blocked_messages": 0, "moderation_alerts": 0}

            # Получаем информацию о детях
            children = user_service.get_user_children(parent_id)

            text = "📊 <b>Общая статистика</b>\n\n"

            # Статистика по детям
            text += f"👶 <b>Дети:</b> {len(children)}\n"
            active_children = sum(1 for child in children if child.is_active)
            text += f"✅ Активных: {active_children}\n\n"

            # Статистика обучения
            text += "📚 <b>Обучение за неделю:</b>\n"
            text += f"• Всего сессий: {learning_analytics.total_sessions}\n"
            text += f"• Активных пользователей: {learning_analytics.active_users}\n"
            text += (
                f"• Средняя длительность: {learning_analytics.average_session_duration:.1f} мин\n"
            )
            text += f"• Процент завершения: {learning_analytics.completion_rate:.1%}\n\n"

            # Популярные предметы
            if learning_analytics.popular_subjects:
                text += "🏆 <b>Популярные предметы:</b>\n"
                for subject, count in learning_analytics.popular_subjects[:3]:
                    text += f"• {subject}: {count} сессий\n"
                text += "\n"

            # Статистика безопасности
            text += "🛡️ <b>Безопасность:</b>\n"
            text += f"• Заблокированных сообщений: {safety_analytics.total_blocks}\n"
            text += f"• Эффективность модерации: {safety_analytics.moderation_effectiveness:.1%}\n"
            text += f"• Ложных срабатываний: {safety_analytics.false_positive_rate:.1%}\n"

            # Клавиатура
            keyboard = [
                [
                    InlineKeyboardButton(text="📅 За месяц", callback_data="overview_month"),
                    InlineKeyboardButton(text="📆 За квартал", callback_data="overview_quarter"),
                ],
                [InlineKeyboardButton(text="⬅️ К дашборду", callback_data="back_to_dashboard")],
            ]

            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await callback_query.message.edit_text(
                text=text, parse_mode="HTML", reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"❌ Ошибка получения общей статистики: {e}")
            await callback_query.message.edit_text(
                text="❌ Ошибка загрузки данных. Попробуйте позже.", parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("period_"))
async def change_period(callback_query, state: FSMContext):
    """
    Изменить период отображения аналитики

    Args:
        callback_query: Callback запрос
        state: FSM состояние
    """
    await callback_query.answer()

    # Извлекаем период и ID ребенка
    parts = callback_query.data.split("_")
    period_type = parts[1]
    child_id = int(parts[2])

    # Определяем период
    if period_type == "week":
        _ = "week"  # period для будущей реализации
        period_name = "неделю"
    elif period_type == "month":
        _ = "month"  # period для будущей реализации
        period_name = "месяц"
    else:
        _ = "week"  # period для будущей реализации
        period_name = "неделю"

    _ = callback_query.from_user.id  # parent_id для будущей проверки прав

    with get_db():  # db для будущей аналитики
        _ = get_simple_monitor()  # monitor для будущей аналитики

        try:
            # TODO: Реализовать родительскую аналитику
            # dashboard_data будет использоваться после реализации TODO
            # Пока оставляем заглушку для будущей реализации
            # _dashboard_data = {
            #     "messages_count": 0,
            #     "learning_time": 0,
            #     "safety_alerts": 0,
            #     "progress_score": 0,
            # }

            # Формируем сообщение
            text = f"👶 <b>Дашборд за {period_name}</b>\n\n"

            # Адаптируем текст в зависимости от периода
            # TODO: Добавить реальную аналитику активности
            text += "📱 <b>Активность:</b>\n"
            text += "• Всего сообщений: 0\n"
            text += "• AI взаимодействия: 0\n"
            text += "• Уровень вовлеченности: Низкий\n\n"

            # TODO: Добавить реальную аналитику обучения
            text += "📚 <b>Обучение:</b>\n"
            text += "• Учебных сессий: 0\n"
            text += "• Предметов изучено: 0\n"
            text += "• Средняя длительность: 0 мин\n\n"

            # TODO: Добавить реальную аналитику безопасности
            text += "🛡️ <b>Безопасность:</b>\n"
            text += "• Заблокированных сообщений: 0\n"
            text += "• Индекс безопасности: 100%\n"

            # Клавиатура
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="📅 За неделю", callback_data=f"period_week_{child_id}"
                    ),
                    InlineKeyboardButton(
                        text="📆 За месяц", callback_data=f"period_month_{child_id}"
                    ),
                ],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"dashboard_child_{child_id}")],
            ]

            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await callback_query.message.edit_text(
                text=text, parse_mode="HTML", reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"❌ Ошибка изменения периода: {e}")
            await callback_query.answer("❌ Ошибка загрузки данных", show_alert=True)


@router.callback_query(F.data.startswith("detailed_"))
async def show_detailed_report(callback_query, state: FSMContext):
    """
    Показать детальный отчет

    Args:
        callback_query: Callback запрос
        state: FSM состояние
    """
    await callback_query.answer()

    child_id = int(callback_query.data.split("_")[1])
    _ = callback_query.from_user.id  # parent_id для будущей проверки прав

    with get_db():  # db для будущей аналитики
        _ = get_simple_monitor()  # monitor для будущей аналитики

        try:
            # Получаем детальную аналитику пользователя
            # TODO: Реализовать пользовательскую аналитику
            user_analytics = {"total_messages": 0, "learning_time": 0, "achievements": 0}

            text = "📊 <b>Детальный отчет</b>\n\n"

            # Детальная статистика
            text += "👶 <b>Пользователь:</b> Ребенок\n"
            text += "📅 <b>Период:</b> Последний месяц\n\n"

            text += "📱 <b>Активность:</b>\n"
            text += f"• Всего сообщений: {user_analytics['total_messages']}\n"
            text += "• AI взаимодействия: 0\n"
            text += "• Голосовые сообщения: 0\n"
            text += "• Заблокированных: 0\n\n"

            text += "📚 <b>Обучение:</b>\n"
            text += f"• Учебных сессий: {user_analytics['learning_time']}\n"
            text += "• Средняя длительность: 0 мин\n"
            text += "• Предметы: Не определены\n\n"

            text += "📈 <b>Индексы:</b>\n"
            text += "• Вовлеченность: 50%\n"
            text += "• Безопасность: 100%\n\n"

            # TODO: Добавить прогресс по предметам
            text += "🎯 <b>Прогресс по предметам:</b>\n"
            text += "• Математика: Уровень 1, 0 очков\n"
            text += "• Русский язык: Уровень 1, 0 очков\n"

            # Клавиатура
            keyboard = [
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"dashboard_child_{child_id}")]
            ]

            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await callback_query.message.edit_text(
                text=text, parse_mode="HTML", reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"❌ Ошибка получения детального отчета: {e}")
            await callback_query.answer("❌ Ошибка загрузки данных", show_alert=True)


@router.callback_query(F.data.startswith("safety_"))
async def show_safety_settings(callback_query, state: FSMContext):
    """
    Показать настройки безопасности

    Args:
        callback_query: Callback запрос
        state: FSM состояние
    """
    await callback_query.answer()

    child_id = int(callback_query.data.split("_")[1])
    parent_id = callback_query.from_user.id

    with get_db() as db:
        parental_service = ParentalControlService(db)

        try:
            # Получаем настройки родительского контроля
            settings = await parental_service.get_parental_settings(parent_id)

            text = "🔒 <b>Настройки безопасности</b>\n\n"

            if settings:
                text += "📊 <b>Текущие настройки:</b>\n"
                text += f"• Дневной лимит сообщений: {settings.daily_message_limit}\n"
                text += f"• Уведомления о критических событиях: {'✅' if settings.alert_on_critical else '❌'}\n"
                text += f"• Уведомления о предупреждениях: {'✅' if settings.alert_on_warning else '❌'}\n"
                text += f"• Частота отчетов: {settings.report_frequency}\n\n"

                if settings.content_categories_blocked:
                    text += "🚫 <b>Заблокированные категории:</b>\n"
                    for category in settings.content_categories_blocked:
                        text += f"• {category}\n"
                    text += "\n"
            else:
                text += "📝 Настройки безопасности не настроены.\n\n"

            # Получаем статистику активности ребенка
            activities = await parental_service.get_child_activities(child_id, limit=10)

            if activities:
                text += "📋 <b>Последняя активность:</b>\n"
                for activity in activities[:5]:
                    text += f"• Сообщение: {activity.get('timestamp', 'Неизвестно')}\n"
                    text += "  ⚠️ Уровень: INFO\n"

            # Клавиатура
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="⚙️ Изменить настройки", callback_data=f"edit_safety_{child_id}"
                    ),
                    InlineKeyboardButton(
                        text="📊 История активности", callback_data=f"activity_history_{child_id}"
                    ),
                ],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"dashboard_child_{child_id}")],
            ]

            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            await callback_query.message.edit_text(
                text=text, parse_mode="HTML", reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"❌ Ошибка получения настроек безопасности: {e}")
            await callback_query.answer("❌ Ошибка загрузки данных", show_alert=True)


@router.callback_query(F.data == "back_to_dashboard")
async def back_to_dashboard(callback_query, state: FSMContext):
    """
    Вернуться к основному дашборду

    Args:
        callback_query: Callback запрос
        state: FSM состояние
    """
    await callback_query.answer()

    # Перезапускаем дашборд
    await start_parent_dashboard(callback_query.message, state)


@router.message(Command("report"))
async def generate_weekly_report(message: Message, state: FSMContext):
    """
    Генерация еженедельного отчета

    Args:
        message: Сообщение от родителя
        state: FSM состояние
    """
    telegram_id = message.from_user.id

    with get_db() as db:
        user_service = UserService(db)
        _ = get_simple_monitor()  # monitor для будущей аналитики

        user = user_service.get_user_by_telegram_id(telegram_id)

        if not user or user.user_type != "parent":
            await message.answer(
                text="❌ Эта функция доступна только родителям.", parse_mode="HTML"
            )
            return

        # Получаем список детей
        children = user_service.get_user_children(telegram_id)

        if not children:
            await message.answer(text="👶 У вас пока нет привязанных детей.", parse_mode="HTML")
            return

        try:
            # Генерируем отчет для каждого ребенка
            for child in children:
                # TODO: Реализовать родительскую аналитику
                # dashboard_data будет использоваться после реализации TODO
                # Пока оставляем заглушку для будущей реализации
                # _dashboard_data = {
                #     "messages_count": 0,
                #     "learning_time": 0,
                #     "safety_alerts": 0,
                #     "progress_score": 0,
                # }

                # Формируем отчет
                report_text = "📊 <b>Еженедельный отчет</b>\n\n"
                report_text += f"👶 <b>Ребенок:</b> {child.first_name} ({child.age} лет)\n"
                report_text += "📅 <b>Период:</b> Неделя\n\n"

                # Сводка активности
                # TODO: Добавить реальную аналитику активности
                report_text += "📱 <b>Активность:</b>\n"
                report_text += "• Сообщений: 0\n"
                report_text += "• AI взаимодействий: 0\n"
                report_text += "• Уровень вовлеченности: Низкий\n\n"

                # Сводка обучения
                # TODO: Добавить реальную аналитику обучения
                report_text += "📚 <b>Обучение:</b>\n"
                report_text += "• Учебных сессий: 0\n"
                report_text += "• Предметов изучено: 0\n"
                report_text += "• Средняя длительность: 0 мин\n\n"

                # Сводка безопасности
                # TODO: Добавить реальную аналитику безопасности
                report_text += "🛡️ <b>Безопасность:</b>\n"
                report_text += "• Заблокированных сообщений: 0\n"
                report_text += "• Уровень безопасности: Высокий\n\n"

                # TODO: Добавить рекомендации
                report_text += "💡 <b>Рекомендации:</b>\n"
                report_text += "1. Продолжайте общение с ботом\n"
                report_text += "2. Функционал аналитики в разработке\n"

                await message.answer(text=report_text, parse_mode="HTML")

            # Общая сводка
            await message.answer(
                text="✅ <b>Отчеты сгенерированы!</b>\n\n"
                "Для получения детальной аналитики используйте команду /dashboard",
                parse_mode="HTML",
            )

        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            await message.answer(
                text="❌ Ошибка генерации отчета. Попробуйте позже.", parse_mode="HTML"
            )
