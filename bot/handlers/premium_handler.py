"""
Обработчики Premium подписки в Telegram боте.

Показывает статус Premium подписки, информацию о сохраненной карте
и позволяет отвязать карту прямо из бота.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from loguru import logger

from bot.config import settings
from bot.database import get_db
from bot.services import SubscriptionService, UserService

router = Router(name="premium")


@router.message(Command("premium"))
async def cmd_premium(message: Message):
    """
    Обработчик команды /premium
    Показывает статус Premium подписки и информацию о сохраненной карте
    """
    telegram_id = message.from_user.id

    logger.info(f"💎 Пользователь {telegram_id} запросил информацию о Premium")

    with get_db() as db:
        user_service = UserService(db)
        subscription_service = SubscriptionService(db)

        user = user_service.get_user_by_telegram_id(telegram_id)

        if not user:
            await message.answer("❌ Пользователь не найден. Напиши /start для регистрации.")
            return

        # Проверяем активную подписку
        subscription = subscription_service.get_active_subscription(telegram_id)

        if not subscription or not subscription.is_active:
            # Нет активной подписки
            premium_text = """
💎 <b>Premium подписка PandaPal</b>

❌ <b>У тебя нет активной Premium подписки</b>

✨ <b>Что ты получишь с Premium:</b>
• Неограниченные вопросы к AI панде
• Помощь по всем школьным предметам
• Игры без ограничений
• Приоритетная поддержка
• Эксклюзивные достижения

🚀 <b>Открой Mini App</b> чтобы оформить подписку!
"""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🚀 Открыть Premium",
                            web_app=WebAppInfo(url=f"{settings.frontend_url}#premium"),
                        )
                    ],
                ]
            )
        else:
            # Есть активная подписка
            from datetime import UTC, datetime

            now = datetime.now(UTC)
            days_left = (subscription.expires_at - now).days

            plan_names = {
                "week": "Неделя",
                "month": "Месяц",
                "year": "Год",
            }
            plan_name = plan_names.get(subscription.plan_id, subscription.plan_id)

            premium_text = f"""
💎 <b>Premium подписка PandaPal</b>

✅ <b>У тебя активная Premium подписка!</b>

📅 <b>Информация о подписке:</b>
• План: {plan_name}
• Действует до: {subscription.expires_at.strftime('%d.%m.%Y %H:%M')}
• Осталось дней: {days_left}
"""

            # Проверяем наличие сохраненной карты
            has_saved_card = bool(subscription.saved_payment_method_id)
            auto_renew = subscription.auto_renew

            if has_saved_card:
                premium_text += f"""
💳 <b>Сохраненная карта:</b>
• Автоплатеж: {'✅ Включен' if auto_renew else '❌ Отключен'}
• Карта сохранена для автоматического продления
"""
                # Добавляем кнопку отвязки карты
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔓 Отвязать карту",
                                callback_data="premium:remove_card",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🚀 Открыть Premium",
                                web_app=WebAppInfo(url=f"{settings.frontend_url}#premium"),
                            )
                        ],
                    ]
                )
            else:
                premium_text += """
💳 <b>Сохраненная карта:</b>
• Карта не сохранена
• Автоплатеж недоступен
"""
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🚀 Открыть Premium",
                                web_app=WebAppInfo(url=f"{settings.frontend_url}#premium"),
                            )
                        ],
                    ]
                )

    await message.answer(
        text=premium_text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "premium:remove_card")
async def remove_card_callback(callback: CallbackQuery):
    """
    Обработчик кнопки "Отвязать карту"
    Показывает подтверждение и отвязывает карту
    """
    telegram_id = callback.from_user.id

    logger.info(f"💳 Пользователь {telegram_id} запросил отвязку карты")

    with get_db() as db:
        subscription_service = SubscriptionService(db)

        # Проверяем наличие сохраненной карты
        subscription = subscription_service.get_active_subscription(telegram_id)

        if not subscription or not subscription.saved_payment_method_id:
            await callback.answer("❌ У тебя нет сохраненной карты", show_alert=True)
            await callback.message.delete()
            return

        # Показываем подтверждение
        confirm_text = """
