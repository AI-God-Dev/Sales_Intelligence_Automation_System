# Contributing Guidelines

Thank you for your interest in contributing to the Sales Intelligence & Automation System!

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Sales_Intelligence_Automation_System.git
   cd Sales_Intelligence_Automation_System
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   make install-dev
   ```

4. **Setup Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## Code Style

- Follow PEP 8 style guide
- Use Black for code formatting (line length: 100)
- Use isort for import sorting
- Type hints are required for all function signatures
- Docstrings should follow Google style

## Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following the style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Tests**
   ```bash
   make test
   ```

4. **Run Linters**
   ```bash
   make lint
   ```

5. **Format Code**
   ```bash
   make format
   ```

6. **Commit Changes**
   ```bash
   git commit -m "feat: add new feature"
   ```
   
   Use conventional commits:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes
   - `refactor:` Code refactoring
   - `test:` Test additions/changes
   - `chore:` Maintenance tasks

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Testing

- Write unit tests for all new functions
- Aim for >80% code coverage
- Run tests before committing: `make test`
- Integration tests should be in `tests/integration/`

## Pull Request Process

1. Update README.md if needed
2. Update CHANGELOG.md with your changes
3. Ensure all tests pass
4. Ensure code coverage doesn't decrease
5. Request review from maintainers

## Code Review Guidelines

- Be respectful and constructive
- Focus on code quality and maintainability
- Ask questions if something is unclear
- Approve when ready, request changes if needed

## Questions?

Open an issue or contact the maintainers.

