"""
Тесты для Yandex Vision Service
Проверка анализа изображений через Yandex Cloud Vision
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.services.vision_service import VisionService


class TestYandexVisionService:
    """Тесты для Yandex Vision сервиса"""

    @pytest.fixture
    def service(self):
        """Создание экземпляра сервиса"""
        return VisionService()

    @pytest.mark.unit
    def test_service_init(self, service):
        """Тест инициализации сервиса"""
        assert service is not None
        assert hasattr(service, "yandex_service")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_with_yandex(self, service):
        """Тест анализа изображения через Yandex Cloud"""
        fake_image_bytes = b"fake_image_data"

        with patch.object(
            service.yandex_service, "analyze_image_with_text", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = "Это пример анализа изображения"

            result = await service.analyze_image(fake_image_bytes, "Что на фото?")

            assert result == "Это пример анализа изображения"
            mock_analyze.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_error_handling(self, service):
        """Тест обработки ошибок при анализе"""
        fake_image_bytes = b"invalid_data"

        with patch.object(
            service.yandex_service, "analyze_image_with_text", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.side_effect = Exception("Network error")

            result = await service.analyze_image(fake_image_bytes, "Что на фото?")

            assert result is None or "ошибк" in result.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_educational_content(self, service):
        """Тест анализа образовательного контента"""
        fake_image_bytes = b"homework_photo"

        with patch.object(
            service.yandex_service, "analyze_image_with_text", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = "Задача: 2+2=4"

            result = await service.analyze_image(fake_image_bytes, "Реши задачу на фото")

            assert result is not None
            mock_analyze.assert_called_once()


@pytest.mark.unit
class TestVisionServiceIntegration:
    """Интеграционные тесты для Vision"""

    @pytest.mark.asyncio
    async def test_vision_service_lazy_init(self):
        """Тест ленивой инициализации"""
        service = VisionService()

        # Проверяем что сервис создан
        assert service is not None
        assert service.yandex_service is not None

    @pytest.mark.asyncio
    async def test_empty_image_handling(self):
        """Тест обработки пустого изображения"""
        service = VisionService()

        result = await service.analyze_image(b"", "test")

        # Должен вернуть None или ошибку
        assert result is None or isinstance(result, str)
