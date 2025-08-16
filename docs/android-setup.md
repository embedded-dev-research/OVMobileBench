# Android SDK/NDK Setup Guide

This guide explains how to install Android SDK and NDK for building and running OVMobileBench on Android devices.

## Automated Installation

We provide a Python script that automatically downloads and installs Android SDK and NDK for Windows, macOS, and Linux.

### Prerequisites

- Python 3.7 or higher
- ~5GB of free disk space
- Internet connection for downloading tools

### Installation Script

Run the installation script from the project root:

```bash
python scripts/setup_android_tools.py
```

This will:
1. Fetch the latest available versions from Google's repository
2. Install both Android SDK and NDK to `~/android-sdk` by default
3. Use the most recent stable versions automatically

### Installation Options

#### Custom Installation Directory

```bash
python scripts/setup_android_tools.py --install-dir /path/to/install
```

#### Install Only NDK (without SDK)

If you only need NDK for building OpenVINO:

```bash
python scripts/setup_android_tools.py --ndk-only
```

#### List Available Versions

To see all available versions fetched from Google:

```bash
python scripts/setup_android_tools.py --list-versions
```

#### Specify Versions

Install specific versions instead of latest:

```bash
# Specific NDK version
python scripts/setup_android_tools.py --ndk-version r26d

# Multiple specific versions
python scripts/setup_android_tools.py \
    --ndk-version r26d \
    --build-tools-version 34.0.0 \
    --platform-version 34
```

#### Offline Mode

To skip fetching from Google and use fallback versions:

```bash
python scripts/setup_android_tools.py --no-fetch
```

#### Keep Downloaded Files

By default, the script removes downloaded archives after installation. To keep them:

```bash
python scripts/setup_android_tools.py --skip-cleanup
```

### What Gets Installed

**Full Installation (default):**
- Android SDK Command Line Tools (latest version)
- Android SDK Platform Tools (includes `adb`)
- Android SDK Build Tools (latest version)
- Android Platform API (latest version)
- Android NDK (latest version)

**NDK-Only Installation:**
- Android NDK (latest version)

Note: The script automatically fetches and uses the most recent versions from Google's repository. You can see available versions with `--list-versions` or specify specific versions with the version flags.

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

After installation, the script will display environment variables to add to your shell configuration:

#### Linux/macOS (bash/zsh)

Add to `~/.bashrc`, `~/.zshrc`, or equivalent:

```bash
export ANDROID_SDK_ROOT="$HOME/android-sdk/sdk"
export ANDROID_HOME="$HOME/android-sdk/sdk"
export ANDROID_NDK_ROOT="$HOME/android-sdk/ndk/r26d"
export ANDROID_NDK_HOME="$HOME/android-sdk/ndk/r26d"
export NDK_ROOT="$HOME/android-sdk/ndk/r26d"
export PATH="$HOME/android-sdk/sdk/platform-tools:$HOME/android-sdk/sdk/cmdline-tools/latest/bin:$PATH"
```

Or source the generated script:

```bash
source ~/android-sdk/android_env.sh
```

#### Windows (PowerShell)

Add to PowerShell profile:

```powershell
$env:ANDROID_SDK_ROOT = "$env:USERPROFILE\android-sdk\sdk"
$env:ANDROID_HOME = "$env:USERPROFILE\android-sdk\sdk"
$env:ANDROID_NDK_ROOT = "$env:USERPROFILE\android-sdk\ndk\r26d"
$env:ANDROID_NDK_HOME = "$env:USERPROFILE\android-sdk\ndk\r26d"
$env:NDK_ROOT = "$env:USERPROFILE\android-sdk\ndk\r26d"
$env:Path += ";$env:USERPROFILE\android-sdk\sdk\platform-tools"
$env:Path += ";$env:USERPROFILE\android-sdk\sdk\cmdline-tools\latest\bin"
```

#### Windows (Command Prompt)

```batch
set ANDROID_SDK_ROOT=%USERPROFILE%\android-sdk\sdk
set ANDROID_HOME=%USERPROFILE%\android-sdk\sdk
set ANDROID_NDK_ROOT=%USERPROFILE%\android-sdk\ndk\r26d
set ANDROID_NDK_HOME=%USERPROFILE%\android-sdk\ndk\r26d
set NDK_ROOT=%USERPROFILE%\android-sdk\ndk\r26d
set PATH=%PATH%;%USERPROFILE%\android-sdk\sdk\platform-tools
set PATH=%PATH%;%USERPROFILE%\android-sdk\sdk\cmdline-tools\latest\bin
```

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