"""
Глобальный middleware для обработки ошибок aiogram handlers.

Гарантирует, что пользователь всегда получит ответ, даже при сбое.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update
from loguru import logger

from bot.services.circuit_breaker import CircuitOpenError

# Стандартные ответы на ошибки
ERROR_MESSAGES = {
    "default": "Упс, что-то пошло не так. Попробуй ещё раз через пару секунд 🐼",
    "circuit_open": "Сервис временно перегружен. Попробуй через минуту 🐼",
    "timeout": "Ответ занял слишком много времени. Попробуй ещё раз 🐼",
}


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware: перехватывает необработанные исключения в handlers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except CircuitOpenError as e:
            logger.warning(f"⚡ Circuit Breaker в handler: {e}")
            await self._send_error_reply(event, ERROR_MESSAGES["circuit_open"])
        except TimeoutError:
            logger.error("❌ Timeout в handler")
            await self._send_error_reply(event, ERROR_MESSAGES["timeout"])
        except Exception as e:
            logger.error(f"❌ Необработанная ошибка в handler: {e}", exc_info=True)
            await self._send_error_reply(event, ERROR_MESSAGES["default"])

    @staticmethod
    async def _send_error_reply(event: TelegramObject, text: str) -> None:
        """Отправить сообщение об ошибке пользователю."""
        message = None

        if isinstance(event, Message):
            message = event
        elif isinstance(event, Update) and event.message:
            message = event.message

        if message:
            try:
                await message.answer(text)
            except Exception as reply_err:
                logger.error(f"❌ Не удалось отправить ошибку пользователю: {reply_err}")


def setup_error_handler(dp: Any) -> None:
    """
    Зарегистрировать error handler middleware на dispatcher.

    Args:
        dp: aiogram Dispatcher
    """
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    logger.info("✅ ErrorHandlerMiddleware зарегистрирован")
