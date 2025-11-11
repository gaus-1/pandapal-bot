"""
Complete monitoring coverage tests
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.monitoring import log_user_activity, monitor_performance


class TestMonitoringComplete:

    @pytest.mark.unit
    def test_log_user_activity_success(self):
        with patch("bot.monitoring.logger") as mock_logger:
            log_user_activity(123, "test_action", True, "success")
            mock_logger.info.assert_called_once()

    @pytest.mark.unit
    def test_log_user_activity_failure(self):
        with patch("bot.monitoring.logger") as mock_logger:
            log_user_activity(123, "test_action", False, "error")
            assert mock_logger.warning.called or mock_logger.info.called

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitor_performance_decorator(self):
        @monitor_performance
        async def test_func(message, state=None):
            return "result"

        mock_message = Mock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123

        result = await test_func(mock_message)
        assert result == "result"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitor_performance_with_error(self):
        @monitor_performance
        async def failing_func(message, state=None):
            raise ValueError("Test error")

        mock_message = Mock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 123

        with pytest.raises(ValueError):
            await failing_func(mock_message)
