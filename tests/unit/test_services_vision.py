"""
Comprehensive tests for Vision Service
"""

import io
from unittest.mock import AsyncMock, Mock, patch

import pytest
from PIL import Image

from bot.models import User
from bot.services.vision_service import (
    ImageAnalysisResult,
    ImageCategory,
    ImageSafetyLevel,
    VisionService,
)


class TestVisionService:

    @pytest.fixture
    def service(self):
        with patch("bot.services.vision_service.genai"):
            return VisionService()

    @pytest.fixture
    def sample_image(self):
        img = Image.new("RGB", (100, 100), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        return buf.getvalue()

    @pytest.fixture
    def mock_user(self):
        return User(telegram_id=123, age=10, grade=5, user_type="child")

    @pytest.mark.unit
    def test_service_init(self, service):
        assert service is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image(self, service, sample_image, mock_user):
        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = "Math problem"
            mock_genai.GenerativeModel.return_value = mock_model

            result = await service.analyze_image(sample_image, mock_user)
            assert isinstance(result, ImageAnalysisResult)

    @pytest.mark.unit
    def test_image_category_enum_values(self):
        assert ImageCategory.EDUCATIONAL.value == "educational"
        assert ImageCategory.MATHEMATICS.value == "mathematics"
        assert ImageCategory.SCIENCE.value == "science"
        assert ImageCategory.HISTORY.value == "history"
        assert ImageCategory.ART.value == "art"
        assert ImageCategory.TEXT.value == "text"
        assert ImageCategory.DIAGRAM.value == "diagram"
        assert ImageCategory.CHART.value == "chart"
        assert ImageCategory.PHOTO.value == "photo"
        assert ImageCategory.DRAWING.value == "drawing"
        assert ImageCategory.INAPPROPRIATE.value == "inappropriate"
        assert ImageCategory.UNKNOWN.value == "unknown"

    @pytest.mark.unit
    def test_image_safety_level_enum_values(self):
        assert ImageSafetyLevel.SAFE.value == "safe"
        assert ImageSafetyLevel.SUSPICIOUS.value == "suspicious"
        assert ImageSafetyLevel.UNSAFE.value == "unsafe"

    @pytest.mark.unit
    def test_image_analysis_result_structure(self):
        result = ImageAnalysisResult(
            category=ImageCategory.EDUCATIONAL,
            safety_level=ImageSafetyLevel.SAFE,
            description="Test",
            educational_content="Math",
            subjects_detected=["math"],
            confidence=0.95,
            moderation_flags=[],
            suggested_activities=[],
        )
        assert result.category == ImageCategory.EDUCATIONAL
        assert result.safety_level == ImageSafetyLevel.SAFE

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_error_handling(self, service, mock_user):
        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("API error")

            result = await service.analyze_image(b"invalid", mock_user)
            assert isinstance(result, ImageAnalysisResult)
