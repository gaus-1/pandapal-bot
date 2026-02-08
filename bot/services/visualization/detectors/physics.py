"""Детекция физических графиков и схем."""

from __future__ import annotations

import re

from loguru import logger


def detect_physics(
    text_lower: str,
    _text: str,
    viz_service,
    has_visualization_request: bool = True,
) -> tuple[bytes | None, str | None]:
    """
    Детектирует запросы на физические графики и схемы.

    Часть паттернов (движение, скорость, температура, климатограммы, блок-схемы,
    таблицы истинности) проверяется безусловно. Электрические схемы и тепловые
    процессы — только при наличии явного запроса визуализации.

    Args:
        text_lower: Текст запроса в нижнем регистре.
        text: Оригинальный текст запроса.
        viz_service: Экземпляр VisualizationService.
        has_visualization_request: Есть ли явный запрос визуализации.

    Returns:
        (image_bytes, visualization_type) или (None, None).
    """

    # Графики движения
    physics_motion_patterns = [
        r"график\s+(?:пути|путь)\s+от\s+времен",
        r"график\s+равномерн[ого]?\s+движени[яе]",
        r"график\s+равноускоренн[ого]?\s+движени[яе]",
        r"график\s+зависимост[ии]?\s+пути\s+от\s+времен",
        r"путь\s+от\s+времен[и]?\s+график",
        r"нарисуй[,\s]+как\s+едет\s+машин",
        r"график\s+пути",
        r"равноускоренное\s+движение\s+график",
        r"график\s+скорост[и]?\s+v\s*\(?\s*t\s*\)?",
        r"торможени[ея]",
    ]
    for pattern in physics_motion_patterns:
        if re.search(pattern, text_lower):
            if re.search(r"равноускоренн", text_lower):
                image = viz_service.generate_physics_motion_graph("accelerated")
            else:
                image = viz_service.generate_physics_motion_graph("uniform")
            if image:
                logger.info("📈 Детектирован график пути от времени")
                return image, "graph"

    # Графики скорости
    physics_velocity_patterns = [
        r"график\s+скорост[и]?\s+от\s+времен",
        r"график\s+зависимост[ии]?\s+скорост[и]?\s+от\s+времен",
        r"скорост[ьи]?\s+от\s+времен[и]?\s+график",
    ]
    for pattern in physics_velocity_patterns:
        if re.search(pattern, text_lower):
            image = viz_service.generate_physics_motion_graph("velocity")
            if image:
                logger.info("📈 Детектирован график скорости от времени")
                return image, "graph"

    # Геометрия: медиана треугольника
    if re.search(r"график\s+медиан", text_lower) or re.search(
        r"медиан[аы]?\s+треугольник", text_lower
    ):
        image = viz_service.generate_median_diagram()
        if image:
            logger.info("📈 Детектирована схема медианы треугольника")
            return image, "graph"

    # График температуры (линейный, по месяцам)
    if re.search(r"график\s+температур", text_lower):
        x_data = list(range(1, 13))
        y_data = [-5, -3, 2, 10, 18, 22, 24, 23, 16, 8, 2, -2]
        image = viz_service.generate_line_chart(
            x_data,
            y_data,
            title="График температуры по месяцам",
            x_label="Месяц",
            y_label="Температура, °C",
        )
        if image:
            logger.info("📈 Детектирован график температуры")
            return image, "graph"

    # Климатограммы
    climatogram_patterns = [
        r"климатограмм[аеыу]",
        r"построй\s+климатограмм[аеыу]",
        r"график\s+температур[ы]?\s+и\s+осадк[ов]",
        r"климат\s+(?:тайг[и]|степ[и]|пустын[и]|тропик[ов]|москв[ы]|сочи|арктик[и])",
        r"осадк[и]?\s+и\s+температур[а]",
    ]
    for pattern in climatogram_patterns:
        if re.search(pattern, text_lower):
            zone = "тайга"
            for z in [
                "тайга",
                "степь",
                "пустыня",
                "тропики",
                "москва",
                "сочи",
                "арктика",
                "экватор",
            ]:
                if z in text_lower:
                    zone = z
                    break
            image = viz_service.generate_climatogram(zone)
            if image:
                logger.info(f"📊 Детектирована климатограмма: {zone}")
                return image, "graph"

    # Блок-схемы алгоритмов
    flowchart_patterns = [
        r"блок[-\s]?схем[аеыу]",
        r"схем[аеыу]?\s+алгоритм[а]",
        r"алгоритм\s+в\s+виде\s+схем[ы]",
        r"нарисуй\s+алгоритм",
        r"покажи\s+алгоритм",
    ]
    for pattern in flowchart_patterns:
        if re.search(pattern, text_lower):
            alg_type = "linear"
            if re.search(r"ветвлени|если|условн", text_lower):
                alg_type = "branching"
            elif re.search(r"цикл|повтор|пока", text_lower):
                alg_type = "loop"
            elif re.search(r"факториал|n!", text_lower):
                alg_type = "factorial"
            image = viz_service.generate_flowchart(alg_type)
            if image:
                logger.info(f"📊 Детектирована блок-схема: {alg_type}")
                return image, "scheme"

    # Таблицы истинности
    truth_table_patterns = [
        r"таблиц[аеыу]?\s+истинност[и]",
        r"логическ[ая]?\s+операци[яи]",
        r"логическ[ое]?\s+и\b",
        r"логическ[ое]?\s+или\b",
        r"логическ[ое]?\s+не\b",
    ]
    for pattern in truth_table_patterns:
        if re.search(pattern, text_lower):
            operation = "and"
            if re.search(r"\bили\b|or", text_lower):
                operation = "or"
            elif re.search(r"\bне\b|not|отрицани", text_lower):
                operation = "not"
            elif re.search(r"исключающ|xor", text_lower):
                operation = "xor"
            image = viz_service.generate_truth_table(operation)
            if image:
                logger.info(f"📊 Детектирована таблица истинности: {operation}")
                return image, "table"

    # Электрические схемы и закон Ома — только при явном запросе визуализации
    if has_visualization_request:
        result = _detect_electric(text_lower, viz_service)
        if result[0]:
            return result

        result = _detect_thermal(text_lower, viz_service)
        if result[0]:
            return result

    return None, None


