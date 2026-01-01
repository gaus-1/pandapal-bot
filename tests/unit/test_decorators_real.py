"""
РЕАЛЬНЫЕ тесты для декораторов
Проверяем реальную работу всех декораторов без моков
"""

import time

import pytest

from bot.decorators import (
    cache_result,
    log_execution_time,
    retry_on_exception,
    validate_input,
)


class TestLogExecutionTimeDecorator:
    """Реальные тесты декоратора log_execution_time"""

    def test_decorator_logs_execution_time(self):
        """Тест что декоратор реально измеряет время"""

        @log_execution_time
        def fast_function():
            return "result"

        result = fast_function()
        assert result == "result"

    def test_decorator_with_sleep(self):
        """Тест измерения времени с реальной задержкой"""

        @log_execution_time
        def slow_function():
            time.sleep(0.1)  # 100ms
            return "slow result"

        start = time.time()
        result = slow_function()
        duration = time.time() - start

        assert result == "slow result"
        assert duration >= 0.1  # Должно быть не меньше 100ms

    def test_decorator_preserves_function_name(self):
        """Тест что декоратор сохраняет имя функции"""

        @log_execution_time
        def my_function():
            return 42

        assert my_function.__name__ == "my_function"

    def test_decorator_with_arguments(self):
        """Тест работы декоратора с аргументами"""

        @log_execution_time
        def add_numbers(a, b):
            return a + b

        result = add_numbers(5, 3)
        assert result == 8

    def test_decorator_with_kwargs(self):
        """Тест работы декоратора с kwargs"""

        @log_execution_time
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result1 = greet("Alice")
        result2 = greet("Bob", greeting="Hi")

        assert result1 == "Hello, Alice!"
        assert result2 == "Hi, Bob!"


class TestRetryOnExceptionDecorator:
    """Реальные тесты декоратора retry_on_exception"""

    def test_successful_function_no_retry(self):
        """Тест что успешная функция выполняется без повторов"""

        call_count = {"count": 0}

        @retry_on_exception(max_attempts=3, delay=0.1)
        def successful_function():
            call_count["count"] += 1
            return "success"

        result = successful_function()

        assert result == "success"
        assert call_count["count"] == 1  # Вызвана только один раз

    def test_retry_on_failure(self):
        """Тест реальных повторных попыток при ошибках"""

        call_count = {"count": 0}

        @retry_on_exception(max_attempts=3, delay=0.05, exceptions=(ValueError,))
        def failing_function():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ValueError("Temporary error")
            return "success on third try"

        result = failing_function()

        assert result == "success on third try"
        assert call_count["count"] == 3  # Три попытки

    def test_all_retries_exhausted(self):
        """Тест когда все попытки исчерпаны"""

        @retry_on_exception(max_attempts=3, delay=0.05)
        def always_failing():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError, match="Always fails"):
            always_failing()

    def test_retry_specific_exception(self):
        """Тест повтора только для конкретных исключений"""

        @retry_on_exception(max_attempts=3, delay=0.05, exceptions=(ValueError,))
        def function_with_type_error():
            raise TypeError("Not retryable")

        # TypeError не в списке exceptions, поэтому не должно быть повторов
        with pytest.raises(TypeError, match="Not retryable"):
            function_with_type_error()

    def test_retry_delay_works(self):
        """Тест что задержка между попытками работает"""

        call_count = {"count": 0}

        @retry_on_exception(max_attempts=2, delay=0.1)
        def failing_with_delay():
            call_count["count"] += 1
            raise ValueError("Test error")

        start_time = time.time()
        try:
            failing_with_delay()
        except ValueError:
            pass
        duration = time.time() - start_time

        # Должно быть минимум 0.1 секунды задержки между двумя попытками
        assert duration >= 0.1


