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

    def generate_function_graph(self, expression: str, x_range: tuple = (-10, 10)) -> bytes | None:
        """
        Генерирует график функции.

        Args:
            expression: Выражение функции (например, "x**2", "2*x+3", "np.sin(x)")
            x_range: Диапазон значений x (min, max)

        Returns:
            bytes: Изображение графика в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            x = np.linspace(x_range[0], x_range[1], 1000)

            # Безопасное вычисление функции
            # Поддерживаем только простые функции для безопасности
            safe_globals = {
                "np": np,
                "x": x,
                "sin": np.sin,
                "cos": np.cos,
                "tan": np.tan,
                "exp": np.exp,
                "log": np.log,
                "sqrt": np.sqrt,
            }

            try:
                y = eval(expression, {"__builtins__": {}}, safe_globals)
            except Exception:
                logger.warning(f"⚠️ Не удалось вычислить функцию: {expression}")
                return None

            fig, ax = plt.subplots(figsize=(8, 6))
            fig.patch.set_facecolor("white")
            ax.plot(x, y, linewidth=2, color="#4A90E2")
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("x", fontsize=12)
            ax.set_ylabel("y", fontsize=12)
            ax.set_title(f"График функции: y = {expression}", fontsize=14, fontweight="bold")
            ax.axhline(y=0, color="k", linewidth=0.5)
            ax.axvline(x=0, color="k", linewidth=0.5)

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
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

    def detect_visualization_request(self, text: str) -> bytes | None:
        """
        Универсальный метод для детекции и генерации визуализации из текста.

        Анализирует текст и определяет, нужна ли визуализация (таблица умножения, график).
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
        full_table_patterns = [
            r"табл[иы]ц[аеы]?\s*умножени[яе](?:\s+на\s+все)?",
            r"покажи\s+табл[иы]ц[аеы]?\s*умножени[яе]",
            r"выведи\s+табл[иы]ц[аеы]?\s*умножени[яе]",
            r"покажи\s+умножени[яе]",
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
            r"табл[иы]ц[аеы]?\s*умножени[яе]\s*на\s*(\d+)",
            r"табл[иы]ц[аеы]?\s*умножени[яе]\s+(\d+)",
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
            r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
            r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
            r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
            r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n]+)",
            r"(?:синусоид|sin|косинус|cos|тангенс|tan|экспонент|exp|логарифм|log|парабол)",
        ]

        # Проверяем графики
        graph_match = None
        for pattern in graph_patterns:
            graph_match = re.search(pattern, text_lower)
            if graph_match:
                break

        if graph_match:
            # Стандартные функции по названию
            if re.search(r"(?:синусоид|sin)", text_lower):
                image = self.generate_function_graph("sin(x)")
                if image:
                    logger.info("📈 Детектирован график синусоиды")
                return image
            elif re.search(r"(?:косинус|cos)", text_lower):
                image = self.generate_function_graph("cos(x)")
                if image:
                    logger.info("📈 Детектирован график косинуса")
                return image
            elif re.search(r"(?:тангенс|tan)", text_lower):
                image = self.generate_function_graph("tan(x)")
                if image:
                    logger.info("📈 Детектирован график тангенса")
                return image
            elif re.search(r"(?:парабол)", text_lower):
                image = self.generate_function_graph("x**2")
                if image:
                    logger.info("📈 Детектирован график параболы")
                return image
            else:
                # Извлекаем выражение из паттерна
                expression = graph_match.group(1).strip() if graph_match.groups() else ""
                if expression:
                    # Заменяем x^2 на x**2 для Python
                    expression = expression.replace("^", "**")
                    # Безопасная проверка выражения
                    if re.match(r"^[x\s+\-*/().\d\s]+$", expression):
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
