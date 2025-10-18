"""
Unit тесты для конфигурации
"""

import os
from unittest.mock import patch

import pytest

from bot.config import AI_SYSTEM_PROMPT, settings


class TestConfig:
    """Тесты для конфигурации приложения"""

    @pytest.mark.unit
    @pytest.mark.config
    def test_settings_loaded(self):
        """Тест загрузки настроек"""
        assert settings is not None
        assert hasattr(settings, "database_url")
        assert hasattr(settings, "telegram_bot_token")
        assert hasattr(settings, "gemini_api_key")

    @pytest.mark.unit
    @pytest.mark.config
    def test_database_url_configuration(self):
        """Тест конфигурации базы данных"""
        assert settings.database_url is not None
        assert len(settings.database_url) > 0
        assert "postgresql" in settings.database_url

    @pytest.mark.unit
    @pytest.mark.config
    def test_telegram_bot_token_configuration(self):
        """Тест конфигурации токена бота"""
        assert settings.telegram_bot_token is not None
        assert len(settings.telegram_bot_token) > 0
        assert ":" in settings.telegram_bot_token  # формат токена Telegram

    @pytest.mark.unit
    @pytest.mark.config
    def test_gemini_api_key_configuration(self):
        """Тест конфигурации API ключа Gemini"""
        assert settings.gemini_api_key is not None
        assert len(settings.gemini_api_key) > 0
        assert settings.gemini_api_key.startswith("AIza")  # формат API ключа Google

    @pytest.mark.unit
    @pytest.mark.config
    def test_gemini_model_configuration(self):
        """Тест конфигурации модели Gemini"""
        assert settings.gemini_model is not None
        assert len(settings.gemini_model) > 0
        assert "gemini" in settings.gemini_model.lower()

    @pytest.mark.unit
    @pytest.mark.config
    def test_ai_temperature_configuration(self):
        """Тест конфигурации температуры ИИ"""
        assert settings.ai_temperature is not None
        assert isinstance(settings.ai_temperature, (int, float))
        assert 0.0 <= settings.ai_temperature <= 1.0

    @pytest.mark.unit
    @pytest.mark.config
    def test_secret_key_configuration(self):
        """Тест конфигурации секретного ключа"""
        assert settings.secret_key is not None
        assert len(settings.secret_key) > 0
        assert len(settings.secret_key) >= 32  # минимальная длина для безопасности

    @pytest.mark.unit
    @pytest.mark.config
    def test_forbidden_topics_configuration(self):
        """Тест конфигурации запрещенных тем"""
        assert settings.forbidden_topics is not None
        assert isinstance(settings.forbidden_topics, str)
        assert len(settings.forbidden_topics) > 0
        # Проверяем наличие основных запрещенных тем
        topics = settings.forbidden_topics.lower()
        assert any(topic in topics for topic in ["политика", "насилие", "наркотики"])

    @pytest.mark.unit
    @pytest.mark.config
    def test_content_filter_level_configuration(self):
        """Тест конфигурации уровня фильтрации контента"""
        assert settings.content_filter_level is not None
        assert isinstance(settings.content_filter_level, int)
        assert 1 <= settings.content_filter_level <= 5

    @pytest.mark.unit
    @pytest.mark.config
    def test_frontend_url_configuration(self):
        """Тест конфигурации URL фронтенда"""
        assert settings.frontend_url is not None
        assert len(settings.frontend_url) > 0
        assert settings.frontend_url.startswith("https://")

    @pytest.mark.unit
    @pytest.mark.config
    def test_debug_configuration(self):
        """Тест конфигурации режима отладки"""
        # debug не настроен в конфигурации
        assert hasattr(settings, "log_level")
        assert settings.log_level is not None

    @pytest.mark.unit
    @pytest.mark.config
    def test_ai_system_prompt(self):
        """Тест системного промпта ИИ"""
        assert AI_SYSTEM_PROMPT is not None
        assert isinstance(AI_SYSTEM_PROMPT, str)
        assert len(AI_SYSTEM_PROMPT) > 0
        assert "PandaPalAI" in AI_SYSTEM_PROMPT
        assert "школьникам" in AI_SYSTEM_PROMPT.lower()

    @pytest.mark.unit
    @pytest.mark.config
    def test_environment_variables_present(self):
        """Тест наличия переменных окружения"""
        # Проверяем, что основные переменные окружения установлены
        env_vars = ["DATABASE_URL", "TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY", "SECRET_KEY"]

        for var in env_vars:
            value = os.getenv(var)
            if value is not None:  # переменная может быть не установлена в тестах
                assert len(value) > 0

    @pytest.mark.unit
    @pytest.mark.config
    def test_settings_immutable(self):
        """Тест неизменяемости настроек"""
        original_token = settings.telegram_bot_token

        # Попытка изменить настройки не должна влиять на оригинал
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"}):
            # Настройки уже загружены, изменения не должны влиять
            assert settings.telegram_bot_token == original_token

    @pytest.mark.unit
    @pytest.mark.config
    def test_config_validation(self):
        """Тест валидации конфигурации"""
        # Проверяем, что все критически важные настройки присутствуют
        critical_settings = ["database_url", "telegram_bot_token", "gemini_api_key", "secret_key"]

        for setting in critical_settings:
            value = getattr(settings, setting)
            assert value is not None, f"Критически важная настройка {setting} не установлена"
            assert len(str(value)) > 0, f"Настройка {setting} пустая"

    @pytest.mark.unit
    @pytest.mark.config
    def test_config_types(self):
        """Тест типов данных в конфигурации"""
        # Проверяем правильность типов данных
        assert isinstance(settings.ai_temperature, (int, float))
        assert isinstance(settings.content_filter_level, int)
        assert isinstance(settings.log_level, str)
        assert isinstance(settings.forbidden_topics, str)
        assert isinstance(settings.gemini_model, str)
        assert isinstance(settings.frontend_url, str)
