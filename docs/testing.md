# Testing Guide

## Overview

OVMobileBench uses pytest for testing with comprehensive coverage across all modules. The test suite is organized to mirror the source code structure for easy navigation and maintenance.

## Test Organization

The test suite is structured by functional modules:

```
tests/
├── android/           # Android-specific functionality
│   └── installer/     # Android SDK/NDK installer module
├── builders/          # OpenVINO build system
├── cli/               # Command-line interface
├── config/            # Configuration and validation
├── core/              # Core utilities
├── devices/           # Device abstraction layer
├── packaging/         # Bundle creation and packaging
├── parsers/           # Output parsing
├── pipeline/          # Pipeline orchestration
├── report/            # Report generation
└── runners/           # Benchmark execution
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific module
pytest tests/config/
pytest tests/devices/
pytest tests/pipeline/

# Run specific test file
pytest tests/config/test_openvino_config.py

# Run specific test class
pytest tests/config/test_openvino_config.py::TestOpenVINOConfig

# Run specific test method
pytest tests/config/test_openvino_config.py::TestOpenVINOConfig::test_build_mode_valid
```

### Coverage Analysis

```bash
# Run with coverage report
pytest tests/ --cov=ovmobilebench --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=ovmobilebench --cov-report=html
open htmlcov/index.html

# Coverage for specific modules
pytest tests/ --cov=ovmobilebench.config --cov=ovmobilebench.pipeline

# Branch coverage
pytest tests/ --cov=ovmobilebench --cov-branch
```

### Test Selection

```bash
# Run only fast tests (exclude slow)
pytest tests/ -m "not slow"

# Run only unit tests
pytest tests/ -m unit

# Run integration tests
pytest tests/ -m integration

# Skip specific tests
pytest tests/ --ignore=tests/android/installer/

# Run failed tests from last run
pytest tests/ --lf

# Run tests that match a pattern
pytest tests/ -k "openvino"
```

### Output Options

```bash
# Quiet mode (minimal output)
pytest tests/ -q

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l

# Show top 10 slowest tests
pytest tests/ --durations=10
```

## Test Categories

### Configuration Tests (`tests/config/`)

Testing configuration loading, validation, and schema enforcement:

- **test_config.py**: Main experiment configuration
- **test_config_loader.py**: YAML loading and environment variables
- **test_device_config.py**: Device configuration validation
- **test_openvino_config.py**: OpenVINO modes (build/install/link)

### Device Tests (`tests/devices/`)

Testing device abstraction and operations:

- **test_android_device.py**: Android device via ADB
- **test_android_device_complete.py**: Extended Android functionality
- **test_ssh_device.py**: Linux SSH device operations
- **test_devices.py**: Device factory and abstraction

### Pipeline Tests (`tests/pipeline/`)

Testing pipeline orchestration and stages:

- **test_pipeline.py**: Main pipeline flow
- **test_pipeline_openvino_modes.py**: OpenVINO distribution modes

### Core Tests (`tests/core/`)

Testing utility functions and helpers:

- **test_core_artifacts.py**: Artifact management
- **test_core_fs.py**: File system operations
- **test_core_logging.py**: Structured logging
- **test_core_shell.py**: Shell command execution

### Builder Tests (`tests/builders/`)

Testing build system integration:

- **test_builders_openvino.py**: OpenVINO cross-compilation

### Packaging Tests (`tests/packaging/`)

Testing bundle creation:

- **test_packaging_packager.py**: Archive creation and management

### Runner Tests (`tests/runners/`)

Testing benchmark execution:

- **test_runners_benchmark.py**: Matrix expansion and execution

### Parser Tests (`tests/parsers/`)

Testing output parsing:

- **test_parser.py**: Benchmark output parsing

### Report Tests (`tests/report/`)

Testing report generation:

- **test_report_sink.py**: JSON/CSV output generation

### CLI Tests (`tests/cli/`)

Testing command-line interface:

- **test_cli.py**: CLI commands and options
- **test_typer_patch.py**: Typer framework extensions

## Writing Tests

### Test Structure

Follow these conventions:

1. **File naming**: `test_<module>_<component>.py`
2. **Class naming**: `Test<ComponentName>`
3. **Method naming**: `test_<functionality>_<scenario>`
4. **Docstrings**: Brief description of what's being tested

### Example Test

```python
"""Tests for OpenVINO configuration."""

import pytest
from pydantic import ValidationError

from ovmobilebench.config.schema import OpenVINOConfig


class TestOpenVINOConfig:
    """Test OpenVINO configuration validation."""

    def test_build_mode_valid(self):
        """Test valid build mode configuration."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            commit="HEAD",
            build_type="Release"
        )
        assert config.mode == "build"
        assert config.source_dir == "/path/to/openvino"

    def test_build_mode_missing_source_dir(self):
        """Test build mode without required source_dir."""
        with pytest.raises(ValidationError) as exc_info:
            OpenVINOConfig(mode="build")

        assert "source_dir is required" in str(exc_info.value)

    @pytest.mark.parametrize("mode,field", [
        ("build", "source_dir"),
        ("install", "install_dir"),
        ("link", "archive_url"),
    ])
    def test_mode_required_fields(self, mode, field):
        """Test that each mode requires its specific field."""
        with pytest.raises(ValidationError):
            OpenVINOConfig(mode=mode)
```

### Using Fixtures

