"""
Модуль визуализации для алгебры.

Степени, формулы сокращенного умножения, свойства степеней и корней.
"""

import math

from bot.services.visualization.base import BaseVisualizationService


class AlgebraVisualization(BaseVisualizationService):
    """Визуализация для алгебры: степени, формулы, свойства."""

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

    def generate_squares_and_cubes_table(self) -> bytes | None:
        """Генерирует таблицу квадратов и кубов чисел (1-20)."""
        headers = ["Число", "Квадрат (x²)", "Куб (x³)"]
        rows = []
        for i in range(1, 21):
            rows.append([str(i), str(i**2), str(i**3)])
        return self.generate_table(headers, rows, "Таблица квадратов и кубов")

    def generate_square_roots_values_table(self) -> bytes | None:
        """Генерирует таблицу значений квадратных корней для чисел 1-50."""
        headers = ["Число n", "√n", "Приближённое значение"]
        rows = []
        for n in range(1, 51):
            val = math.sqrt(n)
            approx = f"{val:.4f}".rstrip("0").rstrip(".")
            rows.append([str(n), f"√{n}", approx])
        return self.generate_table(headers, rows, "Таблица значений квадратных корней")
