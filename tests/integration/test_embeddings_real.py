"""
Тесты EmbeddingService с реальным Yandex Embeddings API.

Требует YANDEX_CLOUD_API_KEY и YANDEX_CLOUD_FOLDER_ID в env.
Запуск: pytest tests/integration/test_embeddings_real.py -v
"""

import os

import pytest

from bot.services.embeddings_service import get_embedding_service


def _has_real_embeddings_api():
    k = os.getenv("YANDEX_CLOUD_API_KEY", "") or ""
    return k and k not in ("test_api_key", "AQVTEST_KEY_FOR_CI") and len(k) > 20


@pytest.mark.integration
@pytest.mark.skipif(not _has_real_embeddings_api(), reason="Требуется реальный Yandex API ключ")
class TestEmbeddingsReal:
    """Тесты EmbeddingService с реальным API."""

    @pytest.mark.asyncio
    async def test_embed_query_returns_vector(self):
        """embed_query возвращает непустой вектор."""
        svc = get_embedding_service()
        vec = await svc.embed_query("таблица умножения")
        assert vec is not None
        assert len(vec) > 0
        assert all(isinstance(x, float) for x in vec)

    @pytest.mark.asyncio
    async def test_embed_document_returns_vector(self):
        """embed_document возвращает непустой вектор."""
        svc = get_embedding_service()
        vec = await svc.embed_document("Квадратный корень из числа n — это такое число x, что x² = n.")
        assert vec is not None
        assert len(vec) > 0

    @pytest.mark.asyncio
    async def test_different_texts_different_vectors(self):
        """Разные тексты дают разные векторы."""
        svc = get_embedding_service()
        v1 = await svc.embed_query("таблица умножения")
        v2 = await svc.embed_query("таблица квадратных корней")
        assert v1 is not None and v2 is not None
        assert v1 != v2
