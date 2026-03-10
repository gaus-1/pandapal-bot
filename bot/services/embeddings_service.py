"""
Сервис эмбеддингов для векторного поиска.

Использует Yandex Embeddings API (text-search-doc, text-search-query).
"""

from loguru import logger

from bot.services.yandex_cloud_service import get_yandex_cloud_service


def _normalize_text(text: str) -> str:
    """Нормализация: схлопнуть пробелы."""
    return " ".join(text.split())


def _truncate_on_word_boundary(text: str, max_len: int) -> str:
    """Обрезать текст по границе слова, не разрывая слова посередине."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    last_space = cut.rfind(" ")
    return cut[:last_space] if last_space > 0 else cut


class EmbeddingService:
    """Сервис эмбеддингов через Yandex Cloud API."""

    MAX_TEXT_LENGTH = 7000  # Yandex limit 8000, оставляем запас

    def __init__(self):
        self._yandex = get_yandex_cloud_service()

    async def embed_query(self, text: str) -> list[float] | None:
        """Эмбеддинг для поискового запроса."""
        normalized = _normalize_text(text)
        if len(normalized) > self.MAX_TEXT_LENGTH:
            normalized = _truncate_on_word_boundary(normalized, self.MAX_TEXT_LENGTH)
        return await self._yandex.get_embedding(normalized, text_type="query")

    async def embed_document(self, text: str) -> list[float] | None:
        """Эмбеддинг для документа."""
        normalized = _normalize_text(text)
        if len(normalized) > self.MAX_TEXT_LENGTH:
            normalized = _truncate_on_word_boundary(normalized, self.MAX_TEXT_LENGTH)
        return await self._yandex.get_embedding(normalized, text_type="doc")

    async def get_embedding(self, text: str, text_type: str = "doc") -> list[float] | None:
        """Получить эмбеддинг текста (doc или query)."""
        normalized = _normalize_text(text)
        if len(normalized) > self.MAX_TEXT_LENGTH:
            normalized = _truncate_on_word_boundary(normalized, self.MAX_TEXT_LENGTH)
        return await self._yandex.get_embedding(normalized, text_type=text_type)


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Синглтон EmbeddingService."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        logger.info("✅ EmbeddingService инициализирован")
    return _embedding_service
