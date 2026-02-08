"""
Сервис объяснения взрослых тем простыми словами для детей.

Объясняет сложные жизненные темы, которые взрослые часто не объясняют детям:
- Финансы (деньги, кредит, ипотека, налоги, банки)
- Дом и быт (ЖКУ, ремонт, страхование)
- Технологии (интернет, связь, облака, подписки)
- Документы (паспорт, договоры, штрафы)
- Работа (зарплата, карьера, собеседование)
- Здоровье (ОМС, врачи, аптечки, лекарства)
- Сложные темы (обязательства, эмоции взрослых, планирование)
"""

from loguru import logger

from bot.config.adult_topics_data import ADULT_TOPICS_DATA


class AdultTopicExplanation:
    """Объяснение одной взрослой темы."""

    def __init__(
        self,
        topic_id: str,
        keywords: list[str],
        title: str,
        explanation: str,
        examples: list[str] | None = None,
        related_topics: list[str] | None = None,
    ):
        """
        Инициализация объяснения темы.

        Args:
            topic_id: Уникальный ID темы
            keywords: Ключевые слова для детекции (в нижнем регистре)
            title: Название темы
            explanation: Простое объяснение для детей
            examples: Примеры из жизни
            related_topics: Связанные темы (topic_id)
        """
        self.topic_id = topic_id
        self.keywords = [kw.lower() for kw in keywords]
        self.title = title
        self.explanation = explanation
        self.examples = examples or []
        self.related_topics = related_topics or []


class AdultTopicsService:
    """
    Сервис объяснения взрослых тем детям простыми словами.

    Данные тем загружаются из bot.config.adult_topics_data (SRP).
    Логика сервиса: детекция, поиск, форматирование.
    """

    def __init__(self):
        """Инициализация сервиса с базой знаний."""
        self.topics: dict[str, AdultTopicExplanation] = {}
        self._init_topics()
        logger.info(f"AdultTopicsService инициализирован: {len(self.topics)} тем")

    def _init_topics(self):
        """Загрузка тем из конфигурации."""
        for topic_data in ADULT_TOPICS_DATA:
            self._add_topic(
                AdultTopicExplanation(
                    topic_id=topic_data["topic_id"],
                    keywords=topic_data["keywords"],
                    title=topic_data["title"],
                    explanation=topic_data["explanation"],
                    examples=topic_data.get("examples"),
                    related_topics=topic_data.get("related_topics"),
                )
            )

    def _add_topic(self, topic: AdultTopicExplanation):
        """Добавить тему в базу знаний."""
        self.topics[topic.topic_id] = topic

    def detect_topic(self, user_message: str) -> AdultTopicExplanation | None:
        """
        Определить, спрашивает ли пользователь про взрослую тему.

        Args:
            user_message: Сообщение пользователя

        Returns:
            AdultTopicExplanation если тема найдена, иначе None
        """
        user_message_lower = user_message.lower()

        # Ищем тему с максимальным количеством совпадений ключевых слов
        best_match = None
        max_matches = 0

        for topic in self.topics.values():
            matches = sum(1 for keyword in topic.keywords if keyword in user_message_lower)
            if matches > max_matches:
                max_matches = matches
                best_match = topic

        if best_match:
            logger.info(f"📚 Обнаружена взрослая тема: {best_match.title}")
            return best_match

        return None

    def try_get_adult_topic_response(self, user_message: str) -> str | None:
        """
        Если сообщение про взрослую тему (ЖКУ, банки и т.д.) — вернуть готовое объяснение, иначе None.
        Единая точка для Telegram, Mini App chat и stream.
        """
        detected = self.detect_topic(user_message)
        if not detected:
            return None
        return self.get_explanation(detected.topic_id)

    def get_explanation(self, topic_id: str) -> str | None:
        """
        Получить объяснение темы по ID.

        Args:
            topic_id: ID темы

        Returns:
            Текст объяснения или None
        """
        topic = self.topics.get(topic_id)
        if not topic:
            return None

        explanation = f"📚 {topic.title}\n\n{topic.explanation}"

        if topic.examples:
            explanation += "\n\n🔍 Примеры:\n"
            for i, example in enumerate(topic.examples, 1):
                explanation += f"\n{i}. {example}"

        if topic.related_topics:
            related_titles = []
            for related_id in topic.related_topics[:3]:  # Максимум 3 связанные темы
                related_topic = self.topics.get(related_id)
                if related_topic:
                    related_titles.append(related_topic.title)
            if related_titles:
                explanation += "\n\n📎 Похожие темы: " + ", ".join(related_titles)

        return explanation

    def get_all_topics(self) -> list[AdultTopicExplanation]:
        """Получить список всех тем."""
        return list(self.topics.values())

    def search_topics(self, query: str) -> list[AdultTopicExplanation]:
        """
        Поиск тем по запросу.

        Args:
            query: Поисковый запрос

        Returns:
            Список найденных тем
        """
        query_lower = query.lower()
        results = []

        for topic in self.topics.values():
            # Ищем в ключевых словах, заголовке и объяснении
            if (
                any(keyword in query_lower for keyword in topic.keywords)
                or query_lower in topic.title.lower()
                or query_lower in topic.explanation.lower()
            ):
                results.append(topic)

        return results


# Singleton instance
_adult_topics_service: AdultTopicsService | None = None


def get_adult_topics_service() -> AdultTopicsService:
    """
    Получить экземпляр AdultTopicsService (singleton).

    Returns:
        AdultTopicsService: Экземпляр сервиса
    """
    global _adult_topics_service
    if _adult_topics_service is None:
        _adult_topics_service = AdultTopicsService()
    return _adult_topics_service
