# E2E Tests for OVMobileBench

This directory contains end-to-end tests for OVMobileBench Android pipeline.

## Scripts

### `run_local.sh`

Full e2e test script that downloads and installs all required components from scratch:

- Installs Android SDK system images
- Creates AVD
- Downloads models
- Runs complete OVMobileBench pipeline

**Usage:**

```bash
./tests/e2e/run_local.sh
```

**Environment variables:**

- `API_LEVEL`: Android API level to use (default: 34)

### `run_quick.sh`

Quick setup script for existing Android SDK installations:

- Uses pre-installed Android SDK components
- Creates minimal AVD setup
- Prepares mock models for testing
- Shows next steps for manual pipeline execution

**Usage:**

```bash
./tests/e2e/run_quick.sh
```

## Helper Scripts

All helper scripts follow the `test_*.py` naming convention to satisfy pre-commit hooks:

### `test_emulator_helper.py`

Android emulator management:

- `create-avd`: Create Android Virtual Device
- `start-emulator`: Start emulator in headless mode
- `wait-for-boot`: Wait for emulator to complete boot
- `stop-emulator`: Stop running emulator
- `delete-avd`: Delete AVD

**Usage examples:**

```bash
python tests/e2e/test_emulator_helper.py create-avd --api 34
python tests/e2e/test_emulator_helper.py start-emulator
python tests/e2e/test_emulator_helper.py wait-for-boot
python tests/e2e/test_emulator_helper.py stop-emulator
```

### `test_model_helper.py`

Model management for testing:

- Downloads and prepares models for benchmarking

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

### `configs/android_resnet50.yaml`

E2E test configuration for ResNet-50 on Android:

- Build settings for arm64-v8a
- Model configuration
- Benchmark matrix parameters
- Report output settings

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

## Manual E2E Pipeline

If you prefer to run the pipeline steps manually:

1. **Setup environment:**

   ```bash
   export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
   export PATH="$JAVA_HOME/bin:$PATH"
   export ANDROID_HOME="/Users/$USER/Library/Android/sdk"
   export ANDROID_SDK_ROOT=$ANDROID_HOME
   export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
   ```

2. **Start emulator:**

   ```bash
   python tests/e2e/test_emulator_helper.py create-avd --api 34
   python tests/e2e/test_emulator_helper.py start-emulator &
   python tests/e2e/test_emulator_helper.py wait-for-boot
   ```

3. **Prepare model:**

   ```bash
   python tests/e2e/test_model_helper.py download-resnet50
   ```

4. **Run OVMobileBench pipeline:**

   ```bash
   python -m ovmobilebench.cli list-devices
   python -m ovmobilebench.cli build -c tests/e2e/configs/android_resnet50.yaml --verbose
   python -m ovmobilebench.cli package -c tests/e2e/configs/android_resnet50.yaml --verbose
   python -m ovmobilebench.cli deploy -c tests/e2e/configs/android_resnet50.yaml --verbose
   python -m ovmobilebench.cli run -c tests/e2e/configs/android_resnet50.yaml --verbose
   python -m ovmobilebench.cli report -c tests/e2e/configs/android_resnet50.yaml --verbose
   ```

5. **Validate results:**

   ```bash
   python tests/e2e/test_validate_results.py
   python tests/e2e/test_display_results.py
   ```

6. **Cleanup:**

   ```bash
   python tests/e2e/test_emulator_helper.py stop-emulator
   ```

## Troubleshooting

### Common Issues

1. **Java not found**: Install OpenJDK 17 via Homebrew
2. **Android SDK not found**: Install Android Studio or standalone SDK
3. **Emulator fails to start**: Check virtualization support and system resources
4. **Device not found**: Wait for emulator to fully boot (can take 2-3 minutes)
5. **Build failures**: Ensure NDK is installed and environment variables are set

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
