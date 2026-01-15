"""Модуль визуализации для географии."""

from bot.services.visualization.base import BaseVisualizationService

try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class GeographyVisualization(BaseVisualizationService):
    """Визуализация для географии: часовые пояса, страны, природные зоны, карты."""

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

    def generate_country_map(self, country_name: str) -> bytes | None:
        """Генерирует схематичную карту страны с координатами и соседями."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        # Координаты основных стран (широта, долгота)
        countries_coords = {
            "япония": (36.2048, 138.2529, "Япония"),
            "россия": (61.5240, 105.3188, "Россия"),
            "китай": (35.8617, 104.1954, "Китай"),
            "сша": (37.0902, -95.7129, "США"),
            "франция": (46.2276, 2.2137, "Франция"),
            "германия": (51.1657, 10.4515, "Германия"),
            "великобритания": (55.3781, -3.4360, "Великобритания"),
            "индия": (20.5937, 78.9629, "Индия"),
            "бразилия": (-14.2350, -51.9253, "Бразилия"),
            "австралия": (-25.2744, 133.7751, "Австралия"),
            "канада": (56.1304, -106.3468, "Канада"),
            "италия": (41.8719, 12.5674, "Италия"),
            "испания": (40.4637, -3.7492, "Испания"),
            "египет": (26.0975, 30.0444, "Египет"),
            "мексика": (23.6345, -102.5528, "Мексика"),
        }

        # Нормализуем название страны
        country_lower = country_name.lower().strip()
        country_key = None
        for key in countries_coords:
            if key in country_lower or country_lower in key:
                country_key = key
                break

        if not country_key:
            # Если страна не найдена, используем общую карту мира
            return self._generate_world_map(country_name)

        try:
            import io

            lat, lon, name = countries_coords[country_key]

            # Создаем фигуру
            fig, ax = plt.subplots(figsize=(12, 8))
            fig.patch.set_facecolor("white")

            # Рисуем схематичную карту мира
            ax.set_xlim(-180, 180)
            ax.set_ylim(-90, 90)
            ax.set_aspect("equal")
            ax.axis("off")

            # Рисуем континенты (упрощенные прямоугольники)
            # Азия
            asia = plt.Rectangle(
                (60, 10),
                (140 - 60),
                (50 - 10),
                facecolor="#E8F5E9",
                edgecolor="#4CAF50",
                linewidth=2,
            )
            ax.add_patch(asia)
            ax.text(
                100,
                30,
                "Азия",
                ha="center",
                va="center",
                fontsize=12,
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.7},
            )

            # Европа
            europe = plt.Rectangle(
                (-10, 35),
                (40 - (-10)),
                (70 - 35),
                facecolor="#E3F2FD",
                edgecolor="#2196F3",
                linewidth=2,
            )
            ax.add_patch(europe)
            ax.text(
                15,
                52,
                "Европа",
                ha="center",
                va="center",
                fontsize=12,
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.7},
            )

            # Северная Америка
            na = plt.Rectangle(
                (-130, 25),
                (-50 - (-130)),
                (70 - 25),
                facecolor="#FFF3E0",
                edgecolor="#FF9800",
                linewidth=2,
            )
            ax.add_patch(na)
            ax.text(
                -90,
                47,
                "Сев. Америка",
                ha="center",
                va="center",
                fontsize=12,
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.7},
            )

            # Отмечаем запрашиваемую страну
            ax.plot(
                lon, lat, "ro", markersize=20, markeredgecolor="red", markeredgewidth=3, label=name
            )
            ax.annotate(
                name,
                (lon, lat),
                xytext=(10, 10),
                textcoords="offset points",
                fontsize=14,
                fontweight="bold",
                color="red",
                bbox={"boxstyle": "round,pad=0.5", "facecolor": "yellow", "alpha": 0.8},
                arrowprops={"arrowstyle": "->", "connectionstyle": "arc3,rad=0.3"},
            )

            # Добавляем координаты
            ax.text(
                0.02,
                0.98,
                f"📍 {name}\nКоординаты: {lat:.2f}°N, {lon:.2f}°E",
                transform=ax.transAxes,
                fontsize=12,
                verticalalignment="top",
                bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.9},
            )

            # Заголовок
            ax.text(
                0.5,
                0.95,
                f"Карта: {name}",
                transform=ax.transAxes,
                ha="center",
                fontsize=16,
                fontweight="bold",
            )

            plt.tight_layout()

            # Сохраняем в bytes
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            plt.close(fig)

            return buf.read()

        except Exception as e:
            from loguru import logger

            logger.error(f"❌ Ошибка генерации карты для {country_name}: {e}")
            return None

    def _generate_world_map(self, country_name: str) -> bytes | None:
        """Генерирует общую карту мира с указанием региона страны."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            import io

            fig, ax = plt.subplots(figsize=(14, 8))
            fig.patch.set_facecolor("white")

            # Рисуем схематичную карту мира
            ax.set_xlim(-180, 180)
            ax.set_ylim(-90, 90)
            ax.set_aspect("equal")
            ax.axis("off")

            # Континенты
            continents = [
                ("Азия", (60, 10), (140, 50), "#E8F5E9", "#4CAF50"),
                ("Европа", (-10, 35), (40, 70), "#E3F2FD", "#2196F3"),
                ("Сев. Америка", (-130, 25), (-50, 70), "#FFF3E0", "#FF9800"),
                ("Юж. Америка", (-80, -55), (-35, 12), "#F3E5F5", "#9C27B0"),
                ("Африка", (-20, -35), (50, 35), "#FFF9C4", "#FBC02D"),
                ("Австралия", (110, -45), (155, -10), "#E1BEE7", "#7B1FA2"),
            ]

            for name, (x1, y1), (x2, y2), facecolor, edgecolor in continents:
                rect = plt.Rectangle(
                    (x1, y1),
                    (x2 - x1),
                    (y2 - y1),
                    facecolor=facecolor,
                    edgecolor=edgecolor,
                    linewidth=2,
                )
                ax.add_patch(rect)
                ax.text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    name,
                    ha="center",
                    va="center",
                    fontsize=11,
                    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.7},
                )

            # Заголовок
            ax.text(
                0.5,
                0.95,
                f"Карта мира: {country_name}",
                transform=ax.transAxes,
                ha="center",
                fontsize=16,
                fontweight="bold",
            )

            ax.text(
                0.5,
                0.05,
                "Схематичная карта мира",
                transform=ax.transAxes,
                ha="center",
                fontsize=12,
                style="italic",
                color="gray",
            )

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            plt.close(fig)

            return buf.read()

        except Exception as e:
            from loguru import logger

            logger.error(f"❌ Ошибка генерации карты мира: {e}")
            return None
