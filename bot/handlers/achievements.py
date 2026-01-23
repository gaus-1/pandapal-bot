"""
Обработчики системы достижений и геймификации PandaPal.

Этот модуль реализует функциональность системы достижений для мотивации
пользователей к активному обучению. Включает в себя просмотр прогресса,
наград и участие в образовательных челленджах.

Основные возможности:
- Просмотр личных достижений и прогресса
- Система очков опыта (XP) и уровней
- Образовательные челленджи и квесты
- Рейтинг пользователей
- Награды за активность и успехи в обучении

Текущий статус:
- UI компоненты готовы
- Базовая структура данных реализована
- Логика достижений в разработке
- Интеграция с AI сервисами планируется

Все достижения привязаны к образовательной активности
и направлены на мотивацию к обучению.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.database import get_db
from bot.keyboards.achievements_kb import get_achievements_keyboard
from bot.services.user_service import UserService

router = Router(name="achievements")


@router.message(F.text == "🏆 Достижения")
async def show_achievements(message: Message, state: FSMContext):  # noqa: ARG001
    """
    Обработчик кнопки "🏆 Достижения"
    Показывает систему достижений пользователя с реальными данными
    """
    telegram_id = message.from_user.id

    logger.info(f"🏆 Пользователь {telegram_id} открыл достижения")

    with get_db() as db:
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(telegram_id)

        if not user:
            await message.answer("❌ Пользователь не найден. Напиши /start для регистрации.")
            return

        # Получаем реальные данные о прогрессе
        from bot.services.gamification_service import GamificationService

        gamification_service = GamificationService(db)
        progress_summary = gamification_service.get_user_progress_summary(telegram_id)
        achievements = gamification_service.get_achievements_with_progress(telegram_id)

    # Формируем текст с реальными данными
    achievements_text = f"""🏆 <b>Система достижений</b>

👤 <b>{user.first_name}</b>
🎯 Уровень: {progress_summary['level']}
⭐ Опыт (XP): {progress_summary['xp']} / {progress_summary['xp'] + progress_summary['xp_for_next_level']}
📊 Достижений: {progress_summary['achievements_unlocked']}/{progress_summary['achievements_total']}

<b>🎮 Доступные достижения:</b>
"""

    # Показываем первые 6 достижений
    for achievement in achievements[:6]:
        status = "✅" if achievement["unlocked"] else "🔒"
        progress_text = (
            "✅ Получено!"
            if achievement["unlocked"]
            else f"Прогресс: {achievement['progress']}/{achievement['progress_max']}"
        )

        achievements_text += f"""
{achievement['icon']} <b>{achievement['title']}</b> - {achievement['xp_reward']} XP
   {achievement['description']}
   <i>{status} {progress_text}</i>
"""

    if len(achievements) > 6:
        achievements_text += f"\n<i>... и еще {len(achievements) - 6} достижений</i>\n"

    achievements_text += "\n💡 <b>Продолжай учиться и собирай достижения!</b>"

    await message.answer(
        text=achievements_text, reply_markup=get_achievements_keyboard(), parse_mode="HTML"
    )


@router.callback_query(F.data == "achievements:my")
async def show_my_achievements(callback: CallbackQuery, state: FSMContext):  # noqa: ARG001
    """Показать полученные достижения с реальными данными"""
    telegram_id = callback.from_user.id

    with get_db() as db:
        from bot.services.gamification_service import GamificationService

        gamification_service = GamificationService(db)
        achievements = gamification_service.get_achievements_with_progress(telegram_id)

    # Фильтруем только разблокированные
    unlocked = [a for a in achievements if a["unlocked"]]

    if not unlocked:
        text = "🏅 <b>Мои достижения</b>\n\n"
        text += (
            "<i>У тебя пока нет достижений. Продолжай общаться с PandaPal чтобы открыть новые!</i>"
        )
    else:
        text = f"🏅 <b>Мои достижения</b> ({len(unlocked)}/{len(achievements)})\n\n"
        for achievement in unlocked:
            unlock_date = achievement.get("unlock_date")
            date_str = ""
            if unlock_date:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(unlock_date.replace("Z", "+00:00"))
                    date_str = f" ({dt.strftime('%d.%m.%Y')})"
                except Exception as e:
                    logger.debug("Ошибка парсинга даты достижения: %s", e)
                    date_str = ""

            text += f"{achievement['icon']} <b>{achievement['title']}</b>{date_str}\n"
            text += f"   {achievement['description']}\n"
            text += f"   +{achievement['xp_reward']} XP\n\n"

    await callback.message.edit_text(
        text=text,
        reply_markup=get_achievements_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "achievements:available")
async def show_available_achievements(callback: CallbackQuery, state: FSMContext):  # noqa: ARG001
    """Показать доступные для получения достижения с реальными данными"""
    telegram_id = callback.from_user.id

    with get_db() as db:
        from bot.services.gamification_service import GamificationService

        gamification_service = GamificationService(db)
        achievements = gamification_service.get_achievements_with_progress(telegram_id)

    # Фильтруем только неразблокированные
    available = [a for a in achievements if not a["unlocked"]]

    if not available:
        text = "🎯 <b>Доступные награды</b>\n\n"
        text += "🎉 <b>Поздравляю! Ты получил все достижения!</b>"
    else:
        text = "🎯 <b>Доступные награды</b>\n\n"
        text += "Вот что ты можешь получить:\n\n"

        # Сортируем по прогрессу (ближайшие к разблокировке первыми)
        available.sort(
            key=lambda x: x["progress"] / x["progress_max"] if x["progress_max"] > 0 else 0,
            reverse=True,
        )

        for achievement in available[:5]:
            progress_pct = (
                int((achievement["progress"] / achievement["progress_max"]) * 100)
                if achievement["progress_max"] > 0
                else 0
            )
            remaining = achievement["progress_max"] - achievement["progress"]
            text += f"{achievement['icon']} <b>{achievement['title']}</b>\n"
            text += (
                f"   {achievement['progress']}/{achievement['progress_max']} ({progress_pct}%)\n"
            )
            if remaining > 0:
                text += f"   Осталось: {remaining}\n"
            text += f"   +{achievement['xp_reward']} XP\n\n"

        if len(available) > 5:
            text += f"<i>... и еще {len(available) - 5} достижений</i>\n\n"

        # Находим ближайшее достижение
        closest = available[0] if available else None
        if closest:
            remaining = closest["progress_max"] - closest["progress"]
            text += f"<i>Ближайшая награда: <b>{closest['title']}</b> - еще {remaining}!</i>"

    await callback.message.edit_text(
        text=text,
        reply_markup=get_achievements_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer(
        "💪 Ты близко к новой награде!" if available else "🎉 Все достижения получены!"
    )


@router.callback_query(F.data == "achievements:leaderboard")
async def show_leaderboard(callback: CallbackQuery, state: FSMContext):  # noqa: ARG001
    """Показать рейтинг пользователей"""
    await callback.message.edit_text(
        text="📈 <b>Рейтинг учеников</b>\n\n"
        "🥇 Алиса - Level 5 (1250 XP)\n"
        "🥈 Максим - Level 4 (980 XP)\n"
        "🥉 София - Level 4 (850 XP)\n"
        "4️⃣ Иван - Level 3 (620 XP)\n"
        "5️⃣ Катя - Level 3 (540 XP)\n\n"
        "...\n\n"
        "🎯 Твоё место: 127 (0 XP)\n\n"
        "<i>Общайся с PandaPal чтобы подняться в рейтинге!</i>",
        reply_markup=get_achievements_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()
