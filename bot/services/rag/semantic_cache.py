"""Semantic cache для RAG системы."""

from datetime import datetime, timedelta


class SemanticCache:
    """
    Кэш с семантическим поиском.

    Вместо точного совпадения использует similarity для нахождения похожих запросов.
    """

    def __init__(self, ttl_hours: int = 24):
        """
        Args:
            ttl_hours: TTL для кэша в часах
        """
        self.cache: list[dict] = []  # [(query, result, timestamp)]
        self.ttl = timedelta(hours=ttl_hours)
        self.max_size = 1000

    def get(self, query: str, threshold: float = 0.85) -> str | None:
        """
        Получить результат из кэша для похожего запроса.

        Args:
            query: Поисковый запрос
            threshold: Порог similarity (0-1)

        Returns:
            Кэшированный результат или None
        """
        # Очистка устаревших записей
        self._cleanup_expired()

        query_lower = query.lower()
        best_match = None
        best_similarity = 0.0

        for entry in self.cache:
            cached_query = entry["query"]

            # Упрощенная similarity (Jaccard)
            similarity = self._calculate_similarity(query_lower, cached_query)

            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = entry

        if best_match:
            return best_match["result"]

        return None

    def set(self, query: str, result: str):
        """
        Сохранить результат в кэш.

        Args:
            query: Поисковый запрос
            result: Результат
        """
        # Проверка размера кэша
        if len(self.cache) >= self.max_size:
            # Удаляем самую старую запись
            self.cache.pop(0)

        entry = {
            "query": query.lower(),
            "result": result,
            "timestamp": datetime.now(),
        }

        self.cache.append(entry)

    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """
        Рассчитать Jaccard similarity между двумя запросами.

        Args:
            query1: Первый запрос
            query2: Второй запрос

        Returns:
            Similarity score (0-1)
        """
        # Токенизация
        tokens1 = set(query1.split())
        tokens2 = set(query2.split())

        if not tokens1 or not tokens2:
            return 0.0

        # Jaccard similarity
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union) if union else 0.0

    def _cleanup_expired(self):
        """Удалить устаревшие записи из кэша."""
        now = datetime.now()
        self.cache = [entry for entry in self.cache if now - entry["timestamp"] < self.ttl]

    def clear(self):
        """Очистить весь кэш."""
        self.cache.clear()

    def stats(self) -> dict:
        """Получить статистику кэша."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_hours": self.ttl.total_seconds() / 3600,
        }
