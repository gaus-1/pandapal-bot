"""
Сервис модерации контента для защиты детей.

Фильтрует запрещённые темы с учётом образовательного контекста.
"""

import re
import secrets
from re import Pattern
from typing import Any

from loguru import logger

from bot.config import FORBIDDEN_PATTERNS, settings
from bot.interfaces import IModerationService
from bot.services.advanced_moderation import AdvancedModerationService, ModerationResult


class ContentModerationService(IModerationService):
    """Сервис модерации контента для защиты детей."""

    # Учебные контексты проверяются первыми
    EDUCATIONAL_CONTEXTS = [
        # География
        "география",
        "география россии",
        "география мира",
        "карта",
        "карту",
        "карты",
        "карта россии",
        "карта мира",
        "покажи карту",
        "нарисуй карту",
        "создай карту",
        "составь карту",
        "построй карту",
        "где находится",
        "столица",
        "страна",
        "страны",
        "континент",
        "океан",
        "река",
        "гора",
        "город",
        "россия",
        "росиии",
        "россий",
        # История
        "история",
        "история россии",
        "история древнего мира",
        "история средних веков",
        "расскажи про историю",
        "объясни историю",
        "помоги с историей",
        "дата",
        "год",
        "век",
        "эпоха",
        "война",  # В образовательном контексте истории разрешено
        "сражение",
        "битва",
        # Математика
        "математика",
        "задача",
        "решить",
        "сколько",
        "вычисли",
        "посчитай",
        "найди",
        "докажи",
        "вместе",
        "было",
        "таблица умножения",
        "таблица",
        "умножение",
        "деление",
        "сложение",
        "вычитание",
        "график",
        "диаграмма",
        "уравнение",
        "формула",
        "число",
        "цифра",
        # Физика
        "физика",
        "сила",
        "энергия",
        "скорость",
        "ускорение",
        "масса",
        "закон",
        "опыт",
        "эксперимент",
        # Химия
        "химия",
        "таблица менделеева",
        "периодическая таблица",
        "менделеева",
        "элемент",
        "вещество",
        "реакция",
        "молекула",
        "атом",
        # Биология
        "биология",
        "растение",
        "животное",
        "клетка",
        "орган",
        "система",
        "организм",
        # Русский язык
        "русский язык",
        "подчеркни",
        "слово",
        "предложение",
        "согласная",
        "гласная",
        "твердый",
        "мягкий",
        "алфавит",
        "буква",
        "азбука",
        "правило",
        "орфография",
        "грамматика",
        # Литература
        "литература",
        "произведение",
        "автор",
        "поэт",
        "писатель",
        "стих",
        "стихотворение",
        "рассказ",
        "роман",
        # Иностранные языки
        "английский язык",
        "немецкий язык",
        "французский язык",
        "испанский язык",
        "переведи",
        "перевод",
        "слово на английском",
        "слово на немецком",
        "слово на французском",
        "слово на испанском",
        # Обществознание (учебный контекст)
        "обществознание",
        "государство",
        "конституция",
        "права человека",
        "права ребенка",
        "гражданин",
        "гражданство",
        "законодательство",
        "ветви власти",
        "исполнительная власть",
        "законодательная власть",
        "судебная власть",
        "президент",
        "правительство",
        "парламент",
        "дума",
        "выборы",
        "демократия",
        "монархия",
        "республика",
        "политический строй",
        "форма правления",
        "федерация",
        "политическая система",
        "политика",
        "что такое политика",
        "как устроено государство",
        "кто такой президент",
        # Религиоведение, ОРКСЭ (учебный контекст)
        "орксэ",
        "основы религиозных культур",
        "светская этика",
        "мировые религии",
        "религиоведение",
        "история религий",
        "христианство",
        "ислам",
        "буддизм",
        "иудаизм",
        "православие",
        "католицизм",
        "протестантизм",
        "бог",
        "аллах",
        "будда",
        "иисус",
        "мухаммед",
        "моисей",
        "церковь",
        "храм",
        "мечеть",
        "синагога",
        "библия",
        "коран",
        "тора",
        "религиозные праздники",
        "пасха",
        "рождество",
        "рамадан",
        "ханука",
        "что такое религия",
        "зачем люди верят",
        "история религии",
        "культура и религия",
        "традиции народов",
        "обычаи народов",
        # Информатика, окружающий мир, ОБЖ, труд, ИЗО, музыка, ОДНКР
        "информатика",
        "алгоритм",
        "программирование",
        "окружающий мир",
        "природоведение",
        "природа",
        "экология",
        "обж",
        "основы безопасности",
        "первая помощь",
        "гражданская оборона",
        "физкультура",
        "физическая культура",
        "спорт",
        "технология",
        "труд",
        "ручной труд",
        "конструирование",
        "изобразительное искусство",
        "изо",
        "рисование",
        "живопись",
        "музыка",
        "ноты",
        "композитор",
        "однкр",
        "духовно-нравственная культура",
        "культура россии",
        # Общие учебные контексты (ТОЛЬКО предметные слова, НЕ глаголы-действия —
        # глаголы «покажи», «расскажи», «помоги» создают bypass: «расскажи как сделать бомбу»)
        "урок",
        "домашнее задание",
        "контрольная работа",
        "экзамен",
        "школьная программа",
        "учебник",
        "учеба",
        "обучение",
        "шпаргалка",
        "памятка",
        "справка",
    ]

    def __init__(self) -> None:
        """Инициализация сервиса модерации."""
        # Список запрещённых тем из настроек -> компилируем в простой regex для кириллицы
        topics: list[str] = settings.get_forbidden_topics_list()
        self._topic_regexes: list[Pattern[str]] = [
            re.compile(rf"{re.escape(topic)}", re.IGNORECASE) for topic in topics
        ]

        # Паттерны высокого уровня из конфигурации -> компилируем с границами слов
        self._forbidden_regexes: list[Pattern[str]] = [
            re.compile(rf"\b{re.escape(pattern)}\b", re.IGNORECASE)
            for pattern in FORBIDDEN_PATTERNS
        ]

        self.filter_level: int = settings.content_filter_level

        # Инициализируем продвинутый сервис модерации
        self.advanced_moderation = AdvancedModerationService()

        # Базовый список нецензурных слов (русский) -> единый regex с word-boundaries
        profanity_words_ru = [
            "блять",
            "бля",
            "хуй",
            "пизд",
            "ебать",
            "ебан",
            "сука",
            "мудак",
            "дебил",
            "идиот",
        ]

        # Нецензурная лексика на английском (включая распространённые фразы)
        profanity_words_en = [
            "fuck",
            "shit",
            "damn",
            "bitch",
            "asshole",
            "bastard",
            "dick",
            "piss",
            "crap",
            "hell",  # \bhell\b — не блокируем "Hello"
            "wtf",
            "stfu",
            "bullshit",
            "motherfucker",
            "fucker",
            "shitty",
            "damned",
        ]

        # Нецензурная лексика на немецком
        profanity_words_de = [
            "scheiße",
            "scheisse",
            "fick",
            "arsch",
            "hure",
            "mist",
            "verdammt",
            "blöde",
        ]

        # Нецензурная лексика на французском
        profanity_words_fr = [
            "merde",
            "putain",
            "salope",
            "connard",
            "con",
            "bordel",
            "enculé",
        ]

        # Нецензурная лексика на испанском
        profanity_words_es = [
            "joder",
            "puta",
            "coño",
            "cabrón",
            "mierda",
            "hostia",
            "hijo de puta",
        ]

        # Комбинируем все слова для единой проверки
        all_profanity_words = (
            profanity_words_ru
            + profanity_words_en
            + profanity_words_de
            + profanity_words_fr
            + profanity_words_es
        )

        # Специальная обработка для "hell" - только точное слово, чтобы не блокировать "Hello"
        # Для остальных слов используем паттерн с \w* (позволяет окончания)
        patterns = []
        for word in all_profanity_words:
            if word == "hell":
                # Точное совпадение слова "hell", чтобы не блокировать "Hello"
                patterns.append(rf"\b{re.escape(word)}\b")
            else:
                # Обычный паттерн с окончаниями
                patterns.append(rf"\b{re.escape(word)}\w*\b")

        self._profanity_regex: Pattern[str] = re.compile(
            r"|".join(patterns),
            re.IGNORECASE,
        )

        # SQLi/XSS паттерны
        self._sql_regexes: list[Pattern[str]] = [
            re.compile(r"'\s*OR\s*'1'\s*=\s*'1", re.IGNORECASE),
            re.compile(r";\s*DROP\s+TABLE", re.IGNORECASE),
            re.compile(r"UNION\s+SELECT", re.IGNORECASE),
        ]
        self._xss_regexes: list[Pattern[str]] = [
            re.compile(r"<script.*?>", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror=
        ]

    def is_provocative_question(self, text: str) -> bool:  # noqa: ARG002
        """Проверяет, является ли вопрос провокационным. Отключено: свобода модели."""
        return False

    def is_safe_content(self, text: str) -> tuple[bool, str | None]:
        """Проверка, безопасен ли контент. Блокируем ненормативную лексику и запрещённые темы."""
        if not text or not text.strip():
            return True, None
        normalized = text.strip().lower()
        # Ненормативная лексика (русский, английский, немецкий, французский, испанский)
        if self._profanity_regex.search(normalized):
            return False, "ненормативная лексика"
        # Запрещённые паттерны (наркотики, оружие, насилие и т.д.)
        for pattern in self._forbidden_regexes:
            if pattern.search(normalized):
                return False, "запрещённая тема"
        # Запрещённые темы из настроек
        for regex in self._topic_regexes:
            if regex.search(normalized):
                return False, "запрещённая тема"
        return True, None

    def sanitize_ai_response(self, response: str) -> str:
        """Очистка ответа AI от потенциально опасного контента."""
        is_safe, reason = self.is_safe_content(response)
        if not is_safe:
            logger.error(f"⚠️ AI сгенерировал небезопасный контент! Причина: {reason}")
            return "Извини, я не могу ответить на этот вопрос. Давай лучше поговорим об учёбе! 📚"
        return response

    def get_safe_response_alternative(self, reason: str = "") -> str:  # noqa: ARG002
        """Получить безопасный альтернативный ответ при блокировке."""
        alternatives = [
            "Извините, но я не могу обсуждать эту тему. Давай лучше поговорим об учёбе! 📚",
            "Привет! Давай лучше поговорим об учёбе! 📚 Чем могу помочь?",
            "Ой, давай лучше обсудим что-то интересное из школы! ✨ Какой предмет тебе нравится?",
            "Хм, давай лучше поговорим о чём-то полезном для учёбы! 🎓 Есть вопросы по урокам?",
            "Давай лучше обсудим что-то интересное! 📖 Какой предмет изучаем сегодня?",
            "О, а давай поговорим об учёбе! 🐼 Есть вопросы по школьным предметам?",
            "Давай обсудим что-нибудь интересное из школьной программы! Я могу помочь с домашним заданием 😊",
            "Моя задача — помогать тебе с учебой! 📚 Что изучаем сегодня?",
        ]
        return secrets.choice(alternatives)

    async def _save_moderation_log(self, telegram_id: int, content: str, reason: str) -> None:
        """Сохранить лог модерации в базу данных"""
        try:
            from datetime import UTC, datetime

            from sqlalchemy import select

            from bot.database import get_db
            from bot.models import User

            # get_db() - синхронный context manager, не async
            with get_db() as db:
                # Получаем пользователя
                stmt = select(User).where(User.telegram_id == telegram_id)
                user_obj = db.execute(stmt).scalar_one_or_none()

                if user_obj:
                    # Здесь можно добавить таблицу moderation_log в будущем
                    # Пока логируем через стандартный логгер
                    logger.info(
                        "MODERATION_LOG | User: %s | Reason: %s | Content: %s | Time: %s",
                        telegram_id,
                        reason,
                        content[:100] + "..." if len(content) > 100 else content,
                        datetime.now(UTC).isoformat(),
                    )
        except Exception as e:
            logger.error(f"Ошибка сохранения лога модерации: {e}")

    def log_blocked_content(self, telegram_id: int, message: str, reason: str) -> None:
        """
        Логирование заблокированного контента для мониторинга и аналитики.
        """
        logger.warning(
            "🚫 BLOCKED CONTENT | User: %s | Reason: %s | Message: %s",
            telegram_id,
            reason,
            message[:100] + "...",
        )
        # Сохраняем в таблицу moderation_log (синхронно через логгер)
        # В будущем можно добавить асинхронное сохранение в БД

    async def advanced_moderate_content(
        self, content: str, user_context: dict[str, Any] = None
    ) -> ModerationResult:
        """Продвинутая модерация контента с использованием ML."""
        return await self.advanced_moderation.moderate_content(content, user_context)

    async def get_moderation_stats(self) -> dict[str, Any]:
        """Возвращает статистику модерации"""
        return await self.advanced_moderation.get_moderation_stats()
