"""
Модерация контента для обеспечения безопасности детей.

Этот модуль реализует базовую модерацию контента, следуя принципу
Single Responsibility. Проверяет текстовые сообщения на наличие
запрещенных тем и паттернов для защиты детей от неподходящего контента.

Основные возможности:
- Проверка текста на запрещенные паттерны
- Фильтрация неподходящего контента
- Логирование заблокированных сообщений
- Возврат причин блокировки

Безопасность:
- Проверка на запрещенные темы
- Фильтрация нецензурной лексики
- Защита от неподходящего контента
- Логирование всех блокировок

Принципы:
- Single Responsibility: только модерация контента
- Open/Closed: легко расширяется новыми паттернами
- Interface Segregation: минимальный интерфейс IModerator
"""

from bot.services.moderation_service import ContentModerationService
from bot.services.yandex_ai_response_generator import IModerator


class ContentModerator(IModerator):
    """
    Модератор контента для обеспечения безопасности детей.

    Реализует базовую проверку текстовых сообщений на наличие
    запрещенных паттернов и тем. Следует принципу Single Responsibility
    - единственная задача: модерация контента.
    """

    def __init__(self) -> None:
        self._moderation_service = ContentModerationService()

    def moderate(self, text: str) -> tuple[bool, str]:
        """Проверка контента на безопасность через ContentModerationService."""
        is_safe, reason = self._moderation_service.is_safe_content(text)
        if is_safe:
            return True, "контент безопасен"
        return False, f"запрещен: {reason or 'запрещённая тема'}"
