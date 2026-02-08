"""Детекция универсальных диаграмм (bar, pie, line, histogram и др.)."""

from __future__ import annotations

import re

from loguru import logger


def detect_diagram(text_lower: str, viz_service) -> tuple[bytes | None, str | None]:
    """
    Детектирует запросы на универсальные диаграммы.

    Проверяется ТОЛЬКО при наличии явного запроса визуализации.

    Args:
        text_lower: Текст запроса в нижнем регистре.
        viz_service: Экземпляр VisualizationService с методами генерации.

    Returns:
        (image_bytes, visualization_type) или (None, None).
    """
    diagram_type_patterns = {
        "столбчат": ("bar", viz_service.generate_bar_chart),
        "столбчатая": ("bar", viz_service.generate_bar_chart),
        "столбчатую": ("bar", viz_service.generate_bar_chart),
        "круговая": ("pie", viz_service.generate_pie_chart),
        "круговую": ("pie", viz_service.generate_pie_chart),
        "кругов": ("pie", viz_service.generate_pie_chart),
        "круговой": ("pie", viz_service.generate_pie_chart),
        "линейн": ("line", viz_service.generate_line_chart),
        "линейный график": ("line", viz_service.generate_line_chart),
        "линейную": ("line", viz_service.generate_line_chart),
        "линейного": ("line", viz_service.generate_line_chart),
        "гистограмм": ("histogram", viz_service.generate_histogram),
        "гистограмму": ("histogram", viz_service.generate_histogram),
        "гистограммы": ("histogram", viz_service.generate_histogram),
        "рассеяни": ("scatter", viz_service.generate_scatter_plot),
        "рассеяния": ("scatter", viz_service.generate_scatter_plot),
        "точечн": ("scatter", viz_service.generate_scatter_plot),
        "точечную": ("scatter", viz_service.generate_scatter_plot),
        "ящик с усами": ("box", viz_service.generate_box_plot),
        "ящик": ("box", viz_service.generate_box_plot),
        "box plot": ("box", viz_service.generate_box_plot),
        "пузырьков": ("bubble", viz_service.generate_bubble_chart),
        "пузырьковую": ("bubble", viz_service.generate_bubble_chart),
        "теплов": ("heatmap", viz_service.generate_heatmap),
        "тепловую": ("heatmap", viz_service.generate_heatmap),
        "heatmap": ("heatmap", viz_service.generate_heatmap),
    }

    # Общие запросы на диаграмму (без указания типа)
    general_diagram_patterns = [
        r"покажи\s+диаграмм",
        r"нарисуй\s+диаграмм",
        r"создай\s+диаграмм",
        r"построй\s+диаграмм",
        r"выведи\s+диаграмм",
        r"отобрази\s+диаграмм",
        r"покажи\s+к\s+ней\s+диаграмм",
        r"покажи\s+к\s+ней\s+круговую",
        r"покажи\s+к\s+задаче\s+диаграмм",
        # Школьные запросы про доли и проценты
        r"дол[июя].*диаграмм",
        r"част[иья].*диаграмм",
        r"процент.*диаграмм",
        r"соотношени.*диаграмм",
        r"распредел.*диаграмм",
        r"структур.*диаграмм",
    ]

    has_general_diagram_request = any(
        re.search(pattern, text_lower) for pattern in general_diagram_patterns
    )

    # Если в запросе есть "схем" — это НЕ диаграмма
    if "схем" in text_lower:
        has_general_diagram_request = False

    # Общий запрос без указания типа → круговая (pie)
    if has_general_diagram_request and not any(
        keyword in text_lower for keyword in diagram_type_patterns
    ):
        try:
            demo_data = {
                "Математика": 30,
                "Русский": 25,
                "Английский": 20,
                "Физика": 15,
                "Химия": 10,
            }
            image = viz_service.generate_pie_chart(demo_data, "Диаграмма")
            if image:
                logger.info("📊 Детектирован общий запрос на диаграмму, сгенерирована круговая")
                return image, "pie"
        except Exception as e:
            logger.warning(f"⚠️ Ошибка генерации круговой диаграммы: {e}")

    for keyword, (diagram_type, generator_func) in diagram_type_patterns.items():
        if keyword in text_lower:
            try:
                image = _generate_demo_diagram(diagram_type, generator_func, viz_service)
                if image:
                    logger.info(f"📊 Детектирован запрос на {diagram_type} диаграмму")
                    return image, diagram_type
            except Exception as e:
                logger.warning(f"⚠️ Ошибка генерации {diagram_type} диаграммы: {e}")
                continue

    return None, None