⚠️ <b>Подтверждение отвязки карты</b>

Ты уверен, что хочешь отвязать карту?

После отвязки:
• Автоплатеж будет отключен
• Подписка не продлится автоматически
• Ты сможешь привязать карту заново при следующей оплате

Карта будет удалена из нашей системы.
"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Да, отвязать",
                        callback_data="premium:confirm_remove_card",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="premium:cancel_remove_card",
                    ),
                ],
            ]
        )

        await callback.message.edit_text(
            text=confirm_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        await callback.answer()


@router.callback_query(F.data == "premium:confirm_remove_card")
async def confirm_remove_card_callback(callback: CallbackQuery):
    """
    Обработчик подтверждения отвязки карты
    Отвязывает карту и обновляет сообщение
    """
    telegram_id = callback.from_user.id

    logger.info(f"💳 Пользователь {telegram_id} подтвердил отвязку карты")

    with get_db() as db:
        subscription_service = SubscriptionService(db)

        # Отвязываем карту
        removed = subscription_service.remove_saved_payment_method(telegram_id)

        if removed:
            db.commit()

            success_text = """
✅ <b>Карта успешно отвязана!</b>

💳 Сохраненная карта удалена из системы.
🔄 Автоплатеж отключен.

Твоя подписка продолжит действовать до окончания срока,
но автоматическое продление больше не будет происходить.

Ты можешь привязать карту заново при следующей оплате.
"""

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🚀 Открыть Premium",
                            web_app=WebAppInfo(url=f"{settings.frontend_url}#premium"),
                        )
                    ],
                ]
            )

            await callback.message.edit_text(
                text=success_text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            await callback.answer("✅ Карта отвязана", show_alert=True)

            logger.info(f"✅ Карта успешно отвязана для user={telegram_id}")
        else:
            await callback.answer("❌ Ошибка отвязки карты", show_alert=True)
            logger.error(f"❌ Ошибка отвязки карты для user={telegram_id}")


@router.callback_query(F.data == "premium:cancel_remove_card")
async def cancel_remove_card_callback(callback: CallbackQuery):
    """
    Обработчик отмены отвязки карты
    Возвращает к информации о Premium
    """
    telegram_id = callback.from_user.id

    logger.info(f"💳 Пользователь {telegram_id} отменил отвязку карты")

    # Возвращаемся к информации о Premium
    with get_db() as db:
        subscription_service = SubscriptionService(db)

        subscription = subscription_service.get_active_subscription(telegram_id)

        if subscription and subscription.is_active:
            from datetime import UTC, datetime

            now = datetime.now(UTC)
            days_left = (subscription.expires_at - now).days

            plan_names = {
                "week": "Неделя",
                "month": "Месяц",
                "year": "Год",
            }
            plan_name = plan_names.get(subscription.plan_id, subscription.plan_id)

            premium_text = f"""
💎 <b>Premium подписка PandaPal</b>

✅ <b>У тебя активная Premium подписка!</b>

📅 <b>Информация о подписке:</b>
• План: {plan_name}
• Действует до: {subscription.expires_at.strftime('%d.%m.%Y %H:%M')}
• Осталось дней: {days_left}
"""

            has_saved_card = bool(subscription.saved_payment_method_id)
            auto_renew = subscription.auto_renew

            if has_saved_card:
                premium_text += f"""
💳 <b>Сохраненная карта:</b>
• Автоплатеж: {'✅ Включен' if auto_renew else '❌ Отключен'}
• Карта сохранена для автоматического продления
"""
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔓 Отвязать карту",
                                callback_data="premium:remove_card",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🚀 Открыть Premium",
                                web_app=WebAppInfo(url=f"{settings.frontend_url}#premium"),
                            )
                        ],
                    ]
                )
            else:
                premium_text += """
💳 <b>Сохраненная карта:</b>
• Карта не сохранена
• Автоплатеж недоступен
"""
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🚀 Открыть Premium",
                                web_app=WebAppInfo(url=f"{settings.frontend_url}#premium"),
                            )
                        ],
                    ]
                )

            await callback.message.edit_text(
                text=premium_text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    await callback.answer("❌ Отменено")
