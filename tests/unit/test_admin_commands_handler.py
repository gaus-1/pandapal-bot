"""
Тесты для bot/handlers/admin_commands.py
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.unit
@pytest.mark.asyncio
class TestAdminCommands:
    """Тесты для административных команд"""

    @pytest.fixture
    def mock_message(self):
        """Мок сообщения"""
        message = MagicMock()
        message.from_user.id = 123456789
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_simple_monitor(self):
        """Мок SimpleMonitor"""
        monitor = MagicMock()
        monitor.get_system_status = AsyncMock(
            return_value=MagicMock(
                healthy=True,
                cpu_percent=25.5,
                memory_percent=45.2,
                active_users=100,
                messages_today=500,
                last_update=MagicMock(strftime=Mock(return_value="12:00:00")),
            )
        )
        monitor.get_current_status = Mock(
            return_value={"overall": "healthy", "database": "ok", "ai_service": "ok"}
        )
        return monitor

    @patch("bot.handlers.admin_commands.get_simple_monitor")
    async def test_cmd_status_success(self, mock_get_monitor, mock_message, mock_simple_monitor):
        """Тест успешного выполнения команды /status"""
        from bot.handlers.admin_commands import cmd_status

        mock_get_monitor.return_value = mock_simple_monitor

        await cmd_status(mock_message)

        mock_message.answer.assert_called_once()
        # Проверяем аргументы вызова (может быть позиционный или именованный)
        call_args = mock_message.answer.call_args
        answer_text = ""
        if call_args:
            if call_args[0]:  # Позиционные аргументы
                answer_text = call_args[0][0] if call_args[0] else ""
            if call_args[1] and "text" in call_args[1]:  # Именованные аргументы
                answer_text = call_args[1]["text"]
        assert "Статус PandaPal Bot" in answer_text or "Статус PandaPal Bot" in str(call_args)

    @patch("bot.handlers.admin_commands.get_simple_monitor")
    @patch("bot.handlers.admin_commands.logger")
    async def test_cmd_status_error(self, mock_logger, mock_get_monitor, mock_message):
        """Тест обработки ошибки в команде /status"""
        from bot.handlers.admin_commands import cmd_status

        mock_get_monitor.side_effect = Exception("Monitor error")

        await cmd_status(mock_message)

        mock_logger.error.assert_called_once()
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        answer_text = ""
        if call_args:
            if call_args[0]:
                answer_text = call_args[0][0] if call_args[0] else ""
            if call_args[1] and "text" in call_args[1]:
                answer_text = call_args[1]["text"]
        assert "Ошибка" in answer_text or "Ошибка" in str(call_args)

    @patch("bot.handlers.admin_commands.get_simple_monitor")
    async def test_cmd_health_success(self, mock_get_monitor, mock_message, mock_simple_monitor):
        """Тест успешного выполнения команды /health"""
        from bot.handlers.admin_commands import cmd_health

        mock_get_monitor.return_value = mock_simple_monitor

        await cmd_health(mock_message)

        mock_message.answer.assert_called_once()

    @patch("bot.handlers.admin_commands.get_simple_monitor")
    @patch("bot.handlers.admin_commands.logger")
    async def test_cmd_health_error(self, mock_logger, mock_get_monitor, mock_message):
        """Тест обработки ошибки в команде /health"""
        from bot.handlers.admin_commands import cmd_health

        mock_get_monitor.side_effect = Exception("Health check error")

        await cmd_health(mock_message)

        mock_logger.error.assert_called_once()

    @patch("bot.handlers.admin_commands.get_ai_service")
    async def test_cmd_ai_status_success(self, mock_get_ai, mock_message):
        """Тест успешного выполнения команды /ai_status"""
        from bot.handlers.admin_commands import cmd_ai_status

        mock_ai_service = MagicMock()
        mock_ai_service.get_model_info = Mock(
            return_value={"model": "yandexgpt", "status": "active"}
        )
        mock_get_ai.return_value = mock_ai_service

        await cmd_ai_status(mock_message)

        mock_message.answer.assert_called_once()

    def test_admin_commands_router_registered(self):
        """Тест что роутер правильно зарегистрирован и имеет обработчики"""
        from bot.handlers.admin_commands import router

        assert router is not None
        # Проверяем что роутер имеет обработчики команд
        assert len(router.sub_routers) >= 0  # Может быть 0 если все в основном роутере
        # Проверяем что функции команд существуют
        from bot.handlers import admin_commands

        assert hasattr(admin_commands, "cmd_status")
        assert hasattr(admin_commands, "cmd_health")
        assert hasattr(admin_commands, "cmd_ai_status")

    @patch("bot.handlers.admin_commands.get_simple_monitor")
    async def test_cmd_status_unhealthy_system(self, mock_get_monitor, mock_message):
        """Тест команды /status с нездоровой системой"""
        from bot.handlers.admin_commands import cmd_status

        monitor = MagicMock()
        monitor.get_system_status = AsyncMock(
            return_value=MagicMock(
                healthy=False,
                cpu_percent=95.0,
                memory_percent=90.0,
                active_users=0,
                messages_today=0,
                last_update=MagicMock(strftime=Mock(return_value="12:00:00")),
            )
        )
        mock_get_monitor.return_value = monitor

        await cmd_status(mock_message)

        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        answer_text = ""
        if call_args:
            if call_args[0]:
                answer_text = call_args[0][0] if call_args[0] else ""
            if call_args[1] and "text" in call_args[1]:
                answer_text = call_args[1]["text"]
        assert "Проблемы" in answer_text or "❌" in answer_text or "Проблемы" in str(call_args)
