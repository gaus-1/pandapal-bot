"""
Интеграционные тесты мотивационного тона панды с реальным API.

Проверяет ответы на реплики «не буду решать» / «не хочу»:
структура сохранена, тон мотивирующий (ирония/по шагам).
"""

import os

import pytest


def _check_real_api_key():
    """Проверяет наличие реального API ключа."""
    env_key = os.environ.get("YANDEX_CLOUD_API_KEY", "")
    if env_key and env_key != "test_api_key" and len(env_key) > 20:
        return True
    try:
        from bot.config.settings import settings

        key = settings.yandex_cloud_api_key
        if key and key not in ("test_api_key", "your_real_yandex_api_key_here") and len(key) > 20:
            return True
    except Exception:
        pass
    return False


REAL_API_KEY_AVAILABLE = _check_real_api_key()


@pytest.mark.integration
@pytest.mark.slow
class TestPandaMotivationReal:
    """Тесты мотивационного тона с реальным Yandex API."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_motivation_response_structured(self):
        """На «Не буду это решать» ответ структурирован и мотивирующий."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()
        response = await ai_service.generate_response(
            user_message="Не буду это решать.",
            chat_history=[],
            user_age=11,
        )
        assert response is not None
        assert len(response) > 20
        # Структура: абзацы или списки
        has_structure = "\n\n" in response or "\n-" in response or "1." in response
        assert has_structure, f"Ответ без структуры: {response[:200]}"
        # Мотивация/ирония/призыв
        low = response.lower()
        has_motivation = (
            "разбер" in low or "шаг" in low or "панда" in low or "передума" in low or "давай" in low
        )
        assert has_motivation, f"Нет мотивирующего тона: {response[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not REAL_API_KEY_AVAILABLE, reason="Требуется реальный Yandex API ключ")
    async def test_motivation_response_no_plain_wall(self):
        """Ответ не сплошной текст без разбивки (грамматика, предложения)."""
        from bot.services.ai_service_solid import get_ai_service

        ai_service = get_ai_service()
        response = await ai_service.generate_response(
            user_message="Не хочу, скучно.",
            chat_history=[],
            user_age=10,
        )
        assert response is not None
        sentences = [
            s.strip() for s in response.replace("!", ".").replace("?", ".").split(".") if s.strip()
        ]
        assert len(sentences) >= 1, "Ответ должен содержать законченные предложения"
        assert "?" in response or "." in response, "Знаки препинания обязательны"
