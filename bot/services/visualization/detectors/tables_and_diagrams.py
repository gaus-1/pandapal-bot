"""
Детекция предметных таблиц, хронологий и периодической таблицы.

Покрывает: таблицы по всем школьным предметам (математика, химия, физика,
английский, русский, география, информатика, обществознание),
исторические хронологии, периодическую таблицу Менделеева.

Карты, физические графики и графики математических функций вынесены
в отдельные модули (maps, physics, math_graphs).
"""

from __future__ import annotations

import re

from loguru import logger


def detect_subject_tables_and_diagrams(
    text_lower: str,
    viz_service,
    _has_visualization_request: bool = True,
    _has_context_pattern: bool = False,
) -> tuple[bytes | None, str | None]:
    """
    Детектирует запросы на предметные таблицы и хронологии.

    Args:
        text_lower: Текст запроса в нижнем регистре.
        viz_service: Экземпляр VisualizationService с методами генерации.
        has_visualization_request: (deprecated, не используется).
        has_context_pattern: (deprecated, не используется).

    Returns:
        (image_bytes, visualization_type) или (None, None).
    """

    # 1. Таблица спряжения/сопряжения глаголов
    verb_patterns = [
        r"табл[иы]ц[аеы]?\s+сопряжени[яе]\s+глагол",
        r"табл[иы]ц[аеы]?\s+спряжени[яе]\s+глагол",
        r"сопряжени[яе]\s+глагол",
        r"спряжени[яе]\s+глагол",
        r"(?<!умножени[яе])(?<!сложени[яе])(?<!вычитани[яе])(?<!делени[яе])табл[иы]ц[аеы]?\s+сопряжени[яе]",
        r"(?<!умножени[яе])(?<!сложени[яе])(?<!вычитани[яе])(?<!делени[яе])табл[иы]ц[аеы]?\s+спряжени[яе]",
    ]
    for pattern in verb_patterns:
        if re.search(pattern, text_lower):
            image = viz_service.generate_russian_verb_conjugation_table()
            if image:
                logger.info("📊 Детектирована таблица спряжения/сопряжения глаголов")
                return image, "table"

    # 2. Алгебра: степени 2 и 10
    if "степен" in text_lower and (
        "2" in text_lower or "10" in text_lower or "двойк" in text_lower or "два" in text_lower
    ):
        image = viz_service.generate_powers_of_2_and_10_table()
        if image:
            logger.info("📊 Детектирована таблица степеней чисел 2 и 10")
            return image, "table"

    # 3. Простые числа
    if (
        ("прост" in text_lower and "числ" in text_lower)
        or "решето" in text_lower
        or "эратосфен" in text_lower
    ):
        image = viz_service.generate_prime_numbers_table()
        if image:
            logger.info("📊 Детектирована таблица простых чисел")
            return image, "table"

    # 4. Формулы сокращенного умножения
    if re.search(
        r"(?:табл[иы]ц[аеы]?\s+)?(?:формул[ы]?\s+сокращенн|сокращенн[ое]?\s+умножен)",
        text_lower,
    ):
        image = viz_service.generate_abbreviated_multiplication_formulas_table()
        if image:
            logger.info("📊 Детектирована таблица формул сокращенного умножения")
            return image, "table"

    # 5. Свойства степеней
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:свойств[а]?\s+степен)", text_lower):
        image = viz_service.generate_power_properties_table()
        if image:
            logger.info("📊 Детектирована таблица свойств степеней")
            return image, "table"

    # 6. Свойства квадратного корня
    if re.search(
        r"(?:табл[иы]ц[аеы]?\s+)?(?:свойств[а]?\s+корн|квадратн[ый]?\s+корен)", text_lower
    ):
        image = viz_service.generate_square_root_properties_table()
        if image:
            logger.info("📊 Детектирована таблица свойств квадратного корня")
            return image, "table"

    # 7. Стандартный вид числа
    if "стандартн" in text_lower and "вид" in text_lower:
        image = viz_service.generate_standard_form_table()
        if image:
            logger.info("📊 Детектирована таблица стандартного вида числа")
            return image, "table"

    # 8. Квадраты и кубы
    if ("квадрат" in text_lower and "куб" in text_lower) and "умнож" not in text_lower:
        image = viz_service.generate_squares_and_cubes_table()
        if image:
            logger.info("📊 Детектирована таблица квадратов и кубов")
            return image, "table"

    # 8a. Геометрия: формулы объёмов (все 3D фигуры)
    volume_patterns = [
        r"(?:табл[иы]ц[аеы]?\s+)?(?:формул[ы]?\s+объёмов|объёмов?\s+фигур)",
        r"объёмн[ые]?\s+фигур[ы]?",
        r"3d\s+фигур",
        r"объём\s+фигур",
        r"формул[ы]?\s+объём",
        r"пространственн[ые]?\s+тел[а]?",
    ]
    for pattern in volume_patterns:
        if re.search(pattern, text_lower.replace("объем", "объём")):
            image = viz_service.generate_geometry_volume_formulas_table()
            if image:
                logger.info("📊 Детектирована таблица формул объёмов")
                return image, "table"
            break

    # 8b. Геометрия: формулы площадей плоских фигур
    area_patterns = [
        r"(?:табл[иы]ц[аеы]?\s+)?(?:формул[ы]?\s+площадей|площадей?\s+фигур)",
        r"плоских\s+фигур",
        r"формул[ы]?\s+площад",
        r"площад[и]?\s+(?:треугольник|круг|трапец)",
    ]
    for pattern in area_patterns:
        if re.search(pattern, text_lower):
            image = viz_service.generate_geometry_area_formulas_table()
            if image:
                logger.info("📊 Детектирована таблица формул площадей")
                return image, "table"
            break

    # 9. Полная таблица умножения
    has_table = "табл" in text_lower
    has_multiply = "умнож" in text_lower
    has_number_pattern = re.search(r"умнож[а-я]*\s+на\s+\d+", text_lower)
    has_specific_table = re.search(
        r"(?:глагол|падеж|алфавит|букв|звук|орфограф|пунктуац|морфемн|стил\s+реч|"
        r"сопряжени[яе]|спряжени[яе]|времен[а]?\s+год|месяц|часов[ые]?\s+пояс|"
        r"страны?|хронологи|ветв[и]?\s+власт|систем[ы]?\s+счислени)",
        text_lower,
    )
    if has_table and has_multiply and not has_number_pattern and not has_specific_table:
        image = viz_service.generate_full_multiplication_table()
        if image:
            logger.info("📊 Детектирована полная таблица умножения")
            return image, "table"

    # 10. Дополнительные паттерны полной таблицы
    full_table_patterns = [
        r"^покажи\s+табл\w*\s*умножени[яе]\s*$",
        r"^выведи\s+табл\w*\s*умножени[яе]\s*$",
        r"табл\w*\s*умножени[яе]\s+на\s+все",
        r"полная\s+табл\w*\s*умножени[яе]",
    ]
    for pattern in full_table_patterns:
        if re.search(pattern, text_lower):
            image = viz_service.generate_full_multiplication_table()
            if image:
                logger.info("📊 Детектирована полная таблица умножения")
            return image, "table"

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
                    image = viz_service.generate_multiplication_table_image(number)
                    if image:
                        logger.info(f"📊 Детектирована таблица умножения на {number}")
                        return image, "table"
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
            image = viz_service.generate_chemistry_solubility_table()
            if image:
                logger.info("📊 Детектирована таблица растворимости")
            return image, "table"

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
            image = viz_service.generate_chemistry_valence_table()
            if image:
                logger.info("📊 Детектирована таблица валентности")
            return image, "table"

    # 14. Физика: константы
    constants_patterns = [
        r"табл[иы]ц[аеы]?\s+(?:физическ|констант)",
        r"физическ[ие]?\s+констант[ы]?",
        r"табл[иы]ц[аеы]?\s+констант",
    ]
    for pattern in constants_patterns:
        if re.search(pattern, text_lower):
            image = viz_service.generate_physics_constants_table()
            if image:
                logger.info("📊 Детектирована таблица физических констант")
            return image, "table"

    # 15. Английский: времена
    english_tenses_patterns = [
        r"табл[иы]ц[аеы]?\s+времен",
        r"времен[а]?\s+(?:английск|англ)",
        r"табл[иы]ц[аеы]?\s+(?:английск|англ)\s+времен",
    ]
    for pattern in english_tenses_patterns:
        if re.search(pattern, text_lower):
            image = viz_service.generate_english_tenses_table()
            if image:
                logger.info("📊 Детектирована таблица времен английского")
            return image, "table"

    # 16. Английский: неправильные глаголы
    if "неправильн" in text_lower and "глагол" in text_lower:
        image = viz_service.generate_english_irregular_verbs_table()
        if image:
            logger.info("📊 Детектирована таблица неправильных глаголов")
            return image, "table"

    # 17. Математика: сложение
    if re.search(r"табл[иы]ц[аеы]?\s+сложени[яе]", text_lower):
        image = viz_service.generate_addition_table()
        if image:
            logger.info("📊 Детектирована таблица сложения")
            return image, "table"

    # 18. Математика: вычитание
    if re.search(r"табл[иы]ц[аеы]?\s+вычитани[яе]", text_lower):
        image = viz_service.generate_subtraction_table()
        if image:
            logger.info("📊 Детектирована таблица вычитания")
            return image, "table"

    # 19. Математика: деление
    if re.search(r"табл[иы]ц[аеы]?\s+делени[яе]", text_lower):
        image = viz_service.generate_division_table()
        if image:
            logger.info("📊 Детектирована таблица деления")
            return image, "table"

    # 20. Единицы измерения
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?единиц[ы]?\s+измерени[яе]", text_lower):
        image = viz_service.generate_units_table()
        if image:
            logger.info("📊 Детектирована таблица единиц измерения")
            return image, "table"

    # 21. Русский: алфавит
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:букв|алфавит|звук)", text_lower):
        image = viz_service.generate_russian_alphabet_table()
        if image:
            logger.info("📊 Детектирована таблица букв и звуков")
            return image, "table"

    # 22. Русский: падежи
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:падеж|склонени)", text_lower):
        image = viz_service.generate_russian_cases_table()
        if image:
            logger.info("📊 Детектирована таблица падежей")
            return image, "table"

    # 23. Русский: орфография
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:орфограф|правописан)", text_lower):
        image = viz_service.generate_russian_orthography_table()
        if image:
            logger.info("📊 Детектирована таблица орфографии")
            return image, "table"

    # 24. Русский: пунктуация
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:пунктуац|знак[и]?\s+препинан)", text_lower):
        image = viz_service.generate_russian_punctuation_table()
        if image:
            logger.info("📊 Детектирована таблица пунктуации")
            return image, "table"

    # 25. Русский: морфемный разбор
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:морфемн|разбор\s+слов)", text_lower):
        image = viz_service.generate_russian_word_analysis_table()
        if image:
            logger.info("📊 Детектирована таблица морфемного разбора")
            return image, "table"

    # 26. Русский: стили речи
    if "стил" in text_lower and "реч" in text_lower:
        image = viz_service.generate_russian_speech_styles_table()
        if image:
            logger.info("📊 Детектирована таблица стилей речи")
            return image, "table"

    # 27. Окружающий мир: времена года
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:времен[а]?\s+год|месяц|дн[ия]?\s+недел)", text_lower):
        image = viz_service.generate_seasons_months_table()
        if image:
            logger.info("📊 Детектирована таблица времен года")
            return image, "table"

    # 28. География: природные зоны
    if re.search(r"природн[ые]?\s+зон", text_lower):
        image = viz_service.generate_natural_zones_table()
        if image:
            logger.info("📊 Детектирована таблица природных зон")
            return image, "table"

    # 29. География: часовые пояса
    if re.search(r"часов[ые]?\s+пояс", text_lower):
        image = viz_service.generate_time_zones_table()
        if image:
            logger.info("📊 Детектирована таблица часовых поясов")
            return image, "table"

    # 30. География: страны
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:крупнейш|страны?\s+мир)", text_lower):
        image = viz_service.generate_countries_table()
        if image:
            logger.info("📊 Детектирована таблица стран")
            return image, "table"

    # 31. История: хронология
    history_patterns = [
        r"(?:табл[иы]ц[аеы]?\s+)?(?:хронологи|истори[яи]?\s+росси)",
        r"карт[аеыу]?\s+войн[ы]",
        r"где\s+проходил\s+крестов[ый]?\s+поход",
        r"схем[аеыу]?\s+битв[ы]?\s+при\s+бородино",
        r"год[ы]?\s+правлени[яе]",
        r"хронологи[яи]",
        r"реформ[ы]",
        r"лент[аеыу]?\s+времен[и]",
    ]
    for pattern in history_patterns:
        if re.search(pattern, text_lower):
            if "схем" in text_lower and "битв" in text_lower:
                battle = "бородино"
                battles = ["бородино", "куликово", "полтава", "сталинград", "ледово"]
                for b in battles:
                    if b in text_lower:
                        battle = b
                        break
                image = viz_service.generate_battle_scheme(battle)
                if image:
                    logger.info(f"📊 Детектирована схема битвы: {battle}")
                    return image, "scheme"
            elif "хронолог" in text_lower or "войн" in text_lower:
                war = "вов"
                if "1812" in text_lower or "наполеон" in text_lower or "отечественн" in text_lower:
                    war = "1812"
                elif "северн" in text_lower or "швец" in text_lower:
                    war = "северная"
                image = viz_service.generate_war_timeline(war)
                if image:
                    logger.info(f"📊 Детектирована хронология войны: {war}")
                    return image, "table"
            else:
                image = viz_service.generate_history_timeline_table()
                if image:
                    logger.info("📊 Детектирована хронологическая таблица")
                    return image, "table"

    # 32. Обществознание: ветви власти
    if re.search(r"ветв[и]?\s+власт", text_lower):
        image = viz_service.generate_government_branches_table()
        if image:
            logger.info("📊 Детектирована таблица ветвей власти")
            return image, "table"

    # 33. Информатика: системы счисления
    if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:систем[ы]?\s+счислени|двоичн|восьмеричн)", text_lower):
        image = viz_service.generate_number_systems_table()
        if image:
            logger.info("📊 Детектирована таблица систем счисления")
            return image, "table"

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
            image = viz_service.generate_periodic_table_simple()
            if image:
                logger.info("📊 Детектирована периодическая таблица Менделеева")
            return image, "table"

    return None, None
