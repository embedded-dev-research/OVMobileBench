# Changelog

All notable changes to OVMobileBench will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Three flexible OpenVINO distribution modes:
  - **Build mode**: Build OpenVINO from source with custom configurations
  - **Install mode**: Use existing OpenVINO installation directory
  - **Link mode**: Download OpenVINO archives with "latest" auto-detection support
- Automatic platform detection for downloading appropriate OpenVINO builds
- Comprehensive test coverage for new OpenVINO modes
- New documentation: `docs/openvino-modes.md` with detailed usage examples
- Support for `archive_url: "latest"` to automatically fetch the latest OpenVINO build

### Changed

- Configuration schema: `build` section renamed to `openvino` with new `mode` field
- Updated example YAML files to demonstrate all three OpenVINO modes
- Improved configuration documentation with mode-specific examples
- Enhanced pipeline to handle OpenVINO distribution flexibly

### Fixed

- Unified YAML comment formatting across example configurations
- Pre-commit hook compliance for all new code

### Migration Guide

To migrate from the old configuration format:

**Old format:**

```yaml
build:
  enabled: true
  openvino_repo: "/path/to/openvino"
  openvino_commit: "HEAD"
```

**New format:**

```yaml
openvino:
  mode: "build"
  source_dir: "/path/to/openvino"
  commit: "HEAD"
```

## [0.2.0] - 2024-12-15

### Added

- Android SDK/NDK installer module for automated setup
- SSH device support for Linux ARM devices
- Temperature monitoring and performance tuning
- GitHub Actions CI/CD integration
- Comprehensive documentation

### Changed

- Improved device abstraction layer
- Enhanced error handling and reporting
- Updated dependencies to latest versions

### Fixed

- ADB connection stability issues
- Memory leaks in long-running benchmarks
- Report generation for large datasets

## [0.1.0] - 2024-11-01

### Added

- Initial release of OVMobileBench
- Basic pipeline for building, packaging, deploying, and benchmarking
- Support for Android devices via ADB
- JSON and CSV report generation
- Matrix testing capabilities
- Basic documentation and examples

[Unreleased]: https://github.com/embedded-dev-research/OVMobileBench/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/embedded-dev-research/OVMobileBench/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/embedded-dev-research/OVMobileBench/releases/tag/v0.1.0
