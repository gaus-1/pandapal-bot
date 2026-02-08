"""Middleware для aiogram."""

from bot.middleware.error_handler import ErrorHandlerMiddleware, setup_error_handler

__all__ = ["ErrorHandlerMiddleware", "setup_error_handler"]
