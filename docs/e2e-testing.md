# E2E Tests for OVMobileBench

This directory contains end-to-end tests for OVMobileBench Android pipeline.

## Quick Start

```bash
# 1. Install dependencies
brew install ninja ccache
pip install -e .

# 2. Setup Java
export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
export PATH="$JAVA_HOME/bin:$PATH"

# 3. Setup Android SDK
python -m ovmobilebench.cli setup-android --api 30 --create-avd --verbose

# 4. Run E2E tests
python helpers/emulator_helper.py -c experiments/android_example.yaml start-emulator &
python helpers/emulator_helper.py -c experiments/android_example.yaml wait-for-boot
python helpers/model_helper.py -c experiments/android_example.yaml download-resnet50
python -m ovmobilebench.cli all -c experiments/android_example.yaml --verbose
```

## Helper Scripts

All helper scripts follow the `test_*.py` naming convention to satisfy pre-commit hooks:

### `test_emulator_helper.py`

Android emulator management. All commands accept `-c/--config` parameter to specify config file.

- `start-emulator`: Start emulator in headless mode
- `wait-for-boot`: Wait for emulator to complete boot
- `stop-emulator`: Stop running emulator
- `create-avd`: Create Android Virtual Device (usually done by setup-android)
- `delete-avd`: Delete AVD

**Usage examples:**

```bash
# Using default config (experiments/android_example.yaml)
python helpers/emulator_helper.py start-emulator
python helpers/emulator_helper.py wait-for-boot
python helpers/emulator_helper.py stop-emulator

# Using custom config
python helpers/emulator_helper.py -c my_config.yaml start-emulator
python helpers/emulator_helper.py -c my_config.yaml wait-for-boot
python helpers/emulator_helper.py -c my_config.yaml stop-emulator
```

### `test_model_helper.py`

Model management for testing. Accepts `-c/--config` parameter to specify config file.

- `download-resnet50`: Download ResNet-50 model to cache directory
- `download-mobilenet`: Download MobileNet model (not implemented yet)
- `list`: List cached models

**Usage examples:**

```bash
# Using default config
python helpers/model_helper.py download-resnet50

# Using custom config
python helpers/model_helper.py -c my_config.yaml download-resnet50
```

### `test_validate_results.py`

Results validation:

- Validates benchmark output format
- Checks performance metrics

### `test_display_results.py`

Results display:

- Formats and displays benchmark results

### `test_pr_comment.py`

GitHub integration:

- Posts benchmark results to PR comments

## Configuration

### `experiments/android_example.yaml`

Main configuration file that controls all aspects of the pipeline:

- **project**: Cache directory and run identification
- **environment**: Java and Android SDK paths (auto-detected)
- **openvino**: Build mode, source location, toolchain, CMake options
- **device**: Android device configuration
- **models**: Model paths and metadata
- **run**: Benchmark execution matrix
- **report**: Output formats and locations

All paths are relative to cache_dir, no need for environment variables!

## Prerequisites

### macOS

```bash
# Install Java
brew install openjdk@17

# Set Java environment
export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
export PATH="$JAVA_HOME/bin:$PATH"
```

### Android SDK

- Android SDK should be installed (typically at `/Users/$USER/Library/Android/sdk`)
- Required components:
  - Platform tools (adb)
  - Emulator
  - System images for target API level
  - NDK (for building)

## Complete E2E Pipeline

### Automatic (Recommended)

```bash
# Setup only Java (once)
export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
export PATH="$JAVA_HOME/bin:$PATH"

# Install Android SDK (once)
python -m ovmobilebench.cli setup-android --api 30 --create-avd --verbose

# Run tests
CONFIG=experiments/android_example.yaml
python helpers/emulator_helper.py -c $CONFIG start-emulator &
python helpers/emulator_helper.py -c $CONFIG wait-for-boot
python helpers/model_helper.py -c $CONFIG download-resnet50

# Run complete pipeline (builds OpenVINO if needed)
python -m ovmobilebench.cli all -c $CONFIG --verbose

# Validate and cleanup
python helpers/validate_results.py
python helpers/display_results.py
python helpers/emulator_helper.py -c $CONFIG stop-emulator
```

### Manual Steps

If you prefer to run individual stages:

```bash
# 1. Build OpenVINO (clones automatically if needed)
python -m ovmobilebench.cli build -c experiments/android_example.yaml --verbose

# 2. Package runtime and models
python -m ovmobilebench.cli package -c experiments/android_example.yaml --verbose

# 3. Deploy to device
python -m ovmobilebench.cli deploy -c experiments/android_example.yaml --verbose

# 4. Run benchmark
python -m ovmobilebench.cli run -c experiments/android_example.yaml --verbose

# 5. Generate report
python -m ovmobilebench.cli report -c experiments/android_example.yaml --verbose
```

## Troubleshooting

### Common Issues

1. **Java not found**: Install OpenJDK 17 via Homebrew (`brew install openjdk@17`)
2. **Ninja not found**: Install Ninja (`brew install ninja`)
3. **OpenVINO submodules missing**: The build now automatically clones with `--recurse-submodules`
4. **Emulator fails to start**: Check that AVD was created during setup-android
5. **Device not found**: Wait for emulator to fully boot (can take 2-3 minutes)
6. **CMake configuration fails**: Check stderr output for missing dependencies

### Environment Check

```bash
# Check Java
java -version

# Check Android SDK
ls $ANDROID_HOME
adb devices

# Check emulator
emulator -list-avds
```

## GitHub Actions Integration

The `.github/workflows/e2e-android-test.yml` workflow runs these tests automatically on:

- Push to main/develop branches
- Pull requests to main
- Manual dispatch

The workflow supports both Ubuntu and macOS runners with proper hardware acceleration setup.
