"""Модуль визуализации для истории."""

import io

from loguru import logger

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Polygon, Rectangle

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from bot.services.visualization.base import BaseVisualizationService


class HistoryVisualization(BaseVisualizationService):
    """Визуализация для истории: хронология, события, карты войн, схемы битв."""

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

    def generate_battle_scheme(self, battle: str = "бородино") -> bytes | None:
        """
        Генерирует схему исторической битвы.

        Args:
            battle: Название битвы (бородино, куликово, полтава, сталинград, ледовое)
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            battle_lower = battle.lower().strip()

            # Данные битв
            battles_data = {
                "бородино": {
                    "title": "Бородинское сражение (1812)",
                    "method": self._draw_borodino_battle,
                },
                "куликово": {
                    "title": "Куликовская битва (1380)",
                    "method": self._draw_kulikovo_battle,
                },
                "полтава": {
                    "title": "Полтавская битва (1709)",
                    "method": self._draw_poltava_battle,
                },
                "сталинград": {
                    "title": "Сталинградская битва (1942-1943)",
                    "method": self._draw_stalingrad_battle,
                },
                "ледовое": {
                    "title": "Ледовое побоище (1242)",
                    "method": self._draw_ledovoe_battle,
                },
            }

            # Находим битву
            data = None
            for key, value in battles_data.items():
                if key in battle_lower:
                    data = value
                    break

            if not data:
                data = battles_data["бородино"]

            fig, ax = plt.subplots(figsize=(12, 9))
            ax.set_xlim(0, 12)
            ax.set_ylim(0, 9)
            ax.axis("off")

            # Рисуем схему битвы
            data["method"](ax)

            ax.set_title(data["title"], fontsize=16, fontweight="bold", y=1.02)

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            buf.seek(0)
            image_bytes = buf.read()
            buf.close()
            plt.close(fig)

            logger.info(f"✅ Сгенерирована схема битвы: {battle}")
            return image_bytes

        except Exception as e:
            logger.error(f"❌ Ошибка генерации схемы битвы: {e}", exc_info=True)
            return None

    def _draw_borodino_battle(self, ax):
        """Схема Бородинского сражения."""
        # Фон - местность
        ax.add_patch(Rectangle((0, 0), 12, 9, facecolor="#e8f5e9", edgecolor="none"))

        # Река Колоча
        river_x = [0, 2, 4, 6, 8, 10, 12]
        river_y = [5.5, 5.8, 5.5, 5.2, 5.5, 5.8, 5.5]
        ax.fill_between(
            river_x,
            [y - 0.3 for y in river_y],
            [y + 0.3 for y in river_y],
            color="#64b5f6",
            alpha=0.7,
        )
        ax.text(1, 5.5, "р. Колоча", fontsize=9, color="blue", style="italic")

        # Русские позиции (красные)
        ax.add_patch(
            Rectangle((1, 2), 3, 1.5, facecolor="#ef5350", edgecolor="darkred", linewidth=2)
        )
        ax.text(
            2.5,
            2.75,
            "Русская армия\n(Кутузов)",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

        # Флеши Багратиона
        for _i, x in enumerate([2, 3, 4]):
            ax.add_patch(
                Polygon(
                    [[x, 1.5], [x + 0.3, 1.8], [x + 0.6, 1.5]],
                    facecolor="#c62828",
                    edgecolor="black",
                )
            )
        ax.text(3.3, 1.2, "Флеши Багратиона", fontsize=8, ha="center")

        # Батарея Раевского
        ax.add_patch(
            Rectangle((5.5, 2.5), 1.5, 0.8, facecolor="#c62828", edgecolor="black", linewidth=2)
        )
        ax.text(6.25, 2.9, "Батарея\nРаевского", ha="center", va="center", fontsize=8)

        # Французские позиции (синие)
        ax.add_patch(
            Rectangle((1, 6.5), 4, 1.5, facecolor="#42a5f5", edgecolor="darkblue", linewidth=2)
        )
        ax.text(
            3,
            7.25,
            "Французская армия\n(Наполеон)",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

        # Стрелки атак
        ax.annotate(
            "",
            xy=(2.5, 4),
            xytext=(2.5, 6.5),
            arrowprops={"arrowstyle": "->", "color": "blue", "lw": 2},
        )
        ax.annotate(
            "",
            xy=(6, 4),
            xytext=(5, 6.5),
            arrowprops={"arrowstyle": "->", "color": "blue", "lw": 2},
        )

        # Легенда
        ax.add_patch(Rectangle((9, 7), 0.5, 0.3, facecolor="#ef5350", edgecolor="black"))
        ax.text(9.7, 7.15, "Русские войска", fontsize=8, va="center")
        ax.add_patch(Rectangle((9, 6.5), 0.5, 0.3, facecolor="#42a5f5", edgecolor="black"))
        ax.text(9.7, 6.65, "Французские войска", fontsize=8, va="center")
        ax.annotate(
            "",
            xy=(9.5, 6.1),
            xytext=(9, 6.1),
            arrowprops={"arrowstyle": "->", "color": "blue", "lw": 2},
        )
        ax.text(9.7, 6.1, "Направление атак", fontsize=8, va="center")

    def _draw_kulikovo_battle(self, ax):
        """Схема Куликовской битвы."""
        ax.add_patch(Rectangle((0, 0), 12, 9, facecolor="#e8f5e9", edgecolor="none"))

        # Реки
        ax.fill_between([0, 3], [4, 4.5], [4.5, 5], color="#64b5f6", alpha=0.7)
        ax.text(1.5, 4.25, "р. Дон", fontsize=9, color="blue", style="italic")
        ax.fill_between([9, 12], [4, 4.5], [4.5, 5], color="#64b5f6", alpha=0.7)
        ax.text(10.5, 4.25, "р. Непрядва", fontsize=9, color="blue", style="italic")

        # Русские войска
        ax.add_patch(Rectangle((4, 1), 4, 1, facecolor="#ef5350", edgecolor="darkred", linewidth=2))
        ax.text(6, 1.5, "Большой полк\n(Дмитрий Донской)", ha="center", va="center", fontsize=9)

        ax.add_patch(Rectangle((2, 2.5), 2, 0.8, facecolor="#ef5350", edgecolor="darkred"))
        ax.text(3, 2.9, "Полк левой руки", ha="center", va="center", fontsize=8)

        ax.add_patch(Rectangle((8, 2.5), 2, 0.8, facecolor="#ef5350", edgecolor="darkred"))
        ax.text(9, 2.9, "Полк правой руки", ha="center", va="center", fontsize=8)

        # Засадный полк
        ax.add_patch(
            Rectangle((10, 1), 1.5, 0.8, facecolor="#c62828", edgecolor="black", linewidth=2)
        )
        ax.text(
            10.75, 1.4, "Засадный\nполк", ha="center", va="center", fontsize=7, fontweight="bold"
        )

        # Ордынцы
        ax.add_patch(
            Rectangle((3, 6.5), 6, 1.5, facecolor="#ffc107", edgecolor="#f57c00", linewidth=2)
        )
        ax.text(
            6,
            7.25,
            "Войско Мамая\n(Золотая Орда)",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

        # Стрелки
        ax.annotate(
            "",
            xy=(6, 3),
            xytext=(6, 6.5),
            arrowprops={"arrowstyle": "->", "color": "#f57c00", "lw": 2},
        )
        ax.annotate(
            "",
            xy=(6, 6.5),
            xytext=(10.5, 2),
            arrowprops={
                "arrowstyle": "->",
                "color": "darkred",
                "lw": 2,
                "connectionstyle": "arc3,rad=0.3",
            },
        )

        # Легенда
        ax.add_patch(Rectangle((0.5, 7.5), 0.5, 0.3, facecolor="#ef5350", edgecolor="black"))
        ax.text(1.2, 7.65, "Русские", fontsize=8, va="center")
        ax.add_patch(Rectangle((0.5, 7), 0.5, 0.3, facecolor="#ffc107", edgecolor="black"))
        ax.text(1.2, 7.15, "Ордынцы", fontsize=8, va="center")

    def _draw_poltava_battle(self, ax):
        """Схема Полтавской битвы."""
        ax.add_patch(Rectangle((0, 0), 12, 9, facecolor="#e8f5e9", edgecolor="none"))

        # Город Полтава
        ax.add_patch(Circle((10, 7), 1, facecolor="#9e9e9e", edgecolor="black", linewidth=2))
        ax.text(10, 7, "Полтава", ha="center", va="center", fontsize=9, fontweight="bold")

        # Русские редуты
        for i in range(6):
            ax.add_patch(
                Rectangle((3 + i * 0.8, 4), 0.6, 0.4, facecolor="#c62828", edgecolor="black")
            )
        ax.text(5.5, 3.5, "Редуты", fontsize=8, ha="center")

        # Русская армия
        ax.add_patch(
            Rectangle((2, 1), 5, 1.5, facecolor="#ef5350", edgecolor="darkred", linewidth=2)
        )
        ax.text(
            4.5,
            1.75,
            "Русская армия\n(Пётр I)",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

        # Шведская армия
        ax.add_patch(
            Rectangle((2, 6.5), 5, 1.5, facecolor="#1565c0", edgecolor="darkblue", linewidth=2)
        )
        ax.text(
            4.5,
            7.25,
            "Шведская армия\n(Карл XII)",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

        # Стрелки атак
        ax.annotate(
            "",
            xy=(4.5, 4.5),
            xytext=(4.5, 6.5),
            arrowprops={"arrowstyle": "->", "color": "blue", "lw": 2},
        )

        # Легенда
        ax.add_patch(Rectangle((9, 1), 0.5, 0.3, facecolor="#ef5350", edgecolor="black"))
        ax.text(9.7, 1.15, "Русские", fontsize=8, va="center")
        ax.add_patch(Rectangle((9, 0.5), 0.5, 0.3, facecolor="#1565c0", edgecolor="black"))
        ax.text(9.7, 0.65, "Шведы", fontsize=8, va="center")

    def _draw_stalingrad_battle(self, ax):
        """Схема Сталинградской битвы (операция Уран)."""
        ax.add_patch(Rectangle((0, 0), 12, 9, facecolor="#e8f5e9", edgecolor="none"))

        # Волга
        ax.fill_between([10, 12], [0, 0], [9, 9], color="#64b5f6", alpha=0.7)
        ax.text(11, 4.5, "Волга", fontsize=10, color="blue", rotation=90, va="center")

        # Сталинград
        ax.add_patch(Rectangle((8, 3), 2, 3, facecolor="#9e9e9e", edgecolor="black", linewidth=2))
        ax.text(9, 4.5, "Сталинград", ha="center", va="center", fontsize=9, fontweight="bold")

        # Немецкие войска в окружении
        ax.add_patch(
            Circle((6, 4.5), 2, facecolor="#424242", edgecolor="black", linewidth=2, alpha=0.7)
        )
        ax.text(6, 4.5, "6-я армия\n(Паулюс)", ha="center", va="center", fontsize=9, color="white")

        # Советские удары (клещи)
        # Северный удар
        ax.annotate(
            "", xy=(4, 6), xytext=(2, 8), arrowprops={"arrowstyle": "->", "color": "red", "lw": 3}
        )
        ax.text(1.5, 8.2, "Юго-Зап.\nфронт", fontsize=8, color="red")

        # Южный удар
        ax.annotate(
            "", xy=(4, 3), xytext=(2, 1), arrowprops={"arrowstyle": "->", "color": "red", "lw": 3}
        )
        ax.text(1.5, 0.5, "Сталингр.\nфронт", fontsize=8, color="red")

        # Точка соединения
        ax.add_patch(Circle((3.5, 4.5), 0.3, facecolor="red", edgecolor="black"))
        ax.text(3.5, 3.8, "Калач", fontsize=8, ha="center")

        # Легенда
        ax.add_patch(Rectangle((0.5, 7), 0.5, 0.3, facecolor="red", edgecolor="black"))
        ax.text(1.2, 7.15, "Советские войска", fontsize=8, va="center")
        ax.add_patch(Rectangle((0.5, 6.5), 0.5, 0.3, facecolor="#424242", edgecolor="black"))
        ax.text(1.2, 6.65, "Немецкие войска", fontsize=8, va="center")

    def _draw_ledovoe_battle(self, ax):
        """Схема Ледового побоища."""
        ax.add_patch(Rectangle((0, 0), 12, 9, facecolor="#e3f2fd", edgecolor="none"))

        # Чудское озеро
        ax.text(
            6, 8.5, "Чудское озеро (лёд)", fontsize=11, ha="center", style="italic", color="blue"
        )

        # Берег
        ax.add_patch(Rectangle((0, 0), 12, 1.5, facecolor="#8d6e63", edgecolor="none"))
        ax.text(6, 0.75, "Берег", fontsize=9, ha="center")

        # Русские войска
        ax.add_patch(
            Rectangle((4, 2), 4, 1.5, facecolor="#ef5350", edgecolor="darkred", linewidth=2)
        )
        ax.text(
            6, 2.75, "Русское войско\n(Александр Невский)", ha="center", va="center", fontsize=9
        )

        # Засада (скрытые отряды)
        ax.add_patch(Rectangle((1, 3), 1.5, 1, facecolor="#c62828", edgecolor="black", linewidth=2))
        ax.text(1.75, 3.5, "Засада", ha="center", va="center", fontsize=7)
        ax.add_patch(
            Rectangle((9.5, 3), 1.5, 1, facecolor="#c62828", edgecolor="black", linewidth=2)
        )
        ax.text(10.25, 3.5, "Засада", ha="center", va="center", fontsize=7)

        # Тевтонский орден (свинья)
        points = [[6, 7.5], [4.5, 6], [7.5, 6], [6, 7.5]]
        ax.add_patch(Polygon(points, facecolor="#424242", edgecolor="black", linewidth=2))
        ax.text(6, 6.5, "Рыцари\n(клин)", ha="center", va="center", fontsize=9, color="white")

        # Стрелки
        ax.annotate(
            "", xy=(6, 4), xytext=(6, 6), arrowprops={"arrowstyle": "->", "color": "gray", "lw": 2}
        )
        ax.annotate(
            "",
            xy=(4.5, 5),
            xytext=(2, 4),
            arrowprops={
                "arrowstyle": "->",
                "color": "red",
                "lw": 2,
                "connectionstyle": "arc3,rad=0.2",
            },
        )
        ax.annotate(
            "",
            xy=(7.5, 5),
            xytext=(10, 4),
            arrowprops={
                "arrowstyle": "->",
                "color": "red",
                "lw": 2,
                "connectionstyle": "arc3,rad=-0.2",
            },
        )

        # Легенда
        ax.add_patch(Rectangle((9, 1), 0.5, 0.3, facecolor="#ef5350", edgecolor="black"))
        ax.text(9.7, 1.15, "Русские", fontsize=8, va="center")
        ax.add_patch(Rectangle((9, 0.5), 0.5, 0.3, facecolor="#424242", edgecolor="black"))
        ax.text(9.7, 0.65, "Тевтонский орден", fontsize=8, va="center")

    def generate_war_timeline(self, war: str = "вов") -> bytes | None:
        """
        Генерирует хронологию войны в виде таблицы.

        Args:
            war: Название войны (вов, 1812, северная, крымская)
        """
        wars_data = {
            "вов": {
                "title": "Великая Отечественная война 1941-1945",
                "headers": ["Дата", "Событие", "Значение"],
                "rows": [
                    ["22.06.1941", "Начало войны", "Вторжение Германии в СССР"],
                    ["30.09-05.12.1941", "Битва за Москву", "Первое крупное поражение вермахта"],
                    ["17.07.1942-02.02.1943", "Сталинградская битва", "Коренной перелом в войне"],
                    ["05.07-23.08.1943", "Курская битва", "Крупнейшее танковое сражение"],
                    ["27.01.1944", "Снятие блокады Ленинграда", "872 дня блокады"],
                    ["09.05.1945", "День Победы", "Капитуляция Германии"],
                ],
            },
            "1812": {
                "title": "Отечественная война 1812 года",
                "headers": ["Дата", "Событие", "Значение"],
                "rows": [
                    ["12.06.1812", "Начало войны", "Вторжение Наполеона"],
                    ["4-6.08.1812", "Смоленское сражение", "Первое крупное сражение"],
                    ["26.08.1812", "Бородинское сражение", "Главная битва войны"],
                    ["2.09.1812", "Оставление Москвы", "Тарутинский маневр"],
                    ["12.10.1812", "Малоярославецкое сражение", "Отступление французов"],
                    ["25.12.1812", "Конец войны", "Изгнание Наполеона"],
                ],
            },
            "северная": {
                "title": "Северная война 1700-1721",
                "headers": ["Дата", "Событие", "Значение"],
                "rows": [
                    ["1700", "Начало войны", "Россия против Швеции"],
                    ["1700", "Поражение под Нарвой", "Начало реформ армии"],
                    ["1703", "Основание Петербурга", "Выход к Балтике"],
                    ["1709", "Полтавская битва", "Разгром шведов"],
                    ["1714", "Гангутское сражение", "Первая морская победа"],
                    ["1721", "Ништадтский мир", "Россия - морская держава"],
                ],
            },
        }

        war_lower = war.lower().strip()
        data = None
        for key, value in wars_data.items():
            if key in war_lower:
                data = value
                break

        if not data:
            data = wars_data["вов"]

        return self.generate_table(data["headers"], data["rows"], data["title"])
