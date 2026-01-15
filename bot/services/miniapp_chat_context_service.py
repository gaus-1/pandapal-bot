"""
Сервис для подготовки контекста чата в Mini App.

Отвечает за:
- Загрузку истории
- Подсчёт сообщений
- Формирование системного промпта
- Получение веб-контекста
"""

from bot.services import ChatHistoryService, UserService
from bot.services.premium_features_service import PremiumFeaturesService


class MiniappChatContextService:
    """Сервис для подготовки контекста чата."""

    def __init__(self, db):
        """
        Инициализация сервиса.

        Args:
            db: Сессия базы данных
        """
        self.db = db
        self.user_service = UserService(db)
        self.history_service = ChatHistoryService(db)
        self.premium_service = PremiumFeaturesService(db)

    def prepare_context(
        self,
        telegram_id: int,
        user_message: str,
        skip_premium_check: bool = False,
    ):
        """Подготавливает контекст для AI запроса.

        Args:
            telegram_id: ID пользователя в Telegram
            user_message: Сообщение пользователя
            skip_premium_check: Пропускать ли проверку лимитов Premium

        Returns:
            dict: Контекст с историей, промптом, пользователем и т.д.
        """
        user = self.user_service.get_user_by_telegram_id(telegram_id)
        if not user:
            raise ValueError(f"User {telegram_id} not found")

        # Проверка Premium (может быть отключена снаружи)
        if not skip_premium_check:
            can_request, limit_reason = self.premium_service.can_make_ai_request(
                telegram_id, username=user.username
            )
            if not can_request:
                raise ValueError(f"AI request blocked: {limit_reason}")

        # Загружаем историю
        history_limit = 50 if self.premium_service.is_premium_active(telegram_id) else 10
        history = self.history_service.get_formatted_history_for_ai(
            telegram_id, limit=history_limit
        )

        # Проверяем, была ли очистка истории
        is_history_cleared = len(history) == 0

        # Проверяем, было ли отправлено автоматическое приветствие
        # Если история содержит только одно сообщение от AI с приветствием - считаем что приветствие было отправлено
        is_auto_greeting_sent = False
        if len(history) == 1:
            first_msg = history[0]
            if first_msg.get("role") == "assistant":
                msg_text = first_msg.get("text", "").lower()
                if "привет" in msg_text or "начнем" in msg_text:
                    is_auto_greeting_sent = True
        elif is_history_cleared:
            # Если история пустая, но была очищена - приветствие могло быть отправлено через miniapp_add_greeting
            # Проверяем через последнее сообщение в истории (может быть добавлено после очистки)
            is_auto_greeting_sent = False  # Будет определено ниже при проверке истории

        # Подсчитываем количество сообщений пользователя с последнего обращения по имени
        user_message_count = 0
        if user.first_name:
            last_name_mention_index = -1
            for i, msg in enumerate(history):
                if (
                    msg.get("role") == "assistant"
                    and user.first_name.lower() in msg.get("text", "").lower()
                ):
                    last_name_mention_index = i
                    break

            if last_name_mention_index >= 0:
                user_message_count = sum(
                    1 for msg in history[last_name_mention_index + 1 :] if msg.get("role") == "user"
                )
            else:
                user_message_count = sum(1 for msg in history if msg.get("role") == "user")
        else:
            user_message_count = sum(1 for msg in history if msg.get("role") == "user")

        # Определяем, является ли вопрос образовательным
        educational_keywords = [
            "математика",
            "алгебра",
            "геометрия",
            "арифметика",
            "русский",
            "литература",
            "сочинение",
            "диктант",
            "история",
            "география",
            "биология",
            "физика",
            "химия",
            "английский",
            "немецкий",
            "французский",
            "испанский",
            "информатика",
            "программирование",
            "задача",
            "решить",
            "решение",
            "пример",
            "уравнение",
            "урок",
            "домашнее",
            "задание",
            "дз",
            "контрольная",
            "объясни",
            "помоги",
            "как решить",
            "как сделать",
            "сколько",
            "вычисли",
            "посчитай",
            "найди",
            "таблица",
            "умножение",
            "деление",
            "сложение",
            "вычитание",
        ]

        user_message_lower = user_message.lower()
        is_educational = any(keyword in user_message_lower for keyword in educational_keywords)

        # Обновляем счетчик непредметных вопросов
        if is_educational:
            user.non_educational_questions_count = 0
        else:
            user.non_educational_questions_count += 1

        # Получаем веб-контекст будем снаружи через ai_service, здесь только бизнес-контекст

        # Формируем системный промпт
        from bot.services.prompt_builder import get_prompt_builder

        prompt_builder = get_prompt_builder()
        enhanced_system_prompt = prompt_builder.build_system_prompt(
            user_age=user.age,
            user_name=user.first_name,
            message_count_since_name=user_message_count,
            is_history_cleared=is_history_cleared,
            chat_history=history,
            user_message=user_message,
            non_educational_questions_count=user.non_educational_questions_count,
            is_auto_greeting_sent=is_auto_greeting_sent,
            is_educational=is_educational,
        )

        # Преобразуем историю в формат Yandex
        yandex_history = []
        if history:
            for msg in history[-10:]:
                role = msg.get("role", "user")
                text = msg.get("text", "").strip()
                if text:
                    yandex_history.append({"role": role, "text": text})

        return {
            "user": user,
            "history": history,
            "yandex_history": yandex_history,
            "system_prompt": enhanced_system_prompt,
            "is_history_cleared": is_history_cleared,
            "is_educational": is_educational,
            "premium_service": self.premium_service,
            "history_service": self.history_service,
        }