class TestValidateInputDecorator:
    """Реальные тесты декоратора validate_input"""

    def test_validate_positive_number(self):
        """Тест валидации положительных чисел (с kwargs)"""

        @validate_input(age=lambda x: x > 0 and x < 150)
        def set_age(age):
            return f"Age set to {age}"

        # Валидное значение (kwargs)
        result = set_age(age=25)
        assert result == "Age set to 25"

        # Невалидное значение
        with pytest.raises(ValueError):
            set_age(age=-5)

    def test_validate_string_length(self):
        """Тест валидации длины строки"""

        @validate_input(name=lambda x: len(x) > 0 and len(x) < 50)
        def set_name(name):
            return f"Name: {name}"

        # Валидное имя (kwargs)
        result = set_name(name="Alice")
        assert result == "Name: Alice"

        # Пустая строка
        with pytest.raises(ValueError):
            set_name(name="")

    def test_validate_multiple_parameters(self):
        """Тест валидации нескольких параметров"""

        @validate_input(
            username=lambda x: len(x) >= 3,
            age=lambda x: x >= 6 and x <= 18,
        )
        def register_user(username, age):
            return f"User {username}, age {age} registered"

        # Валидные значения (kwargs)
        result = register_user(username="alice123", age=10)
        assert result == "User alice123, age 10 registered"

        # Невалидный username
        with pytest.raises(ValueError):
            register_user(username="ab", age=10)

        # Невалидный age
        with pytest.raises(ValueError):
            register_user(username="alice123", age=3)

    def test_validate_with_none_value(self):
        """Тест валидации с None значениями"""

        @validate_input(value=lambda x: x is None or x > 0)
        def set_optional_value(value=None):
            return value if value is not None else "default"

        # None допустим
        result1 = set_optional_value(value=None)
        assert result1 == "default"

        # Положительное число допустимо
        result2 = set_optional_value(value=42)
        assert result2 == 42

        # Отрицательное число недопустимо
        with pytest.raises(ValueError):
            set_optional_value(value=-5)


class TestCacheResultDecorator:
    """Реальные тесты декоратора cache_result"""

    def test_cache_basic_function(self):
        """Тест базового кэширования результата"""

        call_count = {"count": 0}

        @cache_result()
        def expensive_calculation(x):
            call_count["count"] += 1
            return x * x

        # Первый вызов - вычисление
        result1 = expensive_calculation(5)
        assert result1 == 25
        assert call_count["count"] == 1

        # Второй вызов с теми же аргументами - из кэша
        result2 = expensive_calculation(5)
        assert result2 == 25
        assert call_count["count"] == 1  # Не увеличилось

        # Вызов с другими аргументами - новое вычисление
        result3 = expensive_calculation(10)
        assert result3 == 100
        assert call_count["count"] == 2

    def test_cache_with_multiple_arguments(self):
        """Тест кэширования с несколькими аргументами"""

        call_count = {"count": 0}

        @cache_result()
        def add_numbers(a, b):
            call_count["count"] += 1
            return a + b

        # Первый вызов
        result1 = add_numbers(3, 4)
        assert result1 == 7
        assert call_count["count"] == 1

        # Повторный вызов с теми же аргументами
        result2 = add_numbers(3, 4)
        assert result2 == 7
        assert call_count["count"] == 1  # Из кэша

        # Вызов с другими аргументами
        result3 = add_numbers(5, 6)
        assert result3 == 11
        assert call_count["count"] == 2

    def test_cache_with_kwargs(self):
        """Тест кэширования с kwargs"""

        call_count = {"count": 0}

        @cache_result()
        def format_message(text, prefix=">>>"):
            call_count["count"] += 1
            return f"{prefix} {text}"

        # Первый вызов
        result1 = format_message("Hello", prefix="***")
        assert result1 == "*** Hello"
        assert call_count["count"] == 1

        # Повторный вызов
        result2 = format_message("Hello", prefix="***")
        assert result2 == "*** Hello"
        assert call_count["count"] == 1  # Из кэша


