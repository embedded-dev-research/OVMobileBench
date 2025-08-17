# Contributing to OVMobileBench

Thank you for your interest in contributing to OVMobileBench! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Issues

- Check if the issue already exists
- Include a clear description and steps to reproduce
- Provide system information (OS, Python version, device type)
- Include relevant logs and error messages

### Submitting Pull Requests

1. **Fork and Clone**

   ```bash
   git clone https://github.com/embedded-dev-research/OVMobileBench
   cd OVMobileBench
   ```

2. **Create Branch**

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

3. **Set Up Development Environment**

   ```bash
   pip install -r requirements.txt
   pip install -e .
   pre-commit install
   ```

4. **Make Changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation if needed

5. **Run Quality Checks**

   ```bash
   # Run all pre-commit checks
   pre-commit run --all-files

   # Or run individual checks:
   black --check ovmobilebench tests
   ruff check ovmobilebench tests
   mypy ovmobilebench --ignore-missing-imports
   yamllint .
   markdownlint docs/ *.md

   # Auto-fix issues
   pre-commit run --all-files --hook-stage manual

   # Run tests
   pytest tests/
   ```

6. **Commit Changes**

   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `test:` test changes
   - `refactor:` code refactoring
   - `perf:` performance improvements
   - `ci:` CI/CD changes

7. **Push and Create PR**

   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a Pull Request on GitHub.

## Development Guidelines

### Code Style

- Use Black for formatting (100 char line length)
- Follow PEP 8 with Ruff rules
- Add type hints for all functions
- Write docstrings for public APIs

### Testing

- Write tests for new features
- Maintain test coverage above 70%
- Use pytest fixtures for reusable test data
- Mock external dependencies (ADB, SSH, etc.)

### Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for design changes
- Add docstrings to new modules/classes
- Include examples in documentation

## Project Structure

```
ovmobilebench/
├── cli.py           # CLI commands (Typer)
├── config/          # Configuration schemas (Pydantic)
├── devices/         # Device abstractions
├── builders/        # Build systems
├── packaging/       # Package creation
├── runners/         # Benchmark execution
├── parsers/         # Output parsing
├── report/          # Report generation
└── core/            # Shared utilities
```

## Adding New Features

### Adding a New Device Type

1. Create new class in `ovmobilebench/devices/` inheriting from `Device`
2. Implement all abstract methods
3. Update `pipeline.py` to support a new device type
4. Add tests in `tests/test_devices.py`
5. Update documentation

### Adding a New Report Format

1. Create new sink class in `ovmobilebench/report/`
2. Inherit from `ReportSink` and implement `write()`
3. Update `pipeline.py` to handle a new format
4. Add tests and examples

### Adding New Benchmark Parameters

1. Update `RunMatrix` in `config/schema.py`
2. Modify `_build_command()` in `runners/benchmark.py`
3. Update parser if needed
4. Add tests for new parameters

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. CI will automatically create a release

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions in GitHub Discussions
- Check existing documentation and examples

## License

By contributing, you agree that your contributions will be licensed under Apache License 2.0.
