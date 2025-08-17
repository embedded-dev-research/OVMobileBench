# Android Installer Module Documentation

## Overview

The `ovmobilebench.android.installer` module provides a comprehensive Python API for automating the installation and configuration of Android SDK, NDK, and related tools with a modular, type-safe, and well-tested implementation.

## Features

- **Cross-platform support**: Windows, macOS, Linux (x86_64, arm64)
- **Automated SDK/NDK installation**: Downloads and configures Android development tools
- **AVD management**: Create and manage Android Virtual Devices
- **Environment configuration**: Export environment variables for various shells
- **Type safety**: Full type hints and runtime validation
- **Structured logging**: Human-readable and JSON Lines output
- **Idempotent operations**: Safe to run multiple times
- **CI/CD integration**: Optimized for automated environments

## Installation

The module is part of the OVMobileBench package:

```bash
pip install -e .
```

## Quick Start

### Basic Usage

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

print(f"SDK installed at: {result['sdk_root']}")
print(f"NDK installed at: {result['ndk_path']}")
```

### Command Line Interface

```bash
# Install Android tools
ovmobilebench-android-installer setup \
    --sdk-root /path/to/sdk \
    --api 30 \
    --target google_atd \
    --arch arm64-v8a \
    --ndk r26d

# Verify installation
ovmobilebench-android-installer verify --sdk-root /path/to/sdk

# List available targets
ovmobilebench-android-installer list-targets
```

## Module Architecture

### Package Structure

```
ovmobilebench/android/installer/
├── __init__.py         # Package exports
├── api.py              # Public API functions
├── cli.py              # Command-line interface
├── core.py             # Main orchestration logic
├── types.py            # Data models and types
├── errors.py           # Custom exceptions
├── logging.py          # Structured logging
├── detect.py           # Platform detection
├── env.py              # Environment variables
├── plan.py             # Installation planning
├── sdkmanager.py       # SDK management
├── ndk.py              # NDK resolution
└── avd.py              # AVD management
```

### Core Components

#### 1. Types Module (`types.py`)

Defines data models for the installer:

```python
from ovmobilebench.android.installer.types import (
    NdkSpec,           # NDK specification (alias or path)
    AndroidVersion,    # Android API version info
    SystemImageSpec,   # System image specification
    InstallerPlan,     # Installation plan
    InstallerResult,   # Installation result
    HostInfo,          # Host system information
)

# Example: Specify NDK by alias
ndk = NdkSpec(alias="r26d")

# Or by path
ndk = NdkSpec(path="/opt/android-ndk-r26d")
```

#### 2. Core Module (`core.py`)

Main orchestration class:

```python
from ovmobilebench.android.installer.core import AndroidInstaller

installer = AndroidInstaller(sdk_root="/path/to/sdk")

# Perform installation
result = installer.ensure(
    api=30,
    target="google_atd",
    arch="arm64-v8a",
    ndk=NdkSpec(alias="r26d"),
    create_avd_name="my_avd",
    install_build_tools="34.0.0",
    accept_licenses=True,
    dry_run=False
)

# Verify installation
status = installer.verify()

# Clean up temporary files
installer.cleanup(remove_downloads=True, remove_temp=True)
```

#### 3. SDK Manager (`sdkmanager.py`)

Wraps Android SDK Manager:

```python
from ovmobilebench.android.installer.sdkmanager import SdkManager

sdk = SdkManager(sdk_root="/path/to/sdk")

# Install components
sdk.ensure_cmdline_tools()
sdk.ensure_platform_tools()
sdk.ensure_platform(api=30)
sdk.ensure_system_image(api=30, target="google_atd", arch="arm64-v8a")
sdk.ensure_emulator()
sdk.ensure_build_tools("34.0.0")

# Accept licenses
sdk.accept_licenses()

# List installed components
components = sdk.list_installed()
```

#### 4. NDK Resolver (`ndk.py`)

Manages NDK installations:

```python
from ovmobilebench.android.installer.ndk import NdkResolver

ndk = NdkResolver(sdk_root="/path/to/sdk")

# Install NDK
ndk_path = ndk.ensure(NdkSpec(alias="r26d"))

# List installed NDKs
installed = ndk.list_installed()
for version, path in installed:
    print(f"NDK {version}: {path}")
