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
            if num_tables == 1:
                fig, axes = plt.subplots(1, 1, figsize=(6, 8))
                axes = [axes]
            elif num_tables == 2:
                fig, axes = plt.subplots(1, 2, figsize=(14, 8))
            else:  # 3
                fig, axes = plt.subplots(1, 3, figsize=(20, 8))

            fig.patch.set_facecolor("white")

            for idx, number in enumerate(numbers):
                ax = axes[idx]
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
                table.set_fontsize(10 if num_tables > 1 else 12)
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
