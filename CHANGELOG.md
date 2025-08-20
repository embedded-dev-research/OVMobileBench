# Changelog

All notable changes to OVMobileBench will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Three flexible OpenVINO distribution modes**
  - **Build mode**: Build OpenVINO from source with custom configurations
  - **Install mode**: Use existing OpenVINO installation directory
  - **Link mode**: Download OpenVINO archives with "latest" auto-detection support
- **Automatic platform detection** for downloading appropriate OpenVINO builds
- **Comprehensive test coverage** for new OpenVINO modes with 46 new tests
- **New documentation**: `docs/openvino-modes.md` with detailed usage examples
- **Support for `archive_url: "latest"`** to automatically fetch the latest OpenVINO build
- **Enhanced architecture documentation** with Mermaid diagrams
- **Android SDK/NDK installer module** for automated setup
- **SSH device support** for Linux ARM devices using Paramiko
- **Temperature monitoring** and performance tuning capabilities
- **GitHub Actions CI/CD** integration with automated testing
- **Device abstraction layer** supporting Android (ADB) and Linux (SSH)
- **Matrix testing capabilities** for parameter sweep benchmarking
- **JSON and CSV report generation** with detailed metrics
- **Pre-commit hooks** for code quality enforcement
- **Pydantic-based configuration** with strong typing and validation
- **Typer CLI framework** for modern command-line interface
- **Pure Python adbutils** integration (no external ADB binary required)
- **Benchmark result parsing** with detailed metrics extraction
- **Artifact management system** for organized storage of builds and results
- **Custom exception hierarchy** for better error handling
- **Structured logging** with multiple verbosity levels
- **Docker support** for development environment (planned)
- **Web dashboard** for real-time monitoring (planned)

### Changed

- **Configuration schema**: `build` section renamed to `openvino` with new `mode` field
- **Updated example YAML files** to demonstrate all three OpenVINO modes
- **Improved configuration documentation** with mode-specific examples
- **Enhanced pipeline** to handle OpenVINO distribution flexibly
- **Modernized architecture documentation** with professional diagrams
- **Updated pre-commit hooks** to latest versions
- **Improved device abstraction** with pure Python adbutils
- **Enhanced error handling** with custom exception hierarchy
- **Refactored builders** to support multiple platforms
- **Better separation of concerns** in pipeline stages
- **Improved test organization** with dedicated test files per module

### Fixed

- **Unified YAML comment formatting** across example configurations
- **Pre-commit hook compliance** for all new code
- **ADB connection stability** issues on newer Android versions
- **Memory leaks** in long-running benchmarks
- **Report generation** for large datasets
- **SSH timeout issues** on slow network connections
- **CMake cache corruption** on interrupted builds
- **Path handling** for Windows compatibility
- **Unicode handling** in benchmark output parsing
- **Timezone issues** in timestamp generation

### Security

- **No hardcoded credentials** - all secrets via environment variables
- **Input validation** using Pydantic schemas
- **Command injection prevention** with parameterized shell commands
- **Path traversal prevention** in file operations
- **Secure SSH key handling** for Linux devices

### Deprecated

- **Old configuration format** with `build.enabled` field - use `openvino.mode` instead
- **Direct ADB binary calls** - replaced with adbutils Python library
- **Manual device detection** - now automatic with device abstraction layer

### Migration Guide

To migrate from the old configuration format to the new one:

**Old format (deprecated):**

```yaml
build:
  enabled: true
  openvino_repo: "/path/to/openvino"
  openvino_commit: "HEAD"
  build_type: "Release"
```

**New format (current):**

```yaml
openvino:
  mode: "build"  # or "install" or "link"
  source_dir: "/path/to/openvino"
  commit: "HEAD"
  build_type: "Release"
```

### Key Features

- **End-to-end automation**: From build to report generation
- **Multi-platform support**: Android, Linux ARM, iOS (planned)
- **Flexible OpenVINO distribution**: Three modes to suit different workflows
- **Matrix testing**: Comprehensive parameter sweep capabilities
- **Device abstraction**: Uniform interface for different device types
- **Rich reporting**: Multiple output formats with detailed metrics
- **CI/CD ready**: GitHub Actions integration included
- **Extensible architecture**: Plugin system for custom devices and reports
- **Production ready**: Comprehensive testing and error handling

### Supported Platforms

**Host Platforms:**

- Linux (x86_64, ARM64)
- macOS (x86_64, Apple Silicon)
- Windows (x86_64, ARM64)

**Target Devices:**

- Android devices (ARM64, x86_64) via ADB
- Linux ARM devices (Raspberry Pi, Jetson) via SSH
- iOS devices (planned)

**OpenVINO Versions:**

- 2024.x releases
- Nightly builds
- Custom builds from source

### Requirements

- Python 3.11+
- CMake 3.24+ (for build mode)
- Ninja 1.11+ (for build mode)
- Android NDK r26d+ (for Android targets)
- SSH access (for Linux targets)

## Contributors

- Alexander Nesterov (@allnes) - Project Lead
- Community contributors via GitHub

## Links

- [GitHub Repository](https://github.com/embedded-dev-research/OVMobileBench)
- [Documentation](https://github.com/embedded-dev-research/OVMobileBench/tree/main/docs)
- [Issue Tracker](https://github.com/embedded-dev-research/OVMobileBench/issues)
- [Discussions](https://github.com/embedded-dev-research/OVMobileBench/discussions)
