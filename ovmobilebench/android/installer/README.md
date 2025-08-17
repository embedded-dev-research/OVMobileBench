# Android Installer Module

A comprehensive Python module for automated installation and management of Android SDK, NDK, and related tools.

## Quick Start

```python
from ovmobilebench.android.installer import ensure_android_tools

# Install Android SDK and NDK
result = ensure_android_tools(
    sdk_root="/path/to/android-sdk",
    api=30,
    target="google_atd",
    arch="arm64-v8a",
    ndk="r26d"
)
```

## Features

- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ Automated SDK/NDK installation
- ✅ AVD (Android Virtual Device) management
- ✅ Environment variable configuration
- ✅ Type-safe with full type hints
- ✅ Structured logging with JSON Lines support
- ✅ Idempotent operations
- ✅ CI/CD optimized

## Documentation

See [full documentation](../../../docs/android_installer.md) for detailed API reference and examples.

## Module Structure

```
installer/
├── api.py              # Public API functions
├── cli.py              # Command-line interface
├── core.py             # Main orchestration
├── types.py            # Data models
├── errors.py           # Custom exceptions
├── logging.py          # Structured logging
├── detect.py           # Platform detection
├── env.py              # Environment variables
├── plan.py             # Installation planning
├── sdkmanager.py       # SDK management
├── ndk.py              # NDK resolution
└── avd.py              # AVD management
```

## Command Line Usage

```bash
# Install Android tools
ovmobilebench-android-installer setup \
    --sdk-root /path/to/sdk \
    --api 30 \
    --ndk r26d

# Verify installation
ovmobilebench-android-installer verify --sdk-root /path/to/sdk

# List available targets
ovmobilebench-android-installer list-targets
```

## Testing

The module includes comprehensive test coverage:

```bash
# Run all tests
pytest tests/android/installer/ -v

# Run with coverage
pytest tests/android/installer/ --cov=ovmobilebench.android.installer

# Current test status: 217 passed, 16 skipped
```

## Requirements

- Python 3.8+
- Internet connection for downloads
- ~15GB free disk space for full installation
- Java 11+ (for Android tools)

## Supported Configurations

### NDK Versions
- r21e, r22b, r23c, r24, r25c, r26d

### Android API Levels
- API 21-34 (Android 5.0 - 14)

### Architectures
- arm64-v8a (64-bit ARM)
- armeabi-v7a (32-bit ARM)
- x86_64 (64-bit x86)
- x86 (32-bit x86)

### System Image Targets
- default (Basic Android)
- google_apis (With Google Play Services)
- google_atd (Automated Test Device)
- google_apis_playstore (With Play Store)

## License

Apache License 2.0
