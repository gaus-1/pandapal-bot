"""
Классификатор категорий новостей.

Автоматически определяет категорию новости и проверяет релевантность для детской аудитории.
"""

from loguru import logger

from bot.services.yandex_cloud_service import YandexCloudService


class NewsCategoryClassifier:
    """
    Классификатор категорий новостей.

    Использует YandexGPT для определения категории и проверки релевантности.
    """

    # Доступные категории
    CATEGORIES = [
        "игры",
        "мода",
        "образование",
        "еда",
        "спорт",
        "животные",
        "природа",
        "факты",
        "события",
        "приколы",
    ]

    def __init__(self, yandex_service: YandexCloudService | None = None):
        """
        Инициализация классификатора.

        Args:
            yandex_service: Сервис Yandex Cloud (если None, создается новый)
        """
        self.yandex_service = yandex_service or YandexCloudService()

    async def classify(self, title: str, content: str) -> tuple[str, bool]:
        """
        Определить категорию новости и проверить релевантность.

        Args:
            title: Заголовок новости
            content: Текст новости

        Returns:
            tuple[str, bool]: (category, is_relevant)
                - category: Категория новости
                - is_relevant: True если новость релевантна для детей 6-15 лет
        """
        try:
            system_prompt = """Ты классифицируешь новости для детского новостного бота.

Доступные категории: игры, мода, образование, еда, спорт, животные, природа, факты, события, приколы.

Ответь в формате: КАТЕГОРИЯ|РЕЛЕВАНТНОСТЬ
- КАТЕГОРИЯ: одна из доступных категорий
- РЕЛЕВАНТНОСТЬ: ДА если новость интересна детям 6-15 лет, НЕТ если нет

Исключи новости про политику, криминал, взрослые темы."""

            user_message = f"Заголовок: {title}\n\nТекст: {content[:500]}"

            response = await self.yandex_service.generate_text_response(
                user_message=user_message,
                system_prompt=system_prompt,
                temperature=0.3,  # Низкая температура для точности
                max_tokens=100,
            )

            # Парсим ответ
            parts = response.strip().split("|")
            if len(parts) >= 2:
                category = parts[0].strip().lower()
                relevance = parts[1].strip().upper()

                # Проверяем категорию
                if category not in self.CATEGORIES:
                    category = "события"  # Категория по умолчанию

                is_relevant = relevance in ("ДА", "YES", "TRUE", "1")

                logger.info(f"✅ Новость классифицирована: {category}, релевантна={is_relevant}")
                return category, is_relevant

            # Fallback
            logger.warning("⚠️ Не удалось распарсить ответ классификатора")
            return "события", True

        except Exception as e:
            logger.error(f"❌ Ошибка классификации новости: {e}")
            return "события", True  # По умолчанию разрешаем
