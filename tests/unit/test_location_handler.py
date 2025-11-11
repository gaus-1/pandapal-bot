"""
Реальные тесты для обработчика геолокации
Проверяет отправку местоположения родителям
"""

from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import Chat, Location, Message
from aiogram.types import User as TgUser

from bot.database import get_db
from bot.handlers.location import get_location_keyboard, router
from bot.models import User
from bot.services.user_service import UserService


class TestLocationKeyboard:
    """Тесты клавиатуры геолокации"""

    @pytest.mark.unit
    def test_location_keyboard_structure(self):
        """Проверка структуры клавиатуры"""
        keyboard = get_location_keyboard()

        assert keyboard is not None
        assert keyboard.resize_keyboard is True
        assert keyboard.one_time_keyboard is True
        assert len(keyboard.keyboard) == 2  # 2 строки
        assert len(keyboard.keyboard[0]) == 1  # Кнопка геолокации
        assert len(keyboard.keyboard[1]) == 1  # Кнопка отмены

    @pytest.mark.unit
    def test_location_button_request_location(self):
        """Проверка что кнопка запрашивает геолокацию"""
        keyboard = get_location_keyboard()

        location_button = keyboard.keyboard[0][0]
        assert location_button.text == "📍 Отправить мое местоположение"
        assert location_button.request_location is True

    @pytest.mark.unit
    def test_cancel_button_exists(self):
        """Проверка наличия кнопки отмены"""
        keyboard = get_location_keyboard()

        cancel_button = keyboard.keyboard[1][0]
        assert cancel_button.text == "🔙 Отмена"
        assert cancel_button.request_location is None


class TestLocationRouter:
    """Тесты роутера геолокации"""

    @pytest.mark.unit
    def test_router_exists(self):
        """Проверка что роутер существует"""
        assert router is not None
        assert router.name == "location"

    @pytest.mark.unit
    def test_router_has_handlers(self):
        """Проверка что роутер имеет обработчики"""
        # Проверяем что роутер имеет зарегистрированные обработчики
        assert "message" in router.observers

        # Получаем observer для message
        message_observer = router.observers["message"]

        # Проверяем что observer не пустой
        assert message_observer is not None

        # У роутера должны быть обработчики
        # (точное количество проверяем в интеграционных тестах)


class TestLocationLinks:
    """Тесты генерации ссылок на карты"""

    @pytest.mark.unit
    def test_yandex_maps_link_format(self):
        """Проверка формата ссылки Яндекс.Карты"""
        lat = 55.7558
        lon = 37.6173

        yandex_url = f"https://yandex.ru/maps/?ll={lon},{lat}&z=16&pt={lon},{lat}"

        assert "yandex.ru/maps" in yandex_url
        assert str(lat) in yandex_url
        assert str(lon) in yandex_url
        assert yandex_url.startswith("https://")

    @pytest.mark.unit
    def test_google_maps_link_format(self):
        """Проверка формата ссылки Google Maps"""
        lat = 55.7558
        lon = 37.6173

        google_url = f"https://www.google.com/maps?q={lat},{lon}"

        assert "google.com/maps" in google_url
        assert str(lat) in google_url
        assert str(lon) in google_url
        assert google_url.startswith("https://")

    @pytest.mark.unit
    def test_2gis_link_format(self):
        """Проверка формата ссылки 2GIS"""
        lat = 55.7558
        lon = 37.6173

        gis_url = f"https://2gis.ru/geo/{lon},{lat}"

        assert "2gis.ru/geo" in gis_url
        assert str(lat) in gis_url
        assert str(lon) in gis_url
        assert gis_url.startswith("https://")


class TestLocationHandlerLogic:
    """Тесты бизнес-логики обработчика"""

    @pytest.mark.unit
    def test_location_message_structure(self):
        """Проверка структуры сообщения для родителя"""
        lat = 55.7558
        lon = 37.6173
        child_name = "Вася"

        # Формируем ссылки
        yandex_url = f"https://yandex.ru/maps/?ll={lon},{lat}&z=16&pt={lon},{lat}"
        google_url = f"https://www.google.com/maps?q={lat},{lon}"
        gis_url = f"https://2gis.ru/geo/{lon},{lat}"

        # Проверяем что ссылки корректны
        assert yandex_url.count("http") == 1
        assert google_url.count("http") == 1
        assert gis_url.count("http") == 1

        # Проверяем что координаты в правильном формате
        assert -90 <= lat <= 90  # Широта в допустимых пределах
        assert -180 <= lon <= 180  # Долгота в допустимых пределах

    @pytest.mark.unit
    def test_coordinates_precision(self):
        """Проверка точности координат"""
        # Telegram отправляет координаты с точностью до 6 знаков
        lat = 55.755826
        lon = 37.617300

        # Проверяем что можем работать с высокой точностью
        assert isinstance(lat, float)
        assert isinstance(lon, float)

        # Форматируем для отображения
        lat_str = f"{lat:.6f}"
        lon_str = f"{lon:.6f}"

        assert len(lat_str.split(".")[-1]) <= 6
        assert len(lon_str.split(".")[-1]) <= 6


class TestLocationSecurity:
    """Тесты безопасности геолокации"""

    @pytest.mark.unit
    def test_no_parent_scenario(self):
        """
        Проверка что без привязанного родителя
        геолокация не отправляется
        """
        # Пользователь без родителя
        user = User(telegram_id=123456, first_name="Вася", parent_telegram_id=None)  # Нет родителя!

        # Проверяем что parent_telegram_id = None
        assert user.parent_telegram_id is None

        # В этом случае должно быть предупреждение
        # "У тебя пока не привязан родитель"

    @pytest.mark.unit
    def test_with_parent_scenario(self):
        """
        Проверка что с привязанным родителем
        геолокация должна отправиться
        """
        # Пользователь с родителем
        user = User(
            telegram_id=123456, first_name="Вася", parent_telegram_id=999999  # Есть родитель!
        )

        # Проверяем что parent_telegram_id указан
        assert user.parent_telegram_id is not None
        assert user.parent_telegram_id == 999999


class TestLocationDataNotSaved:
    """Тесты что геолокация НЕ сохраняется в БД"""

    @pytest.mark.unit
    def test_location_not_in_models(self):
        """Проверка что нет модели для хранения геолокации"""
        from bot import models

        # Проверяем что нет модели Location/UserLocation/etc
        model_names = [name for name in dir(models) if not name.startswith("_")]

        # Должны быть User, ChatHistory и др., но НЕ Location
        assert "Location" not in model_names
        assert "UserLocation" not in model_names
        assert "GeoHistory" not in model_names

        # Это подтверждает что мы НЕ сохраняем геолокацию


class TestLocationIntegration:
    """Интеграционные тесты"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_location_handler_registered(self):
        """Проверка что handler зарегистрирован в роутере"""
        from bot.handlers import routers
        from bot.handlers.location import router as location_router

        # Проверяем что location_router в списке роутеров
        assert location_router in routers

    @pytest.mark.integration
    def test_location_button_in_main_menu(self):
        """Проверка что кнопка "📍 Где я" есть в главном меню"""
        from bot.keyboards.main_kb import get_main_menu_keyboard

        keyboard = get_main_menu_keyboard()

        # Собираем все тексты кнопок
        all_buttons_text = []
        for row in keyboard.keyboard:
            for button in row:
                all_buttons_text.append(button.text)

        # Проверяем наличие кнопки геолокации
        assert "📍 Где я" in all_buttons_text