```

#### 5. AVD Manager (`avd.py`)

Creates and manages Android Virtual Devices:

```python
from ovmobilebench.android.installer.avd import AvdManager

avd = AvdManager(sdk_root="/path/to/sdk")

# Create AVD
avd.create(
    name="test_avd",
    api=30,
    target="google_atd",
    arch="arm64-v8a",
    device="pixel_5"
)

# List AVDs
avds = avd.list()

# Get AVD info
info = avd.get_info("test_avd")

# Delete AVD
avd.delete("test_avd")
```

#### 6. Environment Exporter (`env.py`)

Manages environment variables:

```python
from ovmobilebench.android.installer.env import EnvExporter

env = EnvExporter(sdk_root="/path/to/sdk")

# Export to dictionary
env_dict = env.export_dict(ndk_path="/path/to/ndk")

# Export to shell script
env.export_to_stdout(ndk_path="/path/to/ndk", format="bash")

# Export to GitHub Actions
env.export_to_github_env(ndk_path="/path/to/ndk")

# Set in current process
env.set_in_process(ndk_path="/path/to/ndk")
```

#### 7. Platform Detection (`detect.py`)

Detects host system capabilities:

```python
from ovmobilebench.android.installer.detect import (
    detect_host,
    detect_java_version,
    check_disk_space,
    is_ci_environment,
    get_recommended_settings
)

# Detect host system
host = detect_host()
print(f"OS: {host.os}, Arch: {host.arch}, KVM: {host.has_kvm}")

# Check Java
java_version = detect_java_version()

# Check disk space
has_space = check_disk_space("/path/to/sdk", required_gb=15)

# Get recommendations
settings = get_recommended_settings()
```

#### 8. Installation Planning (`plan.py`)

Plans and validates installations:

```python
from ovmobilebench.android.installer.plan import Planner

planner = Planner(sdk_root="/path/to/sdk")

# Build installation plan
plan = planner.build_plan(
    api=30,
    target="google_atd",
    arch="arm64-v8a",
    ndk=NdkSpec(alias="r26d"),
    create_avd_name="test_avd"
)

# Validate plan
is_valid = planner.is_valid_combination(api=30, target="google_atd", arch="arm64-v8a")

# Estimate size
size_gb = planner.estimate_size(plan)
```

#### 9. Structured Logging (`logging.py`)

Provides structured logging with timing:

```python
from ovmobilebench.android.installer.logging import StructuredLogger

logger = StructuredLogger(
    name="installer",
    verbose=True,
    jsonl_path="/tmp/install.jsonl"
)

# Log with context
logger.info("Starting installation", api=30, arch="arm64-v8a")

# Track steps with timing
with logger.step("install_ndk", version="r26d"):
    # Installation code here
    pass  # Step duration is automatically tracked

logger.success("Installation complete", duration=45.2)
```

## API Reference

### Public Functions

#### `ensure_android_tools()`

Main function for installing Android tools.

```python
def ensure_android_tools(
    sdk_root: str | Path,
    api: int,
    target: str = "google_atd",
    arch: str = "arm64-v8a",
    ndk: str | Path | NdkSpec | None = None,
    create_avd_name: str | None = None,
    install_platform_tools: bool = True,
    install_emulator: bool = True,
    install_build_tools: str | None = None,
    accept_licenses: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
    jsonl_path: Path | None = None
) -> InstallerResult
```

**Parameters:**
- `sdk_root`: Android SDK installation directory
- `api`: Android API level (e.g., 30, 31, 33)
- `target`: System image target ("google_atd", "google_apis", "default")
- `arch`: Architecture ("arm64-v8a", "x86_64", "x86", "armeabi-v7a")
- `ndk`: NDK specification (alias like "r26d" or absolute path)
- `create_avd_name`: Name for AVD creation (None to skip)
- `install_platform_tools`: Install ADB and platform tools
- `install_emulator`: Install Android Emulator
- `install_build_tools`: Build tools version (e.g., "34.0.0")
- `accept_licenses`: Automatically accept SDK licenses
- `dry_run`: Preview without making changes
- `verbose`: Enable detailed logging
- `jsonl_path`: Path for JSON Lines log output

**Returns:**
`InstallerResult` dictionary with:
- `sdk_root`: SDK installation path
- `ndk_path`: NDK installation path (if installed)
- `avd_created`: Whether AVD was created
- `performed`: Dictionary of performed actions

#### `export_android_env()`

Export Android environment variables.

```python
def export_android_env(
    sdk_root: str | Path,
    ndk_path: str | Path | None = None,
    format: str = "dict"
) -> dict[str, str] | str
```

**Parameters:**
- `sdk_root`: Android SDK root directory
- `ndk_path`: NDK installation path
- `format`: Output format ("dict", "bash", "fish", "windows", "github")

**Returns:**
Environment variables as dictionary or formatted string

#### `verify_installation()`

Verify Android tools installation.

```python
def verify_installation(
    sdk_root: str | Path,
    verbose: bool = True
) -> dict[str, Any]
```

**Parameters:**
- `sdk_root`: Android SDK root directory
- `verbose`: Print verification results

**Returns:**
Dictionary with installation status

## Usage Examples

### Example 1: CI/CD Installation

```python
import os
from ovmobilebench.android.installer import ensure_android_tools

