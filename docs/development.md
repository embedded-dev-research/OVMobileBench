# Development Guide

This guide covers the development setup, tools, and practices for OVMobileBench.

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- Android SDK/NDK (for Android development)
- Docker (optional, for containerized testing)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/embedded-dev-research/OVMobileBench
   cd OVMobileBench
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in editable mode
   ```

4. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

## Code Quality Tools

### Pre-commit Hooks

We use pre-commit to ensure code quality. It runs automatically on `git commit`.

**Included checks:**

- **pyupgrade** - Modernizes Python syntax to 3.11+
- **black** - Code formatting (100 char line length)
- **ruff** - Fast Python linter (replaces flake8, isort, and more)
- **mypy** - Static type checking
- **isort** - Import sorting
- **yamllint** - YAML file linting
- **markdownlint** - Markdown file linting
- **codespell** - Spell checking
- **commitizen** - Commit message validation

### Running Checks Manually

```bash
# Run all checks
pre-commit run --all-files

# Run specific check
pre-commit run black --all-files
pre-commit run ruff --all-files

# Auto-fix issues
pre-commit run --all-files --hook-stage manual

# Run without pre-commit
black ovmobilebench tests
ruff check ovmobilebench tests
mypy ovmobilebench --ignore-missing-imports
pytest tests/
```

### Bypassing Checks (Emergency Only)

```bash
git commit --no-verify -m "Emergency fix"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=ovmobilebench --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::TestConfigLoader::test_load_experiment

# Run with verbose output
pytest tests/ -v

# Run in parallel
pytest tests/ -n auto
```

### Test Structure

```
tests/
├── android/
│   └── installer/     # Android installer tests
├── test_*.py          # Unit tests for each module
├── conftest.py        # Shared fixtures
└── data/              # Test data files
```

### Writing Tests

1. Use pytest fixtures for reusable test data
2. Mock external dependencies (ADB, SSH, file system)
3. Aim for >70% test coverage
4. Test both success and failure cases

Example test:

```python
import pytest
from unittest.mock import Mock, patch

def test_feature():
    # Arrange
    mock_device = Mock()
    mock_device.shell.return_value = "output"

    # Act
    result = process_device(mock_device)

    # Assert
    assert result == "expected"
    mock_device.shell.assert_called_once_with("command")
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI pipeline runs on every push and pull request:

1. **Pre-commit Stage** (Ubuntu only)
   - Runs all linting and formatting checks
   - Fastest stage, fails early on style issues

2. **Test Stage** (Ubuntu, macOS, Windows)
   - Runs unit tests on all platforms
   - Generates coverage reports

3. **Build Stage** (All platforms)
   - Verifies package building
   - Tests installation process

4. **Validation Stage** (All platforms)
   - Validates configuration schemas
   - Tests CLI commands

5. **Device Tests** (When available)
   - Integration tests with real/emulated devices
   - Android emulator tests

### Local CI Testing

Test CI locally using act:

```bash
# Install act
brew install act  # macOS
# or download from https://github.com/nektos/act

# Run CI locally
act push
```

## Code Style Guidelines

### Python

- Use type hints for all function parameters and returns
- Write docstrings for all public functions/classes
- Follow PEP 8 with exceptions defined in `.ruff.toml`
- Maximum line length: 100 characters
- Use f-strings for string formatting
- Prefer pathlib over os.path

### Documentation

- Use Markdown for all documentation
- Include code examples in docstrings
- Keep README.md updated with user-facing changes
- Update ARCHITECTURE.md for design changes

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test changes
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes

Examples:

```bash
git commit -m "feat(android): add AVD creation support"
git commit -m "fix(runner): handle timeout correctly"
git commit -m "docs: update installation guide"
```

## Debugging

### VS Code Configuration

`.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug CLI",
      "type": "python",
      "request": "launch",
      "module": "ovmobilebench",
      "args": ["build", "-c", "experiments/android_example.yaml"],
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm Configuration

1. Create new Python configuration
2. Set module: `ovmobilebench`
3. Set parameters: `build -c experiments/android_example.yaml`
4. Set working directory: project root

### Common Issues

**Import Errors**

```bash
# Reinstall in editable mode
pip install -e .
```

**Type Checking Errors**

```bash
# Install type stubs
pip install types-PyYAML types-paramiko
```

**Pre-commit Failures**

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Clean and reinstall
pre-commit clean
pre-commit install
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release branch: `git checkout -b release/v1.2.3`
4. Run full test suite: `pytest tests/`
5. Create PR to main branch
6. After merge, tag release: `git tag v1.2.3`
7. Push tag: `git push origin v1.2.3`
8. GitHub Actions will automatically publish to PyPI

## Additional Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Pre-commit Hooks](https://pre-commit.com/)
