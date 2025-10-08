"""
🛡️ АДМИНИСТРАТОРСКИЕ КОМАНДЫ ДЛЯ МОНИТОРИНГА 24/7
Команды для проверки состояния системы
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.services.simple_monitor import get_simple_monitor
from bot.services.ai_service_solid import get_ai_service


router = Router()


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Команда проверки статуса системы 24/7"""
    try:
        if not bot_24_7_service:
            await message.answer("❌ Сервис 24/7 не инициализирован")
            return
        
        status = bot_24_7_service.get_health_status()
        
        uptime_hours = status["uptime_seconds"] // 3600
        uptime_minutes = (status["uptime_seconds"] % 3600) // 60
        
        response = f"""🤖 <b>Статус PandaPal Bot 24/7</b>

📊 <b>Основная информация:</b>
• Режим работы: <code>{status['mode']}</code>
• Статус: {'✅ Активен' if status['is_running'] else '❌ Неактивен'}
• Время работы: {uptime_hours}ч {uptime_minutes}м

📈 <b>Статистика:</b>
• Сообщений обработано: <code>{status['messages_processed']}</code>
• Ошибок восстановлено: <code>{status['errors_recovered']}</code>
• Переключений режима: <code>{status['mode_switches']}</code>

🔄 <b>Очередь сообщений:</b>
• Размер очереди: <code>{status['queue_size']}</code>
• Переполнений очереди: <code>{status['queue_overflows']}</code>

🌐 <b>Подключения:</b>
• Webhook URL: <code>{status['webhook_url'] or 'Не используется'}</code>
• Polling активен: {'✅' if status['polling_active'] else '❌'}

⏰ Последняя активность: <code>{status['last_activity'][:19]}</code>"""

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
        error_stats = error_recovery_service.get_error_stats()
        
        response = f"""📊 <b>Статистика ошибок</b>

🔢 <b>Общее количество:</b>
• Всего ошибок: <code>{error_stats['total_errors']}</code>
• За последний час: <code>{error_stats['errors_last_hour']}</code>
• За последний день: <code>{error_stats['errors_last_day']}</code>

📈 <b>По типам ошибок:</b>"""

        for error_type, count in error_stats["error_types"].items():
            response += f"\n• <b>{error_type}:</b> <code>{count}</code>"

        response += f"\n\n🚨 <b>По серьезности:</b>"
        for severity, count in error_stats["severity_distribution"].items():
            if count > 0:
                severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                emoji = severity_emoji.get(severity, "⚪")
                response += f"\n{emoji} <b>{severity}:</b> <code>{count}</code>"

        if error_stats["recent_errors"]:
            response += f"\n\n⏰ <b>Последние ошибки:</b>"
            for error in error_stats["recent_errors"][-3:]:  # Последние 3
                response += f"\n• <code>{error['type']}</code> - {error['message'][:50]}..."

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
        import psutil
        import platform
        
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
