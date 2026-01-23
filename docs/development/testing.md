# Testing Guide

## Test Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests with real APIs
├── e2e/              # End-to-end user scenarios
├── security/         # Security and vulnerability tests
└── performance/      # Load and performance tests
```

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v

# Security tests
pytest tests/security/ -v
```

### With Coverage

```bash
# Generate coverage report
pytest tests/ --cov=bot --cov-report=html

# View report
open htmlcov/index.html
```

### Specific Test File

```bash
pytest tests/unit/test_ai_service.py -v
```

### Specific Test Function

```bash
pytest tests/unit/test_ai_service.py::test_generate_response -v
```

## Writing Tests

### Unit Test Example

```python
import pytest
from bot.services.ai_service_solid import YandexAIService

def test_ai_service_initialization():
    """Test AI service initializes correctly."""
    service = YandexAIService()
    assert service is not None
    assert hasattr(service, 'generate_response')

@pytest.mark.asyncio
async def test_generate_response():
    """Test AI response generation."""
    service = YandexAIService()
    response = await service.generate_response(
        user_message="What is 2+2?",
        chat_history=[],
        user_age=10
    )
    assert isinstance(response, str)
    assert len(response) > 0
```

### Integration Test Example

```python
import pytest
from bot.database import get_db
from bot.services import UserService

@pytest.mark.integration
def test_user_creation():
    """Test user creation in database."""
    with get_db() as db:
        service = UserService(db)
        user = service.get_or_create_user(
            telegram_id=123456,
            username="testuser",
            first_name="Test"
        )
        assert user.telegram_id == 123456
        assert user.username == "testuser"
```

### E2E Test Example

```python
import pytest
from tests.fixtures.bot_client import BotClient

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_chat_flow():
    """Test complete chat interaction."""
    client = BotClient()

    # Send start command
    response = await client.send_command("/start")
    assert "Привет" in response

    # Send question
    response = await client.send_message("What is Python?")
    assert len(response) > 50
    assert "Python" in response
```

## Test Fixtures

### Common Fixtures

Located in `tests/conftest.py`:

```python
@pytest.fixture
def db_session():
    """Provide database session for tests."""
    with get_db() as session:
        yield session
        session.rollback()

@pytest.fixture
def mock_user():
    """Provide mock user for tests."""
    return {
        "telegram_id": 123456,
        "username": "testuser",
        "first_name": "Test",
        "age": 10
    }
```

### Using Fixtures

```python
def test_with_fixtures(db_session, mock_user):
    """Test using fixtures."""
    service = UserService(db_session)
    user = service.get_or_create_user(**mock_user)
    assert user.telegram_id == mock_user["telegram_id"]
```

## Mocking

### Mock External APIs

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch('bot.services.yandex_cloud_service.YandexCloudService.generate_text')
async def test_ai_with_mock(mock_generate):
    """Test AI service with mocked API."""
    mock_generate.return_value = "Mocked response"

    service = YandexAIService()
    response = await service.generate_response(
        user_message="Test",
        chat_history=[],
        user_age=10
    )

    assert response == "Mocked response"
    mock_generate.assert_called_once()
```

## Test Markers

### Available Markers

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.e2e          # End-to-end test
@pytest.mark.security     # Security test
@pytest.mark.slow         # Slow test (skip in CI)
@pytest.mark.asyncio      # Async test
```

### Running Specific Markers

```bash
# Run only unit tests
pytest -m unit

# Run everything except slow tests
pytest -m "not slow"

# Run integration and e2e tests
pytest -m "integration or e2e"
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to main
- Pull requests
- Scheduled daily runs

### CI Configuration

See `.github/workflows/main-ci-cd.yml`

## Test Coverage Goals

- **Overall**: 80%+
- **Critical paths**: 95%+
- **New code**: 90%+

### Check Coverage

```bash
# Generate coverage
pytest tests/ --cov=bot --cov-report=term-missing

# Fail if below threshold
pytest tests/ --cov=bot --cov-fail-under=80
```

## Performance Testing

### Load Testing

```bash
# Run load tests
python scripts/load_testing.py

# JMeter tests
jmeter -n -t tests/performance/load_test.jmx
```

### Profiling

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

## Best Practices

1. **Test naming**: Use descriptive names (test_feature_scenario_expected)
2. **One assertion per test**: Focus on single behavior
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Independent tests**: No dependencies between tests
5. **Fast tests**: Keep unit tests under 1 second
6. **Clean up**: Use fixtures for setup/teardown
7. **Mock external services**: Don't rely on external APIs in unit tests
8. **Test edge cases**: Include boundary conditions
9. **Document complex tests**: Add docstrings explaining why
10. **Keep tests maintainable**: Refactor tests like production code

## Troubleshooting

### Tests Failing Locally

```bash
# Clear pytest cache
pytest --cache-clear

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check database connection
python scripts/check_database.py
```

### Slow Tests

```bash
# Find slowest tests
pytest --durations=10

# Run in parallel
pytest -n auto
```

### Flaky Tests

```bash
# Run test multiple times
pytest tests/test_flaky.py --count=10

# Add retry decorator
@pytest.mark.flaky(reruns=3)
def test_sometimes_fails():
    pass
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock guide](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
