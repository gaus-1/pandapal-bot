"""
Сервис визуализации для генерации графиков и диаграмм.

Создает изображения (графики функций, диаграммы, таблицы) для ответов AI.
Использует matplotlib для генерации изображений без дополнительных ролей Yandex Cloud.
"""

import base64
import io
import re

from loguru import logger

try:
    import matplotlib

    matplotlib.use("Agg")  # Без GUI бэкенд
    import matplotlib.pyplot as plt
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("⚠️ matplotlib недоступен - визуализация отключена")


class VisualizationService:
    """
    Сервис для генерации графиков и диаграмм.

    Возможности:
    - Графики функций (линейные, квадратичные, тригонометрические)
    - Диаграммы (столбчатые, круговые)
    - Таблицы умножения в виде таблицы
    - Визуализация математических задач
    """

    def __init__(self):
        """Инициализация сервиса визуализации."""
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("⚠️ VisualizationService недоступен - matplotlib не установлен")
        else:
            logger.info("✅ VisualizationService инициализирован")

    def generate_full_multiplication_table(self) -> bytes | None:
        """
        Генерирует полную таблицу умножения (1-10).

        Returns:
            bytes: Изображение в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(12, 14))
            fig.patch.set_facecolor("white")
            ax.axis("off")

            # Заголовок
            title = "Таблица умножения"
            ax.text(
                0.5,
                0.98,
                title,
                ha="center",
                va="top",
                fontsize=18,
                fontweight="bold",
                transform=ax.transAxes,
            )

            # Генерируем полную таблицу (10x10)
            table_data = []
            for i in range(1, 11):
                row = []
                for j in range(1, 11):
                    row.append(f"{i}×{j}={i*j}")
                table_data.append(row)

            # Создаем таблицу
            table = ax.table(
                cellText=table_data,
                cellLoc="center",
                loc="center",
                bbox=[0, 0.05, 1, 0.9],
            )
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.5)

            # Стилизация - чередующиеся цвета
            for i in range(10):
                for j in range(10):
                    cell = table[(i, j)]
                    if (i + j) % 2 == 0:
                        cell.set_facecolor("#f0f8ff")
                    else:
                        cell.set_facecolor("white")
                    cell.set_text_props(weight="normal")

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована полная таблица умножения")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации полной таблицы умножения: {e}", exc_info=True)
            return None

    def generate_multiplication_table_image(self, number: int) -> bytes | None:
        """
        Генерирует изображение таблицы умножения для заданного числа.

        Args:
            number: Число для таблицы умножения (например, 3 для таблицы на 3)

        Returns:
            bytes: Изображение в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(6, 8))
            fig.patch.set_facecolor("white")
            ax.axis("off")

            # Заголовок
            title = f"Таблица умножения на {number}"
            ax.text(
                0.5,
                0.95,
                title,
                ha="center",
                va="top",
                fontsize=16,
                fontweight="bold",
                transform=ax.transAxes,
            )

            # Генерируем таблицу
            table_data = []
            for i in range(1, 11):
                result = number * i
                table_data.append([f"{number} × {i} = {result}"])

            # Создаем таблицу
            table = ax.table(
                cellText=table_data, cellLoc="left", loc="center", bbox=[0, 0.1, 1, 0.8]
            )
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 2)

            # Стилизация
            for i in range(len(table_data)):
                cell = table[(i, 0)]
                cell.set_facecolor("#f0f8ff" if i % 2 == 0 else "white")
                cell.set_text_props(weight="normal")

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована таблица умножения на {number}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации таблицы умножения: {e}", exc_info=True)
            return None

    def generate_function_graph(
        self, expression: str, x_range: tuple = (-10, 10), title: str | None = None
    ) -> bytes | None:
        """
        Генерирует график функции.

        Args:
            expression: Выражение функции (например, "x**2", "2*x+3", "np.sin(x)", "np.log(x)")
            x_range: Диапазон значений x (min, max)
            title: Заголовок графика (если None, генерируется автоматически)

        Returns:
            bytes: Изображение графика в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # Для логарифмических и sqrt функций используем только положительные значения x
            if (
                "log" in expression.lower()
                or "ln" in expression.lower()
                or "sqrt" in expression.lower()
            ):
                x_range = (0.01, 10)  # Логарифм и sqrt определены только для x > 0

            x = np.linspace(x_range[0], x_range[1], 1000)

            # Безопасное вычисление функции
            # Поддерживаем только простые функции для безопасности
            # ВАЖНО: Не используем np. в выражениях, так как это требует __import__
            # Вместо этого заменяем np.func на func из safe_globals
            safe_globals = {
                "x": x,
                "sin": np.sin,
                "cos": np.cos,
                "tan": np.tan,
                "exp": np.exp,
                "log": np.log,  # Натуральный логарифм (ln)
                "log10": np.log10,  # Логарифм по основанию 10
                "log2": np.log2,  # Логарифм по основанию 2
                "ln": np.log,  # Алиас для натурального логарифма
                "sqrt": np.sqrt,
                "abs": np.abs,
                "pi": np.pi,  # Число π
            }

            try:
                # Заменяем все функции на версии БЕЗ np. для безопасности
                # Заменяем np.func на func (ВАЖНО: сначала np. версии, потом обычные)
                # Порядок важен - сначала заменяем np.func, потом проверяем обычные
                replacements_np = [
                    ("np.sqrt(", "sqrt("),
                    ("np.log10(", "log10("),
                    ("np.log2(", "log2("),
                    ("np.log(", "log("),
                    ("np.sin(", "sin("),
                    ("np.cos(", "cos("),
                    ("np.tan(", "tan("),
                    ("np.exp(", "exp("),
                    ("np.abs(", "abs("),
                ]
                for old, new in replacements_np:
                    expression = expression.replace(old, new)

                # Теперь заменяем обычные функции (если они еще не заменены)
                # Это нужно для случаев, когда функция уже без np.
                # Но на самом деле они уже правильные, так что просто оставляем как есть

                # Вычисляем функцию с безопасным контекстом
                # ВАЖНО: Используем полностью пустой __builtins__ для максимальной безопасности
                # Функции из numpy уже в safe_globals, они не требуют импорта
                y = eval(expression, {"__builtins__": {}}, safe_globals)
                # Фильтруем NaN и Inf значения
                mask = np.isfinite(y)
                x = x[mask]
                y = y[mask]
            except Exception as e:
                logger.warning(f"⚠️ Не удалось вычислить функцию: {expression}, ошибка: {e}")
                return None

            if len(x) == 0:
                logger.warning(f"⚠️ Нет валидных точек для функции: {expression}")
                return None

            fig, ax = plt.subplots(figsize=(10, 7))
            fig.patch.set_facecolor("white")
            ax.plot(x, y, linewidth=2.5, color="#4A90E2")
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.set_xlabel("x", fontsize=13, fontweight="bold")
            ax.set_ylabel("y", fontsize=13, fontweight="bold")

            # Формируем заголовок
            if title:
                graph_title = title
            else:
                # Красивое форматирование выражения для заголовка
                display_expr = expression.replace("**", "^").replace("*", "·")
                graph_title = f"График функции: y = {display_expr}"

            ax.set_title(graph_title, fontsize=15, fontweight="bold", pad=15)
            ax.axhline(y=0, color="k", linewidth=0.8, linestyle="-")
            ax.axvline(x=0, color="k", linewidth=0.8, linestyle="-")

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирован график функции: {expression}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика: {e}", exc_info=True)
            return None

    def generate_bar_chart(self, data: dict[str, float], title: str = "Диаграмма") -> bytes | None:
        """
        Генерирует столбчатую диаграмму.

        Args:
            data: Словарь {название: значение}
            title: Заголовок диаграммы

        Returns:
            bytes: Изображение диаграммы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            fig.patch.set_facecolor("white")

            categories = list(data.keys())
            values = list(data.values())

            bars = ax.bar(categories, values, color="#4A90E2", alpha=0.7)
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.set_ylabel("Значение", fontsize=12)
            ax.grid(True, alpha=0.3, axis="y")

            # Добавляем значения на столбцы
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{height:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )

            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована столбчатая диаграмма: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации диаграммы: {e}", exc_info=True)
            return None

    def generate_table(
        self, headers: list[str], rows: list[list[str]], title: str = "Таблица"
    ) -> bytes | None:
        """
        Генерирует произвольную таблицу.

        Args:
            headers: Заголовки столбцов
            rows: Строки таблицы (список списков)
            title: Заголовок таблицы

        Returns:
            bytes: Изображение таблицы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(max(10, len(headers) * 2), max(8, len(rows) * 0.5 + 2)))
            fig.patch.set_facecolor("white")
            ax.axis("off")

            # Заголовок
            ax.text(
                0.5,
                0.98,
                title,
                ha="center",
                va="top",
                fontsize=16,
                fontweight="bold",
                transform=ax.transAxes,
            )

            # Подготавливаем данные для таблицы
            table_data = [headers] + rows

            # Создаем таблицу
            table = ax.table(
                cellText=table_data,
                cellLoc="center",
                loc="center",
                bbox=[0, 0.05, 1, 0.9],
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)

            # Стилизация заголовков
            for j in range(len(headers)):
                cell = table[(0, j)]
                cell.set_facecolor("#4A90E2")
                cell.set_text_props(weight="bold", color="white")

            # Стилизация строк (чередующиеся цвета)
            for i in range(1, len(table_data)):
                for j in range(len(headers)):
                    cell = table[(i, j)]
                    if i % 2 == 0:
                        cell.set_facecolor("#f0f8ff")
                    else:
                        cell.set_facecolor("white")

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована таблица: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации таблицы: {e}", exc_info=True)
            return None

    def detect_visualization_request(self, text: str) -> bytes | None:
        """
        Универсальный метод для детекции и генерации визуализации из текста.

        Анализирует текст и определяет, нужна ли визуализация (таблица умножения, график, таблица).
        Если нужна - генерирует и возвращает изображение.

        Args:
            text: Текст сообщения для анализа

        Returns:
            bytes: Изображение визуализации или None, если визуализация не нужна
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        text_lower = text.lower()

        # Сначала проверяем полную таблицу умножения (без указания числа)
        # ВАЖНО: Проверяем ДО паттернов с числами, чтобы не перехватывать "таблица умножения на 5"
        # Используем простой паттерн: "табл" + любые символы + "умнож"
        # Проверяем, что в тексте есть "таблица умножения" БЕЗ "на N"
        if (
            "табл" in text_lower
            and "умнож" in text_lower
            and not re.search(r"умнож[а-я]*\s+на\s+\d+", text_lower)
        ):
            # Это полная таблица умножения
            image = self.generate_full_multiplication_table()
            if image:
                logger.info("📊 Детектирована полная таблица умножения")
                return image

        # Дополнительные паттерны для полной таблицы (более явные)
        full_table_patterns = [
            r"^покажи\s+табл\w*\s*умножени[яе]\s*$",  # "покажи таблицу умножения" точно
            r"^выведи\s+табл\w*\s*умножени[яе]\s*$",  # "выведи таблицу умножения" точно
            r"табл\w*\s*умножени[яе]\s+на\s+все",  # "таблица умножения на все"
            r"полная\s+табл\w*\s*умножени[яе]",  # "полная таблица умножения"
        ]

        for pattern in full_table_patterns:
            if re.search(pattern, text_lower):
                # Генерируем полную таблицу умножения (1-10)
                image = self.generate_full_multiplication_table()
                if image:
                    logger.info("📊 Детектирована полная таблица умножения")
                    return image

        # Паттерны для таблиц умножения на конкретное число
        multiplication_patterns = [
            r"табл\w*\s*умножени[яе]\s*на\s*(\d+)",
            r"табл\w*\s*умножени[яе]\s+(\d+)",
            r"умножени[яе]\s+на\s*(\d+)",
            r"умнож[а-я]*\s+(\d+)",
        ]

        # Проверяем таблицы умножения на конкретное число
        for pattern in multiplication_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    number = int(match.group(1))
                    if 1 <= number <= 10:
                        image = self.generate_multiplication_table_image(number)
                        if image:
                            logger.info(f"📊 Детектирована таблица умножения на {number}")
                        return image
                except (ValueError, IndexError):
                    continue

        # Паттерны для таблицы Менделеева
        mendeleev_patterns = [
            r"табл[иы]ц[аеы]?\s*менделеева",
            r"периодическая\s+табл[иы]ц[аеы]?",
            r"менделеева",
            r"покажи\s+табл[иы]ц[аеы]?\s*менделеева",
            r"покажи\s+периодическую\s+табл[иы]ц[аеы]?",
        ]

        for pattern in mendeleev_patterns:
            if re.search(pattern, text_lower):
                # Пока просто возвращаем None - таблица Менделеева слишком сложная для генерации
                # Но детекция работает, чтобы AI знал, что это образовательный запрос
                logger.info("📊 Детектирован запрос на таблицу Менделеева (образовательная тема)")
                # Возвращаем None, чтобы AI ответил текстом, но это будет образовательный вопрос
                return None

        # Паттерны для графиков функций
        graph_patterns = [
            r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"изобрази\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"создай\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"(?:синусоид|sin|косинус|cos|тангенс|tan|экспонент|exp|логарифм|log|парабол|линейн|квадратичн)",
        ]

        # Проверяем графики
        graph_match = None
        for pattern in graph_patterns:
            graph_match = re.search(pattern, text_lower)
            if graph_match:
                break

        if graph_match:
            # Логарифмические функции (приоритет - детектируем первыми)
            if re.search(r"логарифм|log|ln", text_lower):
                # Пытаемся извлечь основание логарифма
                log_base_match = re.search(
                    r"(?:log|логарифм)\s*(?:по\s+основанию\s+)?(\d+)|(?:log|логарифм)\s*\(|ln|натуральн",
                    text_lower,
                )

                if re.search(r"ln|натуральн", text_lower):
                    # Натуральный логарифм
                    image = self.generate_function_graph("ln(x)", title="График функции: y = ln(x)")
                    if image:
                        logger.info("📈 Детектирован график натурального логарифма")
                        return image
                elif log_base_match and log_base_match.group(1):
                    # Логарифм с указанным основанием
                    try:
                        base = int(log_base_match.group(1))
                        if base == 10:
                            image = self.generate_function_graph(
                                "log10(x)", title="График функции: y = log₁₀(x)"
                            )
                        elif base == 2:
                            image = self.generate_function_graph(
                                "log2(x)", title="График функции: y = log₂(x)"
                            )
                        else:
                            # Для других оснований используем формулу: log_a(x) = ln(x) / ln(a)
                            image = self.generate_function_graph(
                                f"ln(x) / ln({base})", title=f"График функции: y = log_{base}(x)"
                            )
                        if image:
                            logger.info(f"📈 Детектирован график логарифма по основанию {base}")
                            return image
                    except (ValueError, AttributeError):
                        pass

                # Логарифм без указания основания или с нераспознанным основанием - используем натуральный
                image = self.generate_function_graph("ln(x)", title="График функции: y = ln(x)")
                if image:
                    logger.info("📈 Детектирован график логарифма (натуральный по умолчанию)")
                    return image

            # Экспоненциальные функции
            elif re.search(r"экспонент|exp|e\^x|e\*\*x", text_lower):
                image = self.generate_function_graph(
                    "exp(x)", x_range=(-3, 3), title="График функции: y = e^x"
                )
                if image:
                    logger.info("📈 Детектирован график экспоненты")
                    return image

            # Тригонометрические функции
            elif re.search(r"(?:синусоид|sin)", text_lower):
                image = self.generate_function_graph(
                    "sin(x)", x_range=(-2 * np.pi, 2 * np.pi), title="График функции: y = sin(x)"
                )
                if image:
                    logger.info("📈 Детектирован график синусоиды")
                    return image
            elif re.search(r"(?:косинус|cos)", text_lower):
                image = self.generate_function_graph(
                    "cos(x)", x_range=(-2 * np.pi, 2 * np.pi), title="График функции: y = cos(x)"
                )
                if image:
                    logger.info("📈 Детектирован график косинуса")
                    return image
            elif re.search(r"(?:тангенс|tan)", text_lower):
                image = self.generate_function_graph(
                    "tan(x)", x_range=(-np.pi, np.pi), title="График функции: y = tan(x)"
                )
                if image:
                    logger.info("📈 Детектирован график тангенса")
                    return image

            # Квадратичные функции
            elif re.search(r"парабол|квадратичн|x\^2|x\*\*2|x²", text_lower):
                image = self.generate_function_graph("x**2", title="График функции: y = x²")
                if image:
                    logger.info("📈 Детектирован график параболы")
                    return image

            # Линейные функции
            elif re.search(r"линейн|прям", text_lower):
                # Пытаемся извлечь коэффициенты
                linear_match = re.search(
                    r"y\s*=\s*(\d*\.?\d*)\s*\*\s*x\s*([+\-]?\d*\.?\d*)|(\d*\.?\d*)\s*\*\s*x|y\s*=\s*x",
                    text_lower,
                )
                if linear_match:
                    # Упрощенная обработка - просто y = x
                    image = self.generate_function_graph("x", title="График функции: y = x")
                else:
                    image = self.generate_function_graph(
                        "x", title="График линейной функции: y = x"
                    )
                if image:
                    logger.info("📈 Детектирован график линейной функции")
                    return image

            # Извлекаем выражение из паттерна
            expression = graph_match.group(1).strip() if graph_match.groups() else ""
            if expression:
                # Нормализуем выражение
                expression = expression.replace("^", "**").replace("²", "**2").replace("³", "**3")
                # Заменяем русские названия функций на английские
                expression = re.sub(r"логарифм|log", "ln", expression, flags=re.IGNORECASE)
                expression = re.sub(r"синус|sin", "sin", expression, flags=re.IGNORECASE)
                expression = re.sub(r"косинус|cos", "cos", expression, flags=re.IGNORECASE)
                expression = re.sub(r"тангенс|tan", "tan", expression, flags=re.IGNORECASE)
                expression = re.sub(r"экспонент|exp", "exp", expression, flags=re.IGNORECASE)

                # Безопасная проверка выражения (расширенная)
                # Разрешаем: x, числа, операторы, функции, скобки, точки
                safe_pattern = (
                    r"^[x\s+\-*/()\.\d\sln\slog\slog10\slog2\ssin\scos\stan\sexp\ssqrt\sabs\s]+$"
                )
                if re.match(safe_pattern, expression.replace(" ", "")):
                    image = self.generate_function_graph(expression)
                    if image:
                        logger.info(f"📈 Детектирован график функции: {expression}")
                        return image

        return None

    def image_to_base64(self, image_bytes: bytes) -> str:
        """
        Конвертирует изображение в base64 строку для отправки.

        Args:
            image_bytes: Байты изображения

        Returns:
            str: Base64 строка
        """
        return base64.b64encode(image_bytes).decode("utf-8")


def get_visualization_service() -> VisualizationService:
    """Получить экземпляр сервиса визуализации (singleton)."""
    if not hasattr(get_visualization_service, "_instance"):
        get_visualization_service._instance = VisualizationService()
    return get_visualization_service._instance
