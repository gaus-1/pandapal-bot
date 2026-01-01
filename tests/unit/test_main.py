"""
Тесты для bot/main.py - точки входа бота
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.unit
class TestMainModule:
    """Тесты для модуля main.py"""

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database")
    @patch("bot.main.settings")
    async def test_main_function_success(self, mock_settings, mock_init_db, mock_logger):
        """Тест успешного запуска main функции"""
        from bot.main import main

        mock_settings.environment = "test"
        mock_init_db.return_value = None

        # Мокаем uvicorn через sys.modules так как он импортируется внутри функции
        import sys

        mock_uvicorn = MagicMock()
        mock_uvicorn.run = AsyncMock()
        sys.modules["uvicorn"] = mock_uvicorn

        try:
            # Запускаем main с таймаутом
            try:
                await asyncio.wait_for(main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass  # Ожидаемо, так как uvicorn.run работает бесконечно
        finally:
            # Восстанавливаем
            if "uvicorn" in sys.modules and hasattr(sys.modules["uvicorn"], "__file__"):
                del sys.modules["uvicorn"]

        # Проверяем, что функции были вызваны
        mock_logger.info.assert_called()
        mock_init_db.assert_called_once()

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database")
    @patch("bot.main.settings")
    async def test_main_function_production_mode(self, mock_settings, mock_init_db, mock_logger):
        """Тест запуска main в production режиме"""
        from bot.main import main

        mock_settings.environment = "production"
        mock_init_db.return_value = None

        # Запускаем main с таймаутом
        try:
            await asyncio.wait_for(main(), timeout=0.1)
        except asyncio.TimeoutError:
            pass  # Ожидаемо

        mock_logger.info.assert_called()
        mock_init_db.assert_called_once()

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database")
    @patch("bot.main.settings")
    async def test_main_function_database_error(self, mock_settings, mock_init_db, mock_logger):
        """Тест обработки ошибки при инициализации БД"""
        from bot.main import main

        mock_settings.environment = "test"
        mock_init_db.side_effect = Exception("Database connection failed")

        with pytest.raises(SystemExit):
            await main()

        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database")
    @patch("bot.main.settings")
    @patch("bot.main.os.getenv")
    async def test_main_test_server_config(
        self, mock_getenv, mock_settings, mock_init_db, mock_logger
    ):
        """Тест конфигурации тестового сервера"""
        from bot.main import main

        mock_settings.environment = "test"
        mock_init_db.return_value = None
        mock_getenv.side_effect = lambda key, default=None: {
            "TEST_SERVER_HOST": "0.0.0.0",
            "TEST_SERVER_PORT": "9000",
        }.get(key, default)

        # Мокаем uvicorn через sys.modules так как он импортируется внутри функции
        import sys

        original_uvicorn = sys.modules.get("uvicorn")
        mock_uvicorn_module = MagicMock()
        mock_uvicorn_module.run = AsyncMock()
        sys.modules["uvicorn"] = mock_uvicorn_module

        try:
            try:
                await asyncio.wait_for(main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
        finally:
            if original_uvicorn:
                sys.modules["uvicorn"] = original_uvicorn
            elif "uvicorn" in sys.modules:
                del sys.modules["uvicorn"]

        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database")
    @patch("bot.main.settings")
    async def test_main_fastapi_app_creation(self, mock_settings, mock_init_db, mock_logger):
        """Тест создания FastAPI приложения в тестовом режиме"""
        from bot.main import main

        mock_settings.environment = "test"
        mock_init_db.return_value = None

        # Мокаем FastAPI и uvicorn через sys.modules
        import sys

        original_fastapi = sys.modules.get("fastapi")
        original_uvicorn = sys.modules.get("uvicorn")

        mock_fastapi_module = MagicMock()
        mock_fastapi_module.FastAPI = MagicMock(return_value=MagicMock())
        sys.modules["fastapi"] = mock_fastapi_module

        mock_uvicorn_module = MagicMock()
        mock_uvicorn_module.run = AsyncMock()
        sys.modules["uvicorn"] = mock_uvicorn_module

        try:
            try:
                await asyncio.wait_for(main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
        finally:
            if original_fastapi:
                sys.modules["fastapi"] = original_fastapi
            elif "fastapi" in sys.modules:
                del sys.modules["fastapi"]
            if original_uvicorn:
                sys.modules["uvicorn"] = original_uvicorn
            elif "uvicorn" in sys.modules:
                del sys.modules["uvicorn"]

        # Проверяем что логирование было вызвано
        assert mock_logger.info.called

    def test_main_module_structure(self):
        """Тест структуры модуля main - проверяем что все необходимое импортируется"""
        import bot.main

        assert hasattr(bot.main, "main")
        assert asyncio.iscoroutinefunction(bot.main.main)
        assert hasattr(bot.main, "logger")
        assert hasattr(bot.main, "init_database")

    @pytest.mark.asyncio
    @patch("bot.main.logger")
    @patch("bot.main.init_database")
    @patch("bot.main.settings")
    async def test_main_logs_correct_messages(self, mock_settings, mock_init_db, mock_logger):
        """Тест что main логирует правильные сообщения при запуске"""
        from bot.main import main

        mock_settings.environment = "test"
        mock_init_db.return_value = None

        import sys

        mock_uvicorn = MagicMock()
        mock_uvicorn.run = AsyncMock()
        sys.modules["uvicorn"] = mock_uvicorn

        try:
            try:
                await asyncio.wait_for(main(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
        finally:
            if "uvicorn" in sys.modules and hasattr(sys.modules["uvicorn"], "__file__"):
                del sys.modules["uvicorn"]

        # Проверяем, что логирование было вызвано с правильными сообщениями
        assert mock_logger.info.called
        # Проверяем что логируется запуск бота
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("PandaPal" in str(call) for call in log_calls)
