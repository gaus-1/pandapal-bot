"""Модуль визуализации для физики."""

import io

import numpy as np
from loguru import logger

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from bot.services.visualization.base import BaseVisualizationService


class PhysicsVisualization(BaseVisualizationService):
    """Визуализация для физики: константы, графики движения, законы, таблицы."""

    def generate_physics_constants_table(self) -> bytes | None:
        """Генерирует таблицу физических констант."""
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

    def generate_physics_motion_graph(self, motion_type: str = "uniform") -> bytes | None:
        """Генерирует график движения (путь или скорость от времени)."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            t = np.linspace(0, 10, 100)
            if motion_type == "uniform":
                v = 5
                s = v * t
                title = "График пути от времени (равномерное движение)"
                ylabel = "Путь s, м"
            elif motion_type == "accelerated":
                v0 = 2
                a = 1.5
                s = v0 * t + 0.5 * a * t**2
                title = "График пути от времени (равноускоренное движение)"
                ylabel = "Путь s, м"
            else:  # velocity
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

    def generate_melting_graph(self, substance: str = "лед") -> bytes | None:
        """
        Генерирует график плавления/нагревания вещества.

        Показывает три фазы: нагревание твердого тела, плавление (горизонтальный участок),
        нагревание жидкости.
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            # Данные для разных веществ
            substances_data = {
                "лед": {"t_melt": 0, "name": "льда", "t_start": -20, "t_end": 40},
                "вода": {"t_melt": 0, "name": "воды (из льда)", "t_start": -20, "t_end": 40},
                "свинец": {"t_melt": 327, "name": "свинца", "t_start": 200, "t_end": 450},
                "олово": {"t_melt": 232, "name": "олова", "t_start": 100, "t_end": 350},
                "алюминий": {"t_melt": 660, "name": "алюминия", "t_start": 500, "t_end": 800},
            }

            # Нормализуем вещество
            substance_lower = substance.lower().strip()
            data = substances_data.get(substance_lower, substances_data["лед"])

            t_melt = data["t_melt"]
            t_start = data["t_start"]
            t_end = data["t_end"]

            # Фаза 1: нагревание твердого тела
            time1 = np.linspace(0, 3, 30)
            temp1 = np.linspace(t_start, t_melt, 30)

            # Фаза 2: плавление (температура постоянна)
            time2 = np.linspace(3, 6, 30)
            temp2 = np.full(30, t_melt)

            # Фаза 3: нагревание жидкости
            time3 = np.linspace(6, 10, 40)
            temp3 = np.linspace(t_melt, t_end, 40)

            # Объединяем данные
            time = np.concatenate([time1, time2, time3])
            temp = np.concatenate([temp1, temp2, temp3])

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(time, temp, "b-", linewidth=2.5)

            # Подписи фаз
            ax.annotate(
                "Нагрев\nтвердого тела",
                xy=(1.5, (t_start + t_melt) / 2),
                fontsize=10,
                ha="center",
            )
            ax.annotate("Плавление", xy=(4.5, t_melt + 5), fontsize=10, ha="center")
            ax.annotate("Нагрев\nжидкости", xy=(8, (t_melt + t_end) / 2), fontsize=10, ha="center")

            # Горизонтальная пунктирная линия на уровне плавления
            ax.axhline(
                y=t_melt, color="r", linestyle="--", alpha=0.5, label=f"t плавления = {t_melt}°C"
            )

            ax.set_xlabel("Время, мин", fontsize=12)
            ax.set_ylabel("Температура, °C", fontsize=12)
            ax.set_title(
                f"График нагревания и плавления {data['name']}", fontsize=14, fontweight="bold"
            )
            ax.grid(True, alpha=0.3)
            ax.legend(loc="lower right")
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирован график плавления: {substance}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика плавления: {e}", exc_info=True)
            return None

    def generate_heating_cooling_graph(self, process: str = "heating") -> bytes | None:
        """
        Генерирует график нагревания или охлаждения воды.

        Args:
            process: "heating" - нагревание, "cooling" - охлаждение
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            time = np.linspace(0, 10, 100)

            if process == "cooling":
                # Экспоненциальное охлаждение (закон Ньютона)
                temp = 20 + 80 * np.exp(-0.3 * time)
                title = "График охлаждения воды"
                color = "b"
            else:
                # Линейное нагревание до кипения
                temp = np.minimum(20 + 8 * time, 100)
                title = "График нагревания воды"
                color = "r"

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(time, temp, f"{color}-", linewidth=2)

            if process == "heating":
                ax.axhline(
                    y=100, color="gray", linestyle="--", alpha=0.5, label="t кипения = 100°C"
                )
            else:
                ax.axhline(
                    y=20, color="gray", linestyle="--", alpha=0.5, label="t окружающей среды = 20°C"
                )

            ax.set_xlabel("Время, мин", fontsize=12)
            ax.set_ylabel("Температура, °C", fontsize=12)
            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.grid(True, alpha=0.3)
            ax.legend()
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирован график {process}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации графика нагревания/охлаждения: {e}", exc_info=True)
            return None
