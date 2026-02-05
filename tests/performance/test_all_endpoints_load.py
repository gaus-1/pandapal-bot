"""
НАГРУЗОЧНЫЕ ТЕСТЫ для всех API endpoints
Проверяем производительность под нагрузкой

Тестируем:
- Mini App endpoints (AI chat, subjects, dashboard)
- Premium endpoints (create payment, status, features)
- Donation endpoints
- Rate limiting под нагрузкой
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import make_mocked_request

from bot.api.miniapp import miniapp_ai_chat, miniapp_get_subjects
from bot.api.premium_endpoints import (
    create_donation_invoice,
    create_yookassa_payment,
    get_premium_status,
)
from bot.api.premium_features_endpoints import (
    miniapp_get_bonus_lessons,
    miniapp_get_learning_plan,
    miniapp_get_support_queue_status,
)


class TestAllEndpointsLoad:
    """Нагрузочные тесты для всех endpoints"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Создаёт реальную SQLite БД"""
        import os
        import tempfile

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from bot.models import Base

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

    @pytest.fixture
    def test_user(self, real_db_session):
        """Создаёт тестового пользователя"""
        from bot.services import UserService

        user_service = UserService(real_db_session)
        user = user_service.get_or_create_user(
            telegram_id=999888777,
            username="load_test_user",
            first_name="Load",
            last_name="Test",
        )
        real_db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_miniapp_ai_chat_load(self, real_db_session, test_user):
        """Нагрузочный тест: AI chat endpoint под нагрузкой"""
        from contextlib import contextmanager
        from unittest.mock import patch

        @contextmanager
        def mock_get_db():
            yield real_db_session

        # Мокаем Yandex API чтобы не тратить деньги
        async def mock_ai_response(*args, **kwargs):
            return "Тестовый ответ AI"

        with patch("bot.api.miniapp_endpoints.get_db", mock_get_db):
            with patch(
                "bot.api.miniapp_endpoints.yandex_cloud_service.generate_text_response",
                mock_ai_response,
            ):
                # Создаём 50 параллельных запросов
                async def make_request():
                    request = make_mocked_request(
                        "POST",
                        "/api/miniapp/ai/chat",
                        json={"message": "Тестовый вопрос", "telegram_id": 999888777},
                    )
                    return await miniapp_ai_chat(request)

                start_time = time.time()
                tasks = [make_request() for _ in range(50)]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

                # Проверяем результаты
                successful = [r for r in responses if not isinstance(r, Exception)]
                assert len(successful) == 50, f"Не все запросы успешны: {len(successful)}/50"

                # Проверяем время выполнения
                total_time = end_time - start_time
                avg_time = total_time / 50
                assert avg_time < 1.0, f"Слишком медленно: {avg_time:.2f}s на запрос"

                print(
                    f"✅ AI Chat Load Test: {len(successful)}/50 успешно, {avg_time:.3f}s среднее время"
                )

    @pytest.mark.asyncio
    async def test_premium_status_endpoint_load(self, real_db_session, test_user):
        """Нагрузочный тест: Premium status endpoint"""
        from contextlib import contextmanager
        from unittest.mock import patch

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_endpoints.get_db", mock_get_db):
            # Создаём 100 параллельных запросов
            async def make_request():
                request = make_mocked_request(
                    "GET",
                    "/api/miniapp/premium/status/999888777",
                    match_info={"telegram_id": "999888777"},
                )
                return await get_premium_status(request)

            start_time = time.time()
            tasks = [make_request() for _ in range(100)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful = [r for r in responses if not isinstance(r, Exception)]
            assert len(successful) == 100, f"Не все запросы успешны: {len(successful)}/100"

            total_time = end_time - start_time
            avg_time = total_time / 100
            assert avg_time < 0.1, f"Слишком медленно: {avg_time:.3f}s на запрос"

            print(
                f"✅ Premium Status Load Test: {len(successful)}/100 успешно, {avg_time:.3f}s среднее время"
            )

    @pytest.mark.asyncio
    async def test_subjects_endpoint_load(self, real_db_session, test_user):
        """Нагрузочный тест: Subjects endpoint"""
        from contextlib import contextmanager
        from unittest.mock import patch

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.miniapp_endpoints.get_db", mock_get_db):
            # Создаём 200 параллельных запросов
            async def make_request():
                request = make_mocked_request(
                    "GET",
                    "/api/miniapp/subjects",
                    match_info={},
                )
                return await miniapp_get_subjects(request)

            start_time = time.time()
            tasks = [make_request() for _ in range(200)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful = [r for r in responses if not isinstance(r, Exception)]
            assert len(successful) == 200, f"Не все запросы успешны: {len(successful)}/200"

            total_time = end_time - start_time
            avg_time = total_time / 200
            assert avg_time < 0.05, f"Слишком медленно: {avg_time:.3f}s на запрос"

            print(
                f"✅ Subjects Load Test: {len(successful)}/200 успешно, {avg_time:.3f}s среднее время"
            )

    @pytest.mark.asyncio
    async def test_rate_limiting_under_load(self, real_db_session, test_user):
        """Нагрузочный тест: Rate limiting под нагрузкой"""
        from contextlib import contextmanager
        from unittest.mock import patch

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.miniapp_endpoints.get_db", mock_get_db):
            # Создаём 1000 запросов за короткое время (должны быть ограничены)
            async def make_request():
                request = make_mocked_request(
                    "POST",
                    "/api/miniapp/ai/chat",
                    json={"message": "Тест", "telegram_id": 999888777},
                    headers={"X-Forwarded-For": "127.0.0.1"},
                )
                try:
                    return await miniapp_ai_chat(request)
                except Exception as e:
                    return e

            start_time = time.time()
            tasks = [make_request() for _ in range(1000)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Проверяем что rate limiting работает
            rate_limited = [r for r in responses if isinstance(r, web.Response) and r.status == 429]
            assert len(rate_limited) > 0, "Rate limiting не сработал!"

            print(f"✅ Rate Limiting Test: {len(rate_limited)} запросов ограничено из 1000")

    @pytest.mark.asyncio
    async def test_concurrent_premium_features(self, real_db_session, test_user):
        """Нагрузочный тест: Concurrent premium features endpoints"""
        from contextlib import contextmanager
        from unittest.mock import patch

        from bot.services import SubscriptionService

        # Активируем Premium
        subscription_service = SubscriptionService(real_db_session)
        subscription_service.activate_subscription(
            telegram_id=999888777,
            plan_id="month",
            transaction_id="load_test_tx",
            payment_method="stars",
        )
        real_db_session.commit()

        @contextmanager
        def mock_get_db():
            yield real_db_session

        with patch("bot.api.premium_features_endpoints.get_db", mock_get_db):
            # Параллельные запросы к разным premium endpoints
            async def make_learning_plan():
                request = make_mocked_request(
                    "GET",
                    "/api/miniapp/premium/learning-plan/999888777",
                    match_info={"telegram_id": "999888777"},
                )
                return await miniapp_get_learning_plan(request)

            async def make_bonus_lessons():
                request = make_mocked_request(
                    "GET",
                    "/api/miniapp/premium/bonus-lessons/999888777",
                    match_info={"telegram_id": "999888777"},
                )
                return await miniapp_get_bonus_lessons(request)

            async def make_support_queue():
                request = make_mocked_request(
                    "GET",
                    "/api/miniapp/premium/support-queue/999888777",
                    match_info={"telegram_id": "999888777"},
                )
                return await miniapp_get_support_queue_status(request)

            # Создаём смешанную нагрузку
            tasks = []
            for _ in range(30):
                tasks.append(make_learning_plan())
                tasks.append(make_bonus_lessons())
                tasks.append(make_support_queue())

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            successful = [r for r in responses if not isinstance(r, Exception)]
            assert len(successful) == 90, f"Не все запросы успешны: {len(successful)}/90"

            total_time = end_time - start_time
            avg_time = total_time / 90
            assert avg_time < 0.2, f"Слишком медленно: {avg_time:.3f}s на запрос"

            print(
                f"✅ Premium Features Concurrent Test: {len(successful)}/90 успешно, {avg_time:.3f}s среднее время"
            )
