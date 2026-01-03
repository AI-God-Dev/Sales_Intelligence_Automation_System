# Contributing Guidelines

Thank you for your interest in contributing to the Sales Intelligence & Automation System!

## Getting Started

### Prerequisites
- Python 3.11+
- Google Cloud SDK
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Sales_Intelligence_Automation_System.git
cd Sales_Intelligence_Automation_System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### 2. Make Changes

Follow these guidelines:
- Write clean, readable code
- Add type hints to all functions
- Write docstrings (Google style)
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

```bash
# Run tests
pytest

# Run linting
make lint

# Format code
make format
```

### 4. Commit Changes

Use conventional commits:

```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in X"
git commit -m "docs: update README"
```

Commit types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance

### 5. Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub.

## Code Style

### Python
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use isort for imports
- Type hints required

### Example

```python
def process_account(
    account_id: str,
    options: dict[str, Any] | None = None
) -> AccountResult:
    """Process an account for scoring.
    
    Args:
        account_id: The Salesforce account ID.
        options: Optional processing options.
        
    Returns:
        AccountResult with score and recommendations.
        
    Raises:
        ValueError: If account_id is invalid.
    """
    if not validate_account_id(account_id):
        raise ValueError(f"Invalid account ID: {account_id}")
    
    # Implementation...
```

## Testing

### Requirements
- Write tests for all new functionality
- Maintain 80%+ coverage
- Use pytest fixtures

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=.

# Specific file
pytest tests/test_file.py

# Specific test
pytest tests/test_file.py::test_function
```

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/            # End-to-end tests
└── fixtures/       # Test data
```

## Documentation

### When to Update
- Adding new features
- Changing existing behavior
- Adding new configuration options
- Modifying API endpoints

### Documentation Structure

```
docs/
├── setup/          # Setup and configuration
├── architecture/   # System design
├── operations/     # Runbooks
└── user-guides/    # End-user docs
```

## Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No secrets or credentials committed
- [ ] Branch is up to date with main

## Getting Help

- Open an issue for bugs or questions
- Check existing issues before creating new ones
- Use discussions for general questions

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to build great software.
