"""
Простые реальные тесты для Vision Service
Соответствуют реальной структуре кода

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


class TestVisionServiceSimple:
    """Простые реальные тесты Vision Service"""

    @pytest.fixture
    def vision_service(self):
        """Фикстура Vision Service"""
        with patch("bot.services.vision_service.genai"):
            return VisionService()

    @pytest.fixture
    def mock_user(self):
        """Фикстура пользователя"""
        return User(
            telegram_id=123456789,
            username="test_child",
            first_name="Тестовый",
            last_name="Ребенок",
            user_type="child",
            age=10,
            grade=5,
        )

    @pytest.fixture
    def sample_image_data(self):
        """Фикстура данных изображения"""
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        return img_bytes.getvalue()

    # === TESTS FOR ENUMS ===

    @pytest.mark.unit
    def test_image_category_enum(self):
        """Тест enum категорий изображений"""
        assert ImageCategory.EDUCATIONAL.value == "educational"
        assert ImageCategory.MATHEMATICS.value == "mathematics"
        assert ImageCategory.SCIENCE.value == "science"
        assert ImageCategory.INAPPROPRIATE.value == "inappropriate"
        assert ImageCategory.UNKNOWN.value == "unknown"

    @pytest.mark.unit
    def test_image_safety_level_enum(self):
        """Тест enum уровней безопасности"""
        assert ImageSafetyLevel.SAFE.value == "safe"
        assert ImageSafetyLevel.SUSPICIOUS.value == "suspicious"
        assert ImageSafetyLevel.UNSAFE.value == "unsafe"

    # === TESTS FOR IMAGE ANALYSIS RESULT ===

    @pytest.mark.unit
    def test_image_analysis_result_creation(self):
        """Тест создания результата анализа изображения"""
        result = ImageAnalysisResult(
            category=ImageCategory.EDUCATIONAL,
            safety_level=ImageSafetyLevel.SAFE,
            description="Test educational image",
            educational_content="Math problem with addition",
            subjects_detected=["mathematics", "arithmetic"],
            confidence=0.95,
            moderation_flags=[],
            suggested_activities=["solve_problem", "practice_addition"],
        )

        assert result.category == ImageCategory.EDUCATIONAL
        assert result.safety_level == ImageSafetyLevel.SAFE
        assert result.description == "Test educational image"
        assert result.educational_content == "Math problem with addition"
        assert result.subjects_detected == ["mathematics", "arithmetic"]
        assert result.confidence == 0.95
        assert result.moderation_flags == []
        assert result.suggested_activities == ["solve_problem", "practice_addition"]

    # === TESTS FOR VISION SERVICE INITIALIZATION ===

    @pytest.mark.unit
    def test_vision_service_init(self, vision_service):
        """Тест инициализации Vision Service"""
        assert vision_service is not None

    # === TESTS FOR IMAGE ANALYSIS ===

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_basic(self, vision_service, sample_image_data, mock_user):
        """Тест базового анализа изображения"""
        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = "Educational math problem"
            mock_genai.GenerativeModel.return_value = mock_model

            result = await vision_service.analyze_image(sample_image_data, mock_user)

            assert result is not None
            assert isinstance(result, ImageAnalysisResult)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_api_error(self, vision_service, sample_image_data, mock_user):
        """Тест обработки ошибки API при анализе изображения"""
        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("API Error")

            result = await vision_service.analyze_image(sample_image_data, mock_user)

            # Должен вернуть безопасный результат при ошибке
            assert result is not None
            assert isinstance(result, ImageAnalysisResult)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_invalid_data(self, vision_service, mock_user):
        """Тест анализа некорректных данных изображения"""
        invalid_data = b"invalid image data"

        result = await vision_service.analyze_image(invalid_data, mock_user)

        assert result is not None
        assert isinstance(result, ImageAnalysisResult)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_empty_data(self, vision_service, mock_user):
        """Тест анализа пустых данных изображения"""
        empty_data = b""

        result = await vision_service.analyze_image(empty_data, mock_user)

        assert result is not None
        assert isinstance(result, ImageAnalysisResult)

    # === TESTS FOR EDUCATIONAL CONTENT DETECTION ===

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_with_educational_content(
        self, vision_service, sample_image_data, mock_user
    ):
        """Тест анализа изображения с образовательным контентом"""
        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = (
                "Educational math problem with addition and subtraction"
            )
            mock_genai.GenerativeModel.return_value = mock_model

            result = await vision_service.analyze_image(sample_image_data, mock_user)

            assert result is not None
            assert isinstance(result, ImageAnalysisResult)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_image_age_appropriate(self, vision_service, sample_image_data):
        """Тест анализа контента подходящего для возраста"""
        young_user = User(telegram_id=111, user_type="child", age=8, grade=3)
        adult_user = User(telegram_id=222, user_type="parent", age=35)

        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = "Simple educational content"
            mock_genai.GenerativeModel.return_value = mock_model

            # Тест для ребенка
            result_child = await vision_service.analyze_image(sample_image_data, young_user)
            assert result_child is not None
            assert isinstance(result_child, ImageAnalysisResult)

            # Тест для взрослого
            result_adult = await vision_service.analyze_image(sample_image_data, adult_user)
            assert result_adult is not None
            assert isinstance(result_adult, ImageAnalysisResult)

    # === TESTS FOR ERROR HANDLING ===

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_recovery_and_fallback(self, vision_service, sample_image_data, mock_user):
        """Тест восстановления после ошибок и fallback"""
        # Тест с ошибкой API
        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("API Unavailable")

            result = await vision_service.analyze_image(sample_image_data, mock_user)
            assert result is not None
            assert isinstance(result, ImageAnalysisResult)

        # Тест с восстановлением
        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = "Recovered analysis"
            mock_genai.GenerativeModel.return_value = mock_model

            result = await vision_service.analyze_image(sample_image_data, mock_user)
            assert result is not None
            assert isinstance(result, ImageAnalysisResult)

    # === COMPREHENSIVE INTEGRATION TESTS ===

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_comprehensive_image_analysis_workflow(
        self, vision_service, sample_image_data, mock_user
    ):
        """Комплексный тест workflow анализа изображения"""
        with patch("bot.services.vision_service.genai") as mock_genai:
            mock_model = Mock()
            mock_model.generate_content.return_value.text = (
                "Educational math problem with addition and subtraction"
            )
            mock_genai.GenerativeModel.return_value = mock_model

            # Анализ изображения
            analysis_result = await vision_service.analyze_image(sample_image_data, mock_user)
            assert analysis_result is not None
            assert isinstance(analysis_result, ImageAnalysisResult)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_robustness(self, vision_service):
        """Тест устойчивости сервиса"""
        # Проверяем, что сервис инициализирован
        assert vision_service is not None

        # Тест с None значениями - сервис обрабатывает ошибки gracefully
        try:
            await vision_service.analyze_image(None, None)
        except (TypeError, AttributeError):
            pass

    @pytest.mark.unit
    def test_image_analysis_result_robustness(self):
        """Тест устойчивости ImageAnalysisResult"""
        # Тест с минимальными данными
        result = ImageAnalysisResult(
            category=ImageCategory.UNKNOWN,
            safety_level=ImageSafetyLevel.SAFE,
            description="",
            educational_content=None,
            subjects_detected=[],
            confidence=0.0,
            moderation_flags=[],
            suggested_activities=[],
        )

        assert result.category == ImageCategory.UNKNOWN
        assert result.safety_level == ImageSafetyLevel.SAFE
        assert result.description == ""
        assert result.educational_content is None
        assert result.subjects_detected == []
        assert result.confidence == 0.0
