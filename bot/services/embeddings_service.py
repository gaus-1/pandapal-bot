"""
Сервис эмбеддингов для векторного поиска.

Использует Yandex Embeddings API (text-search-doc, text-search-query).
"""

from loguru import logger

from bot.services.yandex_cloud_service import get_yandex_cloud_service


class EmbeddingService:
    """Сервис эмбеддингов через Yandex Cloud API."""

    def __init__(self):
        self._yandex = get_yandex_cloud_service()

    async def embed_query(self, text: str) -> list[float] | None:
        """Эмбеддинг для поискового запроса."""
        return await self._yandex.get_embedding(text, text_type="query")

    async def embed_document(self, text: str) -> list[float] | None:
        """Эмбеддинг для документа."""
        return await self._yandex.get_embedding(text, text_type="doc")

    async def get_embedding(self, text: str, text_type: str = "doc") -> list[float] | None:
        """Получить эмбеддинг текста (doc или query)."""
        return await self._yandex.get_embedding(text, text_type=text_type)


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Синглтон EmbeddingService."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        logger.info("✅ EmbeddingService инициализирован")
    return _embedding_service
