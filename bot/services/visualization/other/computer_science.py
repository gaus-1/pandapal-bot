"""Модуль визуализации для информатики."""

import io

from loguru import logger

try:
    import matplotlib
    import matplotlib.patches as mpatches

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from bot.services.visualization.base import BaseVisualizationService


class ComputerScienceVisualization(BaseVisualizationService):
    """Визуализация для информатики: системы счисления, блок-схемы, логические таблицы."""

    def generate_number_systems_table(self) -> bytes | None:
        """Генерирует таблицу систем счисления."""
        headers = ["Система", "Основание", "Цифры", "Пример"]
        rows = [
            ["Двоичная", "2", "0, 1", "1010₂ = 10₁₀"],
            ["Восьмеричная", "8", "0-7", "12₈ = 10₁₀"],
            ["Десятичная", "10", "0-9", "10₁₀ = 10₁₀"],
            ["Шестнадцатеричная", "16", "0-9, A-F", "A₁₆ = 10₁₀"],
        ]
        return self.generate_table(headers, rows, "Системы счисления")

    def generate_flowchart(self, algorithm_type: str = "linear") -> bytes | None:
        """
        Генерирует блок-схему алгоритма.

        Args:
            algorithm_type: Тип алгоритма (linear, branching, loop, factorial)
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(8, 10))
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 12)
            ax.axis("off")

            if algorithm_type == "branching":
                # Блок-схема с ветвлением (если-то-иначе)
                self._draw_flowchart_branching(ax)
                title = "Блок-схема: Ветвление (если-то-иначе)"
            elif algorithm_type == "loop":
                # Блок-схема с циклом
                self._draw_flowchart_loop(ax)
                title = "Блок-схема: Цикл с условием"
            elif algorithm_type == "factorial":
                # Блок-схема вычисления факториала
                self._draw_flowchart_factorial(ax)
                title = "Блок-схема: Вычисление факториала"
            else:
                # Линейный алгоритм
                self._draw_flowchart_linear(ax)
                title = "Блок-схема: Линейный алгоритм"

            ax.set_title(title, fontsize=14, fontweight="bold", y=1.02)

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована блок-схема: {algorithm_type}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации блок-схемы: {e}", exc_info=True)
            return None

    def _draw_oval(self, ax, x, y, text, width=2.5, height=0.8):
        """Рисует овал (начало/конец)."""
        oval = mpatches.FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.1,rounding_size=0.4",
            facecolor="lightgreen",
            edgecolor="black",
            linewidth=2,
        )
        ax.add_patch(oval)
        ax.text(x, y, text, ha="center", va="center", fontsize=10, fontweight="bold")

    def _draw_rect(self, ax, x, y, text, width=2.5, height=0.8):
        """Рисует прямоугольник (действие)."""
        rect = mpatches.FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="square,pad=0.05",
            facecolor="lightyellow",
            edgecolor="black",
            linewidth=2,
        )
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center", fontsize=9)

    def _draw_parallelogram(self, ax, x, y, text, width=2.5, height=0.8):
        """Рисует параллелограмм (ввод/вывод)."""
        from matplotlib.patches import Polygon

        dx = 0.3
        points = [
            [x - width / 2 + dx, y - height / 2],
            [x + width / 2 + dx, y - height / 2],
            [x + width / 2 - dx, y + height / 2],
            [x - width / 2 - dx, y + height / 2],
        ]
        poly = Polygon(points, facecolor="lightblue", edgecolor="black", linewidth=2)
        ax.add_patch(poly)
        ax.text(x, y, text, ha="center", va="center", fontsize=9)

    def _draw_diamond(self, ax, x, y, text, size=1.2):
        """Рисует ромб (условие)."""
        from matplotlib.patches import Polygon

        points = [
            [x, y + size],
            [x + size, y],
            [x, y - size],
            [x - size, y],
        ]
        poly = Polygon(points, facecolor="lightsalmon", edgecolor="black", linewidth=2)
        ax.add_patch(poly)
        ax.text(x, y, text, ha="center", va="center", fontsize=9)

    def _draw_arrow(self, ax, x1, y1, x2, y2):
        """Рисует стрелку."""
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
        )

    def _draw_flowchart_linear(self, ax):
        """Линейный алгоритм: Начало → Ввод → Действие → Вывод → Конец."""
        cx = 5
        self._draw_oval(ax, cx, 11, "Начало")
        self._draw_arrow(ax, cx, 10.6, cx, 10)
        self._draw_parallelogram(ax, cx, 9.5, "Ввод: a, b")
        self._draw_arrow(ax, cx, 9.1, cx, 8.3)
        self._draw_rect(ax, cx, 7.8, "c = a + b")
        self._draw_arrow(ax, cx, 7.4, cx, 6.6)
        self._draw_parallelogram(ax, cx, 6.1, "Вывод: c")
        self._draw_arrow(ax, cx, 5.7, cx, 5)
        self._draw_oval(ax, cx, 4.5, "Конец")

    def _draw_flowchart_branching(self, ax):
        """Алгоритм с ветвлением."""
        cx = 5
        self._draw_oval(ax, cx, 11, "Начало")
        self._draw_arrow(ax, cx, 10.6, cx, 10)
        self._draw_parallelogram(ax, cx, 9.5, "Ввод: x")
        self._draw_arrow(ax, cx, 9.1, cx, 8)
        self._draw_diamond(ax, cx, 7, "x > 0 ?")

        # Ветка "Да"
        ax.text(cx + 1.5, 7.3, "Да", fontsize=9)
        self._draw_arrow(ax, cx + 1.2, 7, 7.5, 5.5)
        self._draw_rect(ax, 7.5, 5, 'y = "положит."', width=2.2)

        # Ветка "Нет"
        ax.text(cx - 1.5, 7.3, "Нет", fontsize=9)
        self._draw_arrow(ax, cx - 1.2, 7, 2.5, 5.5)
        self._draw_rect(ax, 2.5, 5, 'y = "отриц."', width=2.2)

        # Сходимся
        self._draw_arrow(ax, 7.5, 4.6, cx, 3.5)
        self._draw_arrow(ax, 2.5, 4.6, cx, 3.5)
        self._draw_parallelogram(ax, cx, 3, "Вывод: y")
        self._draw_arrow(ax, cx, 2.6, cx, 2)
        self._draw_oval(ax, cx, 1.5, "Конец")

    def _draw_flowchart_loop(self, ax):
        """Алгоритм с циклом (сумма чисел от 1 до n)."""
        cx = 5
        self._draw_oval(ax, cx, 11, "Начало")
        self._draw_arrow(ax, cx, 10.6, cx, 10)
        self._draw_parallelogram(ax, cx, 9.5, "Ввод: n")
        self._draw_arrow(ax, cx, 9.1, cx, 8.3)
        self._draw_rect(ax, cx, 7.8, "s=0, i=1")
        self._draw_arrow(ax, cx, 7.4, cx, 6.5)
        self._draw_diamond(ax, cx, 5.5, "i ≤ n ?")

        # Ветка "Да" - тело цикла
        ax.text(cx + 1.5, 5.8, "Да", fontsize=9)
        self._draw_arrow(ax, cx + 1.2, 5.5, 8, 4.5)
        self._draw_rect(ax, 8, 4, "s = s + i")
        self._draw_arrow(ax, 8, 3.6, 8, 3)
        self._draw_rect(ax, 8, 2.5, "i = i + 1")
        # Возврат к условию
        ax.annotate(
            "",
            xy=(cx + 1, 5.5),
            xytext=(8, 2.1),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=-0.3"),
        )

        # Ветка "Нет" - выход из цикла
        ax.text(cx - 1.5, 5.8, "Нет", fontsize=9)
        self._draw_arrow(ax, cx - 1.2, 5.5, 2, 3)
        self._draw_parallelogram(ax, 2.5, 2.5, "Вывод: s", width=2)
        self._draw_arrow(ax, 2.5, 2.1, 2.5, 1.5)
        self._draw_oval(ax, 2.5, 1, "Конец", width=2)

    def _draw_flowchart_factorial(self, ax):
        """Алгоритм вычисления факториала."""
        cx = 5
        self._draw_oval(ax, cx, 11, "Начало")
        self._draw_arrow(ax, cx, 10.6, cx, 10)
        self._draw_parallelogram(ax, cx, 9.5, "Ввод: n")
        self._draw_arrow(ax, cx, 9.1, cx, 8.3)
        self._draw_rect(ax, cx, 7.8, "f = 1")
        self._draw_arrow(ax, cx, 7.4, cx, 6.5)
        self._draw_diamond(ax, cx, 5.5, "n > 1 ?")

        # Ветка "Да"
        ax.text(cx + 1.5, 5.8, "Да", fontsize=9)
        self._draw_arrow(ax, cx + 1.2, 5.5, 8, 4.5)
        self._draw_rect(ax, 8, 4, "f = f × n")
        self._draw_arrow(ax, 8, 3.6, 8, 3)
        self._draw_rect(ax, 8, 2.5, "n = n − 1")
        ax.annotate(
            "",
            xy=(cx + 1, 5.5),
            xytext=(8, 2.1),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=-0.3"),
        )

        # Ветка "Нет"
        ax.text(cx - 1.5, 5.8, "Нет", fontsize=9)
        self._draw_arrow(ax, cx - 1.2, 5.5, 2, 3)
        self._draw_parallelogram(ax, 2.5, 2.5, "Вывод: f", width=2)
        self._draw_arrow(ax, 2.5, 2.1, 2.5, 1.5)
        self._draw_oval(ax, 2.5, 1, "Конец", width=2)

    def generate_truth_table(self, operation: str = "and") -> bytes | None:
        """
        Генерирует таблицу истинности для логических операций.

        Args:
            operation: Логическая операция (and, or, not, xor, nand, nor)
        """
        operations = {
            "and": {
                "name": "И (AND, ∧)",
                "headers": ["A", "B", "A ∧ B"],
                "rows": [["0", "0", "0"], ["0", "1", "0"], ["1", "0", "0"], ["1", "1", "1"]],
            },
            "or": {
                "name": "ИЛИ (OR, ∨)",
                "headers": ["A", "B", "A ∨ B"],
                "rows": [["0", "0", "0"], ["0", "1", "1"], ["1", "0", "1"], ["1", "1", "1"]],
            },
            "not": {
                "name": "НЕ (NOT, ¬)",
                "headers": ["A", "¬A"],
                "rows": [["0", "1"], ["1", "0"]],
            },
            "xor": {
                "name": "Исключающее ИЛИ (XOR, ⊕)",
                "headers": ["A", "B", "A ⊕ B"],
                "rows": [["0", "0", "0"], ["0", "1", "1"], ["1", "0", "1"], ["1", "1", "0"]],
            },
            "nand": {
                "name": "И-НЕ (NAND)",
                "headers": ["A", "B", "A NAND B"],
                "rows": [["0", "0", "1"], ["0", "1", "1"], ["1", "0", "1"], ["1", "1", "0"]],
            },
            "nor": {
                "name": "ИЛИ-НЕ (NOR)",
                "headers": ["A", "B", "A NOR B"],
                "rows": [["0", "0", "1"], ["0", "1", "0"], ["1", "0", "0"], ["1", "1", "0"]],
            },
        }

        op_data = operations.get(operation.lower(), operations["and"])
        return self.generate_table(
            op_data["headers"], op_data["rows"], f"Таблица истинности: {op_data['name']}"
        )
