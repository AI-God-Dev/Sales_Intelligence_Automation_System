# Quick Test Guide

## Running Tests

### Basic Commands

```bash
# Activate virtual environment (Windows)
.\.venv\Scripts\activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_validation.py

# Run specific test
pytest tests/test_validation.py::test_validate_email_valid

# Run tests matching pattern
pytest -k "email"

# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run only integration tests
pytest -m integration
```

### Coverage Reports

```bash
# Terminal coverage report
pytest --cov=. --cov-report=term-missing

# HTML coverage report (opens in browser)
pytest --cov=. --cov-report=html
# Then open htmlcov/index.html

# Skip fully covered files
pytest --cov=. --cov-report=term:skip-covered
```

### Debugging Tests

```bash
# Stop at first failure
pytest -x

# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb
```

### Performance

```bash
# Show slowest tests
pytest --durations=10

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Organization

### Test Files
- `tests/test_bigquery_client.py` - BigQuery operations
- `tests/test_entity_resolution.py` - Entity matching logic
- `tests/test_gmail_sync.py` - Gmail synchronization
- `tests/test_salesforce_sync.py` - Salesforce synchronization
- `tests/test_integration.py` - End-to-end integration tests
- `tests/test_email_normalizer.py` - Email utilities
- `tests/test_phone_normalizer.py` - Phone utilities
- `tests/test_validation.py` - Input validation
- `tests/test_retry.py` - Retry mechanisms

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests

## Common Issues

### Import Errors
If you see import errors, make sure:
1. Virtual environment is activated
2. Dependencies are installed: `pip install -r requirements.txt -r requirements-dev.txt`
3. You're in the project root directory

### Coverage Not Showing
Make sure pytest-cov is installed:
```bash
pip install pytest-cov
```

### Tests Hanging
- Check for infinite loops in code
- Verify mocks are properly configured
- Use `pytest -x` to stop at first failure

## Best Practices

1. **Write descriptive test names**: `test_validate_email_with_invalid_format` not `test_email`
2. **One assertion per test** (when possible)
3. **Use fixtures** for common setup
4. **Mock external dependencies**
5. **Test edge cases** and error conditions
6. **Keep tests fast** - unit tests should run in milliseconds

## Continuous Integration

For CI/CD pipelines, use:
```bash
pytest --cov=. --cov-report=xml --junitxml=test-results.xml
```

This generates:
- Coverage XML for coverage tools
- JUnit XML for test result reporting

