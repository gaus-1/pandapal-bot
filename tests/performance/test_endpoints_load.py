"""
Тесты высоконагруженности endpoints
Проверка что endpoints выдерживают большую нагрузку
"""

import asyncio
import os
import tempfile
import time

import pytest
from aiohttp.test_utils import make_mocked_request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.api.miniapp_endpoints import miniapp_get_user
from bot.models import Base, User


class TestEndpointsLoad:
    """Тесты высоконагруженности endpoints"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Создаёт реальную SQLite БД для каждого теста"""
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
    def test_users(self, real_db_session):
        """Создаёт несколько тестовых пользователей"""
        users = []
        for i in range(20):
            user = User(
                telegram_id=1000000 + i,
                username=f"load_test_user_{i}",
                first_name=f"Тестовый{i}",
                last_name="Нагрузка",
                user_type="child",
                age=10,
                grade=5,
            )
            real_db_session.add(user)
            users.append(user)
        real_db_session.commit()
        return users

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_user_requests(self, real_db_session, test_users):
        """Тест: конкурентные запросы к endpoint пользователя"""
        from unittest.mock import patch

        async def make_request(telegram_id):
            """Создать запрос к endpoint"""
            request = make_mocked_request(
                "GET",
                f"/api/miniapp/user/{telegram_id}",
                match_info={"telegram_id": str(telegram_id)},
            )

            with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                response = await miniapp_get_user(request)
                return response.status

        # Создаём 20 конкурентных запросов
        tasks = [make_request(1000000 + i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # Проверяем что все запросы успешны
        assert all(status == 200 for status in results), "Все запросы должны быть успешны"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sequential_requests_performance(self, real_db_session, test_users):
        """Тест: производительность последовательных запросов"""
        from unittest.mock import patch

        start_time = time.time()

        for i in range(50):
            request = make_mocked_request(
                "GET",
                f"/api/miniapp/user/{1000000 + (i % 20)}",
                match_info={"telegram_id": str(1000000 + (i % 20))},
            )

            with patch("bot.api.miniapp_endpoints.get_db") as mock_get_db:
                mock_get_db.return_value.__enter__.return_value = real_db_session
                mock_get_db.return_value.__exit__.return_value = None

                await miniapp_get_user(request)

        elapsed_time = time.time() - start_time
        avg_time = (elapsed_time / 50) * 1000  # среднее время в ms

        assert avg_time < 100, f"Среднее время запроса {avg_time}ms, должно быть < 100ms"
