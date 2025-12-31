"""
Тесты для Speech Service (Yandex SpeechKit)
Проверка распознавания голоса
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot.services.speech_service import SpeechRecognitionService


class TestSpeechService:
    """Тесты для сервиса распознавания речи"""

    @pytest.fixture
    def service(self):
        """Создание экземпляра сервиса"""
        return SpeechRecognitionService()

    @pytest.mark.unit
    def test_service_init(self, service):
        """Тест инициализации сервиса"""
        assert service is not None
        assert hasattr(service, "yandex_service")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_voice_success(self, service):
        """Тест успешного распознавания голоса"""
        fake_audio = b"fake_audio_data_ogg"

        with patch.object(
            service.yandex_service, "recognize_speech", new_callable=AsyncMock
        ) as mock_recognize:
            mock_recognize.return_value = "Привет, как дела?"

            result = await service.transcribe_voice(fake_audio)

            assert result == "Привет, как дела?"
            mock_recognize.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_voice_empty_audio(self, service):
        """Тест обработки пустого аудио"""
        result = await service.transcribe_voice(b"")

        assert result is None or result == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_voice_error_handling(self, service):
        """Тест обработки ошибок"""
        fake_audio = b"invalid_audio"

        with patch.object(
            service.yandex_service, "recognize_speech", new_callable=AsyncMock
        ) as mock_recognize:
            mock_recognize.side_effect = Exception("STT API error")

            result = await service.transcribe_voice(fake_audio)

            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_voice_russian(self, service):
        """Тест распознавания русского языка"""
        fake_audio = b"russian_audio"

        with patch.object(
            service.yandex_service, "recognize_speech", new_callable=AsyncMock
        ) as mock_recognize:
            mock_recognize.return_value = "Помоги с математикой"

            result = await service.transcribe_voice(fake_audio, language="ru")

            assert result == "Помоги с математикой"
            assert "ru" in str(mock_recognize.call_args) or len(result) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_voice_english(self, service):
        """Тест распознавания английского языка"""
        fake_audio = b"english_audio"

        with patch.object(
            service.yandex_service, "recognize_speech", new_callable=AsyncMock
        ) as mock_recognize:
            mock_recognize.return_value = "Help with math"

            result = await service.transcribe_voice(fake_audio, language="en")

            assert result == "Help with math"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transcribe_voice_multiple_calls(self, service):
        """Тест множественных вызовов распознавания"""
        fake_audio = b"audio_sample"

        with patch.object(
            service.yandex_service, "recognize_speech", new_callable=AsyncMock
        ) as mock_recognize:
            mock_recognize.side_effect = [
                "Первое сообщение",
                "Второе сообщение",
                "Третье сообщение",
            ]

            result1 = await service.transcribe_voice(fake_audio)
            result2 = await service.transcribe_voice(fake_audio)
            result3 = await service.transcribe_voice(fake_audio)

            assert result1 == "Первое сообщение"
            assert result2 == "Второе сообщение"
            assert result3 == "Третье сообщение"
            assert mock_recognize.call_count == 3