class TestDecoratorsIntegration:
    """Интеграционные тесты - комбинирование декораторов"""

    def test_multiple_decorators(self):
        """Тест использования нескольких декораторов"""

        @log_execution_time
        @retry_on_exception(max_attempts=2, delay=0.05)
        def function_with_multiple_decorators(value):
            if value < 0:
                raise ValueError("Negative value")
            return value * 2

        # Успешный вызов
        result = function_with_multiple_decorators(5)
        assert result == 10

        # Неуспешный вызов
        with pytest.raises(ValueError):
            function_with_multiple_decorators(-5)

    def test_validate_and_cache(self):
        """Тест комбинации валидации и кэширования"""

        call_count = {"count": 0}

        @cache_result()
        @validate_input(x=lambda v: v > 0)
        def validated_cached_function(x):
            call_count["count"] += 1
            return x**2

        # Валидный вызов (kwargs)
        result1 = validated_cached_function(x=5)
        assert result1 == 25
        assert call_count["count"] == 1

        # Повторный валидный вызов - из кэша
        result2 = validated_cached_function(x=5)
        assert result2 == 25
        assert call_count["count"] == 1

        # Невалидный вызов
        with pytest.raises(ValueError):
            validated_cached_function(x=-5)

    def test_all_decorators_combined(self):
        """Тест использования всех декораторов вместе"""

        @log_execution_time
        @cache_result()
        @retry_on_exception(max_attempts=2, delay=0.05)
        @validate_input(value=lambda x: x >= 0)
        def complex_function(value):
            time.sleep(0.01)  # Симулируем работу
            return value * 3

        # Первый вызов - полное выполнение (kwargs)
        result1 = complex_function(value=10)
        assert result1 == 30

        # Второй вызов - из кэша (должно быть быстрее)
        start = time.time()
        result2 = complex_function(value=10)
        duration = time.time() - start

        assert result2 == 30
        assert duration < 0.01  # Должно быть быстрее благодаря кэшу


class TestRateLimitDecorator:
    """Реальные тесты декоратора rate_limit"""

    def test_rate_limit_basic(self):
        """Тест базовой работы rate_limit"""
        from bot.decorators import rate_limit

        @rate_limit(calls_per_minute=5)
        def limited_function():
            return "success"

        # Первые 5 вызовов должны пройти
        for i in range(5):
            result = limited_function()
            assert result == "success"

        # 6-й вызов должен вызвать ошибку
        with pytest.raises(RuntimeError, match="Превышен лимит вызовов"):
            limited_function()

    def test_rate_limit_with_arguments(self):
        """Тест rate_limit с аргументами"""
        from bot.decorators import rate_limit

        @rate_limit(calls_per_minute=3)
        def limited_with_args(x, y):
            return x + y

        # 3 успешных вызова
        assert limited_with_args(1, 2) == 3
        assert limited_with_args(2, 3) == 5
        assert limited_with_args(3, 4) == 7

        # 4-й вызов должен упасть
        with pytest.raises(RuntimeError):
            limited_with_args(4, 5)


class TestDecoratorsEdgeCases:
    """Тесты граничных случаев"""

    def test_decorator_with_no_arguments(self):
        """Тест декоратора на функции без аргументов"""

        @log_execution_time
        def no_args_function():
            return "no args"

        result = no_args_function()
        assert result == "no args"

    def test_decorator_with_return_none(self):
        """Тест декоратора на функции возвращающей None"""

        @log_execution_time
        def returns_none():
            pass

        result = returns_none()
        assert result is None

    def test_retry_decorator_with_zero_delay(self):
        """Тест retry с нулевой задержкой"""

        call_count = {"count": 0}

        @retry_on_exception(max_attempts=3, delay=0.0)
        def fast_retry():
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise ValueError("Retry me")
            return "success"

        result = fast_retry()
        assert result == "success"
        assert call_count["count"] == 2
