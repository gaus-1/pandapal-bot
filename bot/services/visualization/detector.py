"""
Детектор запросов на визуализацию (SOLID: SRP, OCP).

Анализирует текст и определяет, нужна ли визуализация,
затем вызывает соответствующий метод генерации.

detect() — оркестратор, делегирующий логику подмодулям из detectors/.
"""

import re

from loguru import logger

from bot.config.geo_objects_data import NATURAL_OBJECTS_COORDS
from bot.config.response_rules import VISUALIZATION_TRIGGER_WORDS
from bot.services.visualization.detectors import (
    EXPLANATION_REQUEST_WORDS,
    VISUALIZATION_REQUEST_WORDS,
    detect_diagram,
    detect_map,
    detect_math_graph,
    detect_physics,
    detect_scheme,
    detect_subject_tables_and_diagrams,
)

try:
    import matplotlib

    matplotlib.use("Agg")
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class VisualizationDetector:
    """
    Детектор запросов на визуализацию.

    Анализирует текст пользователя и определяет, какой тип визуализации нужен.
    Использует паттерны для определения типа таблицы/графика.
    """

    def __init__(self, viz_service):
        """
        Инициализация детектора.

        Args:
            viz_service: Экземпляр VisualizationService с методами генерации
        """
        self.viz_service = viz_service

    def detect_geography_question(self, text: str) -> str | None:
        """
        Определяет, является ли запрос географическим вопросом типа "где находится X".

        Такие запросы НЕ должны сразу показывать карту — сначала текстовый ответ,
        затем кнопка "Показать карту?".

        Returns:
            Название объекта для карты или None.
        """
        text_lower = text.lower().strip()

        # Прямой запрос визуализации — не география-вопрос
        if any(kw in text_lower for kw in VISUALIZATION_TRIGGER_WORDS):
            return None

        # Паттерны: захватываем multi-word (река Волга, Чёрное море, ...)
        _WORD = r"[а-яёa-z\-]+"
        _WORDS = rf"{_WORD}(?:\s+{_WORD}){{0,4}}"

        geo_patterns = [
            rf"где\s+находится\s+({_WORDS})",
            rf"где\s+расположен[аоы]?\s+({_WORDS})",
            rf"где\s+(?:течёт|течет|протекает)\s+({_WORDS})",
            rf"в\s+какой\s+части\s+(?:мира|света)\s+находится\s+({_WORDS})",
            rf"на\s+каком\s+(?:континенте|материке)\s+находится\s+({_WORDS})",
            rf"расскажи\s+(?:про\s+)?(?:где\s+)?({_WORDS})\s+(?:находится|расположен)",
            rf"расскажи\s+(?:мне\s+)?про\s+({_WORDS})",
            rf"расскажи\s+(?:мне\s+)?о\s+({_WORDS})",
            rf"что\s+(?:ты\s+)?знаешь\s+(?:о|про)\s+({_WORDS})",
        ]

        for pattern in geo_patterns:
            match = re.search(pattern, text_lower)
            if not match:
                continue

            location = match.group(1).strip()
            # Убираем шумовые слова в конце
            location = re.sub(r"\s+(?:пожалуйста|плиз|плз|пож)$", "", location).strip()
            if len(location) < 2:
                continue

            location_lower = location.lower()

            # 1. Проверяем в справочнике природных объектов
            if self._is_known_natural_object(location_lower):
                logger.info(f"🗺️ Географический вопрос (природный объект): {location}")
                return location

            # 2. Нормализуем падежные окончания для стран/городов
            location_normalized = location_lower
            for ending in ["ию", "ии", "ей", "ью", "ой", "ый", "ая", "ое", "ах", "ях"]:
                if location_normalized.endswith(ending) and len(location_normalized) > 4:
                    base = location_normalized[: -len(ending)]
                    if ending in ("ию", "ии"):
                        location_normalized = base + "ия"
                    elif ending in ("ей", "ью"):
                        location_normalized = base + "ь"
                    elif ending == "ой":
                        location_normalized = base + "а"
                    break

            # 3. Проверяем в списке стран и городов
            if self._is_known_country_or_city(location_normalized):
                logger.info(f"🗺️ Географический вопрос (страна/город): {location}")
                return location

        return None

    @staticmethod
    def _is_known_natural_object(query: str) -> bool:
        """Проверяет, есть ли объект в справочнике природных объектов."""
        # 1. Прямое совпадение
        if query in NATURAL_OBJECTS_COORDS:
            return True
        # 2. Точное вхождение (min 5 chars, избегаем ложных: "китай" в "южно-китайское море")
        if len(query) >= 5:
            for key in NATURAL_OBJECTS_COORDS:
                if key == query:
                    return True
                # Ключ целиком содержит запрос (запрос — подстрока ключа)
                if len(key) >= 5 and query in key:
                    # Только если запрос — отдельное слово в ключе
                    key_words = key.split()
                    if query in key_words:
                        return True
        # 3. Multi-word: "река волга" → ищем "река волга" или "волга"
        words = query.split()
        if len(words) >= 2:
            # Полная фраза
            if query in NATURAL_OBJECTS_COORDS:
                return True
            # Последнее слово (имя объекта): "река волга" → "волга"
            obj_name = words[-1]
            if len(obj_name) >= 3 and obj_name in NATURAL_OBJECTS_COORDS:
                return True
            # Пробуем "тип имя" (нормализованный): "река волга"
            from bot.config.geo_objects_data import GEO_TYPE_PREFIXES

            if words[0] in GEO_TYPE_PREFIXES:
                normalized_prefix = GEO_TYPE_PREFIXES[words[0]]
                normalized_query = f"{normalized_prefix} {' '.join(words[1:])}"
                if normalized_query in NATURAL_OBJECTS_COORDS:
                    return True
        # 4. Стеммированный поиск (min 5 chars stem, не 3)
        if len(query) >= 6:
            stem = query[:-1]
            for key in NATURAL_OBJECTS_COORDS:
                if len(key) >= 5 and key.startswith(stem):
                    return True
        return False

    @staticmethod
    def _is_known_country_or_city(location: str) -> bool:
        """Проверяет, является ли название известной страной или городом."""
        known_locations = frozenset(
            {
                # Страны
                "китай",
                "россия",
                "сша",
                "америка",
                "франция",
                "германия",
                "италия",
                "испания",
                "япония",
                "корея",
                "индия",
                "бразилия",
                "австралия",
                "канада",
                "мексика",
                "египет",
                "турция",
                "греция",
                "польша",
                "украина",
                "англия",
                "великобритания",
                "нидерланды",
                "бельгия",
                "швейцария",
                "австрия",
                "швеция",
                "норвегия",
                "финляндия",
                "дания",
                "чехия",
                "венгрия",
                "румыния",
                "болгария",
                "сербия",
                "хорватия",
                "португалия",
                "ирландия",
                "исландия",
                "тайланд",
                "таиланд",
                "вьетнам",
                "индонезия",
                "филиппины",
                "малайзия",
                "сингапур",
                "иран",
                "ирак",
                "израиль",
                "саудовская",
                "оаэ",
                "эмираты",
                "катар",
                "пакистан",
                "афганистан",
                "казахстан",
                "узбекистан",
                "монголия",
                "грузия",
                "армения",
                "азербайджан",
                "аргентина",
                "чили",
                "перу",
                "колумбия",
                "венесуэла",
                "куба",
                "юар",
                "нигерия",
                "кения",
                "эфиопия",
                "марокко",
                "алжир",
                "беларусь",
                "белоруссия",
                "молдова",
                "литва",
                "латвия",
                "эстония",
                "кыргызстан",
                "таджикистан",
                "туркменистан",
                "непал",
                "бангладеш",
                "мьянма",
                "камбоджа",
                "лаос",
                "сирия",
                "иордания",
                "ливан",
                "йемен",
                "оман",
                "кувейт",
                "бахрейн",
                # Континенты и регионы
                "европа",
                "азия",
                "африка",
                "антарктида",
                "океания",
                "сибирь",
                "арктика",
                # Города
                "москва",
                "мск",
                "петербург",
                "питер",
                "спб",
                "новосибирск",
                "екатеринбург",
                "казань",
                "нижний новгород",
                "челябинск",
                "самара",
                "омск",
                "ростов",
                "уфа",
                "красноярск",
                "пермь",
                "воронеж",
                "волгоград",
                "краснодар",
                "сочи",
                "калининград",
                "лондон",
                "париж",
                "берлин",
                "рим",
                "мадрид",
                "барселона",
                "токио",
                "пекин",
                "шанхай",
                "сеул",
                "бангкок",
                "нью-йорк",
                "лос-анджелес",
                "чикаго",
                "торонто",
                "сидней",
                "дубай",
                "стамбул",
                "каир",
                "мумбаи",
                "дели",
            }
        )
        return any(loc in location or location in loc for loc in known_locations)

    def detect(self, text: str) -> tuple[bytes | None, str | None]:
        """
        Детектирует запрос на визуализацию и генерирует изображение.

        Оркестратор: делегирует логику подмодулям из detectors/.

        Args:
            text: Текст сообщения для анализа

        Returns:
            tuple: (Изображение визуализации или None, Тип визуализации или None)
        """
        if not MATPLOTLIB_AVAILABLE:
            return None, None

        text_lower = text.lower()

        # Определяем тип запроса
        has_visualization_request = any(word in text_lower for word in VISUALIZATION_REQUEST_WORDS)
        has_explanation_request = any(word in text_lower for word in EXPLANATION_REQUEST_WORDS)

        # Объяснение БЕЗ визуализации — пропускаем
        if has_explanation_request and not has_visualization_request:
            logger.debug("🔍 Запрос на объяснение без визуализации - пропускаем генерацию")
            return None, None

        # 1. Специализированные схемы (приоритет выше диаграмм)
        if has_visualization_request:
            result = detect_scheme(text_lower, self.viz_service)
            if result[0]:
                return result

            # 2. Универсальные диаграммы
            result = detect_diagram(text_lower, self.viz_service)
            if result[0]:
                return result

        # 3. Карты — проверяем ПЕРЕД ранним return, т.к. "карта X" может не иметь trigger word
        has_map_pattern = bool(
            re.search(
                r"карт[аеыу]\s+\w|на\s+карте|покажи\s+на\s+карте",
                text_lower,
            )
        )
        if has_map_pattern and not self.detect_geography_question(text):
            result = detect_map(text_lower, self.viz_service)
            if result[0]:
                return result

        # 4. Контекстные паттерны (без явного запроса визуализации)
        has_context_pattern = False
        if not has_visualization_request:
            context_visualization_patterns = [
                r"табл[иы]ц[аеы]?\s*умножени[яе]\s*на\s*\d+",
                r"график\s+функци[ии]",
                r"график\s+y\s*=",
                r"периодическая\s+табл[иы]ц[аеы]?\s*менделеева",
                r"(?:список|таблиц[аеы]?)\s*(?:значений?\s+)?квадратн\w*\s*корн",
            ]
            has_context_pattern = any(
                re.search(p, text_lower) for p in context_visualization_patterns
            )
            if not has_context_pattern:
                logger.debug(
                    "🔍 Нет явного запроса визуализации и контекстных паттернов - пропускаем"
                )
                return None, None

        # 5. Предметные таблицы, хронологии, периодическая таблица
        result = detect_subject_tables_and_diagrams(text_lower, self.viz_service)
        if result[0]:
            return result

        # 6. Карты (повторная проверка для trigger-word запросов: "покажи карту России")
        if not has_map_pattern and not self.detect_geography_question(text):
            result = detect_map(text_lower, self.viz_service)
            if result[0]:
                return result

        # 7. Физика (движение, скорость, электрика, тепловые процессы)
        result = detect_physics(text_lower, text, self.viz_service, has_visualization_request)
        if result[0]:
            return result

        # 8. Графики математических функций
        if has_visualization_request or has_context_pattern:
            result = detect_math_graph(text_lower, text, self.viz_service)
            if result[0]:
                return result

        return None, None
