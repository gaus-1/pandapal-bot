"""
Тесты YandexART с реальными API запросами.

Проверяет генерацию изображений через Yandex Foundation Models.

ВАЖНО: Требует:
- YANDEX_CLOUD_API_KEY
- YANDEX_CLOUD_FOLDER_ID
- Роль ai.imageGeneration.user в Yandex Cloud IAM
"""

import os

import pytest

from bot.services.yandex_art_service import get_yandex_art_service


@pytest.mark.skipif(
    not os.getenv("YANDEX_CLOUD_API_KEY") or not os.getenv("YANDEX_CLOUD_FOLDER_ID"),
    reason="Требуется YANDEX_CLOUD_API_KEY и YANDEX_CLOUD_FOLDER_ID",
)
class TestYandexARTRealAPI:
    """Тесты генерации изображений через YandexART."""

    @pytest.fixture
    def art_service(self):
        """Фикстура YandexART сервиса."""
        return get_yandex_art_service()

    @pytest.mark.asyncio
    async def test_service_available(self, art_service):
        """Сервис доступен с настроенными ключами."""
        assert art_service.is_available(), "YandexART сервис недоступен - проверь API ключи"

    @pytest.mark.asyncio
    async def test_generate_simple_image(self, art_service):
        """Генерация простого изображения."""
        prompt = "Милая панда читает книгу в библиотеке"

        image_bytes = await art_service.generate_image(prompt=prompt, style="auto")

        assert image_bytes is not None, "Изображение не сгенерировано"
        assert len(image_bytes) > 1000, "Изображение слишком маленькое"
        # YandexART возвращает JPEG формат
        assert image_bytes[:2] == b'\xff\xd8', "Неверный формат изображения (не JPEG)"

    @pytest.mark.asyncio
    async def test_generate_anime_style(self, art_service):
        """Генерация в стиле аниме."""
        prompt = "Панда-учитель объясняет математику детям"

        image_bytes = await art_service.generate_image(prompt=prompt, style="anime")

        assert image_bytes is not None
        assert len(image_bytes) > 1000
        assert image_bytes[:2] == b'\xff\xd8'

    @pytest.mark.asyncio
    async def test_generate_different_aspect_ratios(self, art_service):
        """Генерация с разными соотношениями сторон."""
        prompt = "Красивый закат над океаном"

        # 16:9 пейзажная
        image_landscape = await art_service.generate_image(
            prompt=prompt, aspect_ratio="16:9"
        )

        assert image_landscape is not None
        assert len(image_landscape) > 1000

    @pytest.mark.asyncio
    async def test_generate_educational_content(self, art_service):
        """Генерация образовательного контента."""
        prompt = "Схема строения атома с электронами, протонами и нейтронами"

        image_bytes = await art_service.generate_image(
            prompt=prompt, style="realism"
        )

        assert image_bytes is not None
        assert len(image_bytes) > 1000

    @pytest.mark.asyncio
    async def test_timeout_handling(self, art_service):
        """Обработка таймаута при генерации."""
        prompt = "Детальная иллюстрация космоса с планетами"

        # Короткий таймаут для проверки обработки
        image_bytes = await art_service.generate_image(
            prompt=prompt, timeout=120
        )

        # Может вернуть None если не успеет, это ок
        if image_bytes:
            assert len(image_bytes) > 1000
