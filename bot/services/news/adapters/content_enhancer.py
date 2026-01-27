"""
Улучшитель качества новостей.

Делает новости интересными и понятными для детей:
- Улучшение заголовков
- Добавление фактов и контекста
- Структурирование текста
- Вопросы для вовлечения
"""

from loguru import logger

from bot.services.yandex_cloud_service import YandexCloudService


class NewsContentEnhancer:
    """
    Улучшитель качества новостей.

    Делает новости интересными и понятными для детей.
    """

    def __init__(self, yandex_service: YandexCloudService | None = None):
        """
        Инициализация улучшителя.

        Args:
            yandex_service: Сервис Yandex Cloud (если None, создается новый)
        """
        self.yandex_service = yandex_service or YandexCloudService()

    async def enhance(self, news_item: dict, age: int | None = None) -> dict:
        """
        Улучшить новость.

        Args:
            news_item: Новость в формате словаря
            age: Возраст ребенка (для персонализации)

        Returns:
            dict: Улучшенная новость
        """
        try:
            title = news_item.get("title", "")
            content = news_item.get("content", "")

            if not title or not content:
                return news_item

            age_text = f"для ребенка {age} лет" if age else "для ребенка"

            system_prompt = f"""Ты улучшаешь новость {age_text}, чтобы сделать её интересной и понятной.

Сделай:
1. Улучши заголовок - сделай его привлекательным для детей
2. Добавь интересные факты и контекст
3. Структурируй текст - разбей на абзацы, выдели главное
4. Добавь вопрос для размышления: "А что ты думаешь об этом?"
5. Сделай текст информативным, но не скучным

Верни в формате:
ЗАГОЛОВОК: [улучшенный заголовок]
ТЕКСТ: [улучшенный текст]"""

            user_message = f"Заголовок: {title}\n\nТекст: {content}"

            response = await self.yandex_service.generate_text_response(
                user_message=user_message,
                system_prompt=system_prompt,
                temperature=0.6,  # Средняя креативность
                max_tokens=2000,
            )

            # Парсим ответ
            if "ЗАГОЛОВОК:" in response and "ТЕКСТ:" in response:
                parts = response.split("ТЕКСТ:")
                if len(parts) >= 2:
                    title_part = parts[0].replace("ЗАГОЛОВОК:", "").strip()
                    content_part = parts[1].strip()

                    news_item["title"] = title_part
                    news_item["content"] = content_part

                    logger.info(f"✅ Новость улучшена для возраста {age}")
                    return news_item

            # Fallback: улучшаем только текст
            news_item["content"] = response.strip()
            return news_item

        except Exception as e:
            logger.error(f"❌ Ошибка улучшения новости: {e}")
            return news_item  # Возвращаем оригинал при ошибке
