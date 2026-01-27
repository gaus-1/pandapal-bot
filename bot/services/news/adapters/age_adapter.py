"""
Адаптер для адаптации новостей под возраст ребенка.

Качественная адаптация: НЕ тупое копирование, а умная переработка текста.
"""

from loguru import logger

from bot.services.news.interfaces import INewsAdapter
from bot.services.yandex_cloud_service import YandexCloudService


class AgeNewsAdapter(INewsAdapter):
    """
    Адаптер для адаптации новостей под возраст ребенка.

    Использует YandexGPT для умной адаптации контента:
    - Упрощение сложных терминов с объяснениями
    - Добавление контекста и примеров
    - Дружелюбный стиль, понятный для детей
    - Короткие предложения, простые слова
    - Вопросы для вовлечения
    """

    def __init__(self, yandex_service: YandexCloudService | None = None):
        """
        Инициализация адаптера.

        Args:
            yandex_service: Сервис Yandex Cloud (если None, создается новый)
        """
        self.yandex_service = yandex_service or YandexCloudService()

    async def adapt_content(
        self, content: str, age: int | None = None, grade: int | None = None
    ) -> str:
        """
        Адаптировать контент под возраст ребенка.

        Args:
            content: Исходный текст новости
            age: Возраст ребенка (6-15)
            grade: Класс ребенка (1-9)

        Returns:
            str: Адаптированный текст
        """
        try:
            # Формируем промпт для адаптации
            age_text = f"для ребенка {age} лет" if age else "для ребенка"
            grade_text = f"{grade} класса" if grade else "школьника"

            system_prompt = f"""Ты адаптируешь новости для детей {age_text} ({grade_text}).

ВАЖНО: НЕ просто копируй текст, а ПЕРЕРАБОТАЙ его:
- Упрости сложные слова и объясни их
- Добавь примеры и контекст для понимания
- Используй дружелюбный, понятный стиль
- Пиши короткими предложениями
- Добавь вопросы для вовлечения: "А ты знал, что...?"
- Сделай текст интересным, не скучным

Новость должна быть понятна ребенку без объяснений взрослых."""

            user_message = f"Адаптируй эту новость {age_text}:\n\n{content}"

            # Адаптируем через YandexGPT
            adapted = await self.yandex_service.generate_text_response(
                user_message=user_message,
                system_prompt=system_prompt,
                temperature=0.5,  # Баланс между точностью и креативностью
                max_tokens=2000,
            )

            logger.info(f"✅ Новость адаптирована для возраста {age}, класса {grade}")
            return adapted.strip()

        except Exception as e:
            logger.error(f"❌ Ошибка адаптации новости: {e}")
            # Fallback: возвращаем оригинальный текст
            return content
