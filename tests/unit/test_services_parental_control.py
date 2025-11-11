"""
Comprehensive tests for Parental Control Service
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from sqlalchemy.orm import Session

from bot.services.parental_control import (
    ActivityRecord,
    ActivityType,
    AlertLevel,
    ParentalControlService,
    ParentReport,
)


class TestParentalControlService:

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        return ParentalControlService(mock_db)

    @pytest.mark.unit
    def test_service_init(self, service, mock_db):
        assert service.db == mock_db
        assert service.activity_buffer == []
        assert service.buffer_size == 100

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_record_child_activity(self, service, mock_db):
        await service.record_child_activity(
            child_telegram_id=123456789,
            activity_type=ActivityType.MESSAGE_SENT,
            details={"length": 10},
            message_content="Test message",
        )

        assert len(service.activity_buffer) == 1
        assert service.activity_buffer[0].child_id == 123456789
        assert service.activity_buffer[0].activity_type == ActivityType.MESSAGE_SENT

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_record_blocked_message(self, service):
        await service.record_child_activity(
            child_telegram_id=123456789,
            activity_type=ActivityType.MESSAGE_BLOCKED,
            details={"reason": "inappropriate"},
            message_content="Blocked content",
        )

        assert len(service.activity_buffer) == 1
        assert service.activity_buffer[0].activity_type == ActivityType.MESSAGE_BLOCKED

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_activity_buffer_limit(self, service):
        for i in range(150):
            await service.record_child_activity(
                child_telegram_id=123456789,
                activity_type=ActivityType.MESSAGE_SENT,
                details={"index": i},
            )

        assert len(service.activity_buffer) <= service.buffer_size

    @pytest.mark.unit
    def test_activity_record_creation(self):
        record = ActivityRecord(
            child_id=123456789,
            activity_type=ActivityType.MESSAGE_SENT,
            timestamp=datetime.now(),
            details={"test": "data"},
            alert_level=AlertLevel.INFO,
        )

        assert record.child_id == 123456789
        assert record.activity_type == ActivityType.MESSAGE_SENT
        assert record.alert_level == AlertLevel.INFO

    @pytest.mark.unit
    def test_parent_report_creation(self):
        report = ParentReport(
            parent_id=111,
            child_id=222,
            period_start=datetime.now(),
            period_end=datetime.now(),
            total_messages=100,
            blocked_messages=5,
            suspicious_activities=2,
            ai_interactions=50,
            voice_messages=10,
            moderation_summary={},
            recent_activities=[],
            recommendations=[],
        )

        assert report.parent_id == 111
        assert report.child_id == 222
        assert report.total_messages == 100