# Minimal installation for CI
result = ensure_android_tools(
    sdk_root=os.environ.get("ANDROID_HOME", "/opt/android-sdk"),
    api=30,
    target="google_atd",
    arch="arm64-v8a",
    ndk="r26d",
    create_avd_name=None,  # No AVD in CI
    install_emulator=False,  # No emulator needed
    dry_run=False
)

# Export environment for build
from ovmobilebench.android.installer import export_android_env

env_vars = export_android_env(
    sdk_root=result["sdk_root"],
    ndk_path=result["ndk_path"],
    format="github"  # For GitHub Actions
)
```

### Example 2: Development Setup

```python
from pathlib import Path
from ovmobilebench.android.installer import (
    ensure_android_tools,
    verify_installation
)

# Full installation for development
home = Path.home()
sdk_root = home / "Android" / "sdk"

result = ensure_android_tools(
    sdk_root=sdk_root,
    api=33,
    target="google_apis",
    arch="arm64-v8a",
    ndk="r26d",
    create_avd_name="dev_phone",
    install_build_tools="34.0.0",
    verbose=True,
    jsonl_path=home / "android_install.jsonl"
)

# Verify everything is installed
status = verify_installation(sdk_root, verbose=True)
```

### Example 3: NDK-Only Installation

```python
from ovmobilebench.android.installer import ensure_android_tools

# Install only NDK for cross-compilation
result = ensure_android_tools(
    sdk_root="/opt/android-sdk",
    api=30,  # Required for planning
    target="default",
    arch="arm64-v8a",
    ndk="r26d",
    install_platform_tools=False,
    install_emulator=False,
    create_avd_name=None
)

print(f"NDK installed at: {result['ndk_path']}")
```

### Example 4: Dry Run Planning

```python
from ovmobilebench.android.installer import ensure_android_tools

# Preview what would be installed
result = ensure_android_tools(
    sdk_root="/opt/android-sdk",
    api=30,
    target="google_atd",
    arch="x86_64",
    ndk="r26d",
    create_avd_name="test_avd",
    dry_run=True,
    verbose=True
)

print("Would install:", result["performed"])
```

## Supported Platforms

### Host Operating Systems
- **Linux**: x86_64, arm64 (Ubuntu 20.04+, RHEL 8+)
- **macOS**: x86_64, arm64 (macOS 11+)
- **Windows**: x86_64 (Windows 10+)

### Android API Levels
- API 21-34 (Android 5.0 - 14)

### System Image Targets
- `default`: Basic Android system image
- `google_apis`: Includes Google Play Services
- `google_atd`: Automated Test Device (faster, for testing)
- `google_apis_playstore`: Includes Play Store

### Architectures
- `arm64-v8a`: 64-bit ARM (recommended for M1/M2 Macs)
- `armeabi-v7a`: 32-bit ARM
- `x86_64`: 64-bit x86 (recommended for Intel with KVM)
- `x86`: 32-bit x86

### NDK Versions
- Aliases: r21e, r22b, r23c, r24, r25c, r26d
- Direct versions: 21.4.7075529, 22.1.7171670, etc.

## Environment Variables

The module sets the following environment variables:

- `ANDROID_HOME`: Android SDK root directory
- `ANDROID_SDK_ROOT`: Same as ANDROID_HOME
- `ANDROID_NDK_HOME`: NDK installation directory
- `ANDROID_NDK_ROOT`: Same as ANDROID_NDK_HOME
- `PATH`: Updated with platform-tools, emulator, and NDK paths

## Error Handling

The module provides a hierarchy of custom exceptions:

```python
from ovmobilebench.android.installer.errors import (
    InstallerError,           # Base exception
    InvalidArgumentError,     # Invalid parameters
    ComponentNotFoundError,   # Missing component
    DownloadError,           # Download failure
    UnpackError,             # Extraction failure
    SdkManagerError,         # SDK Manager error
    AvdManagerError,         # AVD Manager error
    PermissionError,         # Permission denied
)

