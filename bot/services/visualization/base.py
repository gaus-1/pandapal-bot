"""
Базовый класс для визуализации (SOLID: SRP, DIP).

Содержит общие методы генерации таблиц и графиков,
используемые всеми модулями визуализации.
"""

import io

from loguru import logger

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("⚠️ matplotlib недоступен - визуализация отключена")


class BaseVisualizationService:
    """Базовый класс для генерации визуализаций.

    Предоставляет общие методы для создания таблиц и графиков.
    Наследуется модулями по предметам для специализированной генерации.
    """

    def __init__(self):
        """Инициализация базового сервиса."""
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("⚠️ BaseVisualizationService недоступен - matplotlib не установлен")

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
            fig, ax = plt.subplots(
                figsize=(
                    max(10, len(headers) * 2),
                    max(8, len(rows) * 0.5 + 2),
                )
            )
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

    def generate_function_graph(
        self, expression: str, x_range: tuple = (-10, 10), title: str | None = None
    ) -> bytes | None:
        """
        Генерирует график функции.

        Args:
            expression: Выражение функции
                (например, "x**2", "2*x+3", "sin(x)")
            x_range: Диапазон значений x (min, max)
            title: Заголовок графика
                (если None, генерируется автоматически)

        Returns:
            bytes: Изображение графика в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # Для логарифмических и sqrt функций используем
            # только положительные значения x
            if (
                "log" in expression.lower()
                or "ln" in expression.lower()
                or "sqrt" in expression.lower()
            ):
                x_range = (0.01, 10)

            x = np.linspace(x_range[0], x_range[1], 1000)

            # Безопасное вычисление функции
            safe_globals = {
                "x": x,
                "sin": np.sin,
                "cos": np.cos,
                "tan": np.tan,
                "exp": np.exp,
                "log": np.log,
                "log10": np.log10,
                "log2": np.log2,
                "ln": np.log,
                "sqrt": np.sqrt,
                "abs": np.abs,
                "pi": np.pi,
            }

            try:
                # Нормализуем выражение: поддержка степеней через символы ² и ³ и ^
                expression = expression.replace("²", "**2").replace("³", "**3").replace("^", "**")

                # Заменяем np.func на func для безопасности
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

                y = eval(expression, {"__builtins__": {}}, safe_globals)
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

    def generate_multiple_function_graphs(
        self, expressions: list[str], x_range: tuple = (-10, 10)
    ) -> bytes | None:
        """
        Генерирует несколько графиков функций в одной картинке.

        Args:
            expressions: Список выражений функций (например, ["sin(x)", "cos(x)"])
            x_range: Диапазон значений x (min, max)

        Returns:
            bytes: Изображение с несколькими графиками или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        if not expressions:
            return None

        # Ограничиваем количество графиков (максимум 3 для читаемости)
        expressions = expressions[:3]

        try:
            num_graphs = len(expressions)
            if num_graphs == 1:
                # Если один график - используем обычный метод
                return self.generate_function_graph(expressions[0], x_range)

            # Для нескольких графиков создаем subplots
            if num_graphs == 2:
                fig, axes = plt.subplots(1, 2, figsize=(18, 7))
            else:  # 3
                fig, axes = plt.subplots(1, 3, figsize=(24, 7))

            fig.patch.set_facecolor("white")

            # Цвета для разных графиков
            colors = ["#4A90E2", "#E24A4A", "#4AE24A"]

            for idx, expression in enumerate(expressions):
                ax = axes[idx] if num_graphs > 1 else axes

                # Для логарифмических и sqrt функций используем только положительные значения
                current_range = x_range
                if (
                    "log" in expression.lower()
                    or "ln" in expression.lower()
                    or "sqrt" in expression.lower()
                ):
                    current_range = (0.01, 10)

                x = np.linspace(current_range[0], current_range[1], 1000)

                safe_globals = {
                    "x": x,
                    "sin": np.sin,
                    "cos": np.cos,
                    "tan": np.tan,
                    "exp": np.exp,
                    "log": np.log,
                    "log10": np.log10,
                    "log2": np.log2,
                    "ln": np.log,
                    "sqrt": np.sqrt,
                    "abs": np.abs,
                    "pi": np.pi,
                }

                try:
                    # Нормализуем выражение
                    normalized_expr = (
                        expression.replace("²", "**2").replace("³", "**3").replace("^", "**")
                    )

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
                        normalized_expr = normalized_expr.replace(old, new)

                    y = eval(normalized_expr, {"__builtins__": {}}, safe_globals)
                    mask = np.isfinite(y)
                    x_plot = x[mask]
                    y_plot = y[mask]

                    if len(x_plot) > 0:
                        ax.plot(x_plot, y_plot, linewidth=2.5, color=colors[idx % len(colors)])
                        ax.grid(True, alpha=0.3, linestyle="--")
                        ax.set_xlabel("x", fontsize=11, fontweight="bold")
                        ax.set_ylabel("y", fontsize=11, fontweight="bold")

                        display_expr = normalized_expr.replace("**", "^").replace("*", "·")
                        ax.set_title(f"y = {display_expr}", fontsize=12, fontweight="bold", pad=10)
                        ax.axhline(y=0, color="k", linewidth=0.8, linestyle="-")
                        ax.axvline(x=0, color="k", linewidth=0.8, linestyle="-")
                    else:
                        logger.warning(f"⚠️ Нет валидных точек для функции: {expression}")
                        ax.text(
                            0.5,
                            0.5,
                            f"Не удалось построить\ny = {expression}",
                            ha="center",
                            va="center",
                            transform=ax.transAxes,
                            fontsize=10,
                        )
                        ax.axis("off")

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка вычисления функции {expression}: {e}")
                    ax.text(
                        0.5,
                        0.5,
                        f"Ошибка:\n{expression}",
                        ha="center",
                        va="center",
                        transform=ax.transAxes,
                        fontsize=10,
                    )
                    ax.axis("off")

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерированы графики функций: {expressions}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации нескольких графиков: {e}", exc_info=True)
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

    def generate_pie_chart(
        self, data: dict[str, float], title: str = "Круговая диаграмма"
    ) -> bytes | None:
        """
        Генерирует круговую диаграмму.

        Args:
            data: Словарь {название: значение}
            title: Заголовок диаграммы

        Returns:
            bytes: Изображение диаграммы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(8, 8))
            fig.patch.set_facecolor("white")

            labels = list(data.keys())
            values = list(data.values())

            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

            wedges, texts, autotexts = ax.pie(
                values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90
            )

            # Улучшаем читаемость текста
            for autotext in autotexts:
                autotext.set_color("black")
                autotext.set_fontweight("bold")
                autotext.set_fontsize(10)

            ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована круговая диаграмма: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации круговой диаграммы: {e}", exc_info=True)
            return None

    def image_to_base64(self, image_bytes: bytes) -> str:
        """
        Конвертирует изображение в base64 строку.

        Args:
            image_bytes: Изображение в формате bytes

        Returns:
            str: Base64 строка изображения
        """
        import base64

        try:
            return base64.b64encode(image_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"❌ Ошибка конвертации изображения в base64: {e}", exc_info=True)
            return ""
