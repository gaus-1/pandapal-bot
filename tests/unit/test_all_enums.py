"""
Complete enum coverage tests
"""

import pytest
from bot.services.advanced_moderation import ModerationLevel, ContentCategory
from bot.services.analytics_service import AnalyticsPeriod, UserSegment
from bot.services.parental_control import ActivityType, AlertLevel
from bot.services.performance_monitor import PerformanceLevel
from bot.services.health_monitor import ServiceStatus
from bot.services.vision_service import ImageCategory, ImageSafetyLevel


class TestAllEnums:

    @pytest.mark.unit
    def test_moderation_level_all_values(self):
        assert ModerationLevel.SAFE.value == "safe"
        assert ModerationLevel.WARNING.value == "warning"
        assert ModerationLevel.BLOCKED.value == "blocked"
        assert ModerationLevel.DANGEROUS.value == "dangerous"

    @pytest.mark.unit
    def test_content_category_all_values(self):
        for category in ContentCategory:
            assert category.value is not None
            assert isinstance(category.value, str)

    @pytest.mark.unit
    def test_analytics_period_all_values(self):
        assert AnalyticsPeriod.DAY.value == "day"
        assert AnalyticsPeriod.WEEK.value == "week"
        assert AnalyticsPeriod.MONTH.value == "month"
        assert AnalyticsPeriod.QUARTER.value == "quarter"
        assert AnalyticsPeriod.YEAR.value == "year"

    @pytest.mark.unit
    def test_user_segment_all_values(self):
        for segment in UserSegment:
            assert segment.value is not None

    @pytest.mark.unit
    def test_activity_type_all_values(self):
        for activity in ActivityType:
            assert activity.value is not None

    @pytest.mark.unit
    def test_alert_level_all_values(self):
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.CRITICAL.value == "critical"

    @pytest.mark.unit
    def test_performance_level_all_values(self):
        for level in PerformanceLevel:
            assert level.value is not None

    @pytest.mark.unit
    def test_service_status_all_values(self):
        for status in ServiceStatus:
            assert status.value is not None

    @pytest.mark.unit
    def test_image_category_all_values(self):
        for category in ImageCategory:
            assert category.value is not None

    @pytest.mark.unit
    def test_image_safety_level_all_values(self):
        for level in ImageSafetyLevel:
            assert level.value is not None
