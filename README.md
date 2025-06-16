# tor-selenium-x

Modern Python project using UV for dependency management and virtual environment.

## 🚀 Quick Start

### Prerequisites

- [UV](https://docs.astral.sh/uv/) - Fast Python package installer and resolver

```bash
# Install UV (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv
```

### Setup

```bash
# Clone and setup
git clone <repository-url>
cd tor-selenium-x

# Install dependencies
uv sync --extra dev
```

### Running

```bash
# Run the main script
uv run src/hello.py

# Or run tests
uv run pytest
```

## 🛠️ Development

### Code Quality Tools

```bash
# Format code (4 spaces, 120 line width, Python defaults)
uv run black src tests

# Sort imports
uv run isort src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src

# Run tests with coverage
uv run pytest
```

### All-in-one command

```bash
# Format, lint, and test everything
uv run black src tests && uv run isort src tests && uv run ruff check src tests && uv run mypy src && uv run pytest
```

## 📦 Dependencies

### Add new dependencies

```bash
# Runtime dependency
uv add requests

# Development dependency  
uv add --dev pytest-mock

# Optional dependency group
uv add --optional selenium "selenium>=4.15.0"
```

### Install optional dependencies

```bash
uv sync --extra selenium
```

## 📁 Project Structure

```
tor-selenium-x/
├── src/
│   └── hello.py           # Main source code
├── tests/
│   ├── __init__.py
│   └── test_hello.py      # Test files
├── .cursor/rules/         # Cursor IDE rules
├── .venv/                 # Virtual environment (auto-created)
├── pyproject.toml         # Project configuration
├── uv.lock               # Dependency lock file
└── README.md
```

## ⚙️ Configuration

All development tools are configured in `pyproject.toml`:

- **Black**: 4 spaces indentation, 120 character line width
- **isort**: Import sorting compatible with Black
- **Ruff**: Fast linting with Python best practices
- **mypy**: Static type checking
- **pytest**: Testing with coverage reporting

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_hello.py

# Run with specific markers
uv run pytest -m unit
uv run pytest -m integration
```

## 📊 Code Style

This project follows Python's default coding standards:

- **Indentation**: 4 spaces (enforced by Black)
- **Line Length**: 120 characters
- **Quote Style**: Double quotes
- **Import Style**: Sorted by isort
- **Type Hints**: Required for all functions

## 🚀 Next Steps

1. Add your code in the `src/` directory
2. Write tests in the `tests/` directory
3. Use `uv add package-name` to add dependencies
4. Run the development tools before committing

Happy coding! 🐍✨
