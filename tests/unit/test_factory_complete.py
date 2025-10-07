"""
Complete factory coverage
"""

import pytest
from unittest.mock import Mock, patch
from bot.services.factory import ServiceFactory


class TestServiceFactory:

    @pytest.mark.unit
    def test_factory_singleton(self):
        factory1 = ServiceFactory()
        factory2 = ServiceFactory()
        assert factory1 is factory2

    @pytest.mark.unit
    def test_factory_get_instance(self):
        factory = ServiceFactory.get_instance()
        assert factory is not None

    @pytest.mark.unit
    def test_create_user_service(self):
        factory = ServiceFactory()
        service = factory.create_user_service(Mock())
        assert service is not None

    @pytest.mark.unit
    def test_create_moderation_service(self):
        factory = ServiceFactory()
        service = factory.create_moderation_service()
        assert service is not None

    @pytest.mark.unit
    def test_create_ai_service(self):
        factory = ServiceFactory()
        with patch("bot.services.ai_service.genai"):
            service = factory.create_ai_service()
            assert service is not None

    @pytest.mark.unit
    def test_create_chat_history_service(self):
        factory = ServiceFactory()
        service = factory.create_chat_history_service(Mock())
        assert service is not None

    @pytest.mark.unit
    def test_factory_caching(self):
        factory = ServiceFactory()
        service1 = factory.create_moderation_service()
        service2 = factory.create_moderation_service()
        assert service1 is service2