def _generate_demo_diagram(diagram_type: str, generator_func, _viz_service) -> bytes | None:
    """Генерирует демонстрационную диаграмму указанного типа."""
    if diagram_type == "bar":
        demo_data = {
            "Яблоки": 25,
            "Бананы": 18,
            "Апельсины": 22,
            "Груши": 15,
            "Виноград": 20,
        }
        return generator_func(demo_data, "Пример столбчатой диаграммы")

    if diagram_type == "pie":
        demo_data = {
            "Математика": 30,
            "Русский": 25,
            "Английский": 20,
            "Физика": 15,
            "Химия": 10,
        }
        return generator_func(demo_data, "Пример круговой диаграммы")

    if diagram_type == "line":
        x_data = list(range(1, 13))
        y_data = [-5, -3, 2, 10, 18, 22, 24, 23, 16, 8, 2, -2]
        return generator_func(
            x_data, y_data, "Пример линейного графика", "Месяц", "Температура (°C)"
        )

    if diagram_type == "histogram":
        demo_data = [3, 4, 4, 5, 5, 5, 4, 3, 5, 4, 5, 4, 3, 5, 4, 5, 5, 4, 3, 4]
        return generator_func(demo_data, 5, "Пример гистограммы", "Оценка", "Количество")

    if diagram_type == "scatter":
        x_data = [150, 155, 160, 165, 170, 175, 180, 185, 190]
        y_data = [45, 50, 55, 60, 65, 70, 75, 80, 85]
        return generator_func(x_data, y_data, "Пример диаграммы рассеяния", "Рост (см)", "Вес (кг)")

    if diagram_type == "box":
        demo_data = {
            "Группа A": [65, 70, 72, 75, 78, 80, 82, 85, 88, 90],
            "Группа B": [60, 65, 68, 70, 72, 75, 78, 80, 82, 85],
            "Группа C": [70, 75, 78, 80, 82, 85, 88, 90, 92, 95],
        }
        return generator_func(demo_data, "Пример ящика с усами", "Оценка")

    if diagram_type == "bubble":
        x_data = [1.4, 1.3, 0.3, 0.2, 0.1]
        y_data = [14, 4, 3, 2, 1]
        sizes = [9.6, 3.3, 0.9, 0.8, 0.5]
        labels = ["Китай", "Индия", "США", "Индонезия", "Пакистан"]
        return generator_func(
            x_data,
            y_data,
            sizes,
            labels,
            "Пример пузырьковой диаграммы",
            "Население (млрд)",
            "ВВП (трлн $)",
        )

    if diagram_type == "heatmap":
        demo_data = {
            "Понедельник": {"9:00": 45, "12:00": 60, "15:00": 50, "18:00": 40},
            "Вторник": {"9:00": 50, "12:00": 65, "15:00": 55, "18:00": 45},
            "Среда": {"9:00": 48, "12:00": 70, "15:00": 58, "18:00": 42},
            "Четверг": {"9:00": 52, "12:00": 68, "15:00": 60, "18:00": 48},
            "Пятница": {"9:00": 40, "12:00": 55, "15:00": 45, "18:00": 35},
        }
        return generator_func(demo_data, title="Пример тепловой карты")

    return None
