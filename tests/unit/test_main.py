"""
Тесты для bot/main.py - точки входа бота (CI/CD проверка инициализации)

Продакшен использует web_server.py; main.py — только CI,
поэтому тесты проверяют: init_database, логирование, sys.exit при ошибке.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.unit
class TestMainModule:
    """Тесты для модуля main.py"""

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database", new_callable=AsyncMock)
    async def test_main_function_success(self, mock_init_db, mock_logger):
        """Тест успешного запуска main (CI-режим): init_database + логи"""
        from bot.main import main

        mock_init_db.return_value = None

        await main()

        mock_init_db.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database", new_callable=AsyncMock)
    async def test_main_function_database_error(self, mock_init_db, mock_logger):
        """Тест обработки ошибки при инициализации БД"""
        from bot.main import main

        mock_init_db.side_effect = Exception("Database connection failed")

        with pytest.raises(SystemExit):
            await main()

        mock_logger.error.assert_called()

    def test_main_module_structure(self):
        """Тест структуры модуля main - проверяем что все необходимое импортируется"""
        import bot.main

        assert hasattr(bot.main, "main")
        assert asyncio.iscoroutinefunction(bot.main.main)
        assert hasattr(bot.main, "logger")
        assert hasattr(bot.main, "init_database")

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database", new_callable=AsyncMock)
    async def test_main_logs_correct_messages(self, mock_init_db, mock_logger):
        """Тест что main логирует правильные сообщения при запуске"""
        mock_init_db.return_value = None

        from bot.main import main

        await main()

        assert mock_logger.info.called
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("PandaPal" in str(call) for call in log_calls)