# Вспомогательные функции


def _detect_electric(text_lower: str, viz_service) -> tuple[bytes | None, str | None]:
    """Детектирует электрические схемы и графики закона Ома."""
    electric_scheme_patterns = [
        r"электрическ[ая]?\s+схем[аеыу]",
        r"электрическ[ая]?\s+цеп[ьи]",
        r"схем[аеыу]?\s+электрическ[ого]?\s+цеп[и]",
        r"схем[аеыу]?\s+с\s+ламп[ойой]",
        r"схем[аеыу]?\s+цеп[и]",
        r"нарисуй\s+лампочк[у]?\s+и\s+резистор",
        r"как\s+соединить\s+проводник",
    ]
    for pattern in electric_scheme_patterns:
        if re.search(pattern, text_lower):
            image = viz_service.generate_electric_circuit_scheme()
            if image:
                logger.info("📈 Детектирована электрическая схема цепи")
                return image, "scheme"
            image = viz_service.generate_ohms_law_graph()
            if image:
                logger.info("📈 Детектирована электрическая схема/график закона Ома")
                return image, "graph"

    physics_electric_patterns = [
        r"(?:график\s+)?закон\s+ом[а]?",
        r"сила\s+тока\s+от\s+напряжени[я]",
        r"вольт[-\s]?амперн[ая]?\s+характеристик[аи]",
        r"график\s+сил[ы]?\s+тока\s+от\s+напряжени[я]",
        r"напряжение\s+и\s+ток",
    ]
    for pattern in physics_electric_patterns:
        if re.search(pattern, text_lower):
            image = viz_service.generate_ohms_law_graph()
            if image:
                logger.info("📈 Детектирован график закона Ома")
                return image, "graph"

    return None, None


def _detect_thermal(text_lower: str, viz_service) -> tuple[bytes | None, str | None]:
    """Детектирует графики тепловых процессов."""
    physics_thermal_patterns = [
        r"график\s+нагревани[я]?\s+вод[ы]",
        r"когда\s+лед\s+тает",
        r"график\s+плавлени[я]",
        r"крив[ая]?\s+нагрева",
    ]
    for pattern in physics_thermal_patterns:
        if re.search(pattern, text_lower):
            substance = "лед"
            for s in ["свинец", "олово", "алюминий"]:
                if s in text_lower:
                    substance = s
                    break

            if re.search(r"охлаждени|остывани", text_lower):
                image = viz_service.generate_heating_cooling_graph("cooling")
            elif re.search(r"плавлени|тает|тающ", text_lower):
                image = viz_service.generate_melting_graph(substance)
            else:
                image = viz_service.generate_heating_cooling_graph("heating")

            if image:
                logger.info(f"📈 Детектирован график теплового процесса: {substance}")
                return image, "graph"

    return None, None
