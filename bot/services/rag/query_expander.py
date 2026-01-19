"""Query expansion для улучшения RAG поиска."""

import re


class QueryExpander:
    """Расширение поисковых запросов синонимами и связанными терминами."""

    def __init__(self):
        # Синонимы для школьных предметов и терминов
        self.synonyms = {
            # Математика
            "умножение": ["произведение", "умножить", "перемножение"],
            "деление": ["частное", "разделить", "делимое"],
            "сложение": ["сумма", "прибавить", "слагаемое"],
            "вычитание": ["разность", "отнять", "уменьшаемое"],
            "уравнение": ["равенство", "решить", "найти x"],
            "график": ["диаграмма", "кривая", "функция"],
            # Русский язык
            "глагол": ["действие", "что делать", "спряжение"],
            "существительное": ["предмет", "кто что", "склонение"],
            "прилагательное": ["признак", "какой", "согласование"],
            # История
            "война": ["битва", "сражение", "конфликт"],
            "реформа": ["изменение", "преобразование", "перемены"],
            # География
            "океан": ["море", "водное пространство", "акватория"],
            "материк": ["континент", "суша", "часть света"],
        }

        # Связанные темы
        self.related_terms = {
            "таблица умножения": ["арифметика", "математика", "счет"],
            "синус": ["тригонометрия", "угол", "треугольник"],
            "фотосинтез": ["биология", "растения", "хлорофилл"],
            "падежи": ["русский язык", "склонение", "грамматика"],
        }

    def expand(self, query: str, max_additions: int = 3) -> str:
        """
        Расширить запрос синонимами и связанными терминами.

        Args:
            query: Исходный запрос
            max_additions: Максимум дополнительных терминов

        Returns:
            Расширенный запрос
        """
        query_lower = query.lower()
        additions = []

        # Добавляем синонимы
        for term, syns in self.synonyms.items():
            if term in query_lower and len(additions) < max_additions:
                additions.append(syns[0])  # Добавляем первый синоним

        # Добавляем связанные термины
        for term, related in self.related_terms.items():
            if term in query_lower and len(additions) < max_additions:
                additions.extend(related[: max_additions - len(additions)])

        if additions:
            return f"{query} {' '.join(additions[:max_additions])}"
        return query

    def generate_variations(self, query: str) -> list[str]:
        """
        Генерировать вариации запроса для multi-query RAG.

        Args:
            query: Исходный запрос

        Returns:
            Список вариаций запроса
        """
        variations = [query]

        # Вариация 1: Расширенный запрос
        expanded = self.expand(query)
        if expanded != query:
            variations.append(expanded)

        # Вариация 2: Извлечь ключевые слова
        keywords = self._extract_keywords(query)
        if keywords and keywords != query:
            variations.append(" ".join(keywords))

        # Вариация 3: Формализованный вопрос
        formal = self._formalize_question(query)
        if formal and formal != query:
            variations.append(formal)

        return variations[:3]  # Максимум 3 вариации

    def _extract_keywords(self, query: str) -> list[str]:
        """Извлечь ключевые слова из запроса."""
        # Удаляем стоп-слова
        stop_words = {
            "что",
            "как",
            "где",
            "когда",
            "почему",
            "зачем",
            "это",
            "такое",
            "мне",
            "нужно",
            "помоги",
            "расскажи",
            "объясни",
        }

        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords

    def _formalize_question(self, query: str) -> str:
        """Преобразовать в формальный вопрос."""
        query_lower = query.lower()

        # Паттерны формализации
        patterns = [
            (r"что такое (.+)", r"\1 определение"),
            (r"как решить (.+)", r"\1 решение"),
            (r"расскажи про (.+)", r"\1 информация"),
            (r"объясни (.+)", r"\1 объяснение"),
        ]

        for pattern, replacement in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return re.sub(pattern, replacement, query_lower)

        return query
