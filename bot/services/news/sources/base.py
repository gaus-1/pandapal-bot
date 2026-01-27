"""
Базовый класс для всех источников новостей.

Реализует общую логику: обработка ошибок, retry, таймауты.
"""

import asyncio
from abc import ABC
from typing import Any

import aiohttp
from loguru import logger

from bot.services.news.interfaces import INewsSource


class BaseNewsSource(INewsSource, ABC):
    """
    Базовый класс для всех источников новостей.

    Предоставляет общую функциональность:
    - HTTP клиент с таймаутами
    - Retry логика
    - Обработка ошибок
    """

    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        """
        Инициализация базового источника.

        Args:
            timeout: Таймаут запросов в секундах
            max_retries: Максимальное количество попыток при ошибке
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Создать или получить HTTP сессию."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session

    async def _fetch_with_retry(
        self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None
    ) -> dict | list:
        """
        Выполнить HTTP запрос с retry логикой.

        Args:
            url: URL для запроса
            params: Параметры запроса
            headers: HTTP заголовки

        Returns:
            dict | list: Ответ от API

        Raises:
            Exception: Если все попытки неудачны
        """
        session = await self._ensure_session()

        for attempt in range(self.max_retries):
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        # Rate limit - ждем и повторяем
                        wait_time = 2**attempt
                        logger.warning(
                            f"⚠️ Rate limit для {self.get_source_name()}, ждем {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        response.raise_for_status()
            except TimeoutError:
                logger.warning(
                    f"⚠️ Timeout для {self.get_source_name()} (попытка {attempt + 1}/{self.max_retries})"
                )
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Ошибка запроса к {self.get_source_name()}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)

        raise Exception(
            f"Не удалось получить данные от {self.get_source_name()} после {self.max_retries} попыток"
        )

    async def close(self) -> None:
        """Закрыть HTTP сессию."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход."""
        _ = exc_type, exc_val, exc_tb
        await self.close()
