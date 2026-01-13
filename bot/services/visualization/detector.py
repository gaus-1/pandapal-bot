"""
Детектор запросов на визуализацию (SOLID: SRP, OCP).

Анализирует текст и определяет, нужна ли визуализация,
затем вызывает соответствующий метод генерации.
"""

import re

from loguru import logger

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

    def detect(self, text: str) -> bytes | None:
        """
        Детектирует запрос на визуализацию и генерирует изображение.

        Args:
            text: Текст сообщения для анализа

        Returns:
            bytes: Изображение визуализации или None
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        text_lower = text.lower()

        # Приоритет: сначала специфичные запросы, затем общие

        # 1. Таблица сопряжения/спряжения глаголов (ВЫСОКИЙ ПРИОРИТЕТ - проверяем ПЕРВОЙ)
        # Более точный паттерн: проверяем "таблицу сопряжения глаголов" или "таблицу спряжения глаголов"
        verb_patterns = [
            r"табл[иы]ц[аеы]?\s+сопряжени[яе]\s+глагол",
            r"табл[иы]ц[аеы]?\s+спряжени[яе]\s+глагол",
            r"табл[иы]ц[аеы]?\s+сопряжени[яе]",
            r"табл[иы]ц[аеы]?\s+спряжени[яе]",
            r"сопряжени[яе]\s+глагол",
            r"спряжени[яе]\s+глагол",
        ]
        for pattern in verb_patterns:
            if re.search(pattern, text_lower):
                image = self.viz_service.generate_russian_verb_conjugation_table()
                if image:
                    logger.info("📊 Детектирована таблица спряжения/сопряжения глаголов")
                    return image

        # 2. Алгебра: степени 2 и 10
        if "степен" in text_lower and (
            "2" in text_lower or "10" in text_lower or "двойк" in text_lower or "два" in text_lower
        ):
            image = self.viz_service.generate_powers_of_2_and_10_table()
            if image:
                logger.info("📊 Детектирована таблица степеней чисел 2 и 10")
                return image

        # 3. Простые числа
        if (
            ("прост" in text_lower and "числ" in text_lower)
            or "решето" in text_lower
            or "эратосфен" in text_lower
        ):
            image = self.viz_service.generate_prime_numbers_table()
            if image:
                logger.info("📊 Детектирована таблица простых чисел")
                return image

        # 4. Формулы сокращенного умножения
        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:формул[ы]?\s+сокращенн|сокращенн[ое]?\s+умножен)",
            text_lower,
        ):
            image = self.viz_service.generate_abbreviated_multiplication_formulas_table()
            if image:
                logger.info("📊 Детектирована таблица формул сокращенного умножения")
                return image

        # 5. Свойства степеней
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:свойств[а]?\s+степен)", text_lower):
            image = self.viz_service.generate_power_properties_table()
            if image:
                logger.info("📊 Детектирована таблица свойств степеней")
                return image

        # 6. Свойства квадратного корня
        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:свойств[а]?\s+корн|квадратн[ый]?\s+корен)", text_lower
        ):
            image = self.viz_service.generate_square_root_properties_table()
            if image:
                logger.info("📊 Детектирована таблица свойств квадратного корня")
                return image

        # 7. Стандартный вид числа
        if "стандартн" in text_lower and "вид" in text_lower:
            image = self.viz_service.generate_standard_form_table()
            if image:
                logger.info("📊 Детектирована таблица стандартного вида числа")
                return image

        # 8. Квадраты и кубы (до таблицы умножения)
        if ("квадрат" in text_lower and "куб" in text_lower) and "умнож" not in text_lower:
            image = self.viz_service.generate_squares_and_cubes_table()
            if image:
                logger.info("📊 Детектирована таблица квадратов и кубов")
                return image

        # 9. Полная таблица умножения (без числа)
        has_table = "табл" in text_lower
        has_multiply = "умнож" in text_lower
        has_number_pattern = re.search(r"умнож[а-я]*\s+на\s+\d+", text_lower)
        if has_table and has_multiply and not has_number_pattern:
            image = self.viz_service.generate_full_multiplication_table()
            if image:
                logger.info("📊 Детектирована полная таблица умножения")
                return image

        # 10. Дополнительные паттерны для полной таблицы
        full_table_patterns = [
            r"^покажи\s+табл\w*\s*умножени[яе]\s*$",
            r"^выведи\s+табл\w*\s*умножени[яе]\s*$",
            r"табл\w*\s*умножени[яе]\s+на\s+все",
            r"полная\s+табл\w*\s*умножени[яе]",
        ]
        for pattern in full_table_patterns:
            if re.search(pattern, text_lower):
                image = self.viz_service.generate_full_multiplication_table()
                if image:
                    logger.info("📊 Детектирована полная таблица умножения")
                    return image

        # 11. Таблица умножения на конкретное число
        multiplication_patterns = [
            r"табл\w*\s*умножени[яе]\s*на\s*(\d+)",
            r"табл\w*\s*умножени[яе]\s+(\d+)",
            r"умножени[яе]\s+на\s*(\d+)",
            r"умнож[а-я]*\s+(\d+)",
        ]
        for pattern in multiplication_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    number = int(match.group(1))
                    if 1 <= number <= 10:
                        image = self.viz_service.generate_multiplication_table_image(number)
                        if image:
                            logger.info(f"📊 Детектирована таблица умножения на {number}")
                            return image
                except (ValueError, IndexError):
                    continue

        # 12. Химия: растворимость
        solubility_patterns = [
            r"табл[иы]ц[аеы]?\s+растворимост",
            r"растворимост[ьи]?\s+веществ",
            r"табл[иы]ц[аеы]?\s+раствор",
        ]
        for pattern in solubility_patterns:
            if re.search(pattern, text_lower):
                image = self.viz_service.generate_chemistry_solubility_table()
                if image:
                    logger.info("📊 Детектирована таблица растворимости")
                    return image

        # 13. Химия: валентность
        valence_patterns = [
            r"табл[иы]ц[аеы]?\s+валентност",
            r"валентност[ьи]?\s+элемент",
            r"табл[иы]ц[аеы]?\s+валент",
            r"покажи\s+табл[иы]ц[аеы]?\s+валентност",
            r"покажи\s+валентност",
            r"валентност[ьи]?",
        ]
        for pattern in valence_patterns:
            if re.search(pattern, text_lower):
                image = self.viz_service.generate_chemistry_valence_table()
                if image:
                    logger.info("📊 Детектирована таблица валентности")
                    return image

        # 14. Физика: константы
        constants_patterns = [
            r"табл[иы]ц[аеы]?\s+(?:физическ|констант)",
            r"физическ[ие]?\s+констант[ы]?",
            r"табл[иы]ц[аеы]?\s+констант",
        ]
        for pattern in constants_patterns:
            if re.search(pattern, text_lower):
                image = self.viz_service.generate_physics_constants_table()
                if image:
                    logger.info("📊 Детектирована таблица физических констант")
                    return image

        # 15. Английский: времена
        english_tenses_patterns = [
            r"табл[иы]ц[аеы]?\s+времен",
            r"времен[а]?\s+(?:английск|англ)",
            r"табл[иы]ц[аеы]?\s+(?:английск|англ)\s+времен",
        ]
        for pattern in english_tenses_patterns:
            if re.search(pattern, text_lower):
                image = self.viz_service.generate_english_tenses_table()
                if image:
                    logger.info("📊 Детектирована таблица времен английского")
                    return image

        # 16. Английский: неправильные глаголы
        if "неправильн" in text_lower and "глагол" in text_lower:
            image = self.viz_service.generate_english_irregular_verbs_table()
            if image:
                logger.info("📊 Детектирована таблица неправильных глаголов")
                return image

        # 17. Математика: сложение
        if re.search(r"табл[иы]ц[аеы]?\s+сложени[яе]", text_lower):
            image = self.viz_service.generate_addition_table()
            if image:
                logger.info("📊 Детектирована таблица сложения")
                return image

        # 18. Математика: вычитание
        if re.search(r"табл[иы]ц[аеы]?\s+вычитани[яе]", text_lower):
            image = self.viz_service.generate_subtraction_table()
            if image:
                logger.info("📊 Детектирована таблица вычитания")
                return image

        # 19. Математика: деление
        if re.search(r"табл[иы]ц[аеы]?\s+делени[яе]", text_lower):
            image = self.viz_service.generate_division_table()
            if image:
                logger.info("📊 Детектирована таблица деления")
                return image

        # 20. Единицы измерения
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?единиц[ы]?\s+измерени[яе]", text_lower):
            image = self.viz_service.generate_units_table()
            if image:
                logger.info("📊 Детектирована таблица единиц измерения")
                return image

        # 21. Русский: алфавит
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:букв|алфавит|звук)", text_lower):
            image = self.viz_service.generate_russian_alphabet_table()
            if image:
                logger.info("📊 Детектирована таблица букв и звуков")
                return image

        # 22. Русский: падежи
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:падеж|склонени)", text_lower):
            image = self.viz_service.generate_russian_cases_table()
            if image:
                logger.info("📊 Детектирована таблица падежей")
                return image

        # 23. Русский: орфография
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:орфограф|правописан)", text_lower):
            image = self.viz_service.generate_russian_orthography_table()
            if image:
                logger.info("📊 Детектирована таблица орфографии")
                return image

        # 24. Русский: пунктуация
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:пунктуац|знак[и]?\s+препинан)", text_lower):
            image = self.viz_service.generate_russian_punctuation_table()
            if image:
                logger.info("📊 Детектирована таблица пунктуации")
                return image

        # 25. Русский: морфемный разбор
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:морфемн|разбор\s+слов)", text_lower):
            image = self.viz_service.generate_russian_word_analysis_table()
            if image:
                logger.info("📊 Детектирована таблица морфемного разбора")
                return image

        # 26. Русский: стили речи
        if "стил" in text_lower and "реч" in text_lower:
            image = self.viz_service.generate_russian_speech_styles_table()
            if image:
                logger.info("📊 Детектирована таблица стилей речи")
                return image

        # 27. Окружающий мир: времена года
        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:времен[а]?\s+год|месяц|дн[ия]?\s+недел)", text_lower
        ):
            image = self.viz_service.generate_seasons_months_table()
            if image:
                logger.info("📊 Детектирована таблица времен года")
                return image

        # 28. География: природные зоны
        if re.search(r"природн[ые]?\s+зон", text_lower):
            image = self.viz_service.generate_natural_zones_table()
            if image:
                logger.info("📊 Детектирована таблица природных зон")
                return image

        # 29. География: часовые пояса
        if re.search(r"часов[ые]?\s+пояс", text_lower):
            image = self.viz_service.generate_time_zones_table()
            if image:
                logger.info("📊 Детектирована таблица часовых поясов")
                return image

        # 30. География: страны
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:крупнейш|страны?\s+мир)", text_lower):
            image = self.viz_service.generate_countries_table()
            if image:
                logger.info("📊 Детектирована таблица стран")
                return image

        # 31. История: хронология
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:хронологи|истори[яи]?\s+росси)", text_lower):
            image = self.viz_service.generate_history_timeline_table()
            if image:
                logger.info("📊 Детектирована хронологическая таблица")
                return image

        # 32. Обществознание: ветви власти
        if re.search(r"ветв[и]?\s+власт", text_lower):
            image = self.viz_service.generate_government_branches_table()
            if image:
                logger.info("📊 Детектирована таблица ветвей власти")
                return image

        # 33. Информатика: системы счисления
        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:систем[ы]?\s+счислени|двоичн|восьмеричн)", text_lower
        ):
            image = self.viz_service.generate_number_systems_table()
            if image:
                logger.info("📊 Детектирована таблица систем счисления")
                return image

        # 34. Химия: периодическая таблица Менделеева
        mendeleev_patterns = [
            r"табл[иы]ц[аеы]?\s*менделеева",
            r"периодическая\s+табл[иы]ц[аеы]?",
            r"менделеева",
            r"покажи\s+табл[иы]ц[аеы]?\s*менделеева",
            r"покажи\s+периодическую\s+табл[иы]ц[аеы]?",
        ]
        for pattern in mendeleev_patterns:
            if re.search(pattern, text_lower):
                image = self.viz_service.generate_periodic_table_simple()
                if image:
                    logger.info("📊 Детектирована периодическая таблица Менделеева")
                    return image

        # 35. Физика: графики движения
        if re.search(r"график\s+(?:пути|путь)\s+от\s+времен", text_lower):
            if re.search(r"равноускоренн", text_lower):
                image = self.viz_service.generate_physics_motion_graph("accelerated")
            else:
                image = self.viz_service.generate_physics_motion_graph("uniform")
            if image:
                logger.info("📈 Детектирован график пути от времени")
                return image

        # 36. Физика: график скорости
        if re.search(r"график\s+скорост[и]?\s+от\s+времен", text_lower):
            image = self.viz_service.generate_physics_motion_graph("velocity")
            if image:
                logger.info("📈 Детектирован график скорости от времени")
                return image

        # 37. Физика: закон Ома
        if re.search(
            r"(?:график\s+)?(?:закон\s+ома|сила\s+тока\s+от\s+напряжени|ом[а]?)", text_lower
        ):
            image = self.viz_service.generate_ohms_law_graph()
            if image:
                logger.info("📈 Детектирован график закона Ома")
                return image

        return None
