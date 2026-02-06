"""
Модуль для формирования системных промптов для YandexGPT.

Добавляет динамический контекст (имя, статус приветствия, редирект на учебу,
предпочтение по эмодзи) к базовому системному промпту.
"""

from bot.config.prompts import AI_SYSTEM_PROMPT
from bot.services.emoji_preference import get_emoji_prompt_snippet


class PromptBuilder:
    """Построитель промптов для YandexGPT."""

    def __init__(self):
        self.base_prompt = AI_SYSTEM_PROMPT

    def build_system_prompt(
        self,
        user_message: str = "",
        user_name: str | None = None,
        chat_history: list[dict] | None = None,
        is_history_cleared: bool = False,
        message_count_since_name: int = 0,  # noqa: ARG002
        non_educational_questions_count: int = 0,  # noqa: ARG002
        user_age: int | None = None,  # noqa: ARG002
        user_grade: int | None = None,
        is_auto_greeting_sent: bool = False,
        user_gender: str | None = None,
        emoji_in_chat: bool | None = None,
        allow_emoji_this_turn: bool = False,
    ) -> str:
        """
        Построить системный промпт: базовые правила + опциональный контекст
        (приветствие/прощание, пол, предпочтение по эмодзи).
        """
        greeting = self._get_greeting_context(
            chat_history or [],
            is_history_cleared,
            user_message,
            is_auto_greeting_sent,
            user_name,
            user_grade,
        )
        parts = [self.base_prompt]
        if greeting:
            parts.append(greeting)
        if user_gender:
            g = user_gender.lower().strip()
            gender_hint = "мужской" if g == "male" else "женский" if g == "female" else "не указан"
            parts.append(
                f"Пол пользователя: {gender_hint}. Учитывай при склонениях и подбадриваниях."
            )
        emoji_snippet = get_emoji_prompt_snippet(emoji_in_chat, allow_emoji_this_turn)
        if emoji_snippet:
            parts.append(f"Эмодзи: {emoji_snippet}")
        if len(parts) == 1:
            return parts[0]
        return "\n\n".join(parts)

    def _get_greeting_context(
        self,
        chat_history: list[dict] | None,
        is_history_cleared: bool,
        user_message: str,
        is_auto_greeting_sent: bool,
        user_name: str | None = None,
        user_grade: int | None = None,
    ) -> str | None:
        """Определяет нужно ли приветствоваться или прощаться."""
        if not chat_history:
            chat_history = []

        user_message_lower = user_message.lower().strip()

        # Проверка, здоровалась ли панда
        ai_greeted = False
        if is_auto_greeting_sent:
            ai_greeted = True
        else:
            for msg in chat_history:
                if msg.get("role") == "assistant":
                    txt = msg.get("text", "").lower()
                    if (
                        "привет" in txt
                        or "чем могу помочь" in txt
                        or "начнем" in txt
                        or "пандапал" in txt
                    ):
                        ai_greeted = True
                        break

        # Пользователь прощается - ТОЛЬКО если это явное прощание, не вопрос
        farewell_keywords = [
            "пока",
            "до свидания",
            "до свиданья",
            "прощай",
            "прощайте",
            "bye",
            "goodbye",
            "see you",
            "увидимся",
        ]
        # Проверяем, что это именно прощание, а не вопрос с этими словами
        is_farewell = any(fw in user_message_lower for fw in farewell_keywords)
        # Если есть вопросительные слова - это не прощание
        has_question_words = any(
            qw in user_message_lower for qw in ["что", "как", "где", "когда", "почему", "кто", "?"]
        )
        if is_farewell and not has_question_words:
            return (
                "Пользователь попрощался. Попрощайся в ответ коротко и вежливо. "
                "Только «ты», никогда «Здравствуйте»."
            )

        # КРИТИЧЕСКИ ВАЖНО: После очистки истории приветствие должно быть ТОЛЬКО ОДИН РАЗ
        # Если история очищена И приветствие уже отправлено - НЕ здороваться снова
        if is_history_cleared and ai_greeted:
            return (
                "ВНИМАНИЕ: История очищена, ты уже поздоровалась. "
                "НЕ повторяй приветствие. Никогда не пиши «Здравствуйте». Сразу начинай с решения или объяснения."
            )

        # Пользователь здоровается - ТОЛЬКО если это явное приветствие
        greeting_keywords = [
            "привет",
            "здравствуй",
            "здравствуйте",
            "добрый день",
            "доброе утро",
            "добрый вечер",
            "здравова",
            "хай",
            "hi",
            "hello",
        ]
        user_greeted = any(gw in user_message_lower for gw in greeting_keywords)

        # ОСОБЫЙ СЛУЧАЙ: После очистки корзины, если панда уже поздоровалась и пользователь тоже поздоровался
        # НЕ повторять привет, а спросить имя или что будем изучать
        if is_history_cleared and ai_greeted and user_greeted:
            return (
                "ВНИМАНИЕ: Ты уже поздоровалась, пользователь тоже. НЕ пиши «Привет» снова. "
                "Спроси: «Как тебя зовут?» или «Что будем изучать сегодня?» — сразу с вопроса, без повторного приветствия. "
                "Только «ты», никогда «Здравствуйте»."
            )

        # КРИТИЧЕСКИ ВАЖНО: Если у пользователя нет имени ИЛИ класса - спроси оба при первом заходе
        # Проверяем это через user_name и user_grade, которые передаются в build_system_prompt
        # Если (user_name=None ИЛИ user_grade=None) И (история пуста ИЛИ история очищена И пользователь не прощается)
        needs_name = user_name is None
        needs_grade = user_grade is None
        is_first_visit = (not chat_history or is_history_cleared) and not is_farewell

        if (needs_name or needs_grade) and is_first_visit:
            # Если пользователь явно поздоровался - спроси имя и класс в приветствии
            if user_greeted:
                if needs_name and needs_grade:
                    return (
                        "Поприветствуй один раз: «Привет! Как тебя зовут и в каком ты классе?» (или «Давай знакомиться — как тебя зовут и в каком ты классе?»). "
                        "Только «ты», никогда «Здравствуйте»."
                    )
                elif needs_name:
                    return (
                        "Поприветствуй один раз: «Привет! Как тебя зовут?» (или «Давай знакомиться — как тебя зовут?»). "
                        "Только «ты», никогда «Здравствуйте»."
                    )
                elif needs_grade:
                    return (
                        "Поприветствуй один раз: «Привет! В каком ты классе?» (или «Расскажи, в каком ты классе?»). "
                        "Только «ты», никогда «Здравствуйте»."
                    )
            # Если это первое сообщение (история пустая) - можно спросить имя и класс
            elif not chat_history:
                if needs_name and needs_grade:
                    return (
                        "Первое сообщение, не знаешь имени и класса. Спроси: «Привет! Как тебя зовут и в каком ты классе?». "
                        "Только «ты», никогда «Здравствуйте»."
                    )
                elif needs_name:
                    return (
                        "Первое сообщение, не знаешь имени. Спроси: «Привет! Как тебя зовут?». "
                        "Только «ты», никогда «Здравствуйте»."
                    )
                elif needs_grade:
                    return (
                        "Первое сообщение, не знаешь класса. Спроси: «Привет! В каком ты классе?». "
                        "Только «ты», никогда «Здравствуйте»."
                    )

        # Приветствуем ТОЛЬКО если:
        # 1. Пользователь явно поздоровался И
        # 2. Панда еще НЕ здоровалась И
        # 3. (История пуста ИЛИ история очищена)
        # 4. У пользователя ЕСТЬ имя (чтобы не дублировать запрос имени выше)
        if (
            user_greeted
            and not ai_greeted
            and (not chat_history or is_history_cleared)
            and user_name
        ):
            return (
                "Поприветствуй один раз: «Привет! Я PandaPal. Чем могу помочь сегодня?» (без имени). "
                "Только «ты», никогда «Здравствуйте»."
            )

        # Панда уже здоровалась - НЕ здороваться снова
        if ai_greeted:
            # Но если нужно спросить имя/класс - спроси без приветствия
            needs_name = user_name is None
            needs_grade = user_grade is None
            if needs_name and needs_grade:
                return (
                    "Ты уже поздоровалась. НЕ повторяй «Привет». Спроси: «Как тебя зовут и в каком ты классе?». "
                    "Никогда «Здравствуйте»."
                )
            elif needs_name:
                return (
                    "Ты уже поздоровалась. НЕ повторяй «Привет». Спроси: «Как тебя зовут?». "
                    "Никогда «Здравствуйте»."
                )
            elif needs_grade:
                return (
                    "Ты уже поздоровалась. НЕ повторяй «Привет». Спроси: «В каком ты классе?». "
                    "Никогда «Здравствуйте»."
                )
            return (
                "Ты уже поздоровалась. НЕ повторяй приветствие. Никогда не пиши «Здравствуйте». "
                "Сразу начинай с решения или объяснения."
            )

        return None


# Глобальный экземпляр
_prompt_builder = None


def get_prompt_builder() -> PromptBuilder:
    """Получить глобальный экземпляр PromptBuilder."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder
