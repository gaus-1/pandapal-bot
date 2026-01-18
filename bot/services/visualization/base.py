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
    from matplotlib.patches import Ellipse

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
            # Располагаем графики вертикально (один под другим), чтобы лучше читалось на мобильных
            if num_graphs == 2:
                fig, axes = plt.subplots(2, 1, figsize=(8, 10))
            else:  # 3
                fig, axes = plt.subplots(3, 1, figsize=(8, 14))

            fig.patch.set_facecolor("white")

            # Приводим axes к списку
            if not isinstance(axes, list | tuple):
                axes_list = list(axes) if hasattr(axes, "ravel") else [axes]
            else:
                axes_list = list(axes)

            # Цвета для разных графиков
            colors = ["#4A90E2", "#E24A4A", "#4AE24A"]

            for idx, expression in enumerate(expressions):
                ax = axes_list[idx]

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

    def generate_line_chart(
        self,
        x_data: list[float],
        y_data: list[float],
        title: str = "Линейный график",
        x_label: str = "X",
        y_label: str = "Y",
    ) -> bytes | None:
        """
        Генерирует линейный график для данных.

        Args:
            x_data: Список значений по оси X
            y_data: Список значений по оси Y
            title: Заголовок графика
            x_label: Подпись оси X
            y_label: Подпись оси Y

        Returns:
            bytes: Изображение графика в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            if len(x_data) != len(y_data):
                logger.warning("⚠️ Длины массивов x_data и y_data не совпадают")
                return None

            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("white")

            ax.plot(x_data, y_data, marker="o", linewidth=2, color="#4A90E2", markersize=6)
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            ax.grid(True, alpha=0.3, linestyle="--")

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирован линейный график: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации линейного графика: {e}", exc_info=True)
            return None

    def generate_histogram(
        self,
        data: list[float],
        bins: int = 10,
        title: str = "Гистограмма",
        x_label: str = "Значение",
        y_label: str = "Частота",
    ) -> bytes | None:
        """
        Генерирует гистограмму распределения данных.

        Args:
            data: Список числовых значений
            bins: Количество интервалов (по умолчанию 10)
            title: Заголовок гистограммы
            x_label: Подпись оси X
            y_label: Подпись оси Y

        Returns:
            bytes: Изображение гистограммы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("white")

            ax.hist(data, bins=bins, color="#4A90E2", alpha=0.7, edgecolor="black", linewidth=1.2)
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            ax.grid(True, alpha=0.3, axis="y", linestyle="--")

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована гистограмма: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации гистограммы: {e}", exc_info=True)
            return None

    def generate_scatter_plot(
        self,
        x_data: list[float],
        y_data: list[float],
        title: str = "Диаграмма рассеяния",
        x_label: str = "X",
        y_label: str = "Y",
    ) -> bytes | None:
        """
        Генерирует диаграмму рассеяния (точечную диаграмму).

        Args:
            x_data: Список значений по оси X
            y_data: Список значений по оси Y
            title: Заголовок диаграммы
            x_label: Подпись оси X
            y_label: Подпись оси Y

        Returns:
            bytes: Изображение диаграммы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            if len(x_data) != len(y_data):
                logger.warning("⚠️ Длины массивов x_data и y_data не совпадают")
                return None

            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("white")

            ax.scatter(
                x_data, y_data, color="#4A90E2", alpha=0.6, s=50, edgecolors="black", linewidth=0.5
            )
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            ax.grid(True, alpha=0.3, linestyle="--")

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована диаграмма рассеяния: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации диаграммы рассеяния: {e}", exc_info=True)
            return None

    def generate_box_plot(
        self,
        data: list[list[float]] | dict[str, list[float]],
        title: str = "Ящик с усами",
        y_label: str = "Значение",
    ) -> bytes | None:
        """
        Генерирует ящик с усами (box plot) для визуализации распределения данных.

        Args:
            data: Список списков данных или словарь {название: список значений}
            title: Заголовок диаграммы
            y_label: Подпись оси Y

        Returns:
            bytes: Изображение диаграммы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("white")

            # Обрабатываем разные форматы входных данных
            if isinstance(data, dict):
                labels = list(data.keys())
                data_list = list(data.values())
            else:
                labels = [f"Группа {i+1}" for i in range(len(data))]
                data_list = data

            bp = ax.boxplot(data_list, labels=labels, patch_artist=True)

            # Стилизация ящиков
            for patch in bp["boxes"]:
                patch.set_facecolor("#4A90E2")
                patch.set_alpha(0.7)
                patch.set_edgecolor("black")
                patch.set_linewidth(1.2)

            # Стилизация медианы
            for median in bp["medians"]:
                median.set_color("red")
                median.set_linewidth(2)

            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.set_ylabel(y_label, fontsize=12)
            ax.grid(True, alpha=0.3, axis="y", linestyle="--")

            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирован ящик с усами: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации ящика с усами: {e}", exc_info=True)
            return None

    def generate_bubble_chart(
        self,
        x_data: list[float],
        y_data: list[float],
        sizes: list[float],
        labels: list[str] | None = None,
        title: str = "Пузырьковая диаграмма",
        x_label: str = "X",
        y_label: str = "Y",
    ) -> bytes | None:
        """
        Генерирует пузырьковую диаграмму (bubble chart).

        Args:
            x_data: Список значений по оси X
            y_data: Список значений по оси Y
            sizes: Список размеров пузырьков
            labels: Список подписей для точек (опционально)
            title: Заголовок диаграммы
            x_label: Подпись оси X
            y_label: Подпись оси Y

        Returns:
            bytes: Изображение диаграммы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            if len(x_data) != len(y_data) or len(x_data) != len(sizes):
                logger.warning("⚠️ Длины массивов x_data, y_data и sizes не совпадают")
                return None

            # Нормализуем размеры для лучшей визуализации
            sizes_normalized = np.array(sizes)
            if sizes_normalized.max() > 0:
                sizes_normalized = (sizes_normalized / sizes_normalized.max()) * 1000

            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("white")

            ax.scatter(
                x_data,
                y_data,
                s=sizes_normalized,
                alpha=0.6,
                c=range(len(x_data)),
                cmap="viridis",
                edgecolors="black",
                linewidth=1,
            )

            # Добавляем подписи, если указаны
            if labels:
                for i, label in enumerate(labels):
                    ax.annotate(
                        label,
                        (x_data[i], y_data[i]),
                        xytext=(5, 5),
                        textcoords="offset points",
                        fontsize=9,
                    )

            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            ax.grid(True, alpha=0.3, linestyle="--")

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована пузырьковая диаграмма: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации пузырьковой диаграммы: {e}", exc_info=True)
            return None

    def generate_heatmap(
        self,
        data: list[list[float]] | dict[str, dict[str, float]],
        row_labels: list[str] | None = None,
        col_labels: list[str] | None = None,
        title: str = "Тепловая карта",
        cmap: str = "YlOrRd",
    ) -> bytes | None:
        """
        Генерирует тепловую карту (heatmap).

        Args:
            data: Матрица данных (список списков) или словарь словарей
            row_labels: Подписи строк (опционально)
            col_labels: Подписи столбцов (опционально)
            title: Заголовок карты
            cmap: Цветовая схема (по умолчанию 'YlOrRd')

        Returns:
            bytes: Изображение тепловой карты в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # Преобразуем словарь в матрицу, если нужно
            if isinstance(data, dict):
                if not row_labels:
                    row_labels = list(data.keys())
                if not col_labels:
                    # Собираем все уникальные ключи из вложенных словарей
                    col_labels = sorted(
                        {
                            key
                            for subdict in data.values()
                            if isinstance(subdict, dict)
                            for key in subdict
                        }
                    )

                # Создаем матрицу
                matrix = []
                for row_key in row_labels:
                    row = []
                    for col_key in col_labels:
                        value = data.get(row_key, {}).get(col_key, 0.0)
                        row.append(float(value))
                    matrix.append(row)
                data_matrix = np.array(matrix)
            else:
                data_matrix = np.array(data)
                if not row_labels:
                    row_labels = [f"Строка {i+1}" for i in range(len(data_matrix))]
                if not col_labels:
                    col_labels = [f"Столбец {i+1}" for i in range(len(data_matrix[0]))]

            fig, ax = plt.subplots(
                figsize=(max(10, len(col_labels) * 1.2), max(8, len(row_labels) * 0.8))
            )
            fig.patch.set_facecolor("white")

            im = ax.imshow(data_matrix, cmap=cmap, aspect="auto")

            # Устанавливаем подписи
            ax.set_xticks(np.arange(len(col_labels)))
            ax.set_yticks(np.arange(len(row_labels)))
            ax.set_xticklabels(col_labels)
            ax.set_yticklabels(row_labels)

            # Поворачиваем подписи для лучшей читаемости
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

            # Добавляем значения в ячейки
            for i in range(len(row_labels)):
                for j in range(len(col_labels)):
                    ax.text(
                        j,
                        i,
                        f"{data_matrix[i, j]:.1f}",
                        ha="center",
                        va="center",
                        color="black" if data_matrix[i, j] < data_matrix.max() * 0.5 else "white",
                        fontweight="bold",
                    )

            ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
            fig.colorbar(im, ax=ax)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована тепловая карта: {title}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации тепловой карты: {e}", exc_info=True)
            return None

    def generate_solar_system_scheme(self) -> bytes | None:
        """
        Генерирует схему Солнечной системы с планетами.

        Returns:
            bytes: Изображение схемы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Орбиты планет (упрощенно - расстояния не в масштабе)
            planets = [
                ("Меркурий", 1, "#8C7853"),
                ("Венера", 2, "#FFC649"),
                ("Земля", 3, "#6B93D6"),
                ("Марс", 4, "#C1440E"),
                ("Юпитер", 5, "#D8CA9D"),
                ("Сатурн", 6, "#FAD5A5"),
                ("Уран", 7, "#4FD0E7"),
                ("Нептун", 8, "#4B70DD"),
            ]

            # Солнце в центре
            sun_circle = plt.Circle(
                (0, 0), 0.3, color="#FFD700", ec="orange", linewidth=2, zorder=10
            )
            ax.add_patch(sun_circle)
            ax.text(0, 0, "☉", ha="center", va="center", fontsize=20, zorder=11)

            # Планеты на орбитах
            angles = np.linspace(0, 2 * np.pi, len(planets), endpoint=False)
            for i, (name, orbit_radius, color) in enumerate(planets):
                angle = angles[i]
                x = orbit_radius * np.cos(angle)
                y = orbit_radius * np.sin(angle)

                # Планета
                planet_size = 0.15 + (i * 0.02)
                planet_circle = plt.Circle(
                    (x, y), planet_size, color=color, ec="black", linewidth=1, zorder=5
                )
                ax.add_patch(planet_circle)

                # Подпись планеты
                label_x = (orbit_radius + 0.5) * np.cos(angle)
                label_y = (orbit_radius + 0.5) * np.sin(angle)
                ax.text(
                    label_x, label_y, name, ha="center", va="center", fontsize=9, fontweight="bold"
                )

                # Орбита (пунктирная линия)
                orbit_circle = plt.Circle(
                    (0, 0),
                    orbit_radius,
                    fill=False,
                    ec="gray",
                    linestyle="--",
                    linewidth=0.5,
                    alpha=0.5,
                )
                ax.add_patch(orbit_circle)

            ax.set_xlim(-10, 10)
            ax.set_ylim(-10, 10)
            ax.set_title("Схема Солнечной системы", fontsize=16, fontweight="bold", pad=20)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована схема Солнечной системы")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы Солнечной системы: {e}", exc_info=True)
            return None

    def generate_human_body_structure_scheme(self) -> bytes | None:
        """
        Генерирует упрощенную схему строения тела человека с основными органами.

        Returns:
            bytes: Изображение схемы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(8, 12))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Голова
            head_circle = plt.Circle(
                (0, 6.5), 0.6, color="#FFDBAC", ec="black", linewidth=2, zorder=10
            )
            ax.add_patch(head_circle)

            # Шея
            neck = plt.Rectangle(
                (-0.2, 5.9), 0.4, 0.3, color="#FFDBAC", ec="black", linewidth=1, zorder=9
            )
            ax.add_patch(neck)

            # Туловище
            torso = plt.Rectangle(
                (-0.5, 2), 1, 4, color="#FFDBAC", ec="black", linewidth=2, zorder=8
            )
            ax.add_patch(torso)

            # Основные органы (упрощенно)
            # Сердце
            heart_x = 0.2
            heart_y = 4
            heart_triangle = plt.Polygon(
                [
                    (heart_x, heart_y),
                    (heart_x + 0.15, heart_y + 0.2),
                    (heart_x + 0.15, heart_y - 0.2),
                ],
                color="#E63946",
                ec="black",
                linewidth=1,
                zorder=9,
            )
            ax.add_patch(heart_triangle)
            ax.text(heart_x + 0.3, heart_y, "Сердце", fontsize=9, fontweight="bold")

            # Легкие
            lung_left = Ellipse(
                (-0.15, 4.5), 0.25, 0.6, color="#A8DADC", ec="black", linewidth=1, zorder=9
            )
            lung_right = Ellipse(
                (0.15, 4.5), 0.25, 0.6, color="#A8DADC", ec="black", linewidth=1, zorder=9
            )
            ax.add_patch(lung_left)
            ax.add_patch(lung_right)
            ax.text(0.35, 4.8, "Легкие", fontsize=9, fontweight="bold")

            # Желудок
            stomach = Ellipse((0, 3), 0.3, 0.5, color="#F77F00", ec="black", linewidth=1, zorder=9)
            ax.add_patch(stomach)
            ax.text(0.35, 3, "Желудок", fontsize=9, fontweight="bold")

            # Кишечник (упрощенно)
            intestine = plt.Rectangle(
                (-0.2, 2.2), 0.4, 0.5, color="#E07B39", ec="black", linewidth=1, zorder=9
            )
            ax.add_patch(intestine)
            ax.text(0.35, 2.4, "Кишечник", fontsize=9, fontweight="bold")

            ax.set_xlim(-2, 2)
            ax.set_ylim(-1.5, 8)
            ax.set_title("Схема строения тела человека", fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована схема строения тела человека")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы строения тела: {e}", exc_info=True)
            return None

    def generate_water_cycle_scheme(self) -> bytes | None:
        """
        Генерирует схему круговорота воды в природе.

        Returns:
            bytes: Изображение схемы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 10))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Облака
            cloud1 = Ellipse((2, 6), 1, 0.6, color="#E8E8E8", ec="gray", linewidth=1)
            cloud2 = Ellipse((-2, 7), 1, 0.6, color="#E8E8E8", ec="gray", linewidth=1)
            ax.add_patch(cloud1)
            ax.add_patch(cloud2)

            # Стрелки цикла
            # Испарение (земля -> облака)
            ax.arrow(
                1,
                2,
                1.5,
                4,
                head_width=0.2,
                head_length=0.15,
                fc="#4A90E2",
                ec="#4A90E2",
                linewidth=2,
            )
            ax.text(
                2,
                4,
                "Испарение",
                fontsize=10,
                ha="center",
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#4A90E2"},
            )

            # Конденсация (облака -> облака)
            ax.arrow(
                -1,
                6.5,
                2,
                0.5,
                head_width=0.2,
                head_length=0.15,
                fc="#4A90E2",
                ec="#4A90E2",
                linewidth=2,
            )
            ax.text(
                0,
                7.5,
                "Конденсация",
                fontsize=10,
                ha="center",
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#4A90E2"},
            )

            # Осадки (облака -> земля)
            ax.arrow(
                -2.5,
                6.5,
                -1,
                -4,
                head_width=0.2,
                head_length=0.15,
                fc="#4A90E2",
                ec="#4A90E2",
                linewidth=2,
            )
            ax.text(
                -3.5,
                4,
                "Осадки",
                fontsize=10,
                ha="center",
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#4A90E2"},
            )

            # Река/море
            river = plt.Rectangle((-5, -2), 10, 1, color="#4169E1", ec="navy", linewidth=2)
            ax.add_patch(river)
            ax.text(
                0, -1.5, "Реки и океаны", fontsize=10, ha="center", color="white", fontweight="bold"
            )

            # Стекание (земля -> река)
            ax.arrow(
                -1,
                0,
                -2.5,
                -1.5,
                head_width=0.2,
                head_length=0.15,
                fc="#4A90E2",
                ec="#4A90E2",
                linewidth=2,
            )
            ax.text(
                -2.5,
                -0.5,
                "Стекание",
                fontsize=10,
                ha="center",
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#4A90E2"},
            )

            # Земля
            ground = plt.Rectangle((-5, -1), 10, 1, color="#8B7355", ec="black", linewidth=1)
            ax.add_patch(ground)

            ax.set_xlim(-6, 4)
            ax.set_ylim(-3, 9)
            ax.set_title("Круговорот воды в природе", fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована схема круговорота воды")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы круговорота воды: {e}", exc_info=True)
            return None

    def generate_cell_structure_scheme(self) -> bytes | None:
        """
        Генерирует упрощенную схему строения клетки.

        Returns:
            bytes: Изображение схемы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 10))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Клеточная мембрана (внешний круг)
            membrane = Ellipse((0, 0), 4, 3, fill=False, ec="black", linewidth=3)
            ax.add_patch(membrane)
            ax.text(0, -2.5, "Клеточная мембрана", fontsize=10, ha="center", fontweight="bold")

            # Ядро
            nucleus = Ellipse((1, 0.5), 1.5, 1, color="#E63946", ec="black", linewidth=2)
            ax.add_patch(nucleus)
            ax.text(
                1,
                0.5,
                "Ядро",
                fontsize=9,
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
            )

            # Цитоплазма (заливка)
            cytoplasm = Ellipse((0, 0), 3.8, 2.8, color="#FFEB3B", alpha=0.3, ec="none")
            ax.add_patch(cytoplasm)

            # Митохондрия
            mitochondria = Ellipse((-1, -0.5), 0.8, 0.5, color="#4CAF50", ec="black", linewidth=1)
            ax.add_patch(mitochondria)
            ax.text(-1, -1.2, "Митохондрия", fontsize=8, ha="center")

            # Эндоплазматическая сеть (упрощенно)
            ax.plot([-0.5, 0, 0.5], [0.8, 1.2, 0.8], color="#FF9800", linewidth=2)
            ax.text(0, 1.5, "ЭПС", fontsize=8, ha="center")

            ax.set_xlim(-5, 5)
            ax.set_ylim(-4, 4)
            ax.set_title("Схема строения клетки", fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована схема строения клетки")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы строения клетки: {e}", exc_info=True)
            return None

    def generate_dna_structure_scheme(self) -> bytes | None:
        """
        Генерирует упрощенную схему строения ДНК (двойная спираль).

        Returns:
            bytes: Изображение схемы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(8, 10))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Двойная спираль ДНК
            t = np.linspace(0, 4 * np.pi, 200)
            x1 = 1.5 * np.cos(t)
            y1 = t
            x2 = -1.5 * np.cos(t)
            y2 = t

            # Левая и правая нити
            ax.plot(x1, y1, color="#E63946", linewidth=3, label="Нить ДНК")
            ax.plot(x2, y2, color="#457B9D", linewidth=3, label="Нить ДНК")

            # Связи между нитями (упрощенно - вертикальные линии)
            for i in range(0, len(t), 20):
                ax.plot([x1[i], x2[i]], [y1[i], y2[i]], color="#2A9D8F", linewidth=1, alpha=0.7)

            # Подписи
            ax.text(2.5, 15, "A-T", fontsize=9, color="#2A9D8F", fontweight="bold")
            ax.text(2.5, 10, "G-C", fontsize=9, color="#2A9D8F", fontweight="bold")
            ax.text(0, -2, "Двойная спираль ДНК", fontsize=10, ha="center", fontweight="bold")

            ax.set_xlim(-4, 4)
            ax.set_ylim(-3, 25)
            ax.set_title("Схема строения ДНК", fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована схема строения ДНК")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы строения ДНК: {e}", exc_info=True)
            return None

    def generate_electric_circuit_scheme(self) -> bytes | None:
        """
        Генерирует упрощенную схему электрической цепи.

        Returns:
            bytes: Изображение схемы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Батарея
            ax.add_patch(plt.Rectangle((0, 2), 0.5, 2, color="black", ec="black", linewidth=2))
            ax.add_patch(plt.Rectangle((0, 4.5), 0.5, 0.5, color="white", ec="black", linewidth=2))
            ax.text(
                0.25,
                3,
                "+",
                fontsize=12,
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
            )
            ax.text(
                0.25,
                5,
                "-",
                fontsize=12,
                ha="center",
                va="center",
                color="black",
                fontweight="bold",
            )
            ax.text(0.75, 3.5, "Батарея", fontsize=9)

            # Провода и лампа
            # Провод от батареи вверх
            ax.plot([0.5, 0.5], [4.5, 6], "k-", linewidth=3)
            # Провод вправо
            ax.plot([0.5, 4], [6, 6], "k-", linewidth=3)
            # Лампа (круг)
            lamp = plt.Circle((5, 6), 0.5, fill=False, ec="black", linewidth=3)
            ax.add_patch(lamp)
            ax.text(5, 6, "✕", fontsize=16, ha="center", va="center")
            ax.text(5, 5, "Лампа", fontsize=9, ha="center")
            # Провод вниз
            ax.plot([5, 5], [5.5, 1], "k-", linewidth=3)
            # Резистор
            ax.add_patch(plt.Rectangle((4.5, 1), 1, 0.5, fill=False, ec="black", linewidth=2))
            ax.text(5, 0.5, "Резистор", fontsize=9, ha="center")
            # Провод влево
            ax.plot([4.5, 0.5], [1, 1], "k-", linewidth=3)
            # Провод к батарее
            ax.plot([0.5, 0.5], [1, 2], "k-", linewidth=3)

            ax.set_xlim(-1, 7)
            ax.set_ylim(-1, 8)
            ax.set_title("Схема электрической цепи", fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована схема электрической цепи")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы электрической цепи: {e}", exc_info=True)
            return None

    def generate_algorithm_flowchart_scheme(self) -> bytes | None:
        """
        Генерирует упрощенную блок-схему алгоритма (линейный алгоритм с условием).

        Returns:
            bytes: Изображение схемы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(8, 10))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Начало (скругленный прямоугольник)
            start = plt.Rectangle(
                (2.5, 8), 3, 1, fill=True, facecolor="#90EE90", ec="black", linewidth=2
            )
            ax.add_patch(start)
            ax.text(4, 8.5, "НАЧАЛО", fontsize=10, ha="center", va="center", fontweight="bold")

            # Ввод данных (параллелограмм)
            input_box = plt.Polygon(
                [(2, 6.5), (6, 6.5), (6.5, 7.5), (1.5, 7.5)],
                fill=True,
                facecolor="#FFE4B5",
                ec="black",
                linewidth=2,
            )
            ax.add_patch(input_box)
            ax.text(4, 7, "Ввод данных", fontsize=10, ha="center", va="center")

            # Условие (ромб)
            condition = plt.Polygon(
                [(4, 5.5), (5.5, 4), (4, 2.5), (2.5, 4)],
                fill=True,
                facecolor="#87CEEB",
                ec="black",
                linewidth=2,
            )
            ax.add_patch(condition)
            ax.text(4, 4, "Условие?", fontsize=10, ha="center", va="center", fontweight="bold")

            # Действие 1 (прямоугольник)
            action1 = plt.Rectangle(
                (5.5, 3), 2, 1, fill=True, facecolor="#FFB6C1", ec="black", linewidth=2
            )
            ax.add_patch(action1)
            ax.text(6.5, 3.5, "Действие 1", fontsize=9, ha="center", va="center")

            # Действие 2 (прямоугольник)
            action2 = plt.Rectangle(
                (0.5, 3), 2, 1, fill=True, facecolor="#FFB6C1", ec="black", linewidth=2
            )
            ax.add_patch(action2)
            ax.text(1.5, 3.5, "Действие 2", fontsize=9, ha="center", va="center")

            # Конец (скругленный прямоугольник)
            end = plt.Rectangle(
                (2.5, 1), 3, 1, fill=True, facecolor="#FF6B6B", ec="black", linewidth=2
            )
            ax.add_patch(end)
            ax.text(4, 1.5, "КОНЕЦ", fontsize=10, ha="center", va="center", fontweight="bold")

            # Стрелки
            ax.arrow(
                4,
                8,
                0,
                -0.5,
                head_width=0.2,
                head_length=0.15,
                fc="black",
                ec="black",
                linewidth=1.5,
            )
            ax.arrow(
                4,
                7.5,
                0,
                -0.5,
                head_width=0.2,
                head_length=0.15,
                fc="black",
                ec="black",
                linewidth=1.5,
            )
            ax.arrow(
                5.5,
                4,
                0.7,
                -0.7,
                head_width=0.2,
                head_length=0.15,
                fc="black",
                ec="black",
                linewidth=1.5,
            )
            ax.text(7, 2.5, "Да", fontsize=9)
            ax.arrow(
                2.5,
                4,
                -0.7,
                -0.7,
                head_width=0.2,
                head_length=0.15,
                fc="black",
                ec="black",
                linewidth=1.5,
            )
            ax.text(1, 2.5, "Нет", fontsize=9)
            ax.arrow(
                7.5,
                3,
                -3,
                -1,
                head_width=0.2,
                head_length=0.15,
                fc="black",
                ec="black",
                linewidth=1.5,
            )
            ax.arrow(
                1.5,
                3,
                1,
                -1,
                head_width=0.2,
                head_length=0.15,
                fc="black",
                ec="black",
                linewidth=1.5,
            )
            ax.arrow(
                4,
                2,
                0,
                -0.5,
                head_width=0.2,
                head_length=0.15,
                fc="black",
                ec="black",
                linewidth=1.5,
            )

            ax.set_xlim(-1, 9)
            ax.set_ylim(0, 10)
            ax.set_title("Блок-схема алгоритма", fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована блок-схема алгоритма")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации блок-схемы алгоритма: {e}", exc_info=True)
            return None

    def generate_state_structure_scheme(self) -> bytes | None:
        """
        Генерирует упрощенную схему структуры государства (РФ - ветви власти).

        Returns:
            bytes: Изображение схемы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Центр: Государство
            state_circle = plt.Circle((5, 6), 1, color="#FF6B6B", ec="black", linewidth=2)
            ax.add_patch(state_circle)
            ax.text(
                5,
                6,
                "ГОСУДАРСТВО",
                fontsize=10,
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
            )

            # Три ветви власти
            # Законодательная
            leg_rect = plt.Rectangle((1, 2), 2.5, 1.5, color="#90EE90", ec="black", linewidth=2)
            ax.add_patch(leg_rect)
            ax.text(
                2.25,
                2.75,
                "Законодательная\n(Госдума,\nСовет Федерации)",
                fontsize=9,
                ha="center",
                va="center",
            )

            # Исполнительная
            exec_rect = plt.Rectangle((3.75, 2), 2.5, 1.5, color="#87CEEB", ec="black", linewidth=2)
            ax.add_patch(exec_rect)
            ax.text(
                5,
                2.75,
                "Исполнительная\n(Правительство,\nПрезидент)",
                fontsize=9,
                ha="center",
                va="center",
            )

            # Судебная
            jud_rect = plt.Rectangle((6.5, 2), 2.5, 1.5, color="#FFD700", ec="black", linewidth=2)
            ax.add_patch(jud_rect)
            ax.text(
                7.75, 2.75, "Судебная\n(Верховный суд,\nсуды)", fontsize=9, ha="center", va="center"
            )

            # Стрелки от государства к ветвям
            ax.arrow(
                4,
                5.5,
                -1.5,
                -2,
                head_width=0.3,
                head_length=0.2,
                fc="black",
                ec="black",
                linewidth=2,
            )
            ax.arrow(
                5, 5.5, 0, -2, head_width=0.3, head_length=0.2, fc="black", ec="black", linewidth=2
            )
            ax.arrow(
                6,
                5.5,
                1.5,
                -2,
                head_width=0.3,
                head_length=0.2,
                fc="black",
                ec="black",
                linewidth=2,
            )

            ax.set_xlim(-1, 11)
            ax.set_ylim(0, 9)
            ax.set_title(
                "Схема структуры государства (разделение властей)",
                fontsize=14,
                fontweight="bold",
                pad=20,
            )

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована схема структуры государства")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы структуры государства: {e}", exc_info=True)
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
