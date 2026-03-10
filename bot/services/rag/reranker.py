"""Result reranking для улучшения качества RAG."""

import re
from datetime import UTC, datetime


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
        """Рассчитать текстовую релевантность (упрощенный BM25 + биграммы)."""
        query_terms = set(query.lower().split())

        # Объединяем title и content для поиска
        text = f"{getattr(result, 'title', '')} {getattr(result, 'content', '')}".lower()

        if not text:
            return 0.0

        # Подсчет совпадений (unigrams)
        matches = sum(1 for term in query_terms if term in text)

        # Нормализация
        relevance = matches / len(query_terms) if query_terms else 0.0

        # Бонус за точное совпадение фразы
        if query.lower() in text:
            relevance += 0.3

        # Бонус за совпадение биграмм (пары слов): «теорема Пифагора» > «Пифагор на теореме»
        query_words = query.lower().split()
        if len(query_words) >= 2:
            bigram_matches = 0
            total_bigrams = len(query_words) - 1
            for i in range(total_bigrams):
                bigram = f"{query_words[i]} {query_words[i + 1]}"
                if bigram in text:
                    bigram_matches += 1
            if total_bigrams > 0:
                relevance += 0.2 * (bigram_matches / total_bigrams)

        return min(relevance, 1.0)

    def _calculate_age_match(self, result, user_age: int | None) -> float:
        """Рассчитать соответствие возрасту по сложности контента."""
        if not user_age:
            return 0.5  # Нейтральный score

        content = getattr(result, "content", "")
        if not content:
            return 0.5

        # Эвристика сложности контента по объективным признакам:
        # 1. Средняя длина предложения (длинные = сложнее)
        sentences = [s.strip() for s in re.split(r"[.!?]+\s+", content) if s.strip()]
        avg_sentence_len = (
            sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 10
        )

        # 2. Наличие формул/цифр (больше = сложнее)
        formula_density = len(re.findall(r"[=+\-×÷√∑∫²³⁴⁵⁶⁷⁸⁹°]", content)) / max(len(content), 1)

        # 3. Наличие научных/технических терминов
        technical_terms = len(
            re.findall(
                r"(?:теорема|уравнение|функция|производная|интеграл|коэффициент|"
                r"алгоритм|молекула|атом|ион|реакция|вектор|матрица)",
                content.lower(),
            )
        )

        # Нормализация сложности контента к 0-1
        complexity = min(
            (avg_sentence_len / 25) * 0.4  # Длина предложений (макс при 25 слов)
            + formula_density * 200 * 0.3  # Плотность формул
            + min(technical_terms / 3, 1.0) * 0.3,  # Технические термины
            1.0,
        )

        # Соответствие возрасту: user_age нормализуем к 0-1
        age_complexity = user_age / 18.0
        match = 1.0 - abs(age_complexity - complexity)
        return max(match, 0.1)

    def _calculate_recency(self, result) -> float:
        """Рассчитать актуальность по времени (extracted_at или timestamp)."""
        ts = getattr(result, "extracted_at", None) or getattr(result, "timestamp", None)
        if not ts:
            return 0.5  # Нейтральный score

        try:
            if not isinstance(ts, datetime):
                return 0.5
            # Naive datetime трактуем как UTC для вычитания
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            now_utc = datetime.now(UTC)
            age_days = (now_utc - ts).days
            # Экспоненциальное затухание: свежие = 1.0, старые = 0.0. Полураспад: 180 дней
            recency = 2 ** (-age_days / 180)
            return min(max(recency, 0.0), 1.0)
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
