"""
Сервис визуализации для генерации графиков и диаграмм.

Модульная архитектура (SOLID принципы):
- Разделение по предметам (SRP)
- Общий базовый класс (DIP)
- Детектор запросов (OCP)
"""

from loguru import logger

from bot.services.visualization.base import BaseVisualizationService
from bot.services.visualization.detector import VisualizationDetector
from bot.services.visualization.languages import EnglishVisualization, RussianVisualization
from bot.services.visualization.math import (
    AlgebraVisualization,
    ArithmeticVisualization,
    GeometryVisualization,
)
from bot.services.visualization.other import (
    ComputerScienceVisualization,
    WorldAroundVisualization,
)

# Импорты для остальных модулей
from bot.services.visualization.sciences import (
    ChemistryVisualization,
    PhysicsVisualization,
)
from bot.services.visualization.social import (
    GeographyVisualization,
    HistoryVisualization,
    SocialStudiesVisualization,
)


class VisualizationService(BaseVisualizationService):
    """
    Главный сервис визуализации (Facade pattern).

    Объединяет все модули по предметам и предоставляет единый интерфейс.
    """

    def __init__(self):
        """Инициализация сервиса с модулями по предметам."""
        super().__init__()

        # Инициализируем модули
        self.arithmetic = ArithmeticVisualization()
        self.algebra = AlgebraVisualization()
        self.geometry = GeometryVisualization()
        self.russian = RussianVisualization()
        self.english = EnglishVisualization()
        self.physics = PhysicsVisualization()
        self.chemistry = ChemistryVisualization()
        self.geography = GeographyVisualization()
        self.history = HistoryVisualization()
        self.social_studies = SocialStudiesVisualization()
        self.computer_science = ComputerScienceVisualization()
        self.world_around = WorldAroundVisualization()

        # Детектор запросов
        self.detector = VisualizationDetector(self)

        logger.info("✅ VisualizationService инициализирован (модульная архитектура)")

    def detect_visualization_request(self, text: str) -> tuple[bytes | None, str | None]:
        """
        Детектирует запрос на визуализацию и генерирует изображение.

        Args:
            text: Текст сообщения для анализа

        Returns:
            tuple: (Изображение визуализации или None, Тип визуализации или None)
        """
        return self.detector.detect(text)

    def detect_geography_question(self, text: str) -> str | None:
        """
        Определяет, является ли запрос географическим вопросом типа "где находится X".

        Args:
            text: Текст сообщения для анализа

        Returns:
            str | None: Название страны/города для карты или None
        """
        return self.detector.detect_geography_question(text)

    # Делегируем методы арифметики
    def generate_full_multiplication_table(self) -> bytes | None:
        """Генерирует полную таблицу умножения (1-10)."""
        return self.arithmetic.generate_full_multiplication_table()

    def generate_multiplication_table_image(self, number: int) -> bytes | None:
        """Генерирует таблицу умножения на конкретное число."""
        return self.arithmetic.generate_multiplication_table_image(number)

    def generate_multiple_multiplication_tables(self, numbers: list[int]) -> bytes | None:
        """Генерирует несколько таблиц умножения в одной картинке."""
        return self.arithmetic.generate_multiple_multiplication_tables(numbers)

    def generate_combined_table_and_graph(
        self, table_number: int, graph_expression: str
    ) -> bytes | None:
        """Генерирует комбинированную картинку: таблица умножения + график функции."""
        return self.arithmetic.generate_combined_table_and_graph(table_number, graph_expression)

    def generate_multiple_function_graphs(self, expressions: list[str]) -> bytes | None:
        """Генерирует несколько графиков функций в одной картинке."""
        return super().generate_multiple_function_graphs(expressions)

    def generate_addition_table(self) -> bytes | None:
        """Генерирует таблицу сложения."""
        return self.arithmetic.generate_addition_table()

    def generate_subtraction_table(self) -> bytes | None:
        """Генерирует таблицу вычитания."""
        return self.arithmetic.generate_subtraction_table()

    def generate_division_table(self) -> bytes | None:
        """Генерирует таблицу деления."""
        return self.arithmetic.generate_division_table()

    def generate_units_table(self) -> bytes | None:
        """Генерирует таблицу единиц измерения."""
        return self.arithmetic.generate_units_table()

    # Делегируем методы алгебры
    def generate_powers_of_2_and_10_table(self) -> bytes | None:
        """Генерирует таблицу степеней чисел 2 и 10."""
        return self.algebra.generate_powers_of_2_and_10_table()

    def generate_prime_numbers_table(self) -> bytes | None:
        """Генерирует таблицу простых чисел."""
        return self.algebra.generate_prime_numbers_table()

    def generate_abbreviated_multiplication_formulas_table(self) -> bytes | None:
        """Генерирует таблицу формул сокращенного умножения."""
        return self.algebra.generate_abbreviated_multiplication_formulas_table()

    def generate_power_properties_table(self) -> bytes | None:
        """Генерирует таблицу свойств степеней."""
        return self.algebra.generate_power_properties_table()

    def generate_square_root_properties_table(self) -> bytes | None:
        """Генерирует таблицу свойств квадратного корня."""
        return self.algebra.generate_square_root_properties_table()

    def generate_standard_form_table(self) -> bytes | None:
        """Генерирует таблицу стандартного вида числа."""
        return self.algebra.generate_standard_form_table()

    def generate_squares_and_cubes_table(self) -> bytes | None:
        """Генерирует таблицу квадратов и кубов."""
        return self.algebra.generate_squares_and_cubes_table()

    def generate_square_roots_values_table(self) -> bytes | None:
        """Генерирует таблицу значений квадратных корней (√1–√50)."""
        return self.algebra.generate_square_roots_values_table()

    # Делегируем методы геометрии
    def generate_geometry_area_formulas_table(self) -> bytes | None:
        """Генерирует таблицу формул площадей."""
        return self.geometry.generate_geometry_area_formulas_table()

    def generate_geometry_volume_formulas_table(self) -> bytes | None:
        """Генерирует таблицу формул объемов."""
        return self.geometry.generate_geometry_volume_formulas_table()

    def generate_triangle_classification_table(self) -> bytes | None:
        """Генерирует таблицу классификации треугольников."""
        return self.geometry.generate_triangle_classification_table()

    def generate_quadrilateral_classification_table(self) -> bytes | None:
        """Генерирует таблицу классификации четырехугольников."""
        return self.geometry.generate_quadrilateral_classification_table()

    def generate_trigonometry_table(self) -> bytes | None:
        """Генерирует таблицу тригонометрических функций."""
        return self.geometry.generate_trigonometry_table()

    def generate_median_diagram(self) -> bytes | None:
        """Генерирует схему треугольника с медианами."""
        return self.geometry.generate_median_diagram()

    # Делегируем методы русского языка
    def generate_russian_alphabet_table(self) -> bytes | None:
        """Генерирует таблицу русского алфавита."""
        return self.russian.generate_russian_alphabet_table()

    def generate_russian_cases_table(self) -> bytes | None:
        """Генерирует таблицу падежей."""
        return self.russian.generate_russian_cases_table()

    def generate_russian_verb_conjugation_table(self) -> bytes | None:
        """Генерирует таблицу спряжения глаголов."""
        return self.russian.generate_russian_verb_conjugation_table()

    def generate_russian_orthography_table(self) -> bytes | None:
        """Генерирует таблицу правил орфографии."""
        return self.russian.generate_russian_orthography_table()

    def generate_russian_punctuation_table(self) -> bytes | None:
        """Генерирует таблицу правил пунктуации."""
        return self.russian.generate_russian_punctuation_table()

    def generate_russian_word_analysis_table(self) -> bytes | None:
        """Генерирует таблицу морфемного разбора."""
        return self.russian.generate_russian_word_analysis_table()

    def generate_russian_speech_styles_table(self) -> bytes | None:
        """Генерирует таблицу стилей речи."""
        return self.russian.generate_russian_speech_styles_table()

    # Делегируем методы английского языка
    def generate_english_tenses_table(self) -> bytes | None:
        """Генерирует таблицу времен английского языка."""
        return self.english.generate_english_tenses_table()

    def generate_english_irregular_verbs_table(self) -> bytes | None:
        """Генерирует таблицу неправильных глаголов."""
        return self.english.generate_english_irregular_verbs_table()

    # Делегируем методы физики
    def generate_physics_constants_table(self) -> bytes | None:
        """Генерирует таблицу физических констант."""
        return self.physics.generate_physics_constants_table()

    def generate_physics_motion_graph(self, motion_type: str = "uniform") -> bytes | None:
        """Генерирует график движения."""
        return self.physics.generate_physics_motion_graph(motion_type)

    def generate_ohms_law_graph(self) -> bytes | None:
        """Генерирует график закона Ома."""
        return self.physics.generate_ohms_law_graph()

    def generate_physics_densities_table(self) -> bytes | None:
        """Генерирует таблицу плотностей."""
        return self.physics.generate_physics_densities_table()

    def generate_physics_heat_capacity_table(self) -> bytes | None:
        """Генерирует таблицу удельных теплоемкостей."""
        return self.physics.generate_physics_heat_capacity_table()

    def generate_physics_resistivity_table(self) -> bytes | None:
        """Генерирует таблицу удельных сопротивлений."""
        return self.physics.generate_physics_resistivity_table()

    def generate_melting_graph(self, substance: str = "лед") -> bytes | None:
        """Генерирует график плавления вещества."""
        return self.physics.generate_melting_graph(substance)

    def generate_heating_cooling_graph(self, process: str = "heating") -> bytes | None:
        """Генерирует график нагревания/охлаждения."""
        return self.physics.generate_heating_cooling_graph(process)

    # Делегируем методы химии
    def generate_chemistry_solubility_table(self) -> bytes | None:
        """Генерирует таблицу растворимости."""
        return self.chemistry.generate_chemistry_solubility_table()

    def generate_chemistry_valence_table(self) -> bytes | None:
        """Генерирует таблицу валентности."""
        return self.chemistry.generate_chemistry_valence_table()

    def generate_periodic_table_simple(self) -> bytes | None:
        """Генерирует периодическую таблицу."""
        return self.chemistry.generate_periodic_table_simple()

    # Делегируем методы географии
    def generate_time_zones_table(self) -> bytes | None:
        """Генерирует таблицу часовых поясов."""
        return self.geography.generate_time_zones_table()

    def generate_countries_table(self) -> bytes | None:
        """Генерирует таблицу стран."""
        return self.geography.generate_countries_table()

    def generate_natural_zones_table(self) -> bytes | None:
        """Генерирует таблицу природных зон."""
        return self.geography.generate_natural_zones_table()

    def generate_country_map(self, country_name: str) -> bytes | None:
        """Генерирует схематичную карту страны."""
        return self.geography.generate_country_map(country_name)

    def get_last_map_coordinates(self) -> dict | None:
        """Возвращает координаты последней сгенерированной карты (для интерактивного режима)."""
        return self.geography.get_last_map_coordinates()

    def generate_climatogram(self, zone: str = "тайга") -> bytes | None:
        """Генерирует климатограмму для природной зоны или города."""
        return self.geography.generate_climatogram(zone)

    # Делегируем методы истории
    def generate_history_timeline_table(self) -> bytes | None:
        """Генерирует хронологическую таблицу."""
        return self.history.generate_history_timeline_table()

    def generate_battle_scheme(self, battle: str = "бородино") -> bytes | None:
        """Генерирует схему исторической битвы."""
        return self.history.generate_battle_scheme(battle)

    def generate_war_timeline(self, war: str = "вов") -> bytes | None:
        """Генерирует хронологию войны."""
        return self.history.generate_war_timeline(war)

    # Делегируем методы обществознания
    def generate_government_branches_table(self) -> bytes | None:
        """Генерирует таблицу ветвей власти."""
        return self.social_studies.generate_government_branches_table()

    # Делегируем методы информатики
    def generate_number_systems_table(self) -> bytes | None:
        """Генерирует таблицу систем счисления."""
        return self.computer_science.generate_number_systems_table()

    def generate_flowchart(self, algorithm_type: str = "linear") -> bytes | None:
        """Генерирует блок-схему алгоритма."""
        return self.computer_science.generate_flowchart(algorithm_type)

    def generate_truth_table(self, operation: str = "and") -> bytes | None:
        """Генерирует таблицу истинности для логической операции."""
        return self.computer_science.generate_truth_table(operation)

    # Делегируем методы окружающего мира
    def generate_seasons_months_table(self) -> bytes | None:
        """Генерирует таблицу времен года."""
        return self.world_around.generate_seasons_months_table()

    # Делегируем методы генерации диаграмм из базового класса
    def generate_line_chart(
        self,
        x_data: list[float],
        y_data: list[float],
        title: str = "Линейный график",
        x_label: str = "X",
        y_label: str = "Y",
    ) -> bytes | None:
        """Генерирует линейный график для данных."""
        return super().generate_line_chart(x_data, y_data, title, x_label, y_label)

    def generate_histogram(
        self,
        data: list[float],
        bins: int = 10,
        title: str = "Гистограмма",
        x_label: str = "Значение",
        y_label: str = "Частота",
    ) -> bytes | None:
        """Генерирует гистограмму распределения данных."""
        return super().generate_histogram(data, bins, title, x_label, y_label)

    def generate_scatter_plot(
        self,
        x_data: list[float],
        y_data: list[float],
        title: str = "Диаграмма рассеяния",
        x_label: str = "X",
        y_label: str = "Y",
    ) -> bytes | None:
        """Генерирует диаграмму рассеяния (точечную диаграмму)."""
        return super().generate_scatter_plot(x_data, y_data, title, x_label, y_label)

    def generate_box_plot(
        self,
        data: list[list[float]] | dict[str, list[float]],
        title: str = "Ящик с усами",
        y_label: str = "Значение",
    ) -> bytes | None:
        """Генерирует ящик с усами (box plot) для визуализации распределения данных."""
        return super().generate_box_plot(data, title, y_label)

    def generate_bubble_chart(
        self,
        x_data: list[float],
        y_data: list[float],
        sizes: list[float],
        labels: list[str] | None = None,
        title: str = "Пузырьковая диаграмма",
        x_label: str = "X",
        y_label: str = "Y",
    ) -> bytes | None:
        """Генерирует пузырьковую диаграмму (bubble chart)."""
        return super().generate_bubble_chart(x_data, y_data, sizes, labels, title, x_label, y_label)

    def generate_heatmap(
        self,
        data: list[list[float]] | dict[str, dict[str, float]],
        row_labels: list[str] | None = None,
        col_labels: list[str] | None = None,
        title: str = "Тепловая карта",
        cmap: str = "YlOrRd",
    ) -> bytes | None:
        """Генерирует тепловую карту (heatmap)."""
        return super().generate_heatmap(data, row_labels, col_labels, title, cmap)


# Singleton pattern для глобального доступа
_viz_service_instance: VisualizationService | None = None


def get_visualization_service() -> VisualizationService:
    """
    Получить глобальный экземпляр VisualizationService (singleton).

    Returns:
        VisualizationService: Экземпляр сервиса визуализации
    """
    global _viz_service_instance
    if _viz_service_instance is None:
        _viz_service_instance = VisualizationService()
    return _viz_service_instance
