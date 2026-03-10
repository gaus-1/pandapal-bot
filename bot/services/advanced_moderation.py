"""
Продвинутая система модерации контента
Использует машинное обучение и контекстный анализ для защиты детей

"""

import re
from dataclasses import dataclass
from enum import Enum
from re import Pattern
from typing import Any

from loguru import logger

from bot.config import settings


class ModerationLevel(Enum):
    """Уровни модерации контента"""

    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"
    DANGEROUS = "dangerous"


class ContentCategory(Enum):
    """Категории контента"""

    EDUCATION = "education"
    VIOLENCE = "violence"
    DRUGS = "drugs"
    SEXUAL = "sexual"
    POLITICS = "politics"
    EXTREMISM = "extremism"
    BULLYING = "bullying"
    SELF_HARM = "self_harm"
    SCAM = "scam"
    SPAM = "spam"


@dataclass
class ModerationResult:
    """Результат модерации контента"""

    is_safe: bool
    level: ModerationLevel
    category: ContentCategory | None
    confidence: float
    reason: str
    suggested_action: str
    alternative_response: str | None = None


class AdvancedModerationService:
    """
    Продвинутый сервис модерации контента
    Использует многоуровневый анализ и контекстную обработку
    """

    def __init__(self):
        """Инициализация продвинутого сервиса модерации"""
        self.filter_level = settings.content_filter_level

        # Расширенные паттерны для разных категорий
        self._category_patterns = self._build_category_patterns()

        # Контекстные исключения (образовательный контент)
        self._educational_contexts = self._build_educational_contexts()

        # Эвристики для определения намерений
        self._intent_indicators = self._build_intent_indicators()

        # Синонимы и эвфемизмы
        self._synonyms = self._build_synonyms()

        logger.info(f"🔒 Продвинутая модерация инициализирована (уровень: {self.filter_level})")

    def _build_category_patterns(self) -> dict[ContentCategory, list[Pattern]]:
        """Создает паттерны для разных категорий контента"""
        patterns = {}

        # Насилие
        violence_pattern = (
            r"\b(убить|убийство|смерть|умереть|труп|кровь|ранен|бьют|"
            r"драка|война|оружие|нож|пистолет|бомба|взрыв)\b"
        )
        patterns[ContentCategory.VIOLENCE] = [
            re.compile(violence_pattern, re.IGNORECASE),
            re.compile(
                r"\b(избить|изнасиловать|пытка|мучение|страдание|боль|убийца|преступник)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(самоубийство|суицид|вешаться|отравиться|резать|резаться)\b", re.IGNORECASE
            ),
        ]

        # Наркотики
        patterns[ContentCategory.DRUGS] = [
            re.compile(
                r"\b(наркотик|наркота|героин|кокаин|амфетамин|марихуана|гашиш|спайс|соль|кристалл)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(наркоман|зависимость|доза|инъекция|курение|нюхать|колоться)\b", re.IGNORECASE
            ),
            re.compile(
                r"\b(трава|косяк|джойнт|булька|спиды|экстази|лсд|мескалин)\b", re.IGNORECASE
            ),
        ]

        # Сексуальный контент
        patterns[ContentCategory.SEXUAL] = [
            re.compile(
                r"\b(секс|порно|интим|голый|голая|раздеться|лечь|трахать|ебать|порнография)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(оргазм|возбуждение|мастурбация|педофил|изнасилование|проституция)\b",
                re.IGNORECASE,
            ),
        ]

        # Политика и экстремизм
        patterns[ContentCategory.POLITICS] = [
            re.compile(
                r"\b(путин|зеленский|байден|трамп|выборы|голосование|партия|политика|власть)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(революция|переворот|протест|митинг|демонстрация|бунт|мятеж)\b", re.IGNORECASE
            ),
        ]

        patterns[ContentCategory.EXTREMISM] = [
            re.compile(
                r"\b(фашизм|нацизм|терроризм|ислам|джихад|расизм|ксенофобия|геноцид)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(скинхед|неонацист|террорист|боевик|радикал|экстремист)\b", re.IGNORECASE
            ),
        ]

        # Буллинг
        patterns[ContentCategory.BULLYING] = [
            re.compile(
                r"\b(дурак|тупой|идиот|дебил|кретин|придурок|неудачник|лузер|толстый|урод)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(ненавижу|презираю|убил бы|убью|убейся|сдохни|покончи с собой)\b", re.IGNORECASE
            ),
        ]

        # Мошенничество
        patterns[ContentCategory.SCAM] = [
            re.compile(
                r"\b(деньги|заработать|доход|прибыль|инвестиции|криптовалюта|биткоин|майнинг)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(скидка|акция|бесплатно|подарок|выигрыш|приз|лотерея|казино)\b", re.IGNORECASE
            ),
        ]

        # Спам
        patterns[ContentCategory.SPAM] = [
            re.compile(
                r"\b(реклама|продажа|купить|заказать|доставка|скидка|промокод|акция)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(подписка|регистрация|ссылка|сайт|телефон|звонок|сообщение)\b", re.IGNORECASE
            ),
        ]

        return patterns

    def _build_educational_contexts(self) -> dict[str, list[str]]:
        """Создает контексты, где обычно допустим образовательный контент"""
        return {
            "biology": ["анатомия", "физиология", "репродукция", "генетика", "эволюция"],
            "history": ["война", "революция", "политика", "государство", "власть"],
            "chemistry": ["наркотик", "химия", "вещество", "реакция", "токсин"],
            "psychology": ["психика", "стресс", "депрессия", "тревога", "эмоции"],
            "literature": ["роман", "поэзия", "драма", "трагедия", "герой"],
            "physics": ["взрыв", "энергия", "сила", "давление", "температура"],
        }

    def _build_intent_indicators(self) -> dict[str, list[str]]:
        """Создает индикаторы намерений пользователя"""
        return {
            "educational": [
                "изучать",
                "узнать",
                "понять",
                "объяснить",
                "научить",
                "учебник",
                "урок",
                "задача",
            ],
            "curiosity": ["интересно", "почему", "как", "что", "зачем", "когда", "где"],
            "harmful": ["как сделать", "где купить", "как достать", "помоги найти", "покажи"],
            "dangerous": ["хочу", "планирую", "собираюсь", "буду", "решил"],
        }

    def _build_synonyms(self) -> dict[str, list[str]]:
        """Создает синонимы и эвфемизмы для запрещенных слов.
        ВАЖНО: только однозначный сленг. НЕ включать общеупотребительные слова
        вроде «химия», «отношения», «металл» — они ломают образовательные запросы.
        """
        return {
            "наркотики": ["травка", "дурь"],
            "оружие": ["ствол", "пушка"],
        }

    async def moderate_content(
        self, content: str, user_context: dict[str, Any] = None
    ) -> ModerationResult:
        """
        Основной метод модерации контента

        Args:
            content: Текст для проверки
            user_context: Контекст пользователя (возраст, история и т.д.)

        Returns:
            ModerationResult: Результат анализа
        """
        if not content or not content.strip():
            return ModerationResult(
                is_safe=True,
                level=ModerationLevel.SAFE,
                category=None,
                confidence=1.0,
                reason="Пустое сообщение",
                suggested_action="approve",
            )

        # Проверяем, является ли запрос образовательным запросом про взрослые темы
        # (деньги, ЖКУ, документы и т.д.) - такие запросы НЕ блокируем
        try:
            from bot.services.adult_topics_service import get_adult_topics_service

            adult_topics_service = get_adult_topics_service()
            detected_adult_topic = adult_topics_service.detect_topic(content)

            if detected_adult_topic:
                logger.debug(
                    f"✅ Образовательный запрос про взрослую тему: {detected_adult_topic.title}"
                )
                return ModerationResult(
                    is_safe=True,
                    level=ModerationLevel.SAFE,
                    category=ContentCategory.EDUCATION,
                    confidence=1.0,
                    reason=f"Образовательный запрос: {detected_adult_topic.title}",
                    suggested_action="approve",
                )
        except Exception as e:
            logger.debug(f"⚠️ Ошибка проверки взрослых тем: {e}")

        # Нормализуем текст
        normalized_content = self._normalize_text(content)

        # Анализируем контекст
        context_analysis = self._analyze_context(normalized_content, user_context)

        # Проверяем категории контента
        category_results = []
        for category, patterns in self._category_patterns.items():
            result = self._check_category(normalized_content, category, patterns)
            if result:
                category_results.append(result)

        # Анализируем намерения
        intent_analysis = self._analyze_intent(normalized_content)

        # Принимаем решение
        final_result = self._make_decision(
            category_results, intent_analysis, context_analysis, user_context
        )

        # Логируем результат
        self._log_moderation_result(content, final_result)

        return final_result

    def _normalize_text(self, text: str) -> str:
        """Нормализует текст для анализа"""
        # Убираем лишние пробелы
        text = re.sub(r"\s+", " ", text.strip())

        # Заменяем синонимы на основные слова
        for main_word, synonyms in self._synonyms.items():
            for synonym in synonyms:
                text = re.sub(rf"\b{synonym}\b", main_word, text, flags=re.IGNORECASE)

        return text.lower()

    def _analyze_context(
        self,
        content: str,
        user_context: dict[str, Any] = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Анализирует образовательный контекст"""
        context_score = 0
        detected_subjects = []

        # Проверяем образовательные контексты
        for subject, keywords in self._educational_contexts.items():
            for keyword in keywords:
                if keyword in content:
                    context_score += 1
                    detected_subjects.append(subject)
                    break

        return {
            "score": context_score,
            "subjects": detected_subjects,
            "is_educational": context_score > 0,
        }

    def _check_category(
        self, content: str, category: ContentCategory, patterns: list[Pattern]
    ) -> dict | None:
        """Проверяет контент на конкретную категорию"""
        matches = []

        for pattern in patterns:
            found = pattern.findall(content)
            if found:
                matches.extend(found)

        if matches:
            confidence = min(len(matches) / 3.0, 1.0)  # Максимум 3 совпадения = 100%
            return {
                "category": category,
                "matches": matches,
                "confidence": confidence,
                "count": len(matches),
            }

        return None

    def _analyze_intent(self, content: str) -> dict[str, Any]:
        """Анализирует намерения пользователя"""
        intent_scores = {}

        for intent_type, indicators in self._intent_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in content:
                    score += 1
            intent_scores[intent_type] = score

        # Определяем основной тип намерения
        primary_intent = (
            max(intent_scores.items(), key=lambda x: x[1])[0] if intent_scores else "unknown"
        )

        return {
            "scores": intent_scores,
            "primary": primary_intent,
            "is_harmful": intent_scores.get("harmful", 0) > 0
            or intent_scores.get("dangerous", 0) > 0,
            "is_educational": intent_scores.get("educational", 0) > 0,
        }

    def _make_decision(
        self,
        category_results: list[dict],
        intent_analysis: dict,
        context_analysis: dict,
        user_context: dict[str, Any] = None,  # noqa: ARG002
    ) -> ModerationResult:
        """Принимает финальное решение по модерации"""
        # Если нет категорий - безопасно
        if not category_results:
            return ModerationResult(
                is_safe=True,
                level=ModerationLevel.SAFE,
                category=None,
                confidence=1.0,
                reason="Контент не содержит запрещенных тем",
                suggested_action="approve",
            )

        # Находим самую серьезную категорию
        primary_category = max(category_results, key=lambda x: x["confidence"])
        category = primary_category["category"]
        confidence = primary_category["confidence"]

        # Учитываем образовательный контекст
        if context_analysis["is_educational"] and intent_analysis["is_educational"]:
            confidence *= 0.3  # Снижаем серьезность для образовательного контента

        # Определяем уровень модерации
        if confidence < 0.3:
            level = ModerationLevel.SAFE
            is_safe = True
        elif confidence < 0.6:
            level = ModerationLevel.WARNING
            is_safe = True
        elif confidence < 0.8:
            level = ModerationLevel.BLOCKED
            is_safe = False
        else:
            level = ModerationLevel.DANGEROUS
            is_safe = False

        # Формируем ответ
        reason = f"Обнаружена тема: {category.value} (уверенность: {confidence:.2f})"

        if context_analysis["is_educational"]:
            reason += " в образовательном контексте"

        suggested_action = self._get_suggested_action(level, category, confidence)
        alternative_response = self._get_alternative_response(category, context_analysis)

        return ModerationResult(
            is_safe=is_safe,
            level=level,
            category=category,
            confidence=confidence,
            reason=reason,
            suggested_action=suggested_action,
            alternative_response=alternative_response,
        )

    def _get_suggested_action(
        self,
        level: ModerationLevel,
        category: ContentCategory,  # noqa: ARG002
        confidence: float,  # noqa: ARG002
    ) -> str:
        """Возвращает рекомендуемое действие"""
        actions = {
            ModerationLevel.SAFE: "approve",
            ModerationLevel.WARNING: "approve_with_warning",
            ModerationLevel.BLOCKED: "block_with_alternative",
            ModerationLevel.DANGEROUS: "block_immediately",
        }
        return actions[level]

    def _get_alternative_response(
        self, category: ContentCategory, context_analysis: dict
    ) -> str | None:
        """Возвращает альтернативный безопасный ответ"""
        alternatives = {
            ContentCategory.VIOLENCE: "Давайте поговорим о мирных способах решения конфликтов! 🤝",
            ContentCategory.DRUGS: "Лучше обсудим здоровый образ жизни и спорт! 💪",
            ContentCategory.SEXUAL: "Давайте поговорим о дружбе и уважении! 💙",
            ContentCategory.POLITICS: "Обсудим лучше науку, искусство или спорт! 🎨",
            ContentCategory.BULLYING: "Давайте говорить друг с другом с уважением! 🌟",
            ContentCategory.SCAM: "Лучше обсудим честные способы заработка! 💰",
        }

        if context_analysis["is_educational"]:
            return "Это важная тема для изучения! Расскажи больше о том, что именно тебя интересует? 📚"

        return alternatives.get(category, "Давайте поговорим о чем-то более подходящем! 😊")

    def _log_moderation_result(self, content: str, result: ModerationResult):
        """Логирует результат модерации"""
        if result.level in [ModerationLevel.BLOCKED, ModerationLevel.DANGEROUS]:
            logger.warning(
                f"🚫 BLOCKED CONTENT | Level: {result.level.value} | "
                f"Category: {result.category.value if result.category else 'None'} | "
                f"Confidence: {result.confidence:.2f} | "
                f"Reason: {result.reason} | "
                f"Content: {content[:100]}..."
            )
        else:
            logger.info(
                f"✅ SAFE CONTENT | Level: {result.level.value} | "
                f"Confidence: {result.confidence:.2f} | "
                f"Content: {content[:50]}..."
            )

    async def get_moderation_stats(self) -> dict[str, Any]:
        """Возвращает статистику модерации"""
        # Здесь можно добавить сбор статистики из базы данных
        return {
            "filter_level": self.filter_level,
            "categories_monitored": len(self._category_patterns),
            "educational_contexts": len(self._educational_contexts),
            "synonyms_tracked": sum(len(syns) for syns in self._synonyms.values()),
        }
