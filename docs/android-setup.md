# Android SDK/NDK Setup Guide

This guide explains how to install Android SDK and NDK for building and running OVMobileBench on Android devices.

## Automated Installation

The `ovmobilebench.android.installer` module provides a robust, type-safe, and well-tested solution for Android SDK/NDK installation.

### Prerequisites

- Python 3.8 or higher
- ~15GB of free disk space
- Internet connection for downloading tools
- Java 11+ (for Android tools)

### Python API

```python
from ovmobilebench.android import ensure_android_tools

# Install Android SDK and NDK
result = ensure_android_tools(
    sdk_root="~/android-sdk",
    api=30,
    target="google_atd",
    arch="arm64-v8a",
    ndk="r26d",
    verbose=True
)

print(f"SDK installed at: {result['sdk_root']}")
print(f"NDK installed at: {result['ndk_path']}")
```

### Command Line Interface

```bash
# Install Android SDK and NDK
ovmobilebench-android-installer setup \
    --sdk-root ~/android-sdk \
    --api 30 \
    --target google_atd \
    --arch arm64-v8a \
    --ndk r26d

# Verify installation
ovmobilebench-android-installer verify --sdk-root ~/android-sdk

# List available targets
ovmobilebench-android-installer list-targets
```

### Key Features

- ✅ Type-safe with full type hints
- ✅ Comprehensive error handling
- ✅ Dry-run mode for testing
- ✅ Structured logging with JSON Lines support
- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ Idempotent operations (safe to run multiple times)
- ✅ AVD (Android Virtual Device) management
- ✅ Environment variable export in multiple formats

For complete documentation, see [Android Installer Module Documentation](android_installer.md).

### Installation Options

#### Custom Installation Directory

```bash
ovmobilebench-android-installer setup \
    --sdk-root /path/to/install \
    --api 30 \
    --ndk r26d
```

#### Install Only NDK (without SDK)

If you only need NDK for building OpenVINO:

```bash
ovmobilebench-android-installer setup \
    --sdk-root ~/android-sdk \
    --api 30 \
    --ndk r26d \
    --no-platform-tools \
    --no-emulator
```

#### Specify Versions

Install specific versions:

```bash
# Specific NDK version
ovmobilebench-android-installer setup \
    --sdk-root ~/android-sdk \
    --api 30 \
    --ndk r26d \
    --build-tools 34.0.0
```

#### Dry Run Mode

Preview what would be installed without making changes:

```bash
ovmobilebench-android-installer setup \
    --sdk-root ~/android-sdk \
    --api 30 \
    --ndk r26d \
    --dry-run
```

### What Gets Installed

**Full Installation (default):**
- Android SDK Command Line Tools
- Android SDK Platform Tools (includes `adb`)
- Android SDK Build Tools
- Android Platform API
- Android NDK
- System Images (for emulator)
- Android Emulator (optional)

**NDK-Only Installation:**
- Android SDK Command Line Tools (required)
- Android NDK

### Platform-Specific Details

#### Windows
- Downloads Windows-specific packages
- Installs to `%USERPROFILE%\android-sdk` by default
- Uses `.bat` scripts for SDK manager

#### macOS
- Downloads macOS-specific packages (supports both Intel and Apple Silicon)
- Installs to `~/android-sdk` by default
- Handles DMG extraction for NDK

#### Linux
- Downloads Linux-specific packages
- Installs to `~/android-sdk` by default
- Works on x86_64 and ARM64 architectures

### Environment Setup

After installation, export environment variables using the module:

```python
from ovmobilebench.android import export_android_env

# Get environment variables
env = export_android_env(
    sdk_root="~/android-sdk",
    ndk_path="~/android-sdk/ndk/26.3.11579264",
    format="bash"  # or "fish", "windows", "github"
)
print(env)
```

Or use the CLI to generate export commands:

```bash
# For bash/zsh
ovmobilebench-android-installer export-env \
    --sdk-root ~/android-sdk \
    --ndk-path ~/android-sdk/ndk/26.3.11579264 \
    --format bash >> ~/.bashrc

# For fish shell
ovmobilebench-android-installer export-env \
    --sdk-root ~/android-sdk \
    --ndk-path ~/android-sdk/ndk/26.3.11579264 \
    --format fish >> ~/.config/fish/config.fish

# For Windows PowerShell
ovmobilebench-android-installer export-env `
    --sdk-root C:\android-sdk `
    --ndk-path C:\android-sdk\ndk\26.3.11579264 `
    --format windows
```

The module sets the following environment variables:
- `ANDROID_HOME` - Android SDK root directory
- `ANDROID_SDK_ROOT` - Same as ANDROID_HOME
- `ANDROID_NDK_HOME` - NDK installation directory
- `ANDROID_NDK_ROOT` - Same as ANDROID_NDK_HOME
- `PATH` - Updated with platform-tools and cmdline-tools

### Verification

After installation and environment setup, verify the installation:

```bash
# Check ADB
adb version

# Check NDK
ls $ANDROID_NDK_ROOT/ndk-build  # Linux/macOS
dir %ANDROID_NDK_ROOT%\ndk-build.cmd  # Windows

# List connected Android devices
adb devices
```

### Manual Installation

If you prefer manual installation or the script doesn't work for your system:

#### Android SDK

1. Download command line tools from [Android Developer site](https://developer.android.com/studio#command-tools)
2. Extract to a directory (e.g., `~/android-sdk/cmdline-tools/latest`)
3. Accept licenses: `sdkmanager --licenses`
4. Install platform tools: `sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"`

#### Android NDK

1. Download NDK from [Android NDK Downloads](https://developer.android.com/ndk/downloads)
2. Extract to a directory (e.g., `~/android-sdk/ndk/r26d`)
3. Set `ANDROID_NDK_ROOT` environment variable

### Troubleshooting

#### Permission Denied (Linux/macOS)

If you get permission errors, make sure the script is executable:

```bash
chmod +x scripts/setup_android_tools.py
```

#### Download Failures

If downloads fail, you can:
1. Try again (the script caches partial downloads)
2. Use a VPN if you're in a region with restricted access
3. Download files manually and place them in the installation directory

#### SDK Manager Issues

If `sdkmanager` fails to install packages:
1. Make sure you have Java 11 or higher installed
2. Accept all licenses manually: `sdkmanager --licenses`
3. Check proxy settings if behind a corporate firewall

#### ADB Connection Issues

If `adb devices` doesn't show your device:
1. Enable USB debugging on your Android device
2. Install device drivers (Windows)
3. Add udev rules (Linux):
   ```bash
   echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-android.rules
   sudo udevadm control --reload-rules
   ```

### Using with OVMobileBench

Once Android tools are installed, you can use them with OVMobileBench:

1. **List connected devices:**
   ```bash
   ovmobilebench list-devices
   ```

2. **Build OpenVINO for Android:**
   Configure your experiment YAML with the NDK path:
   ```yaml
   build:
     toolchain:
       android_ndk: "~/android-sdk/ndk/r26d"
       abi: "arm64-v8a"
       api_level: 24
   ```

3. **Deploy and run benchmarks:**
   ```bash
   ovmobilebench all -c experiments/android_config.yaml
   ```

### Updating Android Tools

To update SDK packages:

```bash
sdkmanager --update
```

To update NDK, run the installation script with a new version:

```bash
python scripts/setup_android_tools.py --ndk-version r27 --ndk-only
```

### Uninstalling

To uninstall, simply remove the installation directory:

```bash
# Linux/macOS
rm -rf ~/android-sdk

# Windows
rmdir /s %USERPROFILE%\android-sdk
```

And remove the environment variables from your shell configuration.
