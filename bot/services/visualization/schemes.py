"""
Модуль генерации специализированных схем (SOLID: SRP).

Содержит методы генерации схем для различных предметов:
- Астрономия: Солнечная система
- Биология: тело человека, клетка, ДНК, круговорот воды
- Физика: электрические цепи
- Информатика: блок-схемы алгоритмов
- Обществознание: структура государства
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
    logger.warning("⚠️ matplotlib недоступен - схемы отключены")


class BaseSchemeMixin:
    """Mixin класс для генерации специализированных схем.

    Содержит методы генерации схем для различных школьных предметов.
    Используется через множественное наследование с BaseVisualizationService.
    """

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
