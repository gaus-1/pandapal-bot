"""
Bot initialization and main module tests
"""

import pytest
from unittest.mock import Mock, patch
import bot
from bot import __init__ as bot_init


class TestBotInit:

    @pytest.mark.unit
    def test_bot_module_exists(self):
        assert bot is not None

    @pytest.mark.unit
    def test_bot_init_module(self):
        assert bot_init is not None

    @pytest.mark.unit
    def test_handlers_package_exists(self):
        import bot.handlers

        assert bot.handlers is not None

    @pytest.mark.unit
    def test_services_package_exists(self):
        import bot.services

        assert bot.services is not None

    @pytest.mark.unit
    def test_keyboards_package_exists(self):
        import bot.keyboards

        assert bot.keyboards is not None

    @pytest.mark.unit
    def test_models_module_exists(self):
        from bot import models

        assert models is not None

    @pytest.mark.unit
    def test_config_module_exists(self):
        from bot import config

        assert config is not None

    @pytest.mark.unit
    def test_database_module_exists(self):
        from bot import database

        assert database is not None

    @pytest.mark.unit
    def test_monitoring_module_exists(self):
        from bot import monitoring

        assert monitoring is not None
