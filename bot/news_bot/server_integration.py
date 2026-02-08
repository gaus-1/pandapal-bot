"""
Интеграция новостного бота с веб-сервером PandaPal.

Функции, извлеченные из PandaPalBotServer для уменьшения размера web_server.py.
Каждая функция принимает server (экземпляр PandaPalBotServer) первым аргументом.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

from bot.config.news_bot_settings import news_bot_settings

if TYPE_CHECKING:
    from web_server import PandaPalBotServer


async def init_news_bot(server: PandaPalBotServer) -> None:
    """Инициализация новостного бота."""
    try:
        logger.info("📰 Инициализация новостного бота...")

        # Проверяем токен
        if not news_bot_settings.news_bot_token:
            logger.error("❌ NEWS_BOT_TOKEN не установлен, новостной бот отключен")
            server.news_bot_enabled = False
            return

        from aiogram import BaseMiddleware, Bot, Dispatcher
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from aiogram.types import CallbackQuery, Message

        # Создаем Bot для новостей
        server.news_bot = Bot(
            token=news_bot_settings.news_bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        # Создаем Dispatcher для новостного бота
        storage = await server._create_fsm_storage()
        server.news_dp = Dispatcher(storage=storage)

        # Middleware для логирования обновлений
        class NewsBotLoggingMiddleware(BaseMiddleware):
            """Middleware для логирования всех обновлений новостного бота."""

            async def __call__(self, handler, event, data):
                """Логирование обновлений."""
                update_type = type(event).__name__
                logger.info(f"📰 News bot update received: type={update_type}")

                if isinstance(event, Message):
                    user_id = event.from_user.id if event.from_user else "unknown"
                    text = event.text[:50] if event.text else "non-text"
                    logger.info(f"📰 News bot message: user={user_id}, text={text}")
                elif isinstance(event, CallbackQuery):
                    user_id = event.from_user.id if event.from_user else "unknown"
                    cb_data = event.data[:50] if event.data else "no-data"
                    logger.info(f"📰 News bot callback: user={user_id}, data={cb_data}")

                return await handler(event, data)

        # Регистрируем роутер новостного бота
        from bot.handlers.news_bot import router as news_bot_router

        # Логируем обработчики в роутере ДО включения
        logger.info(
            f"📰 News bot router handlers: "
            f"message={len(news_bot_router.message.handlers)}, "
            f"callback_query={len(news_bot_router.callback_query.handlers)}"
        )

        server.news_dp.include_router(news_bot_router)
        logger.info("✅ Роутер новостного бота зарегистрирован")

        # Добавляем middleware для логирования ПОСЛЕ регистрации роутера
        server.news_dp.message.middleware(NewsBotLoggingMiddleware())
        server.news_dp.callback_query.middleware(NewsBotLoggingMiddleware())

        # В aiogram 3.x обработчики остаются в роутере, не копируются в dispatcher
        logger.info(
            f"📰 News bot router handlers: "
            f"message={len(news_bot_router.message.handlers)}, "
            f"callback_query={len(news_bot_router.callback_query.handlers)}"
        )

        # Проверяем, что бот работает
        bot_info = await server.news_bot.get_me()
        logger.info(
            f"✅ Новостной бот инициализирован: @{bot_info.username} ({bot_info.first_name})"
        )
        logger.info(f"📋 Токен: {news_bot_settings.news_bot_token[:10]}...")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации новостного бота: {e}", exc_info=True)
        # Не прерываем запуск основного бота
        server.news_bot_enabled = False
        server.news_bot = None
        server.news_dp = None


async def setup_news_bot_webhook(server: PandaPalBotServer) -> str:
    """Настройка webhook для новостного бота."""
    try:
        if not server.news_bot:
            logger.error("❌ News bot не инициализирован, невозможно установить webhook")
            return ""

        # Используем тот же домен, что и основной бот
        webhook_domain = server.settings.webhook_domain
        webhook_url = f"https://{webhook_domain}/webhook/news"
        logger.info(f"🔗 Установка webhook новостного бота: {webhook_url}")
        logger.info(f"📋 Токен новостного бота: {news_bot_settings.news_bot_token[:10]}...")

        # Принудительно удаляем старый webhook перед установкой нового
        try:
            await server.news_bot.delete_webhook(drop_pending_updates=True)
            logger.info("🗑️ Старый webhook новостного бота удален")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка удаления старого webhook (может не существовать): {e}")

        # Небольшая задержка перед установкой нового webhook
        await asyncio.sleep(0.5)

        await server.news_bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "inline_query"],
        )

        webhook_info = await server.news_bot.get_webhook_info()
        logger.info(f"✅ Webhook новостного бота установлен: {webhook_info.url}")
        logger.info(
            f"📊 Webhook info: url={webhook_info.url}, "
            f"pending={webhook_info.pending_update_count}, "
            f"last_error={webhook_info.last_error_message}, "
            f"last_error_date={webhook_info.last_error_date}, "
            f"ip_address={webhook_info.ip_address}, "
            f"max_connections={webhook_info.max_connections}, "
            f"allowed_updates={webhook_info.allowed_updates}"
        )

        # Проверяем, что webhook действительно установлен
        if not webhook_info.url or webhook_info.url != webhook_url:
            logger.error(
                f"❌ КРИТИЧНО: Webhook новостного бота НЕ установлен правильно! "
                f"Ожидали: {webhook_url}, Получили: {webhook_info.url}"
            )
            raise RuntimeError(f"Webhook новостного бота не установлен: {webhook_info.url}")
        else:
            logger.info(f"✅ Webhook URL совпадает: {webhook_info.url}")

        # Проверяем ошибки
        if webhook_info.last_error_message:
            logger.error(
                f"❌ Ошибка webhook новостного бота: {webhook_info.last_error_message} "
                f"(дата: {webhook_info.last_error_date})"
            )
        else:
            logger.info("✅ Ошибок webhook нет")

        # Проверяем pending updates
        if webhook_info.pending_update_count > 0:
            logger.warning(
                f"⚠️ Есть {webhook_info.pending_update_count} ожидающих обновлений "
                f"для новостного бота"
            )
        else:
            logger.info("✅ Ожидающих обновлений нет")

        # Дополнительная диагностика
        if webhook_info.url != webhook_url:
            logger.error(
                f"❌ КРИТИЧНО: Webhook URL не совпадает! "
                f"Ожидали: {webhook_url}, Получили: {webhook_info.url}"
            )
        if webhook_info.last_error_message:
            logger.error(
                f"❌ Ошибка webhook новостного бота: {webhook_info.last_error_message} "
                f"(дата: {webhook_info.last_error_date})"
            )
        if webhook_info.pending_update_count > 0:
            logger.warning(
                f"⚠️ Есть {webhook_info.pending_update_count} ожидающих обновлений "
                f"для новостного бота"
            )

        return webhook_url

    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook новостного бота: {e}", exc_info=True)
        raise


async def check_news_bot_webhook_periodically(server: PandaPalBotServer) -> None:
    """Периодическая проверка и переустановка webhook новостного бота."""
    await asyncio.sleep(10)  # Ждем 10 сек после старта для первой проверки

    # Первая проверка сразу после старта
    try:
        if server.news_bot_enabled and server.news_bot:
            webhook_info = await server.news_bot.get_webhook_info()
            expected_url = f"https://{server.settings.webhook_domain}/webhook/news"
            if not webhook_info.url or webhook_info.url != expected_url:
                logger.warning(
                    f"⚠️ Webhook новостного бота не установлен при старте! "
                    f"Ожидали: {expected_url}, Получили: {webhook_info.url or 'пусто'}"
                )
                logger.info("🔗 Устанавливаем webhook...")
                await setup_news_bot_webhook(server)
    except Exception as e:
        logger.error(f"❌ Ошибка проверки webhook при старте: {e}", exc_info=True)

    logger.info("🔄 Запущена периодическая проверка webhook новостного бота (каждые 2 минуты)")

    while True:
        try:
            await asyncio.sleep(120)  # Проверяем каждые 2 минуты

            if not server.news_bot_enabled or not server.news_bot:
                break

            webhook_info = await server.news_bot.get_webhook_info()
            expected_url = f"https://{server.settings.webhook_domain}/webhook/news"

            if not webhook_info.url or webhook_info.url != expected_url:
                logger.warning(
                    f"⚠️ Webhook новостного бота сброшен! "
                    f"Ожидали: {expected_url}, Получили: {webhook_info.url or 'пусто'}"
                )
                logger.info("🔗 Переустанавливаем webhook...")

                try:
                    await setup_news_bot_webhook(server)
                    webhook_info = await server.news_bot.get_webhook_info()
                    if webhook_info.url == expected_url:
                        logger.info("✅ Webhook новостного бота успешно переустановлен")
                    else:
                        logger.error(f"❌ Не удалось переустановить webhook: {webhook_info.url}")
                except Exception as e:
                    logger.error(f"❌ Ошибка переустановки webhook: {e}", exc_info=True)
            else:
                logger.debug(f"✅ Webhook новостного бота в порядке: {webhook_info.url}")

        except asyncio.CancelledError:
            logger.info("🛑 Периодическая проверка webhook остановлена")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка проверки webhook: {e}", exc_info=True)
            await asyncio.sleep(60)  # При ошибке ждем минуту перед следующей попыткой


async def check_and_collect_news_on_startup(server: PandaPalBotServer) -> None:
    """При старте всегда запускаем сбор, чтобы бот был с новостями."""
    try:
        await asyncio.sleep(2)  # Короткая пауза для инициализации БД

        from bot.database import get_db
        from bot.services.news.repository import NewsRepository

        with get_db() as db:
            repo = NewsRepository(db)
            news_count = repo.count_all()

        if news_count < 50:
            logger.info(f"📰 В БД {news_count} новостей, запускаю сбор при старте...")
            await collect_news_now(server)
        else:
            logger.info(f"📰 В БД уже {news_count} новостей, дозаполняю при старте для свежести")
            await collect_news_now(server)
    except Exception as e:
        logger.error(f"❌ Ошибка проверки новостей при старте: {e}", exc_info=True)


async def news_collection_loop(server: PandaPalBotServer) -> None:
    """Фоновая задача: первый сбор через 5 мин, далее каждые 15 мин."""
    first_run = True
    while True:
        try:
            if first_run:
                logger.info("📰 Первый периодический сбор новостей через 5 мин")
                await asyncio.sleep(300)  # 5 мин до первого сбора
                first_run = False
            else:
                logger.info("📰 Следующий сбор новостей через 15 мин")
                await asyncio.sleep(900)  # 15 мин

            await collect_news_now(server)

        except asyncio.CancelledError:
            logger.info("🛑 Автоматический сбор новостей остановлен")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле сбора новостей: {e}", exc_info=True)
            await asyncio.sleep(900)


async def collect_news_now(server: PandaPalBotServer) -> None:
    """Выполнить сбор новостей прямо сейчас."""
    if not server.news_collection_enabled:
        return

    try:
        logger.info("📰 Начинаю сбор новостей...")
        from bot.services.news.sources.humor_site_source import HumorSiteSource
        from bot.services.news.sources.joke_api_source import JokeAPISource
        from bot.services.news.sources.lenta_ru_source import LentaRuSource
        from bot.services.news.sources.local_humor_source import LocalHumorSource
        from bot.services.news.sources.newsapi_source import NewsAPISource
        from bot.services.news.sources.rbc_rss_source import RbcRssSource
        from bot.services.news.sources.web_scraper_source import WebScraperNewsSource
        from bot.services.news.sources.world_news_api_source import WorldNewsAPISource
        from bot.services.news_collector_service import NewsCollectorService

        # Lenta первым — больше новостей с Lenta.ru в ленте
        sources = [
            RbcRssSource(),
            LentaRuSource(),
            WorldNewsAPISource(),
            NewsAPISource(),
            WebScraperNewsSource(),
            HumorSiteSource(),
            JokeAPISource(),
            LocalHumorSource(),
        ]

        collector = NewsCollectorService(sources=sources)
        total_collected = await collector.collect_news(limit_per_source=15)
        await collector.close()

        logger.info(f"✅ Сбор новостей завершен: собрано {total_collected} новостей")
    except Exception as e:
        logger.error(f"❌ Ошибка сбора новостей: {e}", exc_info=True)
