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

    def generate_squares_and_cubes_table(self) -> bytes | None:
        """
        Генерирует таблицу квадратов и кубов чисел (1-20).

        Returns:
            bytes: Изображение таблицы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            headers = ["Число", "Квадрат (x²)", "Куб (x³)"]
            rows = []
            for i in range(1, 21):
                rows.append([str(i), str(i**2), str(i**3)])

            return self.generate_table(headers, rows, "Таблица квадратов и кубов")
        except Exception as e:
            logger.error(f"❌ Ошибка генерации таблицы квадратов и кубов: {e}", exc_info=True)
            return None

    def generate_chemistry_solubility_table(self) -> bytes | None:
        """
        Генерирует упрощенную таблицу растворимости веществ.

        Returns:
            bytes: Изображение таблицы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            headers = ["Вещество", "Формула", "Растворимость"]
            rows = [
                ["Хлорид натрия", "NaCl", "Растворим"],
                ["Сульфат натрия", "Na₂SO₄", "Растворим"],
                ["Карбонат кальция", "CaCO₃", "Нерастворим"],
                ["Гидроксид натрия", "NaOH", "Растворим"],
                ["Сульфат бария", "BaSO₄", "Нерастворим"],
                ["Нитрат калия", "KNO₃", "Растворим"],
                ["Хлорид серебра", "AgCl", "Нерастворим"],
                ["Сульфат кальция", "CaSO₄", "Малорастворим"],
            ]

            return self.generate_table(headers, rows, "Таблица растворимости веществ")
        except Exception as e:
            logger.error(f"❌ Ошибка генерации таблицы растворимости: {e}", exc_info=True)
            return None

    def generate_chemistry_valence_table(self) -> bytes | None:
        """
        Генерирует таблицу валентности элементов.

        Returns:
            bytes: Изображение таблицы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            headers = ["Элемент", "Символ", "Валентность"]
            rows = [
                ["Водород", "H", "I"],
                ["Кислород", "O", "II"],
                ["Азот", "N", "III, IV, V"],
                ["Углерод", "C", "IV"],
                ["Хлор", "Cl", "I, III, V, VII"],
                ["Сера", "S", "II, IV, VI"],
                ["Фосфор", "P", "III, V"],
                ["Калий", "K", "I"],
                ["Натрий", "Na", "I"],
                ["Кальций", "Ca", "II"],
                ["Магний", "Mg", "II"],
                ["Алюминий", "Al", "III"],
            ]

            return self.generate_table(headers, rows, "Таблица валентности элементов")
        except Exception as e:
            logger.error(f"❌ Ошибка генерации таблицы валентности: {e}", exc_info=True)
            return None

    def generate_physics_constants_table(self) -> bytes | None:
        """
        Генерирует таблицу физических констант.

        Returns:
            bytes: Изображение таблицы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            headers = ["Константа", "Обозначение", "Значение"]
            rows = [
                ["Скорость света", "c", "3·10⁸ м/с"],
                ["Гравитационная постоянная", "G", "6.67·10⁻¹¹ Н·м²/кг²"],
                ["Постоянная Планка", "h", "6.63·10⁻³⁴ Дж·с"],
                ["Элементарный заряд", "e", "1.6·10⁻¹⁹ Кл"],
                ["Масса электрона", "mₑ", "9.1·10⁻³¹ кг"],
                ["Масса протона", "mₚ", "1.67·10⁻²⁷ кг"],
                ["Число Авогадро", "Nₐ", "6.02·10²³ моль⁻¹"],
                ["Постоянная Больцмана", "k", "1.38·10⁻²³ Дж/К"],
            ]

            return self.generate_table(headers, rows, "Таблица физических констант")
        except Exception as e:
            logger.error(f"❌ Ошибка генерации таблицы констант: {e}", exc_info=True)
            return None

    def generate_english_tenses_table(self) -> bytes | None:
        """
        Генерирует упрощенную таблицу времен английского языка.

        Returns:
            bytes: Изображение таблицы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            headers = ["Время", "Утверждение", "Отрицание", "Вопрос"]
            rows = [
                [
                    "Present Simple",
                    "I work",
                    "I don't work",
                    "Do I work?",
                ],
                [
                    "Past Simple",
                    "I worked",
                    "I didn't work",
                    "Did I work?",
                ],
                [
                    "Future Simple",
                    "I will work",
                    "I won't work",
                    "Will I work?",
                ],
                [
                    "Present Continuous",
                    "I am working",
                    "I'm not working",
                    "Am I working?",
                ],
                [
                    "Past Continuous",
                    "I was working",
                    "I wasn't working",
                    "Was I working?",
                ],
            ]

            return self.generate_table(headers, rows, "Таблица времен английского языка")
        except Exception as e:
            logger.error(f"❌ Ошибка генерации таблицы времен: {e}", exc_info=True)
            return None

    def generate_english_irregular_verbs_table(self) -> bytes | None:
        """
        Генерирует таблицу неправильных глаголов (топ-20).

        Returns:
            bytes: Изображение таблицы в формате PNG или None при ошибке
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            headers = ["Infinitive", "Past Simple", "Past Participle", "Перевод"]
            rows = [
                ["be", "was/were", "been", "быть"],
                ["have", "had", "had", "иметь"],
                ["do", "did", "done", "делать"],
                ["go", "went", "gone", "идти"],
                ["see", "saw", "seen", "видеть"],
                ["come", "came", "come", "приходить"],
                ["take", "took", "taken", "брать"],
                ["get", "got", "got/gotten", "получать"],
                ["make", "made", "made", "делать"],
                ["know", "knew", "known", "знать"],
                ["think", "thought", "thought", "думать"],
                ["say", "said", "said", "говорить"],
                ["find", "found", "found", "находить"],
                ["give", "gave", "given", "давать"],
                ["tell", "told", "told", "рассказывать"],
            ]

            return self.generate_table(headers, rows, "Таблица неправильных глаголов")
        except Exception as e:
            logger.error(f"❌ Ошибка генерации таблицы глаголов: {e}", exc_info=True)
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

    def generate_russian_alphabet_table(self) -> bytes | None:
        """Генерирует таблицу букв и звуков русского алфавита."""
        headers = ["Буква", "Звук", "Тип", "Пример"]
        rows = [
            ["А", "[а]", "гласный", "арка"],
            ["Б", "[б], [б']", "согласный", "бант, белка"],
            ["В", "[в], [в']", "согласный", "волк, ветер"],
            ["Г", "[г], [г']", "согласный", "гора, гиря"],
            ["Д", "[д], [д']", "согласный", "дом, день"],
            ["Е", "[э], [й'э]", "гласный", "ель, еда"],
            ["Ё", "[о], [й'о]", "гласный", "ёлка, ёж"],
            ["Ж", "[ж]", "согласный", "жук"],
            ["З", "[з], [з']", "согласный", "замок, зима"],
            ["И", "[и]", "гласный", "игла"],
            ["Й", "[й']", "согласный", "йод"],
            ["К", "[к], [к']", "согласный", "кот, кит"],
            ["Л", "[л], [л']", "согласный", "лук, лёд"],
            ["М", "[м], [м']", "согласный", "мак, мяч"],
            ["Н", "[н], [н']", "согласный", "нос, няня"],
            ["О", "[о]", "гласный", "окно"],
            ["П", "[п], [п']", "согласный", "парк, пир"],
            ["Р", "[р], [р']", "согласный", "рак, река"],
            ["С", "[с], [с']", "согласный", "сок, синий"],
            ["Т", "[т], [т']", "согласный", "ток, тир"],
            ["У", "[у]", "гласный", "ухо"],
            ["Ф", "[ф], [ф']", "согласный", "флаг, филин"],
            ["Х", "[х], [х']", "согласный", "хлеб, хит"],
            ["Ц", "[ц]", "согласный", "цапля"],
            ["Ч", "[ч']", "согласный", "чай"],
            ["Ш", "[ш]", "согласный", "шар"],
            ["Щ", "[щ']", "согласный", "щука"],
            ["Ъ", "-", "твёрдый знак", "подъезд"],
            ["Ы", "[ы]", "гласный", "рыба"],
            ["Ь", "-", "мягкий знак", "день"],
            ["Э", "[э]", "гласный", "эхо"],
            ["Ю", "[у], [й'у]", "гласный", "юла, юг"],
            ["Я", "[а], [й'а]", "гласный", "яма, яблоко"],
        ]
        return self.generate_table(headers, rows, "Русский алфавит: буквы и звуки")

    def generate_russian_cases_table(self) -> bytes | None:
        """Генерирует таблицу падежных окончаний."""
        headers = ["Падеж", "Вопросы", "Окончания (сущ. 1 скл.)", "Пример"]
        rows = [
            ["Именительный", "кто? что?", "-а, -я", "мама, земля"],
            ["Родительный", "кого? чего?", "-ы, -и", "мамы, земли"],
            ["Дательный", "кому? чему?", "-е, -е", "маме, земле"],
            ["Винительный", "кого? что?", "-у, -ю", "маму, землю"],
            ["Творительный", "кем? чем?", "-ой, -ей", "мамой, землёй"],
            ["Предложный", "о ком? о чём?", "-е, -е", "о маме, о земле"],
        ]
        return self.generate_table(headers, rows, "Падежи русского языка")

    def generate_russian_verb_conjugation_table(self) -> bytes | None:
        """Генерирует таблицу спряжения глаголов."""
        headers = ["Лицо", "Единственное число", "Множественное число"]
        rows = [
            ["1-е спряжение", "", ""],
            ["1 лицо", "я читаю", "мы читаем"],
            ["2 лицо", "ты читаешь", "вы читаете"],
            ["3 лицо", "он/она читает", "они читают"],
            ["", "", ""],
            ["2-е спряжение", "", ""],
            ["1 лицо", "я говорю", "мы говорим"],
            ["2 лицо", "ты говоришь", "вы говорите"],
            ["3 лицо", "он/она говорит", "они говорят"],
        ]
        return self.generate_table(headers, rows, "Спряжение глаголов")

    def generate_seasons_months_table(self) -> bytes | None:
        """Генерирует таблицу времен года, месяцев, дней недели."""
        headers = ["Время года", "Месяцы", "Дни недели"]
        rows = [
            ["Зима", "декабрь, январь, февраль", "понедельник, вторник"],
            ["Весна", "март, апрель, май", "среда, четверг"],
            ["Лето", "июнь, июль, август", "пятница, суббота"],
            ["Осень", "сентябрь, октябрь, ноябрь", "воскресенье"],
        ]
        return self.generate_table(headers, rows, "Времена года, месяцы, дни недели")

    def generate_natural_zones_table(self) -> bytes | None:
        """Генерирует таблицу природных зон."""
        headers = ["Природная зона", "Климат", "Растительность", "Животные"]
        rows = [
            ["Арктика", "холодный", "лишайники, мхи", "белый медведь, тюлень"],
            ["Тундра", "холодный", "мхи, карликовые деревья", "олень, песец"],
            ["Тайга", "умеренный", "хвойные леса", "медведь, волк, лось"],
            ["Смешанный лес", "умеренный", "хвойные и лиственные", "белка, заяц"],
            ["Степь", "сухой", "травы", "суслик, дрофа"],
            ["Пустыня", "жаркий, сухой", "кактусы, верблюжья колючка", "верблюд, скорпион"],
        ]
        return self.generate_table(headers, rows, "Природные зоны России")

    def generate_time_zones_table(self) -> bytes | None:
        """Генерирует таблицу часовых поясов России."""
        headers = ["Часовой пояс", "Смещение (UTC)", "Города"]
        rows = [
            ["Калининград", "UTC+2", "Калининград"],
            ["Москва", "UTC+3", "Москва, Санкт-Петербург"],
            ["Самара", "UTC+4", "Самара, Ижевск"],
            ["Екатеринбург", "UTC+5", "Екатеринбург, Пермь"],
            ["Омск", "UTC+6", "Омск"],
            ["Красноярск", "UTC+7", "Красноярск, Новосибирск"],
            ["Иркутск", "UTC+8", "Иркутск, Улан-Удэ"],
            ["Якутск", "UTC+9", "Якутск, Чита"],
            ["Владивосток", "UTC+10", "Владивосток, Хабаровск"],
            ["Магадан", "UTC+11", "Магадан"],
            ["Камчатка", "UTC+12", "Петропавловск-Камчатский"],
        ]
        return self.generate_table(headers, rows, "Часовые пояса России")

    def generate_countries_table(self) -> bytes | None:
        """Генерирует таблицу крупнейших стран по площади и населению."""
        headers = ["Страна", "Площадь (млн км²)", "Население (млн чел.)", "Столица"]
        rows = [
            ["Россия", "17.1", "146", "Москва"],
            ["Канада", "10.0", "38", "Оттава"],
            ["Китай", "9.6", "1400", "Пекин"],
            ["США", "9.5", "330", "Вашингтон"],
            ["Бразилия", "8.5", "215", "Бразилиа"],
            ["Австралия", "7.7", "26", "Канберра"],
            ["Индия", "3.3", "1380", "Нью-Дели"],
            ["Аргентина", "2.8", "45", "Буэнос-Айрес"],
        ]
        return self.generate_table(headers, rows, "Крупнейшие страны мира")

    def generate_history_timeline_table(self) -> bytes | None:
        """Генерирует хронологическую таблицу истории России."""
        headers = ["Период", "Событие", "Годы"]
        rows = [
            ["Древняя Русь", "Образование Древнерусского государства", "862-1240"],
            ["Монгольское иго", "Зависимость от Золотой Орды", "1240-1480"],
            ["Московское царство", "Объединение русских земель", "1480-1721"],
            ["Российская империя", "Правление династии Романовых", "1721-1917"],
            ["СССР", "Советский период", "1922-1991"],
            ["Российская Федерация", "Современная Россия", "1991-н.в."],
        ]
        return self.generate_table(headers, rows, "Хронология истории России")

    def generate_government_branches_table(self) -> bytes | None:
        """Генерирует таблицу ветвей власти."""
        headers = ["Ветвь власти", "Функции", "Органы"]
        rows = [
            ["Законодательная", "Принятие законов", "Государственная Дума, Совет Федерации"],
            ["Исполнительная", "Исполнение законов", "Правительство, министерства"],
            ["Судебная", "Правосудие", "Верховный суд, Конституционный суд"],
        ]
        return self.generate_table(headers, rows, "Ветви власти в России")

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

    def generate_periodic_table_simple(self) -> bytes | None:
        """Генерирует упрощенную периодическую таблицу (первые 20 элементов)."""
        headers = ["№", "Элемент", "Символ", "Атомная масса", "Валентность"]
        rows = [
            ["1", "Водород", "H", "1", "I"],
            ["2", "Гелий", "He", "4", "0"],
            ["3", "Литий", "Li", "7", "I"],
            ["4", "Бериллий", "Be", "9", "II"],
            ["5", "Бор", "B", "11", "III"],
            ["6", "Углерод", "C", "12", "IV"],
            ["7", "Азот", "N", "14", "III, V"],
            ["8", "Кислород", "O", "16", "II"],
            ["9", "Фтор", "F", "19", "I"],
            ["10", "Неон", "Ne", "20", "0"],
            ["11", "Натрий", "Na", "23", "I"],
            ["12", "Магний", "Mg", "24", "II"],
            ["13", "Алюминий", "Al", "27", "III"],
            ["14", "Кремний", "Si", "28", "IV"],
            ["15", "Фосфор", "P", "31", "III, V"],
            ["16", "Сера", "S", "32", "II, IV, VI"],
            ["17", "Хлор", "Cl", "35.5", "I, III, V, VII"],
            ["18", "Аргон", "Ar", "40", "0"],
            ["19", "Калий", "K", "39", "I"],
            ["20", "Кальций", "Ca", "40", "II"],
        ]
        return self.generate_table(headers, rows, "Периодическая таблица (первые 20 элементов)")

    def generate_physics_motion_graph(self, motion_type: str = "uniform") -> bytes | None:
        """Генерирует график движения (путь или скорость от времени)."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            t = np.linspace(0, 10, 100)
            if motion_type == "uniform":
                # Равномерное движение: s = v*t
                v = 5  # скорость м/с
                s = v * t
                title = "График пути от времени (равномерное движение)"
                ylabel = "Путь s, м"
            elif motion_type == "accelerated":
                # Равноускоренное движение: v = v0 + a*t
                v0 = 2  # начальная скорость
                a = 1.5  # ускорение
                s = v0 * t + 0.5 * a * t**2
                title = "График пути от времени (равноускоренное движение)"
                ylabel = "Путь s, м"
            else:  # velocity
                # Скорость от времени
                v0 = 0
                a = 2
                v = v0 + a * t
                title = "График скорости от времени"
                ylabel = "Скорость v, м/с"

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(t, s if motion_type != "velocity" else v, "b-", linewidth=2)
            ax.set_xlabel("Время t, с", fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирован график движения: {motion_type}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика движения: {e}", exc_info=True)
            return None

    def generate_ohms_law_graph(self) -> bytes | None:
        """Генерирует график зависимости силы тока от напряжения (закон Ома)."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # current = U / R, где R = 10 Ом
            R = 10
            U = np.linspace(0, 50, 100)
            current = U / R

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(U, current, "r-", linewidth=2)
            ax.set_xlabel("Напряжение U, В", fontsize=12)
            ax.set_ylabel("Сила тока I, А", fontsize=12)
            ax.set_title(
                "График зависимости силы тока от напряжения (закон Ома)",
                fontsize=14,
                fontweight="bold",
            )
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирован график закона Ома")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика закона Ома: {e}", exc_info=True)
            return None

    # ========== РУССКИЙ ЯЗЫК: ДОПОЛНИТЕЛЬНЫЕ ТАБЛИЦЫ ==========

    def generate_russian_orthography_table(self) -> bytes | None:
        """Генерирует таблицу правил орфографии."""
        headers = ["Правило", "Пример", "Исключение"]
        rows = [
            ["ЖИ-ШИ пиши с И", "жить, шить", "нет"],
            ["ЧА-ЩА пиши с А", "чаща, чай", "нет"],
            ["ЧУ-ЩУ пиши с У", "чувство, щука", "нет"],
            ["Н/НН в причастиях", "сделанный (НН), крашеный (Н)", "деревянный, оловянный"],
            ["О/Ё после шипящих", "шёлк, чёрный (под ударением)", "шорох, шов"],
            ["И/Ы после Ц", "цирк, цыган", "цыплёнок, цыц"],
        ]
        return self.generate_table(headers, rows, "Правила орфографии")

    def generate_russian_punctuation_table(self) -> bytes | None:
        """Генерирует таблицу правил пунктуации."""
        headers = ["Правило", "Пример", "Знак"]
        rows = [
            ["Однородные члены", "Купил хлеб, молоко, сыр", "запятая"],
            ["Обращение", "Мама, помоги мне", "запятая"],
            ["Вводные слова", "Конечно, я помогу", "запятая"],
            ["Сложное предложение", "Я устал, но продолжал работать", "запятая"],
            ["Прямая речь", 'Он сказал: "Привет!"', "двоеточие, кавычки"],
            ["Причастный оборот", "Книга, лежащая на столе, интересная", "запятые"],
        ]
        return self.generate_table(headers, rows, "Правила пунктуации")

    def generate_russian_word_analysis_table(self) -> bytes | None:
        """Генерирует таблицу морфемного разбора."""
        headers = ["Слово", "Приставка", "Корень", "Суффикс", "Окончание", "Основа"]
        rows = [
            ["подводный", "под-", "вод", "-н-", "-ый", "подводн"],
            ["переписать", "пере-", "пис", "-а-", "-ть", "переписа"],
            ["учитель", "-", "уч", "-итель", "-", "учитель"],
            ["бежать", "-", "беж", "-а-", "-ть", "бежа"],
        ]
        return self.generate_table(headers, rows, "Морфемный разбор слов")

    def generate_russian_speech_styles_table(self) -> bytes | None:
        """Генерирует таблицу стилей речи."""
        headers = ["Стиль", "Сфера", "Признаки", "Пример"]
        rows = [
            ["Разговорный", "быт", "неофициальность, простота", "Привет! Как дела?"],
            ["Научный", "наука", "точность, термины", "Клетка - единица жизни"],
            ["Официально-деловой", "документы", "стандартность, точность", "Настоящим уведомляю"],
            ["Публицистический", "СМИ", "эмоциональность, призыв", "Важно помнить!"],
            [
                "Художественный",
                "литература",
                "образность, выразительность",
                "Белая береза под моим окном",
            ],
        ]
        return self.generate_table(headers, rows, "Стили речи")

    # ========== АЛГЕБРА: ДОПОЛНИТЕЛЬНЫЕ ТАБЛИЦЫ ==========

    def generate_powers_of_2_and_10_table(self) -> bytes | None:
        """Генерирует таблицу степеней чисел 2 и 10."""
        headers = ["Степень", "2ⁿ", "10ⁿ"]
        rows = []
        for n in range(0, 11):
            rows.append([str(n), str(2**n), str(10**n)])
        return self.generate_table(headers, rows, "Таблица степеней чисел 2 и 10")

    def generate_prime_numbers_table(self) -> bytes | None:
        """Генерирует таблицу простых чисел до 100."""
        primes = [
            2,
            3,
            5,
            7,
            11,
            13,
            17,
            19,
            23,
            29,
            31,
            37,
            41,
            43,
            47,
            53,
            59,
            61,
            67,
            71,
            73,
            79,
            83,
            89,
            97,
        ]
        headers = ["Простые числа до 100"]
        rows = [[str(p)] for p in primes]
        return self.generate_table(headers, rows, "Простые числа (решето Эратосфена)")

    def generate_abbreviated_multiplication_formulas_table(self) -> bytes | None:
        """Генерирует таблицу формул сокращенного умножения."""
        headers = ["Формула", "Раскрытие", "Пример"]
        rows = [
            ["(a+b)²", "a² + 2ab + b²", "(x+3)² = x² + 6x + 9"],
            ["(a-b)²", "a² - 2ab + b²", "(x-3)² = x² - 6x + 9"],
            ["(a+b)(a-b)", "a² - b²", "(x+3)(x-3) = x² - 9"],
            ["(a+b)³", "a³ + 3a²b + 3ab² + b³", "(x+2)³ = x³ + 6x² + 12x + 8"],
            ["(a-b)³", "a³ - 3a²b + 3ab² - b³", "(x-2)³ = x³ - 6x² + 12x - 8"],
            ["a³+b³", "(a+b)(a²-ab+b²)", "x³+8 = (x+2)(x²-2x+4)"],
            ["a³-b³", "(a-b)(a²+ab+b²)", "x³-8 = (x-2)(x²+2x+4)"],
        ]
        return self.generate_table(headers, rows, "Формулы сокращенного умножения")

    def generate_power_properties_table(self) -> bytes | None:
        """Генерирует таблицу свойств степеней."""
        headers = ["Свойство", "Формула", "Пример"]
        rows = [
            ["Умножение", "aⁿ · aᵐ = aⁿ⁺ᵐ", "2³ · 2² = 2⁵ = 32"],
            ["Деление", "aⁿ / aᵐ = aⁿ⁻ᵐ", "2⁵ / 2² = 2³ = 8"],
            ["Возведение в степень", "(aⁿ)ᵐ = aⁿᵐ", "(2³)² = 2⁶ = 64"],
            ["Степень произведения", "(ab)ⁿ = aⁿbⁿ", "(2·3)² = 2²·3² = 36"],
            ["Степень частного", "(a/b)ⁿ = aⁿ/bⁿ", "(6/2)² = 6²/2² = 9"],
            ["Отрицательная степень", "a⁻ⁿ = 1/aⁿ", "2⁻³ = 1/2³ = 1/8"],
            ["Нулевая степень", "a⁰ = 1", "5⁰ = 1"],
        ]
        return self.generate_table(headers, rows, "Свойства степеней")

    def generate_square_root_properties_table(self) -> bytes | None:
        """Генерирует таблицу свойств арифметического квадратного корня."""
        headers = ["Свойство", "Формула", "Пример"]
        rows = [
            ["Корень из произведения", "√(ab) = √a · √b", "√(4·9) = √4 · √9 = 6"],
            ["Корень из частного", "√(a/b) = √a / √b", "√(16/4) = √16 / √4 = 2"],
            ["Корень из степени", "√(aⁿ) = aⁿ/²", "√(x⁴) = x²"],
            ["Возведение в квадрат", "(√a)² = a", "(√9)² = 9"],
            ["Корень из квадрата", "√(a²) = |a|", "√((-3)²) = 3"],
        ]
        return self.generate_table(headers, rows, "Свойства арифметического квадратного корня")

    def generate_standard_form_table(self) -> bytes | None:
        """Генерирует таблицу стандартного вида числа."""
        headers = ["Число", "Стандартный вид", "Порядок"]
        rows = [
            ["3000000", "3·10⁶", "6"],
            ["0.00005", "5·10⁻⁵", "-5"],
            ["450000", "4.5·10⁵", "5"],
            ["0.000123", "1.23·10⁻⁴", "-4"],
        ]
        return self.generate_table(headers, rows, "Стандартный вид числа")

    # ========== ГЕОМЕТРИЯ: ТАБЛИЦЫ ==========

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

    # ========== ФИЗИКА: ДОПОЛНИТЕЛЬНЫЕ ТАБЛИЦЫ И ГРАФИКИ ==========

    def generate_physics_densities_table(self) -> bytes | None:
        """Генерирует таблицу плотностей веществ."""
        headers = ["Вещество", "Плотность, кг/м³", "Состояние"]
        rows = [
            ["Вода", "1000", "жидкость"],
            ["Лед", "900", "твердое"],
            ["Железо", "7800", "твердое"],
            ["Алюминий", "2700", "твердое"],
            ["Воздух", "1.29", "газ"],
            ["Ртуть", "13600", "жидкость"],
            ["Золото", "19300", "твердое"],
        ]
        return self.generate_table(headers, rows, "Плотности веществ")

    def generate_physics_heat_capacity_table(self) -> bytes | None:
        """Генерирует таблицу удельных теплоемкостей."""
        headers = ["Вещество", "Удельная теплоемкость, Дж/(кг·°C)"]
        rows = [
            ["Вода", "4200"],
            ["Лед", "2100"],
            ["Железо", "460"],
            ["Алюминий", "920"],
            ["Медь", "400"],
            ["Свинец", "130"],
        ]
        return self.generate_table(headers, rows, "Удельные теплоемкости веществ")

    def generate_physics_resistivity_table(self) -> bytes | None:
        """Генерирует таблицу удельных сопротивлений."""
        headers = ["Материал", "Удельное сопротивление, Ом·м"]
        rows = [
            ["Серебро", "1.6·10⁻⁸"],
            ["Медь", "1.7·10⁻⁸"],
            ["Алюминий", "2.8·10⁻⁸"],
            ["Железо", "9.8·10⁻⁸"],
            ["Никелин", "4.2·10⁻⁷"],
            ["Резина", "10¹³-10¹⁶"],
        ]
        return self.generate_table(headers, rows, "Удельные сопротивления проводников")

    def generate_hookes_law_graph(self) -> bytes | None:
        """Генерирует график зависимости силы упругости от удлинения (закон Гука)."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # F = kx, где k = 100 Н/м
            k = 100
            x = np.linspace(0, 0.1, 100)  # удлинение в метрах
            F = k * x

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(x * 100, F, "b-", linewidth=2)  # x в см для удобства
            ax.set_xlabel("Удлинение x, см", fontsize=12)
            ax.set_ylabel("Сила упругости F, Н", fontsize=12)
            ax.set_title(
                "График зависимости силы упругости от удлинения (закон Гука)",
                fontsize=14,
                fontweight="bold",
            )
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирован график закона Гука")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика закона Гука: {e}", exc_info=True)
            return None

    def generate_temperature_graph(self) -> bytes | None:
        """Генерирует график зависимости температуры от времени при нагревании и охлаждении."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # Нагревание: T = T₀ + at
            t = np.linspace(0, 10, 100)
            T_heating = 20 + 5 * t  # начальная 20°C, нагрев 5°C/мин

            # Охлаждение: T = T₀ - at
            T_cooling = 70 - 3 * t  # начальная 70°C, охлаждение 3°C/мин

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

            # График нагревания
            ax1.plot(t, T_heating, "r-", linewidth=2)
            ax1.set_xlabel("Время t, мин", fontsize=12)
            ax1.set_ylabel("Температура T, °C", fontsize=12)
            ax1.set_title("Нагревание", fontsize=14, fontweight="bold")
            ax1.grid(True, alpha=0.3)

            # График охлаждения
            ax2.plot(t, T_cooling, "b-", linewidth=2)
            ax2.set_xlabel("Время t, мин", fontsize=12)
            ax2.set_ylabel("Температура T, °C", fontsize=12)
            ax2.set_title("Охлаждение", fontsize=14, fontweight="bold")
            ax2.grid(True, alpha=0.3)

            plt.suptitle(
                "Графики зависимости температуры от времени", fontsize=16, fontweight="bold"
            )
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирован график зависимости температуры от времени")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика температуры: {e}", exc_info=True)
            return None

    def generate_melting_graph(self) -> bytes | None:
        """Генерирует график плавления и кристаллизации."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # Плавление: температура постоянна при плавлении
            t1 = np.linspace(0, 2, 50)
            T1 = 20 + 10 * t1  # нагрев до температуры плавления
            t2 = np.linspace(2, 4, 50)
            T2 = np.full(50, 40)  # плавление при постоянной температуре
            t3 = np.linspace(4, 6, 50)
            T3 = 40 + 5 * (t3 - 4)  # нагрев после плавления

            t = np.concatenate([t1, t2, t3])
            T = np.concatenate([T1, T2, T3])

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(t, T, "b-", linewidth=2)
            ax.axhline(y=40, color="r", linestyle="--", alpha=0.5, label="Температура плавления")
            ax.set_xlabel("Время t, мин", fontsize=12)
            ax.set_ylabel("Температура T, °C", fontsize=12)
            ax.set_title("График плавления и кристаллизации", fontsize=14, fontweight="bold")
            ax.grid(True, alpha=0.3)
            ax.legend()
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирован график плавления и кристаллизации")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика плавления: {e}", exc_info=True)
            return None

    def generate_isoprocess_graphs(self) -> bytes | None:
        """Генерирует графики изопроцессов в газах."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # Изотерма: PV = const, P = const/V
            V = np.linspace(0.1, 2, 100)
            P_isotherm = 10 / V  # PV = 1

            # Изобара: V/T = const, V = const*T
            T = np.linspace(200, 400, 100)
            V_isobar = 0.01 * T  # V/T = 0.01

            # Изохора: P/T = const, P = const*T
            P_isochor = 0.05 * T  # P/T = 0.05

            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))

            # Изотерма
            ax1.plot(V, P_isotherm, "r-", linewidth=2)
            ax1.set_xlabel("Объем V, м³", fontsize=10)
            ax1.set_ylabel("Давление P, Па", fontsize=10)
            ax1.set_title("Изотерма (T=const)", fontsize=12, fontweight="bold")
            ax1.grid(True, alpha=0.3)

            # Изобара
            ax2.plot(T, V_isobar, "b-", linewidth=2)
            ax2.set_xlabel("Температура T, К", fontsize=10)
            ax2.set_ylabel("Объем V, м³", fontsize=10)
            ax2.set_title("Изобара (P=const)", fontsize=12, fontweight="bold")
            ax2.grid(True, alpha=0.3)

            # Изохора
            ax3.plot(T, P_isochor, "g-", linewidth=2)
            ax3.set_xlabel("Температура T, К", fontsize=10)
            ax3.set_ylabel("Давление P, Па", fontsize=10)
            ax3.set_title("Изохора (V=const)", fontsize=12, fontweight="bold")
            ax3.grid(True, alpha=0.3)

            plt.suptitle("Графики изопроцессов в газах", fontsize=14, fontweight="bold")
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерированы графики изопроцессов")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графиков изопроцессов: {e}", exc_info=True)
            return None

    def generate_ac_current_graph(self) -> bytes | None:
        """Генерирует график зависимости силы тока от времени в цепи переменного тока."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # current = I₀ sin(ωt), где I₀ = 5 А, ω = 2π/T, T = 0.02 с (50 Гц)
            t = np.linspace(0, 0.1, 1000)
            I0 = 5
            f = 50  # частота 50 Гц
            omega = 2 * np.pi * f
            current = I0 * np.sin(omega * t)

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(t * 1000, current, "b-", linewidth=2)  # время в мс
            ax.set_xlabel("Время t, мс", fontsize=12)
            ax.set_ylabel("Сила тока I, А", fontsize=12)
            ax.set_title("График переменного тока (синусоида)", fontsize=14, fontweight="bold")
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color="k", linestyle="-", linewidth=0.5)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info("✅ Сгенерирован график переменного тока")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика переменного тока: {e}", exc_info=True)
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

        # Алгебра: дополнительные таблицы
        # Степени 2 и 10 - проверяем разные варианты (приоритет - проверяем первыми)
        if "степен" in text_lower and (
            "2" in text_lower or "10" in text_lower or "двойк" in text_lower or "два" in text_lower
        ):
            image = self.generate_powers_of_2_and_10_table()
            if image:
                logger.info("📊 Детектирована таблица степеней чисел 2 и 10")
                return image

        # Простые числа - более гибкий паттерн (приоритет - проверяем первыми)
        if "прост" in text_lower and "числ" in text_lower:
            image = self.generate_prime_numbers_table()
            if image:
                logger.info("📊 Детектирована таблица простых чисел")
                return image
        if "решето" in text_lower or "эратосфен" in text_lower:
            image = self.generate_prime_numbers_table()
            if image:
                logger.info("📊 Детектирована таблица простых чисел")
                return image

        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:формул[ы]?\s+сокращенн|сокращенн[ое]?\s+умножен)",
            text_lower,
        ):
            image = self.generate_abbreviated_multiplication_formulas_table()
            if image:
                logger.info("📊 Детектирована таблица формул сокращенного умножения")
                return image

        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:свойств[а]?\s+степен)", text_lower):
            image = self.generate_power_properties_table()
            if image:
                logger.info("📊 Детектирована таблица свойств степеней")
                return image

        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:свойств[а]?\s+корн|квадратн[ый]?\s+корен)", text_lower
        ):
            image = self.generate_square_root_properties_table()
            if image:
                logger.info("📊 Детектирована таблица свойств квадратного корня")
                return image

        # Стандартный вид числа - более гибкий паттерн
        if "стандартн" in text_lower and "вид" in text_lower:
            image = self.generate_standard_form_table()
            if image:
                logger.info("📊 Детектирована таблица стандартного вида числа")
                return image

        # Сначала проверяем таблицу квадратов и кубов (до таблицы умножения, чтобы не перехватывать)
        if ("квадрат" in text_lower and "куб" in text_lower) and "умнож" not in text_lower:
            image = self.generate_squares_and_cubes_table()
            if image:
                logger.info("📊 Детектирована таблица квадратов и кубов")
                return image

        # Проверяем полную таблицу умножения (без указания числа)
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

        # Паттерны для таблицы растворимости
        solubility_patterns = [
            r"табл[иы]ц[аеы]?\s+растворимост",
            r"растворимост[ьи]?\s+веществ",
            r"табл[иы]ц[аеы]?\s+раствор",
        ]

        for pattern in solubility_patterns:
            if re.search(pattern, text_lower):
                image = self.generate_chemistry_solubility_table()
                if image:
                    logger.info("📊 Детектирована таблица растворимости")
                    return image

        # Паттерны для таблицы валентности
        valence_patterns = [
            r"табл[иы]ц[аеы]?\s+валентност",
            r"валентност[ьи]?\s+элемент",
            r"табл[иы]ц[аеы]?\s+валент",
            r"покажи\s+табл[иы]ц[аеы]?\s+валентност",
            r"покажи\s+валентност",
            r"валентност[ьи]?",
        ]

        for pattern in valence_patterns:
            if re.search(pattern, text_lower):
                image = self.generate_chemistry_valence_table()
                if image:
                    logger.info("📊 Детектирована таблица валентности")
                    return image

        # Паттерны для таблицы физических констант
        constants_patterns = [
            r"табл[иы]ц[аеы]?\s+(?:физическ|констант)",
            r"физическ[ие]?\s+констант[ы]?",
            r"табл[иы]ц[аеы]?\s+констант",
        ]

        for pattern in constants_patterns:
            if re.search(pattern, text_lower):
                image = self.generate_physics_constants_table()
                if image:
                    logger.info("📊 Детектирована таблица физических констант")
                    return image

        # Паттерны для таблицы времен английского
        english_tenses_patterns = [
            r"табл[иы]ц[аеы]?\s+времен",
            r"времен[а]?\s+(?:английск|англ)",
            r"табл[иы]ц[аеы]?\s+(?:английск|англ)\s+времен",
        ]

        for pattern in english_tenses_patterns:
            if re.search(pattern, text_lower):
                image = self.generate_english_tenses_table()
                if image:
                    logger.info("📊 Детектирована таблица времен английского")
                    return image

        # Паттерны для таблицы неправильных глаголов
        if "неправильн" in text_lower and "глагол" in text_lower:
            image = self.generate_english_irregular_verbs_table()
            if image:
                logger.info("📊 Детектирована таблица неправильных глаголов")
                return image

        # Математика 1-4 классы: таблицы сложения, вычитания, деления
        if re.search(r"табл[иы]ц[аеы]?\s+сложени[яе]", text_lower):
            image = self.generate_addition_table()
            if image:
                logger.info("📊 Детектирована таблица сложения")
                return image

        if re.search(r"табл[иы]ц[аеы]?\s+вычитани[яе]", text_lower):
            image = self.generate_subtraction_table()
            if image:
                logger.info("📊 Детектирована таблица вычитания")
                return image

        if re.search(r"табл[иы]ц[аеы]?\s+делени[яе]", text_lower):
            image = self.generate_division_table()
            if image:
                logger.info("📊 Детектирована таблица деления")
                return image

        # Единицы измерения
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?единиц[ы]?\s+измерени[яе]", text_lower):
            image = self.generate_units_table()
            if image:
                logger.info("📊 Детектирована таблица единиц измерения")
                return image

        # Русский язык: алфавит, падежи, спряжение
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:букв|алфавит|звук)", text_lower):
            image = self.generate_russian_alphabet_table()
            if image:
                logger.info("📊 Детектирована таблица букв и звуков")
                return image

        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:падеж|склонени)", text_lower):
            image = self.generate_russian_cases_table()
            if image:
                logger.info("📊 Детектирована таблица падежей")
                return image

        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:спряжени[яе]|глагол)", text_lower):
            image = self.generate_russian_verb_conjugation_table()
            if image:
                logger.info("📊 Детектирована таблица спряжения глаголов")
                return image

        # Русский язык: дополнительные таблицы
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:орфограф|правописан)", text_lower):
            image = self.generate_russian_orthography_table()
            if image:
                logger.info("📊 Детектирована таблица орфографии")
                return image

        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:пунктуац|знак[и]?\s+препинан)", text_lower):
            image = self.generate_russian_punctuation_table()
            if image:
                logger.info("📊 Детектирована таблица пунктуации")
                return image

        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:морфемн|разбор\s+слов)", text_lower):
            image = self.generate_russian_word_analysis_table()
            if image:
                logger.info("📊 Детектирована таблица морфемного разбора")
                return image

        # Стили речи - более гибкий паттерн
        if "стил" in text_lower and "реч" in text_lower:
            image = self.generate_russian_speech_styles_table()
            if image:
                logger.info("📊 Детектирована таблица стилей речи")
                return image

        # Окружающий мир: времена года, природные зоны
        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:времен[а]?\s+год|месяц|дн[ия]?\s+недел)", text_lower
        ):
            image = self.generate_seasons_months_table()
            if image:
                logger.info("📊 Детектирована таблица времен года")
                return image

        # Окружающий мир: природные зоны (проверяем ДО других зон)
        if re.search(r"природн[ые]?\s+зон", text_lower):
            image = self.generate_natural_zones_table()
            if image:
                logger.info("📊 Детектирована таблица природных зон")
                return image

        # География: часовые пояса (проверяем ДО других зон)
        if re.search(r"часов[ые]?\s+пояс", text_lower):
            image = self.generate_time_zones_table()
            if image:
                logger.info("📊 Детектирована таблица часовых поясов")
                return image

        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:крупнейш|страны?\s+мир)", text_lower):
            image = self.generate_countries_table()
            if image:
                logger.info("📊 Детектирована таблица стран")
                return image

        # История: хронология
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:хронологи|истори[яи]?\s+росси)", text_lower):
            image = self.generate_history_timeline_table()
            if image:
                logger.info("📊 Детектирована хронологическая таблица")
                return image

        # Обществознание: ветви власти
        if re.search(r"ветв[и]?\s+власт", text_lower):
            image = self.generate_government_branches_table()
            if image:
                logger.info("📊 Детектирована таблица ветвей власти")
                return image

        # Информатика: системы счисления
        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:систем[ы]?\s+счислени|двоичн|восьмеричн)", text_lower
        ):
            image = self.generate_number_systems_table()
            if image:
                logger.info("📊 Детектирована таблица систем счисления")
                return image

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
                image = self.generate_periodic_table_simple()
                if image:
                    logger.info("📊 Детектирована периодическая таблица Менделеева")
                    return image

        # Физика: графики движения и закон Ома
        if re.search(r"график\s+(?:пути|путь)\s+от\s+времен", text_lower):
            if re.search(r"равноускоренн", text_lower):
                image = self.generate_physics_motion_graph("accelerated")
            else:
                image = self.generate_physics_motion_graph("uniform")
            if image:
                logger.info("📈 Детектирован график пути от времени")
                return image

        if re.search(r"график\s+скорост[и]?\s+от\s+времен", text_lower):
            image = self.generate_physics_motion_graph("velocity")
            if image:
                logger.info("📈 Детектирован график скорости от времени")
                return image

        if re.search(
            r"(?:график\s+)?(?:закон\s+ома|сила\s+тока\s+от\s+напряжени|ом[а]?)", text_lower
        ):
            image = self.generate_ohms_law_graph()
            if image:
                logger.info("📈 Детектирован график закона Ома")
                return image

        # Физика: дополнительные графики
        if re.search(
            r"(?:график\s+)?(?:закон\s+гука|сил[аы]?\s+упругост[и]?\s+от\s+удлинени|гука)",
            text_lower,
        ):
            image = self.generate_hookes_law_graph()
            if image:
                logger.info("📈 Детектирован график закона Гука")
                return image

        if re.search(
            r"(?:график\s+)?(?:температур[аы]?\s+от\s+времен|нагревани[яе]|охлаждени[яе])",
            text_lower,
        ):
            image = self.generate_temperature_graph()
            if image:
                logger.info("📈 Детектирован график зависимости температуры от времени")
                return image

        if re.search(r"(?:график\s+)?(?:плавлени[яе]|кристаллизац)", text_lower):
            image = self.generate_melting_graph()
            if image:
                logger.info("📈 Детектирован график плавления и кристаллизации")
                return image

        if re.search(r"(?:график\s+)?(?:изопроцесс|изотерм|изобар|изохор)", text_lower):
            image = self.generate_isoprocess_graphs()
            if image:
                logger.info("📈 Детектированы графики изопроцессов")
                return image

        # Переменный ток - более гибкий паттерн
        if "переменн" in text_lower and "ток" in text_lower:
            image = self.generate_ac_current_graph()
            if image:
                logger.info("📈 Детектирован график переменного тока")
                return image
        if "синусоид" in text_lower and "ток" in text_lower:
            image = self.generate_ac_current_graph()
            if image:
                logger.info("📈 Детектирован график переменного тока")
                return image

        # Физика: дополнительные таблицы
        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:плотност[и]?\s+веществ|плотност[и]?)", text_lower):
            image = self.generate_physics_densities_table()
            if image:
                logger.info("📊 Детектирована таблица плотностей")
                return image

        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:удельн[ая]?\s+теплоемкост|теплоемкост)", text_lower
        ):
            image = self.generate_physics_heat_capacity_table()
            if image:
                logger.info("📊 Детектирована таблица удельных теплоемкостей")
                return image

        # Удельные сопротивления - более гибкий паттерн
        if "удельн" in text_lower and "сопротивлени" in text_lower:
            image = self.generate_physics_resistivity_table()
            if image:
                logger.info("📊 Детектирована таблица удельных сопротивлений")
                return image
        if "сопротивлени" in text_lower and "проводник" in text_lower:
            image = self.generate_physics_resistivity_table()
            if image:
                logger.info("📊 Детектирована таблица удельных сопротивлений")
                return image

        # Геометрия: таблицы
        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:формул[ы]?\s+площад[ей]|площад[и]?\s+фигур)", text_lower
        ):
            image = self.generate_geometry_area_formulas_table()
            if image:
                logger.info("📊 Детектирована таблица формул площадей")
                return image

        if re.search(
            r"(?:табл[иы]ц[аеы]?\s+)?(?:формул[ы]?\s+объем[ов]|объем[ы]?\s+тел)", text_lower
        ):
            image = self.generate_geometry_volume_formulas_table()
            if image:
                logger.info("📊 Детектирована таблица формул объемов")
                return image

        # Классификация треугольников - более гибкий паттерн
        if (
            "классификац" in text_lower or "виды" in text_lower or "типы" in text_lower
        ) and "треугольник" in text_lower:
            image = self.generate_triangle_classification_table()
            if image:
                logger.info("📊 Детектирована таблица классификации треугольников")
                return image

        # Классификация четырехугольников - более гибкий паттерн
        if (
            "классификац" in text_lower or "виды" in text_lower or "типы" in text_lower
        ) and "четырехугольник" in text_lower:
            image = self.generate_quadrilateral_classification_table()
            if image:
                logger.info("📊 Детектирована таблица классификации четырехугольников")
                return image

        if re.search(r"(?:табл[иы]ц[аеы]?\s+)?(?:тригонометр|sin\s+cos\s+tan)", text_lower):
            image = self.generate_trigonometry_table()
            if image:
                logger.info("📊 Детектирована таблица тригонометрических функций")
                return image

        # Проверяем квадратный корень ДО всех других графиков
        if ("корен" in text_lower or "корня" in text_lower) and (
            "квадратн" in text_lower or "sqrt" in text_lower
        ):
            image = self.generate_function_graph("sqrt(x)", title="График функции: y = √x")
            if image:
                logger.info("📈 Детектирован график квадратного корня")
                return image

        # Паттерны для графиков функций
        graph_patterns = [
            r"график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"нарисуй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"построй\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"покажи\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"изобрази\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"создай\s+график\s+(?:функции\s+)?(?:y\s*=\s*)?([^,\n\.]+)",
            r"(?:синусоид|sin|косинус|cos|тангенс|tan|экспонент|exp|логарифм|log|парабол|линейн|квадратичн|корен)",
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
            elif re.search(r"(?:тангенс|tan|тангенсоид)", text_lower):
                image = self.generate_function_graph(
                    "tan(x)", x_range=(-np.pi, np.pi), title="График функции: y = tan(x)"
                )
                if image:
                    logger.info("📈 Детектирован график тангенса")
                return image

            # Обратная пропорциональность y = k/x
            elif re.search(r"обратн|гипербол|k\s*/\s*x|1\s*/\s*x", text_lower):
                # Для гиперболы используем диапазон с исключением нуля
                # Фильтрация NaN/Inf в generate_function_graph обработает деление на ноль
                image = self.generate_function_graph(
                    "1/x", x_range=(-5, 5), title="График функции: y = 1/x (гипербола)"
                )
                if image:
                    logger.info("📈 Детектирован график обратной пропорциональности")
                    return image

            # Кубическая функция y = x³
            elif re.search(r"кубическ|x\^3|x\*\*3|x³", text_lower):
                image = self.generate_function_graph("x**3", title="График функции: y = x³")
                if image:
                    logger.info("📈 Детектирован график кубической функции")
                    return image

            # Функция модуля y = |x|
            elif re.search(r"модул|абсолютн|abs\(x\)|\|x\|", text_lower):
                image = self.generate_function_graph("abs(x)", title="График функции: y = |x|")
                if image:
                    logger.info("📈 Детектирован график модуля")
                    return image

            # Квадратичные функции (проверяем ПОСЛЕ квадратного корня)
            elif re.search(r"парабол|квадратичн|x\^2|x\*\*2|x²", text_lower):
                # Убеждаемся, что это не квадратный корень
                if "корен" not in text_lower:
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
                    expression = (
                        expression.replace("^", "**").replace("²", "**2").replace("³", "**3")
                    )
                    # Заменяем русские названия функций на английские
                    expression = re.sub(r"логарифм|log", "ln", expression, flags=re.IGNORECASE)
                    expression = re.sub(r"синус|sin", "sin", expression, flags=re.IGNORECASE)
                    expression = re.sub(r"косинус|cos", "cos", expression, flags=re.IGNORECASE)
                    expression = re.sub(r"тангенс|tan", "tan", expression, flags=re.IGNORECASE)
                    expression = re.sub(r"экспонент|exp", "exp", expression, flags=re.IGNORECASE)

                    # Безопасная проверка выражения (расширенная)
                    # Разрешаем: x, числа, операторы, функции, скобки, точки
                    safe_pattern = r"^[x\s+\-*/()\.\d\sln\slog\slog10\slog2\ssin\scos\stan\sexp\ssqrt\sabs\s]+$"
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
