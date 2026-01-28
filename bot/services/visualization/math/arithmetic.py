"""
Модуль визуализации для арифметики (1-4 классы).

Таблицы умножения, сложения, вычитания, деления.
"""

import io

from loguru import logger

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from bot.services.visualization.base import BaseVisualizationService


class ArithmeticVisualization(BaseVisualizationService):
    """Визуализация для арифметики: таблицы умножения, сложения, вычитания, деления."""

    def generate_full_multiplication_table(self) -> bytes | None:
        """
        Генерирует полную таблицу умножения (1-10) в двух частях для лучшей читаемости.

        Returns:
            bytes: Изображение в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # Создаем фигуру с двумя подграфиками (вертикально)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
            fig.patch.set_facecolor("white")

            # Общий заголовок
            fig.suptitle("Таблица умножения", fontsize=18, fontweight="bold", y=0.98)

            # Первая таблица: 1-5
            ax1.axis("off")
            ax1.text(
                0.5,
                0.95,
                "От 1 до 5",
                ha="center",
                va="top",
                fontsize=14,
                fontweight="bold",
                transform=ax1.transAxes,
            )

            table_data_1 = []
            for i in range(1, 6):
                row = []
                for j in range(1, 11):
                    row.append(f"{i}×{j}={i*j}")
                table_data_1.append(row)

            table1 = ax1.table(
                cellText=table_data_1,
                cellLoc="center",
                loc="center",
                bbox=[0, 0.1, 1, 0.8],
            )
            table1.auto_set_font_size(False)
            table1.set_fontsize(10)
            table1.scale(1, 1.8)

            for i in range(5):
                for j in range(10):
                    cell = table1[(i, j)]
                    if (i + j) % 2 == 0:
                        cell.set_facecolor("#f0f8ff")
                    else:
                        cell.set_facecolor("white")
                    cell.set_text_props(weight="normal")

            # Вторая таблица: 6-10
            ax2.axis("off")
            ax2.text(
                0.5,
                0.95,
                "От 6 до 10",
                ha="center",
                va="top",
                fontsize=14,
                fontweight="bold",
                transform=ax2.transAxes,
            )

            table_data_2 = []
            for i in range(6, 11):
                row = []
                for j in range(1, 11):
                    row.append(f"{i}×{j}={i*j}")
                table_data_2.append(row)

            table2 = ax2.table(
                cellText=table_data_2,
                cellLoc="center",
                loc="center",
                bbox=[0, 0.1, 1, 0.8],
            )
            table2.auto_set_font_size(False)
            table2.set_fontsize(10)
            table2.scale(1, 1.8)

            for i in range(5):
                for j in range(10):
                    cell = table2[(i, j)]
                    if (i + j) % 2 == 0:
                        cell.set_facecolor("#f0f8ff")
                    else:
                        cell.set_facecolor("white")
                    cell.set_text_props(weight="normal")

            plt.tight_layout(rect=[0, 0, 1, 0.97])

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована полная таблица умножения (оптимизированная)")
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

    def generate_addition_table(self) -> bytes | None:
        """Генерирует таблицу сложения (1-10)."""
        headers = ["+"] + [str(i) for i in range(1, 11)]
        rows = []
        for i in range(1, 11):
            row = [str(i)] + [str(i + j) for j in range(1, 11)]
            rows.append(row)
        return self.generate_table(headers, rows, "Таблица сложения")

    def generate_subtraction_table(self) -> bytes | None:
        """Генерирует таблицу вычитания (1-10)."""
        headers = ["-"] + [str(i) for i in range(1, 11)]
        rows = []
        for i in range(1, 11):
            row = [str(i)] + [str(max(0, i - j)) if i >= j else "-" for j in range(1, 11)]
            rows.append(row)
        return self.generate_table(headers, rows, "Таблица вычитания")

    def generate_division_table(self) -> bytes | None:
        """Генерирует таблицу деления (1-10)."""
        headers = ["÷"] + [str(i) for i in range(1, 11)]
        rows = []
        for i in range(1, 11):
            row = [str(i)] + [
                f"{i // j}" if i % j == 0 else f"{i / j:.1f}" if j != 0 else "-"
                for j in range(1, 11)
            ]
            rows.append(row)
        return self.generate_table(headers, rows, "Таблица деления")

    def generate_units_table(self) -> bytes | None:
        """Генерирует таблицу единиц измерения."""
        headers = ["Величина", "Основная единица", "Краткие единицы", "Примеры"]
        rows = [
            ["Длина", "метр (м)", "см, мм, км", "1 м = 100 см = 1000 мм"],
            ["Масса", "килограмм (кг)", "г, т", "1 кг = 1000 г"],
            ["Время", "секунда (с)", "мин, ч, сут", "1 ч = 60 мин = 3600 с"],
            ["Площадь", "квадратный метр (м²)", "см², км²", "1 м² = 10000 см²"],
            ["Объем", "кубический метр (м³)", "л, мл", "1 л = 1000 мл"],
        ]
        return self.generate_table(headers, rows, "Таблица единиц измерения")

    def generate_multiple_multiplication_tables(self, numbers: list[int]) -> bytes | None:
        """
        Генерирует несколько таблиц умножения в одной картинке.

        Args:
            numbers: Список чисел для таблиц умножения (например, [7, 9])

        Returns:
            bytes: Изображение с несколькими таблицами или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        if not numbers:
            return None

        # Ограничиваем количество таблиц (максимум 3 для читаемости)
        numbers = sorted(set(numbers))[:3]

        try:
            # Вычисляем размер фигуры в зависимости от количества таблиц
            num_tables = len(numbers)
            # Располагаем таблицы вертикально (одна под другой), чтобы лучше читалось на мобильных
            if num_tables == 1:
                fig, axes = plt.subplots(1, 1, figsize=(6, 8))
            elif num_tables == 2:
                fig, axes = plt.subplots(2, 1, figsize=(6, 12))
            else:  # 3
                fig, axes = plt.subplots(3, 1, figsize=(6, 16))

            fig.patch.set_facecolor("white")

            # Нормализуем axes в список (учитываем, что subplots возвращает np.ndarray)
            import numpy as _np  # локальный импорт, чтобы не полз вверх по файлу

            if isinstance(axes, _np.ndarray):
                axes_list = axes.ravel().tolist()
            elif isinstance(axes, list | tuple):
                axes_list = list(axes)
            else:
                axes_list = [axes]

            for idx, number in enumerate(numbers):
                ax = axes_list[idx]
                ax.axis("off")

                title = f"Таблица умножения на {number}"
                ax.text(
                    0.5,
                    0.95,
                    title,
                    ha="center",
                    va="top",
                    fontsize=14,
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
                # Чуть увеличиваем шрифт, особенно для 2-3 таблиц
                table.set_fontsize(12 if num_tables == 1 else 11)
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

            logger.info(f"✅ Сгенерированы таблицы умножения на {numbers}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации нескольких таблиц умножения: {e}", exc_info=True)
            return None

    def generate_combined_table_and_graph(
        self, table_number: int, graph_expression: str
    ) -> bytes | None:
        """
        Генерирует комбинированную картинку: таблица умножения + график функции.

        Args:
            table_number: Число для таблицы умножения (1-10)
            graph_expression: Выражение функции для графика (например, "sin(x)")

        Returns:
            bytes: Изображение с таблицей сверху и графиком снизу или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        if not (1 <= table_number <= 10):
            logger.warning(f"⚠️ Некорректное число для таблицы: {table_number}")
            return None

        try:
            import numpy as np

            # Создаем фигуру с двумя subplots: таблица сверху, график снизу
            fig = plt.figure(figsize=(10, 12))
            fig.patch.set_facecolor("white")

            # Верхний subplot для таблицы
            ax_table = plt.subplot(2, 1, 1)
            ax_table.axis("off")

            # Заголовок таблицы
            ax_table.text(
                0.5,
                0.95,
                f"Таблица умножения на {table_number}",
                ha="center",
                va="top",
                fontsize=16,
                fontweight="bold",
                transform=ax_table.transAxes,
            )

            # Генерируем данные таблицы
            table_data = []
            for i in range(1, 11):
                table_data.append([f"{table_number} × {i} = {table_number * i}"])

            # Создаем таблицу
            table = ax_table.table(
                cellText=table_data,
                cellLoc="center",
                loc="center",
                bbox=[0.2, 0.1, 0.6, 0.8],
            )
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 2)

            # Стилизация таблицы
            for i in range(len(table_data)):
                cell = table[(i, 0)]
                cell.set_facecolor("#f0f8ff" if i % 2 == 0 else "white")
                cell.set_text_props(weight="normal")

            # Нижний subplot для графика
            ax_graph = plt.subplot(2, 1, 2)

            # Нормализуем выражение
            normalized_expr = (
                graph_expression.replace("²", "**2").replace("³", "**3").replace("^", "**")
            )

            # Генерируем данные для графика
            x = np.linspace(-10, 10, 1000)
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
                y = eval(normalized_expr, {"__builtins__": {}}, safe_globals)
                mask = np.isfinite(y)
                x = x[mask]
                y = y[mask]
            except Exception as e:
                logger.warning(f"⚠️ Не удалось вычислить функцию: {graph_expression}, ошибка: {e}")
                plt.close(fig)
                return None

            if len(x) == 0:
                logger.warning(f"⚠️ Нет валидных точек для функции: {graph_expression}")
                plt.close(fig)
                return None

            # Рисуем график
            ax_graph.plot(x, y, linewidth=2.5, color="#4A90E2")
            ax_graph.grid(True, alpha=0.3, linestyle="--")
            ax_graph.set_xlabel("x", fontsize=13, fontweight="bold")
            ax_graph.set_ylabel("y", fontsize=13, fontweight="bold")

            # Формируем заголовок графика
            display_expr = graph_expression.replace("**", "^").replace("*", "·")
            graph_title = f"График функции: y = {display_expr}"
            ax_graph.set_title(graph_title, fontsize=15, fontweight="bold", pad=15)
            ax_graph.axhline(y=0, color="k", linewidth=0.8, linestyle="-")
            ax_graph.axvline(x=0, color="k", linewidth=0.8, linestyle="-")

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(
                f"✅ Сгенерирована комбинированная визуализация: таблица на {table_number} + график {graph_expression}"
            )
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации комбинированной визуализации: {e}", exc_info=True)
            return None
