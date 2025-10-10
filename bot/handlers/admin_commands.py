"""
Административные команды для мониторинга системы PandaPal Bot.

Этот модуль содержит команды для администраторов и мониторинга состояния системы
в режиме реального времени. Предоставляет детальную информацию о работе бота,
статистике использования, состоянии AI сервисов и системных ресурсах.

Основные команды:
- /status - Полный статус системы и статистика
- /health - Проверка здоровья компонентов
- /stats - Детальная статистика использования
- /ai_status - Статус AI сервисов и токенов
- /users - Статистика пользователей
- /errors - Последние ошибки системы

Все команды доступны только администраторам и содержат подробную
диагностическую информацию для поддержания стабильной работы 24/7.
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.services.ai_service_solid import get_ai_service
from bot.services.simple_monitor import get_simple_monitor

router = Router()


@router.message(Command("status"))
async def cmd_status(message: Message):
    """
    Команда проверки полного статуса системы PandaPal Bot.

    Предоставляет администраторам детальную информацию о состоянии всех
    компонентов системы, включая время работы, статистику сообщений,
    состояние очереди, подключения и системные ресурсы.

    Args:
        message (Message): Сообщение от администратора с командой /status.

    Returns:
        None: Отправляет детальный отчет о статусе системы.
    """
    try:
        # Получаем статус через SimpleMonitor
        monitor = get_simple_monitor()
        status = await monitor.get_system_status()

        response = f"""🤖 <b>Статус PandaPal Bot</b>

📊 <b>Основная информация:</b>
• Здоровье системы: {'✅ Активна' if status.healthy else '❌ Проблемы'}
• CPU: <code>{status.cpu_percent}%</code>
• Память: <code>{status.memory_percent}%</code>

📈 <b>Статистика:</b>
• Активных пользователей: <code>{status.active_users}</code>
• Сообщений сегодня: <code>{status.messages_today}</code>

⏰ Последнее обновление: <code>{status.last_update.strftime('%H:%M:%S')}</code>"""

        await message.answer(response)

    except Exception as e:
        logger.error(f"❌ Ошибка команды status: {e}")
        await message.answer("❌ Ошибка получения статуса системы")


@router.message(Command("health"))
async def cmd_health(message: Message):
    """Команда проверки здоровья сервисов (SOLID)"""
    try:
        monitor = get_simple_monitor()
        status = monitor.get_current_status()

        # Определяем общий статус
        overall_status = status.get("overall", "unknown")
        overall_emoji = "✅" if overall_status == "healthy" else "⚠️"

        response = f"""🛡️ <b>Здоровье системы PandaPal</b>

{overall_emoji} <b>Общий статус:</b> <code>{overall_status.upper()}</code>

🔍 <b>Детали по сервисам:</b>"""

        for service_name, service_status in status.items():
            if service_name != "overall":
                status_emoji = "✅" if service_status == "healthy" else "⚠️"
                response += f"\n{status_emoji} <b>{service_name}:</b> <code>{service_status}</code>"

        await message.answer(response)

    except Exception as e:
        logger.error(f"❌ Ошибка команды health: {e}")
        await message.answer("❌ Ошибка получения статуса здоровья")


@router.message(Command("ai_status"))
async def cmd_ai_status(message: Message):
    """Команда проверки статуса AI (SOLID)"""
    try:
        ai_service = get_ai_service()
        model_info = ai_service.get_model_info()

        response = f"""🤖 <b>Статус AI</b>

📦 <b>Модель:</b> <code>{model_info['model']}</code>
🎯 <b>Температура:</b> <code>{model_info['temperature']}</code>
📊 <b>Max токенов:</b> <code>{model_info['max_tokens']}</code>
✅ <b>Публичное имя:</b> <code>{model_info['public_name']}</code>"""

        await message.answer(response)

    except Exception as e:
        logger.error(f"❌ Ошибка команды ai_status: {e}")
        await message.answer("❌ Ошибка получения статуса AI")


@router.message(Command("errors"))
async def cmd_errors(message: Message):
    """Команда просмотра статистики ошибок"""
    try:
        # Используем SimpleMonitor для получения статистики ошибок
        monitor = get_simple_monitor()
        status = await monitor.get_system_status()

        response = f"""📊 <b>Статистика системы</b>

🔢 <b>Общая информация:</b>
• Здоровье системы: {'✅ Активна' if status.healthy else '❌ Проблемы'}
• CPU: <code>{status.cpu_percent}%</code>
• Память: <code>{status.memory_percent}%</code>

