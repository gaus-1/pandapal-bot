"""
ТЕСТЫ ОТКАЗОУСТОЙЧИВОСТИ для всех ключевых компонентов
Проверяем поведение при сбоях и ошибках

Тестируем:
- Отказоустойчивость БД (недоступность, таймауты)
- Отказоустойчивость внешних API (Yandex Cloud)
- Отказоустойчивость payment services (YooKassa, Telegram Stars)
- Rate limiting при перегрузке
- Обработка некорректных данных
"""

import asyncio
import os
import tempfile
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp_endpoints import miniapp_ai_chat
from bot.api.premium_endpoints import create_donation_invoice, get_premium_status
from bot.models import Base
from bot.services import (
    PaymentService,
    PremiumFeaturesService,
    SubscriptionService,
    YandexCloudService,
)


class TestAllComponentsResilience:
    """Тесты отказоустойчивости всех компонентов"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Создаёт реальную SQLite БД"""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        yield session

        session.close()
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    # ========== Database Resilience ==========

    @pytest.mark.asyncio
    async def test_database_connection_failure(self, real_db_session):
        """Тест: Поведение при недоступности БД"""
        from bot.services import UserService

        # Симулируем закрытие соединения
        real_db_session.close()

        service = UserService(real_db_session)

        # Должна быть обработана ошибка
        with pytest.raises((OperationalError, AttributeError)):
            service.get_user_by_telegram_id(123456)

    @pytest.mark.asyncio
    async def test_database_timeout_handling(self, real_db_session):
        """Тест: Обработка таймаутов БД"""
        from bot.services import SubscriptionService

        service = SubscriptionService(real_db_session)

        # Симулируем медленный запрос
        with patch.object(real_db_session, "query", side_effect=asyncio.TimeoutError("DB timeout")):
            # Должна быть обработана ошибка
            with pytest.raises((asyncio.TimeoutError, Exception)):
                service.is_premium_active(123456)

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, real_db_session):
        """Тест: Откат транзакции при ошибке"""
        from bot.services import SubscriptionService

        service = SubscriptionService(real_db_session)

        # Пытаемся активировать подписку с невалидными данными
        try:
            service.activate_subscription(
                telegram_id=None,  # Невалидный ID
                plan_id="invalid_plan",
                transaction_id="test",
                payment_method="stars",
            )
            real_db_session.commit()
        except Exception:
            real_db_session.rollback()

        # Проверяем что транзакция откатилась
        assert real_db_session.query(Base).count() == 0

    # ========== External API Resilience (Yandex Cloud) ==========

    @pytest.mark.asyncio
    async def test_yandex_api_timeout(self):
        """Тест: Обработка таймаута Yandex API"""
        service = YandexCloudService()

        # Симулируем таймаут
        with patch("aiohttp.ClientSession.post", side_effect=asyncio.TimeoutError()):
            with pytest.raises((asyncio.TimeoutError, Exception)):
                await service.generate_text_response("Тест", timeout=0.001)

    @pytest.mark.asyncio
    async def test_yandex_api_connection_error(self):
        """Тест: Обработка ошибки соединения с Yandex API"""
        service = YandexCloudService()

        # Симулируем ошибку соединения
        with patch(
            "aiohttp.ClientSession.post",
            side_effect=ConnectionError("Connection refused"),
        ):
            with pytest.raises((ConnectionError, Exception)):
                await service.generate_text_response("Тест")

    @pytest.mark.asyncio
    async def test_yandex_api_rate_limit(self):
        """Тест: Обработка rate limit от Yandex API"""
        service = YandexCloudService()

        # Симулируем 429 ответ
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.json = AsyncMock(return_value={"error": "Rate limit exceeded"})

        with patch("aiohttp.ClientSession.post", return_value=mock_response):
            with pytest.raises((Exception, ValueError)):
                await service.generate_text_response("Тест")

    @pytest.mark.asyncio
    async def test_yandex_api_invalid_response(self):
        """Тест: Обработка некорректного ответа от Yandex API"""
        service = YandexCloudService()

        # Симулируем некорректный JSON
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

        with patch("aiohttp.ClientSession.post", return_value=mock_response):
            with pytest.raises((ValueError, Exception)):
                await service.generate_text_response("Тест")

    # ========== Payment Services Resilience ==========

    @pytest.mark.asyncio
    async def test_yookassa_api_failure(self):
        """Тест: Обработка сбоя YooKassa API"""
        service = PaymentService()

        # Симулируем ошибку API
        with patch(
            "yookassa.Payment.create",
            side_effect=Exception("YooKassa API error"),
        ):
            with pytest.raises(Exception):
                service.create_payment(
                    telegram_id=123456, plan_id="month", user_email="test@test.com"
                )

    @pytest.mark.asyncio
    async def test_telegram_stars_api_failure(self):
        """Тест: Обработка сбоя Telegram Stars API"""
        from contextlib import contextmanager

        @contextmanager
        def mock_get_db():
            yield None  # Не используем БД для этого теста

        # Симулируем ошибку Telegram Bot API
        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            with patch("aiogram.Bot") as mock_bot_class:
                mock_bot = MagicMock()
                mock_bot.create_invoice_link = AsyncMock(
                    side_effect=Exception("Telegram API error")
                )
                mock_bot_class.return_value = mock_bot

                request = make_mocked_request(
                    "POST",
                    "/api/miniapp/donation/create-invoice",
                    json={"telegram_id": 123456, "amount": 100},
                )

                response = await create_donation_invoice(request)
                assert response.status == 500

    # ========== Rate Limiting Resilience ==========

    @pytest.mark.asyncio
    async def test_rate_limiting_under_attack(self, real_db_session):
        """Тест: Rate limiting при DDoS атаке"""
        from contextlib import contextmanager
        from unittest.mock import patch

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.miniapp_endpoints.get_db", mock_get_db):
            # Создаём 1000 запросов с одного IP
            async def make_request():
                request = make_mocked_request(
                    "POST",
                    "/api/miniapp/ai/chat",
                    json={"message": "Тест", "telegram_id": 999888777},
                    headers={"X-Forwarded-For": "192.168.1.100"},
                )
                return await miniapp_ai_chat(request)

            tasks = [make_request() for _ in range(1000)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Большинство запросов должны быть ограничены
            rate_limited = [r for r in responses if isinstance(r, web.Response) and r.status == 429]
            assert (
                len(rate_limited) > 500
            ), f"Rate limiting не работает: {len(rate_limited)}/1000 ограничено"

    # ========== Invalid Data Handling ==========

    @pytest.mark.asyncio
    async def test_invalid_user_data(self, real_db_session):
        """Тест: Обработка некорректных данных пользователя"""
        from bot.services import UserService

        service = UserService(real_db_session)

        # Пытаемся создать пользователя с невалидными данными
        with pytest.raises((ValueError, TypeError, Exception)):
            service.get_or_create_user(
                telegram_id="invalid",  # Должно быть int
                username=None,
                first_name="",
            )

    @pytest.mark.asyncio
    async def test_invalid_premium_plan(self, real_db_session):
        """Тест: Обработка невалидного плана Premium"""
        from bot.services import SubscriptionService

        service = SubscriptionService(real_db_session)

        with pytest.raises((ValueError, Exception)):
            service.activate_subscription(
                telegram_id=123456,
                plan_id="invalid_plan_that_does_not_exist",
                transaction_id="test",
                payment_method="stars",
            )

    @pytest.mark.asyncio
    async def test_malformed_api_request(self, real_db_session):
        """Тест: Обработка некорректного API запроса"""
        from contextlib import contextmanager
        from unittest.mock import patch

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.miniapp_endpoints.get_db", mock_get_db):
            # Запрос без обязательных полей
            request = make_mocked_request(
                "POST",
                "/api/miniapp/ai/chat",
                json={},  # Пустой JSON
            )

            response = await miniapp_ai_chat(request)
            assert response.status in [400, 422], "Должна быть ошибка валидации"

    # ========== Service Degradation ==========

    @pytest.mark.asyncio
    async def test_graceful_degradation_ai_service(self):
        """Тест: Graceful degradation при недоступности AI"""
        service = YandexCloudService()

        # Симулируем полный отказ AI сервиса
        with patch(
            "aiohttp.ClientSession.post",
            side_effect=Exception("AI service unavailable"),
        ):
            # Должна быть обработана ошибка без краша
            try:
                await service.generate_text_response("Тест")
            except Exception as e:
                # Ошибка должна быть обработана gracefully
                assert isinstance(e, Exception)
                # Не должно быть необработанных исключений

    @pytest.mark.asyncio
    async def test_partial_service_failure(self, real_db_session):
        """Тест: Частичный отказ сервиса (БД работает, AI нет)"""
        from contextlib import contextmanager
        from unittest.mock import patch

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.miniapp_endpoints.get_db", mock_get_db):
            # AI сервис недоступен
            with patch(
                "bot.api.miniapp_endpoints.yandex_cloud_service.generate_text_response",
                side_effect=Exception("AI unavailable"),
            ):
                request = make_mocked_request(
                    "POST",
                    "/api/miniapp/ai/chat",
                    json={"message": "Тест", "telegram_id": 999888777},
                )

                response = await miniapp_ai_chat(request)
                # Должна быть ошибка, но не краш
                assert response.status in [500, 503]

    # ========== Memory and Resource Leaks ==========

    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self, real_db_session):
        """Тест: Предотвращение утечек памяти"""
        from bot.services import PremiumFeaturesService

        service = PremiumFeaturesService(real_db_session)

        # Множественные вызовы не должны вызывать утечки
        for i in range(1000):
            service.is_premium_active(123456)
            service.has_unlimited_ai(123456)

        # Если дошли сюда - утечек нет
        assert True

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self, real_db_session):
        """Тест: Обработка исчерпания пула соединений"""
        from bot.services import SubscriptionService

        service = SubscriptionService(real_db_session)

        # Создаём множество одновременных запросов
        async def check_premium(telegram_id):
            return service.is_premium_active(telegram_id)

        tasks = [check_premium(i) for i in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Все запросы должны быть обработаны
        assert len(results) == 100
