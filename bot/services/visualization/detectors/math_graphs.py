"""Детекция математических графиков функций."""

from __future__ import annotations

import re

from loguru import logger


def detect_math_graph(text_lower: str, _text: str, viz_service) -> tuple[bytes | None, str | None]:
    """
    Детектирует запросы на графики математических функций.

    Вызывается из оркестратора ТОЛЬКО при has_visualization_request
    или has_context_pattern.

    Args:
        text_lower: Текст запроса в нижнем регистре.
        text: Оригинальный текст запроса.
        viz_service: Экземпляр VisualizationService.

    Returns:
        (image_bytes, visualization_type) или (None, None).
    """
    math_graph_patterns = [
        # Линейная функция (y = kx + b)
        r"график\s+линейн[ойая]?\s+функци",
        r"линейн[ая]?\s+функци[яю]?\s+график",
        r"прямо\s*[-]?\s*пропорциональн[ая]?\s+(?:зависимость|функци)",
        r"обратно\s*[-]?\s*пропорциональн[ая]?\s+(?:зависимость|функци)",
        r"график\s+y\s*=\s*k?x\s*[\+\-]?\s*b?",
        r"график\s+y\s*=\s*\d*x\s*[\+\-]\s*\d+",
        r"y\s*=\s*kx\s*\+\s*b",
        r"график\s+прям[ойая]",
        # Квадратичная функция (парабола)
        r"график\s+(?:парабол|квадратичн)",
        r"график\s+y\s*=\s*x\^2",
        r"график\s+y\s*=\s*a?x\^?2",
        r"квадратичн[ая]?\s+функци",
        # Тригонометрия
        r"график\s+(?:синус|косинус|тангенс)",
        r"график\s+y\s*=\s*sin",
        r"график\s+y\s*=\s*cos",
        r"график\s+y\s*=\s*tan",
        # Другие функции
        r"график\s+(?:логарифм|экспонент|степенн|гипербол|корн)",
        r"график\s+y\s*=\s*log",
        r"график\s+y\s*=\s*exp",
        r"график\s+y\s*=\s*\d+\^x",
        r"график\s+y\s*=\s*1/x",
        r"график\s+y\s*=\s*sqrt",
        r"график\s+y\s*=\s*\|?x\|?",
        # Названия функций
        r"парабол[аы]",
        r"синусоид[аы]",
        r"гипербол[аы]",
    ]

    for pattern in math_graph_patterns:
        if not re.search(pattern, text_lower):
            continue

        # Линейная функция
        if re.search(r"линейн|прямо\s*[-]?\s*пропорц|y\s*=\s*k?x\s*[\+\-]|прям[ойая]", text_lower):
            linear_match = re.search(
                r"y\s*=\s*(-?\d*\.?\d*)?\s*x\s*([\+\-]\s*\d+\.?\d*)?", text_lower
            )
            if linear_match:
                k = linear_match.group(1) if linear_match.group(1) else "1"
                b = linear_match.group(2).replace(" ", "") if linear_match.group(2) else ""
                if k == "" or k == "-":
                    k = "-1" if k == "-" else "1"
                function_expr = f"{k}*x{b}" if b else f"{k}*x"
            else:
                function_expr = "2*x + 1"
            image = viz_service.generate_function_graph(function_expr)
            if image:
                logger.info(f"📈 Детектирован график линейной функции: {function_expr}")
                return image, "graph"

        # Обратная пропорциональность (гипербола)
        if re.search(r"обратно\s*[-]?\s*пропорц|гипербол", text_lower):
            image = viz_service.generate_function_graph("1/x")
            if image:
                logger.info("📈 Детектирован график обратной пропорциональности (гиперболы)")
                return image, "graph"

        # Квадратичная функция (парабола)
        if re.search(r"парабол|квадратичн|y\s*=\s*x\^?2", text_lower):
            image = viz_service.generate_function_graph("x**2")
            if image:
                logger.info("📈 Детектирован график параболы")
                return image, "graph"

        # Тригонометрия
        if "синус" in text_lower or "синусоид" in text_lower:
            image = viz_service.generate_function_graph("sin(x)")
            if image:
                logger.info("📈 Детектирован график синуса")
                return image, "graph"
        elif "косинус" in text_lower:
            image = viz_service.generate_function_graph("cos(x)")
            if image:
                logger.info("📈 Детектирован график косинуса")
                return image, "graph"
        elif "тангенс" in text_lower:
            image = viz_service.generate_function_graph("tan(x)")
            if image:
                logger.info("📈 Детектирован график тангенса")
                return image, "graph"

        # Корень
        if re.search(r"корен|sqrt|корн", text_lower):
            image = viz_service.generate_function_graph("sqrt(x)")
            if image:
                logger.info("📈 Детектирован график корня")
                return image, "graph"

        # Модуль
        if re.search(r"модул|\|x\|", text_lower):
            image = viz_service.generate_function_graph("abs(x)")
            if image:
                logger.info("📈 Детектирован график модуля")
                return image, "graph"

        # Общий случай: извлекаем y = ... из текста
        function_match = re.search(r"y\s*=\s*([^,\n]+)", text_lower)
        if function_match:
            function_expr = function_match.group(1).strip()
            function_expr = re.sub(r"[^\w\s\+\-\*\/\^\(\)\.]", "", function_expr)
            if function_expr:
                try:
                    image = viz_service.generate_function_graph(function_expr)
                    if image:
                        logger.info(f"📈 Детектирован график функции: {function_expr}")
                        return image, "graph"
                except Exception as e:
                    logger.debug(f"⚠️ Ошибка генерации графика функции: {e}")

    return None, None