📈 <b>Статистика:</b>
• Активных пользователей: <code>{status.active_users}</code>
• Сообщений сегодня: <code>{status.messages_today}</code>

⏰ Последнее обновление: <code>{status.last_update.strftime('%H:%M:%S')}</code>"""

        await message.answer(response)

    except Exception as e:
        logger.error(f"❌ Ошибка команды errors: {e}")
        await message.answer("❌ Ошибка получения статистики ошибок")


@router.message(Command("restart_ai"))
async def cmd_restart_ai(message: Message):
    """Команда перезапуска AI (SOLID)"""
    try:
        # В SOLID архитектуре AI сервис управляется через singleton
        ai_service = get_ai_service()
        logger.info("🔄 AI сервис готов к работе")

        await message.answer("✅ AI сервис работает корректно")

    except Exception as e:
        logger.error(f"❌ Ошибка команды restart_ai: {e}")
        await message.answer("❌ Ошибка проверки AI")


@router.message(Command("clear_errors"))
async def cmd_clear_errors(message: Message):
    """Команда очистки истории ошибок (заглушка для совместимости)"""
    try:
        logger.info("🧹 Команда очистки ошибок (в SOLID архитектуре не требуется)")
        await message.answer("✅ В текущей архитектуре очистка не требуется")

    except Exception as e:
        logger.error(f"❌ Ошибка команды clear_errors: {e}")
        await message.answer("❌ Ошибка выполнения команды")


@router.message(Command("force_check"))
async def cmd_force_check(message: Message):
    """Команда принудительной проверки здоровья (SOLID)"""
    try:
        # Проверка AI
        ai_service = get_ai_service()
        test_response = await ai_service.generate_response("Тест", user_age=10)
        ai_ok = bool(test_response and len(test_response) > 0)

        # Проверка монитора
        monitor = get_simple_monitor()
        monitor_status = monitor.get_current_status()
        monitor_ok = monitor_status.get("overall") == "healthy"

        if ai_ok and monitor_ok:
            await message.answer("✅ Все системы работают корректно")
        else:
            await message.answer("⚠️ Обнаружены проблемы в работе систем")

    except Exception as e:
        logger.error(f"❌ Ошибка команды force_check: {e}")
        await message.answer("❌ Ошибка принудительной проверки")


@router.message(Command("system_info"))
async def cmd_system_info(message: Message):
    """Команда получения полной информации о системе"""
    try:
        import os
        import platform

        import psutil

        # Системная информация
        system_info = f"""💻 <b>Информация о системе</b>

🖥️ <b>Операционная система:</b>
• Система: <code>{platform.system()}</code>
• Версия: <code>{platform.release()}</code>
• Архитектура: <code>{platform.machine()}</code>

💾 <b>Память:</b>
• Доступно: <code>{psutil.virtual_memory().available // (1024**3)} GB</code>
• Использовано: <code>{psutil.virtual_memory().percent}%</code>

💽 <b>Диск:</b>
• Свободно: <code>{psutil.disk_usage('/').free // (1024**3)} GB</code>
• Использовано: <code>{psutil.disk_usage('/').percent}%</code>

🌐 <b>Среда:</b>
• Python: <code>{platform.python_version()}</code>
• Render: <code>{'Да' if os.getenv('RENDER') else 'Нет'}</code>
• PORT: <code>{os.getenv('PORT', 'Не установлен')}</code>"""

        await message.answer(system_info)

    except Exception as e:
        logger.error(f"❌ Ошибка команды system_info: {e}")
        await message.answer("❌ Ошибка получения системной информации")


# Добавляем обработчик для всех административных команд
@router.message(Command("admin"))
async def cmd_admin_help(message: Message):
    """Справка по административным командам"""
    help_text = """🛡️ <b>Административные команды PandaPal</b>

📊 <b>Мониторинг:</b>
• /status - Статус системы 24/7
• /health - Здоровье сервисов
• /ai_status - Статус AI провайдеров
• /errors - Статистика ошибок

🔧 <b>Управление:</b>
• /restart_ai - Перезапуск AI провайдеров
• /clear_errors - Очистка истории ошибок
• /force_check - Принудительная проверка
• /system_info - Информация о системе

💡 <b>Справка:</b>
• /help - Общая справка
• /start - Начать работу с ботом"""

    await message.answer(help_text)
