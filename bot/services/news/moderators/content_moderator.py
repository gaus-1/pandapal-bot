"""
Модератор новостного контента.

Обертка над ContentModerationService с дополнительными проверками для детского контента.
"""

from typing import Any

from loguru import logger

from bot.services.moderation_service import ContentModerationService
from bot.services.news.interfaces import INewsModerator


class NewsContentModerator(INewsModerator):
    """
    Модератор новостного контента.

    Использует ContentModerationService для базовой модерации
    и добавляет дополнительные проверки для детского контента.
    """

    def __init__(self, moderation_service: ContentModerationService | None = None):
        """
        Инициализация модератора.

        Args:
            moderation_service: Сервис модерации (если None, создается новый)
        """
        self.moderation_service = moderation_service or ContentModerationService()

    async def moderate(self, news_item: dict[str, Any]) -> tuple[bool, str]:
        """
        Проверить новость на безопасность.

        Args:
            news_item: Новость в формате словаря

        Returns:
            tuple[bool, str]: (is_safe, reason)
                - is_safe: True если новость безопасна
                - reason: Причина отклонения (если is_safe=False)
        """
        try:
            title = news_item.get("title", "")
            content = news_item.get("content", "")

            if not title or not content:
                return False, "Отсутствует заголовок или текст"

            # Базовая модерация через ContentModerationService
            full_text = f"{title} {content}"
            is_safe, reason = self.moderation_service.is_safe_content(full_text)

            if not is_safe:
                logger.warning(f"⚠️ Новость заблокирована модерацией: {reason}")
                return False, f"Модерация: {reason}"

            # Дополнительные проверки для детского контента
            # Проверка на минимальную длину
            if len(content) < 50:
                return False, "Слишком короткий текст"

            # Проверка на пустоту
            if not content.strip():
                return False, "Пустой текст"

            logger.info("✅ Новость прошла модерацию")
            return True, "OK"

        except Exception as e:
            logger.error(f"❌ Ошибка модерации новости: {e}")
            return False, f"Ошибка модерации: {e}"