```python
import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_config():
    """Create mock experiment configuration."""
    config = Mock()
    config.project.name = "test"
    config.project.run_id = "test-123"
    config.openvino.mode = "build"
    config.device.kind = "android"
    return config


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for testing."""
    test_dir = tmp_path / "test_workspace"
    test_dir.mkdir()
    return test_dir


class TestPipeline:
    """Test pipeline orchestration."""

    def test_build_mode(self, mock_config, temp_dir):
        """Test pipeline with build mode."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure:
            mock_ensure.return_value = temp_dir

            pipeline = Pipeline(mock_config)
            result = pipeline.build()

            assert result.exists()
```

### Mocking Best Practices

```python
# Mock external dependencies
@patch("ovmobilebench.devices.android.AdbClient")
def test_android_device(mock_adb):
    """Test Android device operations."""
    mock_device = Mock()
    mock_adb.return_value.device.return_value = mock_device

    device = AndroidDevice("serial123")
    device.push("local.txt", "/remote/path")

    mock_device.push.assert_called_once()

# Mock file operations
@patch("pathlib.Path.exists")
@patch("pathlib.Path.mkdir")
def test_ensure_dir(mock_mkdir, mock_exists):
    """Test directory creation."""
    mock_exists.return_value = False

    ensure_dir("/test/path")

    mock_mkdir.assert_called_once()
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_long_running_operation():
    """Test that takes more than 5 seconds."""
    pass

@pytest.mark.unit
def test_unit_functionality():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_integration_scenario():
    """Test requiring multiple components."""
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Linux only")
def test_linux_specific():
    """Test for Linux platform only."""
    pass
```

## Coverage Requirements

### Target Coverage

- **Overall**: 80%+ coverage
- **Critical modules**: 90%+ coverage
  - `ovmobilebench.config`
  - `ovmobilebench.pipeline`
  - `ovmobilebench.devices`

### Checking Coverage

```bash
# Check current coverage
pytest tests/ --cov=ovmobilebench --cov-report=term

# Find uncovered lines
pytest tests/ --cov=ovmobilebench --cov-report=term-missing

# Fail if coverage below threshold
pytest tests/ --cov=ovmobilebench --cov-fail-under=80
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:

- Pull requests
- Push to main branch
- Scheduled nightly runs

Configuration in `.github/workflows/test.yml`:

```yaml
- name: Run tests
  run: |
    pytest tests/ --cov=ovmobilebench --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Pre-commit Hooks

Tests can be run before commit:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest tests/ -x
      language: system
      pass_filenames: false
      always_run: true
```

## Debugging Tests

### Using pdb

```python
def test_complex_logic():
    """Test with debugging."""
    import pdb; pdb.set_trace()
    # Code to debug
```

Run with:

```bash
pytest tests/ -s  # Don't capture output
```

### Verbose Failure Output

```bash
# Show full diff
pytest tests/ -vv

# Show local variables
pytest tests/ -l

# Show full traceback
pytest tests/ --tb=long
```

### Test Isolation

```python
# Use tmp_path fixture for file operations
def test_file_operation(tmp_path):
    """Test with isolated file system."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    assert test_file.exists()
    # tmp_path is automatically cleaned up
```

## Performance Testing

### Benchmarking

```python
@pytest.mark.benchmark
def test_performance(benchmark):
    """Test performance of operation."""
    result = benchmark(expensive_operation, arg1, arg2)
    assert result == expected
```

Run benchmarks:

```bash
pytest tests/ --benchmark-only
pytest tests/ --benchmark-compare
```

### Profiling

```bash
# Profile test execution
pytest tests/ --profile

# Generate call graph
pytest tests/ --profile-svg
```

## Test Data

### Using Fixtures for Test Data

```python
@pytest.fixture
def sample_yaml():
    """Sample YAML configuration."""
    return """
    project:
      name: test
      run_id: test-123
    openvino:
      mode: build
      source_dir: /test/path
    """

def test_config_loading(sample_yaml, tmp_path):
    """Test configuration loading."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(sample_yaml)

    config = load_config(config_file)
    assert config.project.name == "test"
```

### Parametrized Test Data

```python
@pytest.mark.parametrize("input,expected", [
    ("1.5K", 1536),
    ("2.5M", 2621440),
    ("1.2G", 1288490188),
])
def test_parse_size(input, expected):
    """Test size parsing."""
    assert parse_size(input) == expected
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure PYTHONPATH includes project root

   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Missing dependencies**: Install test requirements

   ```bash
   pip install -e ".[test]"
   ```

3. **Flaky tests**: Use retry mechanism

   ```python
   @pytest.mark.flaky(reruns=3)
   def test_network_operation():
       pass
   ```

4. **Slow tests**: Mark and skip in CI

   ```python
   @pytest.mark.slow
   @pytest.mark.skipif(os.getenv("CI"), reason="Skip slow tests in CI")
   def test_slow_operation():
       pass
   ```

## Best Practices

1. **Keep tests fast**: Mock external dependencies
2. **Test one thing**: Each test should verify single behavior
3. **Use descriptive names**: Test names should explain what's tested
4. **Avoid test interdependence**: Tests should run in any order
5. **Use fixtures**: Share setup code via fixtures
6. **Assert specific errors**: Check error messages, not just exceptions
7. **Clean up resources**: Use context managers and fixtures
8. **Document complex tests**: Add comments for non-obvious logic