try:
    result = ensure_android_tools(...)
except InvalidArgumentError as e:
    print(f"Invalid configuration: {e}")
except DownloadError as e:
    print(f"Download failed: {e}")
except InstallerError as e:
    print(f"Installation failed: {e}")
```

## Logging

The module supports multiple logging modes:

### Console Logging
```python
# Verbose console output
ensure_android_tools(..., verbose=True)
```

### JSON Lines Logging
```python
# Structured logging to file
ensure_android_tools(..., jsonl_path="/tmp/install.jsonl")

# Parse logs
import json
with open("/tmp/install.jsonl") as f:
    for line in f:
        log = json.loads(line)
        print(f"{log['timestamp']}: {log['message']}")
```

### Custom Logger
```python
from ovmobilebench.android.installer.logging import StructuredLogger
from ovmobilebench.android.installer import set_logger

# Use custom logger
logger = StructuredLogger("custom", verbose=True)
set_logger(logger)

ensure_android_tools(...)
```

## Best Practices

### 1. Use Dry Run First
Always test with `dry_run=True` before actual installation:

```python
# Test configuration
result = ensure_android_tools(..., dry_run=True)
if result["performed"]:
    # Proceed with actual installation
    result = ensure_android_tools(..., dry_run=False)
```

### 2. Verify After Installation
Always verify the installation succeeded:

```python
result = ensure_android_tools(...)
status = verify_installation(result["sdk_root"])
assert status["cmdline_tools"], "Missing cmdline-tools"
assert status["ndk"], "Missing NDK"
```

### 3. Handle Errors Gracefully
Wrap installations in try-except blocks:

```python
try:
    result = ensure_android_tools(...)
except PermissionError:
    print("Run with elevated permissions")
except DownloadError:
    print("Check network connection")
```

### 4. Use Appropriate Targets
- Use `google_atd` for CI/testing (faster)
- Use `google_apis` for development
- Use `google_apis_playstore` for Play Store testing

### 5. Clean Up Temporary Files
Remove downloads after installation:

```python
from ovmobilebench.android.installer.core import AndroidInstaller

installer = AndroidInstaller(sdk_root)
result = installer.ensure(...)
installer.cleanup(remove_downloads=True)
```

## Troubleshooting

### Common Issues

#### 1. SSL Certificate Errors
```
DownloadError: certificate verify failed
```
**Solution**: Update certificates or use corporate proxy settings

#### 2. Permission Denied
```
PermissionError: Permission denied: /opt/android-sdk
```
**Solution**: Ensure write permissions or use user directory

#### 3. Disk Space
```
Warning: Low disk space detected (< 15GB free)
```
**Solution**: Free up space or use different location

#### 4. Java Not Found
```
Warning: Java not detected
```
**Solution**: Install JDK 11+ and ensure it's in PATH

#### 5. KVM Not Available
```
Info: KVM not available, using software acceleration
```
**Solution**: Enable virtualization in BIOS or use ARM images on ARM hosts

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

result = ensure_android_tools(
    ...,
    verbose=True,
    jsonl_path="/tmp/debug.jsonl"
)
```

## Integration with OVMobileBench

The module integrates with OVMobileBench pipeline:

```yaml
# experiments/android_example.yaml
build:
  android_ndk: r26d
  android_api: 30

device:
  type: android
  platform: arm64-v8a
```

The pipeline automatically uses this module to ensure NDK is installed before building.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## License

Apache License 2.0. See [LICENSE](../LICENSE) for details.