"""
🤖 СИСТЕМА 24/7 РАБОТЫ TELEGRAM БОТА
Автоматическое восстановление webhook, fallback на polling, очередь сообщений
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import traceback

from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError, TelegramRetryAfter
from aiogram.types import Update, Message, CallbackQuery, InlineQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web, ClientSession
import aiohttp
from sqlalchemy.exc import OperationalError


class BotMode(Enum):
    """Режимы работы бота"""
    WEBHOOK = "webhook"
    POLLING = "polling"
    HYBRID = "hybrid"  # Webhook + fallback на polling


@dataclass
class QueuedMessage:
    """Сообщение в очереди"""
    update_id: int
    update_data: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 1  # 1 = высший приоритет, 5 = низший


@dataclass
class BotHealth:
    """Состояние здоровья бота"""
    mode: BotMode
    is_running: bool
    last_activity: datetime
    messages_processed: int = 0
    errors_count: int = 0
    webhook_url: Optional[str] = None
    polling_active: bool = False
    queue_size: int = 0


class Bot24_7Service:
    """🤖 Сервис 24/7 работы Telegram бота"""
    
    def __init__(self, bot: Bot, dispatcher: Dispatcher):
        self.bot = bot
        self.dispatcher = dispatcher
        self.current_mode = BotMode.WEBHOOK
        self.health = BotHealth(
            mode=self.current_mode,
            is_running=False,
            last_activity=datetime.now()
        )
        # Защита от дублирования обновлений
        self.processed_updates: set = set()
        
        # Очередь сообщений
        self.message_queue: List[QueuedMessage] = []
        self.queue_processor_task: Optional[asyncio.Task] = None
        
        # Мониторинг и восстановление
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.webhook_monitor_task: Optional[asyncio.Task] = None
        
        # Настройки
        self.webhook_url = None
        self.polling_fallback_enabled = True
        self.queue_processing_enabled = True
        self.max_queue_size = 1000
        
        # Статистика
        self.stats = {
            "messages_processed": 0,
            "errors_recovered": 0,
            "mode_switches": 0,
            "queue_overflows": 0,
            "uptime_start": datetime.now()
        }
    
    async def start_24_7_mode(self, webhook_url: Optional[str] = None):
        """Запуск режима 24/7 работы"""
        
        logger.info("🤖 Запуск режима 24/7 работы бота")
        
        self.webhook_url = webhook_url
        self.health.is_running = True
        
        try:
            # Определяем оптимальный режим работы
            if webhook_url and await self._test_webhook_setup():
                self.current_mode = BotMode.WEBHOOK
                await self._setup_webhook()
            elif self.polling_fallback_enabled:
                self.current_mode = BotMode.POLLING
                await self._start_polling()
            else:
                raise Exception("Не удалось настроить ни webhook, ни polling")
            
            # Запускаем фоновые задачи
            await self._start_background_tasks()
            
            self.health.mode = self.current_mode
            logger.success(f"✅ Бот запущен в режиме {self.current_mode.value}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            await self._emergency_fallback()
    
    async def _test_webhook_setup(self) -> bool:
        """Тестирование настройки webhook"""
        try:
            if not self.webhook_url:
                return False
            
            # Проверяем доступность webhook URL
            async with ClientSession() as session:
                async with session.get(self.webhook_url, timeout=10) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"⚠️ Webhook недоступен: {e}")
            return False
    
    async def _setup_webhook(self):
        """Настройка webhook"""
        try:
            logger.info("🔗 Настройка webhook...")
            
            # Удаляем старый webhook
            await self.bot.delete_webhook()
            await asyncio.sleep(1)
            
            # Устанавливаем новый webhook
            await self.bot.set_webhook(
                url=self.webhook_url,
                allowed_updates=["message", "callback_query", "inline_query", "chosen_inline_result"]
            )
            
            # Проверяем установку
            webhook_info = await self.bot.get_webhook_info()
            if webhook_info.url == self.webhook_url:
                logger.success("✅ Webhook успешно настроен")
                self.health.webhook_url = self.webhook_url
            else:
                raise Exception("Webhook не установлен корректно")
                
        except Exception as e:
            logger.error(f"❌ Ошибка настройки webhook: {e}")
            raise
    
    async def _start_polling(self):
        """Запуск polling"""
        try:
            logger.info("🔄 Запуск polling...")
            
            # Удаляем webhook перед polling
            await self.bot.delete_webhook()
            
            # Запускаем polling в фоновом режиме
            polling_task = asyncio.create_task(self._polling_loop())
            self.health.polling_active = True
            
            logger.success("✅ Polling запущен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска polling: {e}")
            raise
    
    async def _polling_loop(self):
        """Основной цикл polling"""
        while self.health.is_running and self.current_mode == BotMode.POLLING:
            try:
                # Получаем обновления
                updates = await self.bot.get_updates(
                    offset=-1,
                    limit=10,
                    timeout=30,
                    allowed_updates=["message", "callback_query", "inline_query"]
                )
                
                if updates:
                    for update in updates:
                        await self._process_update(update)
                        self.health.last_activity = datetime.now()
                
                # Короткая пауза между запросами
                await asyncio.sleep(1)
                
            except TelegramRetryAfter as e:
                logger.warning(f"⚠️ Rate limit, ждем {e.retry_after} секунд")
                await asyncio.sleep(e.retry_after)
                
            except (TelegramAPIError, TelegramNetworkError) as e:
                logger.error(f"❌ Ошибка polling: {e}")
                await self._handle_polling_error(e)
                
            except Exception as e:
                logger.error(f"❌ Неизвестная ошибка polling: {e}")
                await asyncio.sleep(5)
    
    async def _start_background_tasks(self):
        """Запуск фоновых задач"""
        
        # Мониторинг здоровья
        self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
        
        # Мониторинг webhook (если используется)
        if self.current_mode == BotMode.WEBHOOK:
            self.webhook_monitor_task = asyncio.create_task(self._webhook_monitor_loop())
        
        # Обработчик очереди сообщений
        if self.queue_processing_enabled:
            self.queue_processor_task = asyncio.create_task(self._queue_processor_loop())
        
        logger.info("🔄 Фоновые задачи запущены")
    
    async def _health_monitor_loop(self):
        """Мониторинг здоровья бота"""
        while self.health.is_running:
            try:
                await self._check_bot_health()
                await asyncio.sleep(30)  # Проверяем каждые 30 секунд
                
            except Exception as e:
                logger.error(f"❌ Ошибка мониторинга здоровья: {e}")
                await asyncio.sleep(10)
    
    async def _webhook_monitor_loop(self):
        """Мониторинг webhook"""
        while self.health.is_running and self.current_mode == BotMode.WEBHOOK:
            try:
                # Проверяем статус webhook
                webhook_info = await self.bot.get_webhook_info()
                
                if not webhook_info.url or webhook_info.url != self.webhook_url:
                    logger.warning("⚠️ Webhook потерян, восстанавливаем...")
                    await self._setup_webhook()
                
                # Проверяем последнюю активность
                if self.health.last_activity < datetime.now() - timedelta(minutes=5):
                    logger.warning("⚠️ Нет активности 5 минут, проверяем соединение...")
                    await self._test_bot_connection()
                
                await asyncio.sleep(60)  # Проверяем каждую минуту
                
            except Exception as e:
                logger.error(f"❌ Ошибка мониторинга webhook: {e}")
                await self._switch_to_polling()
                break
    
    async def _queue_processor_loop(self):
        """Обработка очереди сообщений"""
        while self.health.is_running:
            try:
                if self.message_queue:
                    # Обрабатываем сообщения по приоритету
                    self.message_queue.sort(key=lambda x: (x.priority, x.timestamp))
                    
                    message = self.message_queue.pop(0)
                    await self._process_queued_message(message)
                
                await asyncio.sleep(0.1)  # Частая проверка очереди
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки очереди: {e}")
                await asyncio.sleep(1)
    
    async def _check_bot_health(self):
        """Проверка здоровья бота"""
        try:
            # Проверяем подключение к Telegram
            me = await self.bot.get_me()
            if not me:
                raise Exception("Не удалось получить информацию о боте")
            
            # Обновляем статистику
            self.health.messages_processed = self.stats["messages_processed"]
            self.health.errors_count = self.stats["errors_recovered"]
            self.health.queue_size = len(self.message_queue)
            
            logger.debug(f"📊 Статистика бота: сообщений={self.stats['messages_processed']}, ошибок={self.stats['errors_recovered']}, очередь={len(self.message_queue)}")
            
        except Exception as e:
            logger.error(f"❌ Проблемы со здоровьем бота: {e}")
            await self._handle_health_issues()
    
    async def _process_update(self, update: Update):
        """Обработка обновления"""
        try:
            # Защита от дублирования - проверяем, не обрабатывали ли мы уже это обновление
            if update.update_id in self.processed_updates:
                logger.debug(f"Пропускаем дублирующее обновление {update.update_id}")
                return
            
            # Добавляем в список обработанных
            self.processed_updates.add(update.update_id)
            
            # Очищаем старые записи (оставляем только последние 1000)
            if len(self.processed_updates) > 1000:
                self.processed_updates = set(list(self.processed_updates)[-500:])
            
            # Если очередь переполнена, обрабатываем критичные сообщения напрямую
            if len(self.message_queue) >= self.max_queue_size:
                if self._is_critical_message(update):
                    await self._process_critical_message(update)
                else:
                    self.stats["queue_overflows"] += 1
                    logger.warning("⚠️ Очередь переполнена, сообщение отброшено")
                return
            
            # Добавляем в очередь для обработки
            queued_msg = QueuedMessage(
                update_id=update.update_id,
                update_data=update.model_dump(),
                timestamp=datetime.now(),
                priority=self._get_message_priority(update)
            )
            
            self.message_queue.append(queued_msg)
            self.stats["messages_processed"] += 1
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки обновления: {e}")
            self.stats["errors_recovered"] += 1
    
    async def _process_queued_message(self, message: QueuedMessage):
        """Обработка сообщения из очереди"""
        try:
            # Создаем объект Update из данных
            update = Update.model_validate(message.update_data)
            
            # Обрабатываем через dispatcher
            await self.dispatcher.feed_update(self.bot, update)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения из очереди: {e}")
            
            # Повторяем попытку если не превышен лимит
            if message.retry_count < message.max_retries:
                message.retry_count += 1
                message.timestamp = datetime.now()  # Обновляем время для повторной обработки
                self.message_queue.append(message)
            else:
                logger.error(f"💀 Сообщение {message.update_id} отброшено после {message.max_retries} попыток")
    
    def _is_critical_message(self, update: Update) -> bool:
        """Проверка критичности сообщения"""
        if update.message:
            text = update.message.text or ""
            # Критичные команды
            critical_commands = ["/start", "/help", "/emergency"]
            return any(cmd in text.lower() for cmd in critical_commands)
        return False
    
    def _get_message_priority(self, update: Update) -> int:
        """Определение приоритета сообщения"""
        if self._is_critical_message(update):
            return 1  # Высший приоритет
        
        if update.message:
            return 2  # Обычные сообщения
        
        if update.callback_query:
            return 3  # Callback запросы
        
        return 4  # Остальные обновления
    
    async def _process_critical_message(self, update: Update):
        """Обработка критичного сообщения напрямую"""
        try:
            await self.dispatcher.feed_update(self.bot, update)
        except Exception as e:
            logger.error(f"❌ Ошибка обработки критичного сообщения: {e}")
    
    async def _handle_polling_error(self, error: Exception):
        """Обработка ошибки polling"""
        if isinstance(error, TelegramNetworkError):
            logger.warning("⚠️ Сетевая ошибка, переключаемся на webhook")
            await self._switch_to_webhook()
        else:
            logger.error(f"❌ Ошибка polling: {error}")
            await asyncio.sleep(10)  # Пауза перед повторной попыткой
    
    async def _switch_to_polling(self):
        """Переключение на polling"""
        if self.current_mode == BotMode.POLLING:
            return
        
        logger.info("🔄 Переключение на polling...")
        
        try:
            await self.bot.delete_webhook()
            self.current_mode = BotMode.POLLING
            self.health.mode = self.current_mode
            self.stats["mode_switches"] += 1
            
            # Перезапускаем polling
            await self._start_polling()
            
            logger.success("✅ Переключение на polling завершено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка переключения на polling: {e}")
    
    async def _switch_to_webhook(self):
        """Переключение на webhook"""
        if not self.webhook_url or self.current_mode == BotMode.WEBHOOK:
            return
        
        logger.info("🔄 Переключение на webhook...")
        
        try:
            if await self._test_webhook_setup():
                await self._setup_webhook()
                self.current_mode = BotMode.WEBHOOK
                self.health.mode = self.current_mode
                self.stats["mode_switches"] += 1
                
                logger.success("✅ Переключение на webhook завершено")
            else:
                logger.warning("⚠️ Webhook недоступен, остаемся на polling")
                
        except Exception as e:
            logger.error(f"❌ Ошибка переключения на webhook: {e}")
    
    async def _test_bot_connection(self):
        """Тестирование подключения бота"""
        try:
            me = await self.bot.get_me()
            logger.debug(f"✅ Соединение с ботом OK: @{me.username}")
        except Exception as e:
            logger.error(f"❌ Проблемы с соединением бота: {e}")
            await self._handle_connection_issues()
    
    async def _handle_health_issues(self):
        """Обработка проблем со здоровьем"""
        logger.warning("⚠️ Обнаружены проблемы со здоровьем бота")
        
        # Переключаем режим работы
        if self.current_mode == BotMode.WEBHOOK:
            await self._switch_to_polling()
        else:
            await self._switch_to_webhook()
    
    async def _handle_connection_issues(self):
        """Обработка проблем с соединением"""
        logger.error("❌ Проблемы с соединением, активируем аварийный режим")
        await self._emergency_fallback()
    
    async def _emergency_fallback(self):
        """Аварийный fallback режим"""
        logger.critical("🚨 Активация аварийного режима")
        
        try:
            # Пытаемся перезапустить в режиме polling
            await self.bot.delete_webhook()
            await asyncio.sleep(5)
            
            self.current_mode = BotMode.POLLING
            self.health.mode = self.current_mode
            
            await self._start_polling()
            
            logger.success("✅ Аварийный режим активирован")
            
        except Exception as e:
            logger.critical(f"💀 Критическая ошибка, бот недоступен: {e}")
            self.health.is_running = False
    
    async def stop_24_7_mode(self):
        """Остановка режима 24/7"""
        logger.info("🛑 Остановка режима 24/7")
        
        self.health.is_running = False
        
        # Останавливаем фоновые задачи
        tasks = [
            self.health_monitor_task,
            self.webhook_monitor_task,
            self.queue_processor_task
        ]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Очищаем webhook
        try:
            await self.bot.delete_webhook()
        except Exception as e:
            logger.error(f"❌ Ошибка очистки webhook: {e}")
        
        logger.success("✅ Режим 24/7 остановлен")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья бота"""
        uptime = datetime.now() - self.stats["uptime_start"]
        
        return {
            "mode": self.health.mode.value,
            "is_running": self.health.is_running,
            "last_activity": self.health.last_activity.isoformat(),
            "messages_processed": self.stats["messages_processed"],
            "errors_recovered": self.stats["errors_recovered"],
            "mode_switches": self.stats["mode_switches"],
            "queue_size": len(self.message_queue),
            "queue_overflows": self.stats["queue_overflows"],
            "uptime_seconds": int(uptime.total_seconds()),
            "webhook_url": self.health.webhook_url,
            "polling_active": self.health.polling_active,
            "timestamp": datetime.now().isoformat()
        }
    
    async def force_health_check(self) -> bool:
        """Принудительная проверка здоровья"""
        try:
            await self._check_bot_health()
            return True
        except Exception as e:
            logger.error(f"❌ Принудительная проверка здоровья не удалась: {e}")
            return False


# Глобальный экземпляр сервиса 24/7
bot_24_7_service: Optional[Bot24_7Service] = None
