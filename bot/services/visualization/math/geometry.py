"""
Модуль визуализации для геометрии.

Формулы площадей, объемов, классификация фигур, тригонометрия.
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


class GeometryVisualization(BaseVisualizationService):
    """Визуализация для геометрии: формулы, классификация, тригонометрия."""

    def generate_geometry_area_formulas_table(self) -> bytes | None:
        """Генерирует таблицу формул площадей плоских фигур."""
        headers = ["Фигура", "Формула", "Обозначения"]
        rows = [
            ["Треугольник", "S = (1/2)ah", "a - основание, h - высота"],
            ["Параллелограмм", "S = ah", "a - сторона, h - высота"],
            ["Ромб", "S = (1/2)d₁d₂", "d₁, d₂ - диагонали"],
            ["Трапеция", "S = (1/2)(a+b)h", "a, b - основания, h - высота"],
            ["Круг", "S = πr²", "r - радиус"],
            ["Прямоугольник", "S = ab", "a, b - стороны"],
            ["Квадрат", "S = a²", "a - сторона"],
        ]
        return self.generate_table(headers, rows, "Формулы площадей плоских фигур")

    def generate_geometry_volume_formulas_table(self) -> bytes | None:
        """Генерирует таблицу формул объемов пространственных тел."""
        headers = ["Тело", "Формула", "Обозначения"]
        rows = [
            ["Призма", "V = Sh", "S - площадь основания, h - высота"],
            ["Пирамида", "V = (1/3)Sh", "S - площадь основания, h - высота"],
            ["Цилиндр", "V = πr²h", "r - радиус, h - высота"],
            ["Конус", "V = (1/3)πr²h", "r - радиус, h - высота"],
            ["Шар", "V = (4/3)πr³", "r - радиус"],
            ["Куб", "V = a³", "a - ребро"],
            ["Параллелепипед", "V = abc", "a, b, c - измерения"],
        ]
        return self.generate_table(headers, rows, "Формулы объемов пространственных тел")

    def generate_triangle_classification_table(self) -> bytes | None:
        """Генерирует таблицу классификации треугольников."""
        headers = ["Признак", "Вид", "Описание"]
        rows = [
            ["По сторонам", "Равносторонний", "все стороны равны"],
            ["По сторонам", "Равнобедренный", "две стороны равны"],
            ["По сторонам", "Разносторонний", "все стороны разные"],
            ["По углам", "Остроугольный", "все углы < 90°"],
            ["По углам", "Прямоугольный", "один угол = 90°"],
            ["По углам", "Тупоугольный", "один угол > 90°"],
        ]
        return self.generate_table(headers, rows, "Классификация треугольников")

    def generate_quadrilateral_classification_table(self) -> bytes | None:
        """Генерирует таблицу классификации четырехугольников."""
        headers = ["Четырехугольник", "Признаки", "Свойства"]
        rows = [
            ["Параллелограмм", "противоположные стороны параллельны", "диагонали делятся пополам"],
            ["Прямоугольник", "параллелограмм с прямыми углами", "диагонали равны"],
            ["Ромб", "параллелограмм с равными сторонами", "диагонали перпендикулярны"],
            ["Квадрат", "прямоугольник с равными сторонами", "все свойства"],
            ["Трапеция", "одна пара сторон параллельна", "средняя линия = (a+b)/2"],
        ]
        return self.generate_table(headers, rows, "Классификация четырехугольников")

    def generate_trigonometry_table(self) -> bytes | None:
        """Генерирует таблицу тригонометрических функций для стандартных углов."""
        headers = ["Угол", "sin", "cos", "tan", "cot"]
        rows = [
            ["0°", "0", "1", "0", "не определен"],
            ["30°", "1/2", "√3/2", "√3/3", "√3"],
            ["45°", "√2/2", "√2/2", "1", "1"],
            ["60°", "√3/2", "1/2", "√3", "√3/3"],
            ["90°", "1", "0", "не определен", "0"],
            ["180°", "0", "-1", "0", "не определен"],
        ]
        return self.generate_table(headers, rows, "Тригонометрические функции")

    def generate_median_diagram(self) -> bytes | None:
        """
        Генерирует схему треугольника с медианами.

        Returns:
            bytes: Изображение в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            fig.patch.set_facecolor("white")
            ax.set_aspect("equal")
            ax.axis("off")

            # Координаты вершин треугольника
            A = (0, 0)
            B = (6, 0)
            C = (3, 5)

            # Рисуем треугольник
            triangle = plt.Polygon([A, B, C], fill=False, edgecolor="black", linewidth=2)
            ax.add_patch(triangle)

            # Находим середины сторон
            M_AB = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)  # Середина AB
            M_BC = ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2)  # Середина BC
            M_AC = ((A[0] + C[0]) / 2, (A[1] + C[1]) / 2)  # Середина AC

            # Рисуем медианы
            ax.plot([A[0], M_BC[0]], [A[1], M_BC[1]], "r-", linewidth=2, label="Медиана")
            ax.plot([B[0], M_AC[0]], [B[1], M_AC[1]], "r-", linewidth=2)
            ax.plot([C[0], M_AB[0]], [C[1], M_AB[1]], "r-", linewidth=2)

            # Точка пересечения медиан (центроид)
            centroid = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
            ax.plot(centroid[0], centroid[1], "ro", markersize=10, label="Центроид")

            # Подписи вершин
            ax.text(A[0] - 0.3, A[1] - 0.3, "A", fontsize=14, fontweight="bold")
            ax.text(B[0] + 0.3, B[1] - 0.3, "B", fontsize=14, fontweight="bold")
            ax.text(C[0], C[1] + 0.3, "C", fontsize=14, fontweight="bold")

            # Подписи середин сторон
            ax.text(M_AB[0] + 0.2, M_AB[1] - 0.3, "M", fontsize=12, color="blue")
            ax.text(M_BC[0] - 0.3, M_BC[1] - 0.3, "M", fontsize=12, color="blue")
            ax.text(M_AC[0] - 0.3, M_AC[1] + 0.2, "M", fontsize=12, color="blue")

            # Подпись центроида
            ax.text(
                centroid[0] + 0.2,
                centroid[1] + 0.2,
                "O",
                fontsize=12,
                color="red",
                fontweight="bold",
            )

            # Заголовок
            ax.text(
                0.5,
                0.95,
                "Треугольник с медианами",
                transform=ax.transAxes,
                ha="center",
                fontsize=16,
                fontweight="bold",
            )

            # Легенда
            ax.legend(loc="upper right", fontsize=10)

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирована схема треугольника с медианами")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы медианы: {e}", exc_info=True)
            return None
