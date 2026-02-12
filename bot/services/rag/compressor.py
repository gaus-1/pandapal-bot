"""Context compression для RAG."""

import re

_LIST_TABLE_PATTERNS = frozenset(
    {"список", "таблица", "таблиц", "значений", "значения", "перечень"}
)


class ContextCompressor:
    """Сжатие контекста для уменьшения токенов в промпте."""

    def compress(
        self,
        context: str,
        question: str,
        max_sentences: int = 5,
    ) -> str:
        """
        Сжать контекст, оставив только релевантные части.

        Args:
            context: Полный контекст
            question: Вопрос пользователя
            max_sentences: Максимум предложений

        Returns:
            Сжатый контекст
        """
        if not context:
            return ""

        # Для запросов списка/таблицы — не сжимать, чтобы не потерять перечисления
        q_words = set(question.lower().split())
        if q_words & _LIST_TABLE_PATTERNS:
            return context

        # Разбиваем на предложения
        sentences = self._split_sentences(context)

        # Ранжируем по релевантности к вопросу
        scored_sentences = [(sent, self._sentence_relevance(sent, question)) for sent in sentences]

        # Сортируем и берем топ-K
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:max_sentences]]

        # Восстанавливаем порядок
        top_sentences.sort(key=lambda s: sentences.index(s))

        return " ".join(top_sentences)

    def _split_sentences(self, text: str) -> list[str]:
        """Разбить текст на предложения."""
        # Простое разбиение по знакам препинания
        sentences = re.split(r"[.!?]+\s+", text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    def _sentence_relevance(self, sentence: str, question: str) -> float:
        """Рассчитать релевантность предложения к вопросу."""
        sentence_lower = sentence.lower()
        question_lower = question.lower()

        # Извлекаем ключевые слова из вопроса
        question_words = set(question_lower.split())
        sentence_words = set(sentence_lower.split())

        # Подсчет совпадений
        matches = question_words & sentence_words
        if not question_words:
            return 0.0

        relevance = len(matches) / len(question_words)

        # Бонус за числовые паттерны (√, ≈, цифры) при запросах корней/таблиц
        if re.search(r"(?:√|≈|\d+[,.]?\d*)", sentence) and re.search(
            r"(?:корн|таблиц|значен)", question_lower
        ):
            relevance += 0.3

        # Бонус за длину предложения (больше информации)
        length_bonus = min(len(sentence) / 200, 0.2)  # Макс 0.2

        return relevance + length_bonus
