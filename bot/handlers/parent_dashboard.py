"""
Обработчики дашборда для родителей
Предоставляет аналитику и отчеты о деятельности детей

"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from loguru import logger

from bot.database import get_db
from bot.services import UserService
from bot.services.analytics_service import AnalyticsPeriod, AnalyticsService
from bot.services.parental_control import ParentalControlService

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
    parent_id = callback_query.from_user.id

    with get_db() as db:
        analytics_service = AnalyticsService(db)

        try:
            # Получаем данные дашборда
            dashboard_data = await analytics_service.get_parent_dashboard(
                parent_id=parent_id, child_id=child_id, period=AnalyticsPeriod.WEEK
            )

            # Формируем сообщение с аналитикой
            text = f"👶 <b>Дашборд: {dashboard_data.child_id}</b>\n\n"

            # Сводка активности
            activity = dashboard_data.activity_summary
            text += f"📱 <b>Активность:</b>\n"
            text += f"• Всего сообщений: {activity['total_interactions']}\n"
            text += f"• AI взаимодействия: {activity['ai_usage']}\n"
            text += f"• Голосовые сообщения: {activity['voice_usage']}\n"
            text += f"• Уровень вовлеченности: {activity['engagement_level']}\n\n"

            # Сводка обучения
            learning = dashboard_data.learning_summary
            text += f"📚 <b>Обучение:</b>\n"
            text += f"• Учебных сессий: {learning['sessions_count']}\n"
            text += f"• Предметов изучено: {learning['subjects_covered']}\n"
            text += f"• Средняя длительность: {learning['average_duration']:.1f} мин\n"
            if learning["top_subject"]:
                text += f"• Любимый предмет: {learning['top_subject']}\n\n"

            # Сводка безопасности
            safety = dashboard_data.safety_summary
            text += f"🛡️ <b>Безопасность:</b>\n"
            text += f"• Заблокированных сообщений: {safety['blocked_messages']}\n"
            text += f"• Индекс безопасности: {safety['safety_score']:.1%}\n"
            text += f"• Уровень риска: {safety['risk_level']}\n\n"

            # Рекомендации
            if dashboard_data.recommendations:
                text += f"💡 <b>Рекомендации:</b>\n"
                for i, rec in enumerate(dashboard_data.recommendations[:3], 1):
                    text += f"{i}. {rec}\n"

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
        analytics_service = AnalyticsService(db)
        user_service = UserService(db)

        try:
            # Получаем общую аналитику
            learning_analytics = await analytics_service.get_learning_analytics(
                AnalyticsPeriod.WEEK
            )
            safety_analytics = await analytics_service.get_safety_analytics(AnalyticsPeriod.WEEK)

            # Получаем информацию о детях
            children = user_service.get_user_children(parent_id)

            text = "📊 <b>Общая статистика</b>\n\n"

            # Статистика по детям
            text += f"👶 <b>Дети:</b> {len(children)}\n"
            active_children = sum(1 for child in children if child.is_active)
            text += f"✅ Активных: {active_children}\n\n"

            # Статистика обучения
            text += f"📚 <b>Обучение за неделю:</b>\n"
            text += f"• Всего сессий: {learning_analytics.total_sessions}\n"
            text += f"• Активных пользователей: {learning_analytics.active_users}\n"
            text += (
                f"• Средняя длительность: {learning_analytics.average_session_duration:.1f} мин\n"
            )
            text += f"• Процент завершения: {learning_analytics.completion_rate:.1%}\n\n"

            # Популярные предметы
            if learning_analytics.popular_subjects:
                text += f"🏆 <b>Популярные предметы:</b>\n"
                for subject, count in learning_analytics.popular_subjects[:3]:
                    text += f"• {subject}: {count} сессий\n"
                text += "\n"

            # Статистика безопасности
            text += f"🛡️ <b>Безопасность:</b>\n"
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
        period = AnalyticsPeriod.WEEK
        period_name = "неделю"
    elif period_type == "month":
        period = AnalyticsPeriod.MONTH
        period_name = "месяц"
    else:
        period = AnalyticsPeriod.WEEK
        period_name = "неделю"

    parent_id = callback_query.from_user.id

    with get_db() as db:
        analytics_service = AnalyticsService(db)

        try:
            # Получаем данные дашборда с новым периодом
            dashboard_data = await analytics_service.get_parent_dashboard(
                parent_id=parent_id, child_id=child_id, period=period
            )

            # Формируем сообщение
            text = f"👶 <b>Дашборд за {period_name}</b>\n\n"

            # Адаптируем текст в зависимости от периода
            activity = dashboard_data.activity_summary
            text += f"📱 <b>Активность:</b>\n"
            text += f"• Всего сообщений: {activity['total_interactions']}\n"
            text += f"• AI взаимодействия: {activity['ai_usage']}\n"
            text += f"• Уровень вовлеченности: {activity['engagement_level']}\n\n"

            learning = dashboard_data.learning_summary
            text += f"📚 <b>Обучение:</b>\n"
            text += f"• Учебных сессий: {learning['sessions_count']}\n"
            text += f"• Предметов изучено: {learning['subjects_covered']}\n"
            text += f"• Средняя длительность: {learning['average_duration']:.1f} мин\n\n"

            safety = dashboard_data.safety_summary
            text += f"🛡️ <b>Безопасность:</b>\n"
            text += f"• Заблокированных сообщений: {safety['blocked_messages']}\n"
            text += f"• Индекс безопасности: {safety['safety_score']:.1%}\n"

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
    parent_id = callback_query.from_user.id

    with get_db() as db:
        analytics_service = AnalyticsService(db)

        try:
            # Получаем детальную аналитику пользователя
            user_analytics = await analytics_service.get_user_analytics(
                child_id, AnalyticsPeriod.MONTH
            )

            text = f"📊 <b>Детальный отчет</b>\n\n"

            # Детальная статистика
            text += f"👶 <b>Пользователь:</b> {user_analytics.user_id}\n"
            text += f"📅 <b>Период:</b> Последний месяц\n\n"

            text += f"📱 <b>Активность:</b>\n"
            text += f"• Всего сообщений: {user_analytics.total_messages}\n"
            text += f"• AI взаимодействия: {user_analytics.ai_interactions}\n"
            text += f"• Голосовые сообщения: {user_analytics.voice_messages}\n"
            text += f"• Заблокированных: {user_analytics.blocked_messages}\n\n"

            text += f"📚 <b>Обучение:</b>\n"
            text += f"• Учебных сессий: {user_analytics.learning_sessions}\n"
            text += f"• Средняя длительность: {user_analytics.average_session_duration:.1f} мин\n"
            text += f"• Предметы: {', '.join(user_analytics.subjects_covered)}\n\n"

            text += f"📈 <b>Индексы:</b>\n"
            text += f"• Вовлеченность: {user_analytics.engagement_score:.1%}\n"
            text += f"• Безопасность: {user_analytics.safety_score:.1%}\n\n"

            # Прогресс по предметам
            if user_analytics.learning_progress:
                text += f"🎯 <b>Прогресс по предметам:</b>\n"
                for subject, progress in user_analytics.learning_progress.items():
                    text += (
                        f"• {subject}: Уровень {progress['level']}, {progress['points']} очков\n"
                    )

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

            text = f"🔒 <b>Настройки безопасности</b>\n\n"

            if settings:
                text += f"📊 <b>Текущие настройки:</b>\n"
                text += f"• Дневной лимит сообщений: {settings.daily_message_limit}\n"
                text += f"• Уведомления о критических событиях: {'✅' if settings.alert_on_critical else '❌'}\n"
                text += f"• Уведомления о предупреждениях: {'✅' if settings.alert_on_warning else '❌'}\n"
                text += f"• Частота отчетов: {settings.report_frequency}\n\n"

                if settings.content_categories_blocked:
                    text += f"🚫 <b>Заблокированные категории:</b>\n"
                    for category in settings.content_categories_blocked:
                        text += f"• {category}\n"
                    text += "\n"
            else:
                text += "📝 Настройки безопасности не настроены.\n\n"

            # Получаем статистику активности ребенка
            activities = await parental_service.get_child_activities(child_id, limit=10)

            if activities:
                text += f"📋 <b>Последняя активность:</b>\n"
                for activity in activities[:5]:
                    text += f"• {activity.activity_type}: {activity.timestamp.strftime('%d.%m %H:%M')}\n"
                    if activity.alert_level != "INFO":
                        text += f"  ⚠️ Уровень: {activity.alert_level}\n"

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
        analytics_service = AnalyticsService(db)

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
                dashboard_data = await analytics_service.get_parent_dashboard(
                    parent_id=telegram_id, child_id=child.telegram_id, period=AnalyticsPeriod.WEEK
                )

                # Формируем отчет
                report_text = f"📊 <b>Еженедельный отчет</b>\n\n"
                report_text += f"👶 <b>Ребенок:</b> {child.first_name} ({child.age} лет)\n"
                report_text += f"📅 <b>Период:</b> {dashboard_data.period.value}\n\n"

                # Сводка активности
                activity = dashboard_data.activity_summary
                report_text += f"📱 <b>Активность:</b>\n"
                report_text += f"• Сообщений: {activity['total_interactions']}\n"
                report_text += f"• AI взаимодействий: {activity['ai_usage']}\n"
                report_text += f"• Уровень вовлеченности: {activity['engagement_level']}\n\n"

                # Сводка обучения
                learning = dashboard_data.learning_summary
                report_text += f"📚 <b>Обучение:</b>\n"
                report_text += f"• Учебных сессий: {learning['sessions_count']}\n"
                report_text += f"• Предметов изучено: {learning['subjects_covered']}\n"
                report_text += f"• Средняя длительность: {learning['average_duration']:.1f} мин\n\n"

                # Сводка безопасности
                safety = dashboard_data.safety_summary
                report_text += f"🛡️ <b>Безопасность:</b>\n"
                report_text += f"• Заблокированных сообщений: {safety['blocked_messages']}\n"
                report_text += f"• Уровень безопасности: {safety['safety_level']}\n\n"

                # Рекомендации
                if dashboard_data.recommendations:
                    report_text += f"💡 <b>Рекомендации:</b>\n"
                    for i, rec in enumerate(dashboard_data.recommendations, 1):
                        report_text += f"{i}. {rec}\n"

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
