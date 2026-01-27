"""
Фильтр контента для API источников.

Умная фильтрация новостей от World News API и NewsAPI:
- Проверка на детские темы
- Исключение взрослого контента
- Оценка качества и интереса
"""

from loguru import logger

from bot.services.yandex_cloud_service import YandexCloudService


class NewsContentFilter:
    """
    Фильтр контента для API источников.

    Проверяет новости на релевантность для детской аудитории.
    """

    def __init__(self, yandex_service: YandexCloudService | None = None):
        """
        Инициализация фильтра.

        Args:
            yandex_service: Сервис Yandex Cloud (если None, создается новый)
        """
        self.yandex_service = yandex_service or YandexCloudService()

        # Ключевые слова для фильтрации недетского контента
        self.adult_keywords = [
            "политика",
            "криминал",
            "убийство",
            "наркотики",
            "алкоголь",
            "курение",
            "18+",
            "взрослый",
            "секс",
            "насилие",
        ]

        # Ключевые слова для детского контента
        self.kids_keywords = [
            "дети",
            "ребенок",
            "школа",
            "ученик",
            "игра",
            "игрушка",
            "мультфильм",
            "животное",
            "природа",
            "спорт",
            "образование",
        ]

    def _check_keywords(self, text: str) -> tuple[bool, str]:
        """
        Проверить текст по ключевым словам.

        Args:
            text: Текст для проверки

        Returns:
            tuple[bool, str]: (is_safe, reason)
        """
        text_lower = text.lower()

        # Проверка на взрослый контент
        for keyword in self.adult_keywords:
            if keyword in text_lower:
                return False, f"Содержит взрослую тему: {keyword}"

        # Проверка на детский контент
        has_kids_content = any(keyword in text_lower for keyword in self.kids_keywords)

        if not has_kids_content:
            return False, "Не содержит детских тем"

        return True, "OK"

    def _check_quality(self, title: str, content: str) -> tuple[bool, str]:
        """
        Проверить качество новости.

        Args:
            title: Заголовок
            content: Текст

        Returns:
            tuple[bool, str]: (is_good, reason)
        """
        # Минимальная длина
        if len(title) < 10:
            return False, "Слишком короткий заголовок"

        if len(content) < 50:
            return False, "Слишком короткий текст"

        # Проверка на "тупость" - слишком простые или бессмысленные новости
        if len(content) < 100 and "..." in content:
            return False, "Неполный контент"

        return True, "OK"

    async def filter(self, news_item: dict) -> tuple[bool, str]:
        """
        Отфильтровать новость.

        Args:
            news_item: Новость в формате словаря

        Returns:
            tuple[bool, str]: (should_keep, reason)
                - should_keep: True если новость подходит
                - reason: Причина отклонения (если should_keep=False)
        """
        try:
            title = news_item.get("title", "")
            content = news_item.get("content", "")

            if not title or not content:
                return False, "Отсутствует заголовок или текст"

            # Проверка по ключевым словам
            is_safe, reason = self._check_keywords(f"{title} {content}")
            if not is_safe:
                return False, reason

            # Проверка качества
            is_good, quality_reason = self._check_quality(title, content)
            if not is_good:
                return False, quality_reason

            # Дополнительная проверка через YandexGPT (если нужно)
            # Для экономии токенов используем только для сомнительных случаев
            if len(content) < 200:
                # Короткие новости проверяем через AI
                try:
                    system_prompt = """Проверь, подходит ли эта новость для детей 6-15 лет.

Ответь: ДА или НЕТ.
Исключи политику, криминал, взрослые темы."""

                    response = await self.yandex_service.generate_text_response(
                        user_message=f"Заголовок: {title}\nТекст: {content}",
                        system_prompt=system_prompt,
                        temperature=0.2,
                        max_tokens=50,
                    )

                    if "НЕТ" in response.upper() or "NO" in response.upper():
                        return False, "Не подходит для детей (проверка AI)"

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка AI проверки: {e}")

            return True, "OK"

        except Exception as e:
            logger.error(f"❌ Ошибка фильтрации новости: {e}")
            return False, f"Ошибка фильтрации: {e}"
