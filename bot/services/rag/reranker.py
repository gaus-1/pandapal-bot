"""Result reranking для улучшения качества RAG."""

from datetime import datetime


class ResultReranker:
    """Переранжирование результатов поиска по релевантности."""

    def __init__(self):
        # Веса для разных факторов ранжирования
        self.weights = {
            "relevance": 0.4,  # Текстовая релевантность
            "age_match": 0.3,  # Соответствие возрасту
            "recency": 0.2,  # Актуальность по времени
            "source_quality": 0.1,  # Качество источника
        }

    def rerank(
        self,
        query: str,
        results: list,
        user_age: int | None = None,
        top_k: int = 3,
    ) -> list:
        """
        Переранжировать результаты.

        Args:
            query: Поисковый запрос
            results: Список результатов (должны иметь атрибуты: content, title)
            user_age: Возраст пользователя
            top_k: Количество результатов для возврата

        Returns:
            Топ-K переранжированных результатов
        """
        if not results:
            return []

        scored_results = []
        for result in results:
            score = self._calculate_score(query, result, user_age)
            scored_results.append((result, score))

        # Сортировка по убыванию score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return [r[0] for r in scored_results[:top_k]]

    def _calculate_score(self, query: str, result, user_age: int | None) -> float:
        """Рассчитать итоговый score для результата."""
        scores = {}

        # 1. Текстовая релевантность (BM25-like)
        scores["relevance"] = self._calculate_relevance(query, result)

        # 2. Соответствие возрасту
        scores["age_match"] = self._calculate_age_match(result, user_age)

        # 3. Актуальность (если есть timestamp)
        scores["recency"] = self._calculate_recency(result)

        # 4. Качество источника
        scores["source_quality"] = self._calculate_source_quality(result)

        # Взвешенная сумма
        total_score = sum(scores[k] * self.weights[k] for k in scores)
        return total_score

    def _calculate_relevance(self, query: str, result) -> float:
        """Рассчитать текстовую релевантность (упрощенный BM25)."""
        query_terms = set(query.lower().split())

        # Объединяем title и content для поиска
        text = f"{getattr(result, 'title', '')} {getattr(result, 'content', '')}".lower()

        if not text:
            return 0.0

        # Подсчет совпадений
        matches = sum(1 for term in query_terms if term in text)

        # Нормализация
        relevance = matches / len(query_terms) if query_terms else 0.0

        # Бонус за точное совпадение фразы
        if query.lower() in text:
            relevance += 0.3

        return min(relevance, 1.0)

    def _calculate_age_match(self, result, user_age: int | None) -> float:
        """Рассчитать соответствие возрасту."""
        if not user_age:
            return 0.5  # Нейтральный score

        # Проверяем метаданные о сложности контента
        content = getattr(result, "content", "")

        # Простая эвристика: ищем индикаторы сложности
        complexity_indicators = {
            "простой": 0.2,
            "базовый": 0.3,
            "средний": 0.5,
            "сложный": 0.7,
            "продвинутый": 0.9,
        }

        for indicator, complexity in complexity_indicators.items():
            if indicator in content.lower():
                # Соответствие возрасту: чем ближе, тем лучше
                age_complexity = user_age / 18.0  # Нормализация к 0-1
                match = 1.0 - abs(age_complexity - complexity)
                return max(match, 0.0)

        return 0.5  # По умолчанию

    def _calculate_recency(self, result) -> float:
        """Рассчитать актуальность по времени."""
        # Если есть timestamp, используем его
        timestamp = getattr(result, "timestamp", None)
        if not timestamp:
            return 0.5  # Нейтральный score

        try:
            # Рассчитываем давность (в днях)
            if isinstance(timestamp, datetime):
                age_days = (datetime.now() - timestamp).days
            else:
                return 0.5

            # Экспоненциальное затухание: свежие = 1.0, старые = 0.0
            # Полураспад: 180 дней
            recency = 2 ** (-age_days / 180)
            return recency

        except Exception:
            return 0.5

    def _calculate_source_quality(self, result) -> float:
        """Рассчитать качество источника."""
        source_url = getattr(result, "source_url", "")

        # Качественные образовательные источники
        quality_domains = {
            "wikipedia.org": 1.0,
            "nsportal.ru": 0.9,
            "school203.ru": 0.9,
            "edu.ru": 0.8,
            "uchi.ru": 0.8,
            ".gov": 0.7,
        }

        for domain, quality in quality_domains.items():
            if domain in source_url.lower():
                return quality

        return 0.5  # По умолчанию средний
