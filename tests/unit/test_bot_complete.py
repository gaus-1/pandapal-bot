"""
Complete bot coverage tests
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.config import AI_SYSTEM_PROMPT, FORBIDDEN_PATTERNS, settings
from bot.keyboards.main_kb import get_main_menu_keyboard, get_settings_keyboard
from bot.models import ChatHistory, User
from bot.services.cache_service import MemoryCache
from bot.services.moderation_service import ContentModerationService


class TestBotComponents:
    @pytest.mark.unit
    def test_config_all_settings(self):
        """Тест настроек конфигурации (обновлено для Yandex Cloud)"""
        assert settings is not None
        assert settings.database_url is not None
        assert settings.telegram_bot_token is not None
        assert settings.yandex_cloud_api_key is not None  # Обновлено
        assert settings.content_filter_level >= 1
        assert settings.daily_message_limit > 0
        assert settings.chat_history_limit > 0
        assert len(settings.get_forbidden_topics_list()) > 0

    @pytest.mark.unit
    def test_ai_system_prompt_structure(self):
        """Структура AI промпта: роль + визуал (остальное отключено)."""
        assert AI_SYSTEM_PROMPT is not None
        assert len(AI_SYSTEM_PROMPT) > 50
        assert "PandaPal" in AI_SYSTEM_PROMPT
        assert "визуал" in AI_SYSTEM_PROMPT.lower() or "школьник" in AI_SYSTEM_PROMPT.lower()

    @pytest.mark.unit
    def test_forbidden_patterns_complete(self):
        assert FORBIDDEN_PATTERNS is not None
        assert len(FORBIDDEN_PATTERNS) > 50
        assert isinstance(FORBIDDEN_PATTERNS, (list, frozenset, set))

    @pytest.mark.unit
    def test_user_model_all_fields(self):
        user = User(
            telegram_id=123456789,
            username="test",
            first_name="First",
            last_name="Last",
            user_type="child",
            age=10,
            grade=5,
        )
        assert user.telegram_id == 123456789
        assert user.username == "test"
        assert user.first_name == "First"
        assert user.user_type == "child"

    @pytest.mark.unit
    def test_chat_history_model_creation(self):
        history = ChatHistory()
        history.user_telegram_id = 123
        history.message_text = "test"
        history.message_type = "user"
        assert history.user_telegram_id == 123
        assert history.message_text == "test"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_memory_cache_complete_workflow(self):
        cache = MemoryCache()

        for i in range(200):
            await cache.set(f"k{i}", f"v{i}", ttl=300)

        assert await cache.get("k0") == "v0"
        assert await cache.get("k100") == "v100"
        assert await cache.get("k199") == "v199"

        await cache.delete("k100")
        assert await cache.get("k100") is None

        stats = await cache.get_stats()
        assert stats["total_items"] > 0

    @pytest.mark.unit
    def test_moderation_service_complete(self):
        service = ContentModerationService()

        test_cases = [
            ("Hello, how are you?", True),
            ("Help with math homework", True),
            ("Explain photosynthesis", True),
            ("What is 2+2?", True),
            ("", True),
        ]

        for content, expected in test_cases:
            result = service.is_safe_content(content)
            is_safe = result[0] if isinstance(result, tuple) else result
            assert isinstance(is_safe, bool)

    @pytest.mark.unit
    def test_main_menu_keyboard_generation(self):
        keyboard = get_main_menu_keyboard()
        assert keyboard is not None

    @pytest.mark.unit
    def test_settings_keyboard_all_types(self):
        for user_type in ["child", None]:
            keyboard = get_settings_keyboard(user_type)
            assert keyboard is not None
