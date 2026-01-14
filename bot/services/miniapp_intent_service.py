"""
Сервис для понимания намерений пользователя в Mini App.

Парсит весь текст/аудио запроса, извлекает все слова, цифры, числа
и определяет, что именно нужно визуализировать.
"""

import re
from dataclasses import dataclass
from typing import Literal

from loguru import logger


@dataclass
class VisualizationIntent:
    """
    Намерение пользователя на визуализацию.

    Attributes:
        kind: Тип визуализации ("table" | "graph" | "both" | None)
        subject: Предмет ("math" | "physics" | "chemistry" | ...)
        items: Список элементов для визуализации (числа для таблиц, функции для графиков)
        raw_text: Оригинальный текст запроса
        needs_explanation: Нужно ли текстовое объяснение (True если "объясни", "расскажи")
    """

    kind: Literal["table", "graph", "both", None] = None
    subject: str | None = None
    items: list[int | str] = None
    raw_text: str = ""
    needs_explanation: bool = False

    def __post_init__(self):
        """Инициализация после создания."""
        if self.items is None:
            self.items = []


class MiniappIntentService:
    """
    Сервис для понимания намерений пользователя.

    Парсит весь текст запроса, извлекает все числа, слова, контекст.
    """

    # Паттерны для извлечения чисел
    NUMBER_PATTERN = re.compile(r"\b(\d+)\b")
    # Паттерны для таблиц умножения
    MULTIPLICATION_PATTERNS = [
        r"табл[иы]ц[аеы]?\s*умножени[яе]\s*на\s*(\d+)",
        r"табл[иы]ц[аеы]?\s*умножени[яе]\s+(\d+)",
        r"умножени[яе]\s+на\s*(\d+)",
        r"умнож[а-я]*\s+(\d+)",
        r"(\d+)\s*[×x*]\s*(\d+)",  # "7×9" или "7 x 9"
    ]
    # Паттерны для графиков функций
    GRAPH_PATTERNS = [
        r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
        r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
        r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
        r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
    ]
    # Слова-соединители для множественных запросов
    CONJUNCTIONS = ["и", "и", "а", "также", "плюс", "еще", "ещё"]
    # Слова для запросов на объяснение
    EXPLANATION_WORDS = ["объясни", "расскажи", "объясни", "опиши", "что такое", "как"]

    def parse_intent(self, user_message: str) -> VisualizationIntent:
        """
        Парсит весь текст запроса и определяет намерение.

        Args:
            user_message: Полный текст запроса пользователя

        Returns:
            VisualizationIntent: Структурированное намерение
        """
        intent = VisualizationIntent(raw_text=user_message)
        text_lower = user_message.lower()

        # Проверяем, нужен ли текстовый ответ
        intent.needs_explanation = any(word in text_lower for word in self.EXPLANATION_WORDS)

        # Извлекаем ВСЕ числа из текста
        all_numbers = [int(match.group(1)) for match in self.NUMBER_PATTERN.finditer(user_message)]
        logger.info(f"🔍 Intent: Найдены числа в запросе: {all_numbers}")

        # Проверяем запросы на таблицы умножения
        # КРИТИЧНО: Сначала проверяем все числа из текста (приоритет для "3, 5 и 7")
        # Затем паттерны как fallback
        multiplication_numbers = []

        # КРИТИЧНО: Если есть упоминание таблицы/умножения И числа 1-10 в тексте - используем ВСЕ числа
        # Это обрабатывает случаи "таблица на 7 и 9" или "таблица на 3, 5 и 7"
        if ("таблица" in text_lower or "умножение" in text_lower) and any(
            1 <= n <= 10 for n in all_numbers
        ):
            # Используем ВСЕ числа из текста (приоритет)
            valid_numbers = sorted({n for n in all_numbers if 1 <= n <= 10})
            if valid_numbers:
                intent.kind = "table"
                intent.subject = "math"
                intent.items = valid_numbers
                logger.info(
                    f"📊 Intent: Таблица умножения на числа: {intent.items} "
                    f"(извлечено из всех чисел в тексте)"
                )
        else:
            # Fallback: проверяем паттерны (для случаев без явного упоминания "таблица")
            for pattern in self.MULTIPLICATION_PATTERNS:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    groups = match.groups()
                    for group in groups:
                        try:
                            num = int(group)
                            if 1 <= num <= 10:
                                multiplication_numbers.append(num)
                        except (ValueError, TypeError):
                            continue

            if multiplication_numbers:
                intent.kind = "table"
                intent.subject = "math"
                intent.items = sorted(set(multiplication_numbers))
                logger.info(
                    f"📊 Intent: Таблица умножения на числа: {intent.items} "
                    f"(извлечено из паттернов)"
                )

        # Проверяем запросы на графики
        graph_functions = []

        # Сначала проверяем стандартные функции по ключевым словам (приоритет)
        if "синус" in text_lower or "синусоид" in text_lower or "sin" in text_lower:
            graph_functions.append("sin(x)")
        if "косинус" in text_lower or "cos" in text_lower:
            graph_functions.append("cos(x)")
        if "тангенс" in text_lower or "tan" in text_lower:
            graph_functions.append("tan(x)")
        if "парабол" in text_lower or "порабол" in text_lower:
            graph_functions.append("x**2")
        if "экспонент" in text_lower or "exp" in text_lower:
            graph_functions.append("exp(x)")
        if "логарифм" in text_lower or "log" in text_lower:
            graph_functions.append("log(x)")

        # Затем парсим паттерны для извлечения формул
        for pattern in self.GRAPH_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                if match.groups():
                    expr = match.group(1).strip()
                    if expr:
                        # КРИТИЧНО: Парсим несколько функций из строки (разделители: "и", ",", "и y =")
                        # Примеры: "x² и y = x³" → ["x**2", "x**3"]
                        #          "синуса и косинуса" → уже обработано выше через ключевые слова

                        # Разделяем по "и" или ","
                        parts = re.split(r"\s+и\s+|,\s*|\s+и\s+y\s*=\s*", expr, flags=re.IGNORECASE)
                        for part in parts:
                            part = part.strip()
                            if not part:
                                continue

                            # Нормализуем выражение: убираем "y =", заменяем ², ³, ^
                            part = re.sub(r"^y\s*=\s*", "", part, flags=re.IGNORECASE)
                            part = part.replace("²", "**2").replace("³", "**3").replace("^", "**")

                            # Проверяем, что это валидное математическое выражение
                            # Разрешаем: x, числа, операторы, функции sin/cos/tan/exp/log/sqrt
                            if re.match(r"^[x\s+\-*/().\d\s]+$", part) or re.match(
                                r"^(sin|cos|tan|exp|log|sqrt|ln)\(x\)$", part, re.IGNORECASE
                            ):
                                # Нормализуем функции к стандартному виду
                                part = re.sub(r"^ln\(", "log(", part, flags=re.IGNORECASE)
                                graph_functions.append(part)
                            # Если это просто "x²" или "x³" без "y ="
                            elif re.match(r"^x[²³]$", part):
                                part = part.replace("²", "**2").replace("³", "**3")
                                graph_functions.append(part)

        if graph_functions:
            intent.kind = "graph" if intent.kind is None else "both"
            intent.subject = "math" if intent.subject is None else intent.subject
            # Убираем дубликаты, но сохраняем порядок
            # КРИТИЧНО: Фильтруем только валидные выражения (не сырой текст)
            valid_functions = []
            seen = set()
            for func in graph_functions:
                # Пропускаем сырой текст типа "синуса и косинуса"
                if not re.match(
                    r"^(sin|cos|tan|exp|log|sqrt)\(x\)$|^x\*\*?\d+$|^[x\s+\-*/().\d\s]+$",
                    func,
                    re.IGNORECASE,
                ):
                    continue
                if func not in seen:
                    seen.add(func)
                    valid_functions.append(func)
            intent.items = valid_functions
            logger.info(f"📈 Intent: Графики функций: {intent.items}")

        # Если нашли и таблицы и графики - это "both"
        if multiplication_numbers and graph_functions:
            intent.kind = "both"

        # Определяем предмет по ключевым словам (если еще не определили)
        # Расширенный список по всем предметам из школьной программы 1-9 классов
        if intent.subject is None:
            # Физика
            if any(
                word in text_lower
                for word in [
                    "физик",
                    "закон",
                    "ом",
                    "движени",
                    "скорост",
                    "ускорен",
                    "сила",
                    "энерги",
                    "ток",
                    "напряжен",
                    "колебан",
                    "волн",
                ]
            ):
                intent.subject = "physics"
            # Химия
            elif any(
                word in text_lower
                for word in [
                    "хими",
                    "растворим",
                    "менделеев",
                    "периодическ",
                    "валентност",
                    "реакц",
                    "веществ",
                    "элемент",
                ]
            ):
                intent.subject = "chemistry"
            # География
            elif any(
                word in text_lower
                for word in [
                    "географ",
                    "климат",
                    "страны",
                    "материк",
                    "океан",
                    "рельеф",
                    "природн",
                    "зон",
                ]
            ):
                intent.subject = "geography"
            # Русский язык
            elif any(
                word in text_lower
                for word in [
                    "русск",
                    "падеж",
                    "спряжен",
                    "склонен",
                    "орфограф",
                    "пунктуац",
                    "морфем",
                    "фонетик",
                ]
            ):
                intent.subject = "russian"
            # Английский язык
            elif any(
                word in text_lower
                for word in ["английск", "англ", "времен", "глагол", "неправильн"]
            ):
                intent.subject = "english"
            # Геометрия
            elif any(
                word in text_lower
                for word in [
                    "геометр",
                    "площад",
                    "объем",
                    "треугольник",
                    "четырехугольник",
                    "окружност",
                    "круг",
                ]
            ):
                intent.subject = "geometry"
            # Биология
            elif any(
                word in text_lower
                for word in [
                    "биолог",
                    "клетк",
                    "орган",
                    "систем",
                    "эволюц",
                    "экологи",
                ]
            ):
                intent.subject = "biology"
            # История
            elif any(
                word in text_lower
                for word in [
                    "истори",
                    "хронологи",
                    "правител",
                    "династи",
                    "войн",
                    "революц",
                ]
            ):
                intent.subject = "history"
            # Обществознание
            elif any(
                word in text_lower
                for word in [
                    "обществознан",
                    "общество",
                    "государств",
                    "власт",
                    "право",
                    "экономик",
                ]
            ):
                intent.subject = "social_studies"
            # Информатика
            elif any(
                word in text_lower
                for word in [
                    "информатик",
                    "программирован",
                    "алгоритм",
                    "систем",
                    "счислен",
                ]
            ):
                intent.subject = "computer_science"
            else:
                intent.subject = "math"  # По умолчанию математика

        logger.info(
            f"✅ Intent: kind={intent.kind}, subject={intent.subject}, "
            f"items={intent.items}, needs_explanation={intent.needs_explanation}"
        )

        # #region agent log
        try:
            import json as _json_debug
            import time as _time_debug

            debug_log_path = r"c:\Users\Vyacheslav\PandaPal\.cursor\debug.log"
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(
                    _json_debug.dumps(
                        {
                            "sessionId": "debug-session",
                            "runId": "intent",
                            "hypothesisId": "A",
                            "location": "miniapp_intent_service.py:parse_intent",
                            "message": "Результат разбора намерения",
                            "data": {
                                "raw_text": user_message[:200],
                                "kind": intent.kind,
                                "subject": intent.subject,
                                "items": intent.items,
                                "needs_explanation": intent.needs_explanation,
                            },
                            "timestamp": _time_debug.time() * 1000,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:
            pass
        # #endregion

        return intent


# Singleton
_intent_service_instance: MiniappIntentService | None = None


def get_intent_service() -> MiniappIntentService:
    """
    Получить глобальный экземпляр MiniappIntentService.

    Returns:
        MiniappIntentService: Экземпляр сервиса
    """
    global _intent_service_instance
    if _intent_service_instance is None:
        _intent_service_instance = MiniappIntentService()
    return _intent_service_instance
