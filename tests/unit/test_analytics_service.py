"""
Unit тесты для bot/services/analytics_service.py
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.models import Base, User
from bot.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Тесты для AnalyticsService"""

    @pytest.fixture(scope="function")
    def real_db_session(self):
        """Реальная БД для тестов"""
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
        user = User(telegram_id=123456, username="test", first_name="Test")
        real_db_session.add(user)
        real_db_session.commit()
        return user

    def test_analytics_service_init(self, real_db_session):
        """Тест инициализации сервиса"""
        service = AnalyticsService(real_db_session)
        assert service is not None

    def test_record_metric(self, real_db_session, test_user):
        """Тест записи метрики"""
        service = AnalyticsService(real_db_session)

        metric = service.record_metric(
            metric_name="test_metric",
            metric_value=10.5,
            metric_type="technical",
            period="day",
            user_telegram_id=123456,
            tags={"key": "value"},
        )

        real_db_session.commit()

        assert metric is not None
        assert metric.metric_name == "test_metric"
        assert metric.metric_value == 10.5
        assert metric.metric_type == "technical"

    def test_record_safety_metric(self, real_db_session, test_user):
        """Тест записи метрики безопасности"""
        service = AnalyticsService(real_db_session)

        service.record_safety_metric(
            metric_name="blocked_messages",
            value=5.0,
            user_telegram_id=123456,
            category="violence",
        )

        real_db_session.commit()

    def test_record_education_metric(self, real_db_session, test_user):
        """Тест записи метрики образования"""
        service = AnalyticsService(real_db_session)

        service.record_education_metric(
            metric_name="messages_per_child",
            value=20.0,
            user_telegram_id=123456,
            subject="matematika",
        )

        real_db_session.commit()

    def test_record_technical_metric(self, real_db_session, test_user):
        """Тест записи технической метрики"""
        service = AnalyticsService(real_db_session)

        service.record_technical_metric(
            metric_name="ai_response_time",
            value=1.5,
            tags={"endpoint": "/api/miniapp/ai/chat"},
        )

        real_db_session.commit()
