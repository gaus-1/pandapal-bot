"""
Обработчики системы достижений и геймификации
Показ прогресса, наград и рейтинга
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.database import get_db
from bot.keyboards.achievements_kb import get_achievements_keyboard
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.services.user_service import UserService

router = Router(name="achievements")


@router.message(F.text == "🏆 Достижения")
async def show_achievements(message: Message, state: FSMContext):
    """
    Обработчик кнопки "🏆 Достижения"
    Показывает систему достижений пользователя
    """
    telegram_id = message.from_user.id
    
    logger.info(f"🏆 Пользователь {telegram_id} открыл достижения")
    
    with get_db() as db:
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(
                "❌ Пользователь не найден. Напиши /start для регистрации."
            )
            return
    
    # Временная заглушка с информацией о разработке
    achievements_text = f"""
🏆 <b>Система достижений</b>

👤 <b>{user.first_name}</b>
🎯 Уровень: 1
⭐ Опыт (XP): 0 / 100

<b>🎮 Доступные достижения:</b>

🌟 <b>Первый шаг</b> - 10 XP
   Отправь первое сообщение
   <i>✅ Получено!</i>

💬 <b>Болтун</b> - 50 XP
   Отправь 100 сообщений
   <i>Прогресс: 0/100</i>

❓ <b>Любознательный</b> - 100 XP
   Задай 50 вопросов
   <i>Прогресс: 0/50</i>

🔥 <b>Неделя подряд</b> - 200 XP
   Используй бота 7 дней подряд
   <i>Прогресс: 0/7</i>

🎓 <b>Отличник</b> - 150 XP
   Реши 20 задач правильно
   <i>Прогресс: 0/20</i>

📚 <b>Эрудит</b> - 300 XP
   Задавай вопросы по 5+ предметам
   <i>Прогресс: 0/5</i>

<b>🚧 Система достижений активно дорабатывается!</b>
<i>Скоро здесь будут настоящие награды и бейджи! 🎉</i>

💡 <b>Продолжай учиться и собирай достижения!</b>
"""
    
    await message.answer(
        text=achievements_text,
        reply_markup=get_achievements_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "achievements:my")
async def show_my_achievements(callback: CallbackQuery, state: FSMContext):
    """Показать полученные достижения"""
    await callback.message.edit_text(
        text="🏅 <b>Мои достижения</b>\n\n"
        "🌟 Первый шаг - ✅\n"
        "💬 Болтун - 🔒 (0/100)\n"
        "❓ Любознательный - 🔒 (0/50)\n\n"
        "<i>Продолжай общаться с PandaPal чтобы открыть новые достижения!</i>",
        reply_markup=get_achievements_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "achievements:available")
async def show_available_achievements(callback: CallbackQuery, state: FSMContext):
    """Показать доступные для получения достижения"""
    await callback.message.edit_text(
        text="🎯 <b>Доступные награды</b>\n\n"
        "Вот что ты можешь получить:\n\n"
        "💬 Болтун (40/100) - ещё 60 сообщений\n"
        "❓ Любознательный (0/50) - задай 50 вопросов\n"
        "🔥 Неделя подряд (0/7) - общайся 7 дней подряд\n"
        "🎓 Отличник (0/20) - реши 20 задач\n"
        "📚 Эрудит (0/5) - изучи 5 предметов\n\n"
        "<i>Ближайшая награда: <b>Болтун</b> - еще 60 сообщений!</i>",
        reply_markup=get_achievements_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("💪 Ты близко к новой награде!")


@router.callback_query(F.data == "achievements:leaderboard")
async def show_leaderboard(callback: CallbackQuery, state: FSMContext):
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
        parse_mode="HTML"
    )
    await callback.answer()

