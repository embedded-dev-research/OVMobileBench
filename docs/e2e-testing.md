# End-to-End Testing

This document describes the E2E testing infrastructure for OVMobileBench, which demonstrates the complete pipeline from building OpenVINO to running benchmarks on Android devices.

## Overview

The E2E test suite provides a comprehensive example of using OVMobileBench to:

- Build OpenVINO for Android ARM64
- Package runtime and models
- Deploy to Android devices/emulators
- Run benchmarks with various configurations
- Generate and validate reports

## Test Structure

```
tests/e2e/
├── configs/
│   └── android_resnet50.yaml    # OVMobileBench configuration
├── emulator_helper.py            # Android emulator management
├── model_helper.py               # Model download utilities
├── validate_results.py          # Result validation
├── display_results.py           # Result formatting
└── pr_comment.py                # GitHub PR integration
```

## Running E2E Tests

### Local Development

```bash
# Run E2E tests separately (excluded from regular tests)
make test-e2e

# Or directly with pytest
pytest tests/e2e/ -v
```

### CI/CD Pipeline

E2E tests run automatically on:

- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch

The CI runs on two platforms:

- **Ubuntu Latest**: x64 with ARM64 emulation
- **macOS Latest**: Apple Silicon (M1/M2) with native ARM64

## GitHub Actions Workflow

The E2E workflow (`.github/workflows/e2e-android-test.yml`) demonstrates the complete OVMobileBench pipeline with intelligent caching for optimal performance:

### Caching Strategy

The workflow uses multi-layer caching to reduce build times:

- **Android SDK Cache**: Saves ~10-15 minutes by caching SDK, NDK, and system images
- **Python Dependencies**: Caches pip packages to save ~1-2 minutes
- **OpenVINO Build Cache**: Caches compiled libraries to save ~20-30 minutes
- **Models Cache**: Caches downloaded models to save ~2-5 minutes

#### Manual Cache Control

When running the workflow manually:

- Set `clear_cache: true` to rebuild everything from scratch
- Useful for debugging cache-related issues or ensuring clean builds

### 1. Environment Setup

```yaml
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'

- name: Install OVMobileBench
  run: |
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
```

### 2. Android SDK/NDK Setup

OVMobileBench handles the complete Android toolchain installation:

```yaml
- name: Setup Android SDK/NDK using OVMobileBench
  run: |
    python -m ovmobilebench.cli setup-android \
      --api 30 \
      --create-avd \
      --sdk-root $HOME/android-sdk \
      --verbose
```

This command:

- Downloads Android command-line tools
- Installs platform-tools, emulator, and system images
- Installs NDK r26d
- Creates an AVD for testing

### 3. Hardware Acceleration

Platform-specific acceleration is configured:

**Linux (KVM)**:

```yaml
- name: Enable KVM for Android emulator (Linux only)
  if: runner.os == 'Linux'
  run: |
    echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger --name-match=kvm
```

**macOS (Hypervisor.framework)**:

```yaml
- name: Enable Hypervisor.framework for Android emulator (macOS only)
  if: runner.os == 'macOS'
  run: |
    sysctl -n kern.hv_support || echo "Hypervisor.framework not available"
    echo "ANDROID_EMULATOR_USE_SYSTEM_LIBS=1" >> $GITHUB_ENV
```

### 4. OVMobileBench Pipeline

The workflow demonstrates both individual stages and the all-in-one approach:

#### Individual Stages

```yaml
# Build OpenVINO
- name: Build OpenVINO for Android
  run: |
    python -m ovmobilebench.cli build \
      -c tests/e2e/configs/android_resnet50.yaml \
      --verbose

# Package runtime and models
- name: Package OpenVINO runtime and model
  run: |
    python -m ovmobilebench.cli package \
      -c tests/e2e/configs/android_resnet50.yaml \
      --verbose

# Deploy to device
- name: Deploy to Android device
  run: |
    python -m ovmobilebench.cli deploy \
      -c tests/e2e/configs/android_resnet50.yaml \
      --verbose

# Run benchmark
- name: Run benchmark on device
  run: |
    python -m ovmobilebench.cli run \
      -c tests/e2e/configs/android_resnet50.yaml \
      --verbose

# Generate report
- name: Generate benchmark report
  run: |
    python -m ovmobilebench.cli report \
      -c tests/e2e/configs/android_resnet50.yaml \
      --verbose
```

#### All-in-One

```yaml
# Alternative: run complete pipeline
- name: Run complete pipeline
  run: |
    python -m ovmobilebench.cli all \
      -c tests/e2e/configs/android_resnet50.yaml \
      --verbose
```

## Configuration

The E2E test uses a sample configuration (`tests/e2e/configs/android_resnet50.yaml`):

```yaml
project:
  name: "e2e-android-resnet50"
  run_id: "test_001"

build:
  enabled: true
  type: openvino
  openvino:
    source: "latest"
    cmake_args:
      - "-DCMAKE_BUILD_TYPE=Release"
      - "-DENABLE_INTEL_CPU=ON"
  android:
    abi: "arm64-v8a"
    api_level: 30
    stl: "c++_shared"

device:
  type: android
  serial: "emulator-5554"

models:
  - name: "resnet-50"
    path: "ovmb_cache/models/resnet-50-pytorch.xml"
    framework: "openvino"

run:
  enabled: true
  matrix:
    niter: [100]
    threads: [4]
    device: ["CPU"]
    infer_precision: ["FP16"]

report:
  enabled: true
  format: ["json", "csv"]
  output_dir: "artifacts/reports"
```

## Helper Scripts

### Emulator Management (`emulator_helper.py`)

```bash
# Create AVD
python tests/e2e/emulator_helper.py create-avd --api 30

# Start emulator
python tests/e2e/emulator_helper.py start-emulator

# Wait for boot
python tests/e2e/emulator_helper.py wait-for-boot

# Stop emulator
python tests/e2e/emulator_helper.py stop-emulator
```

### Model Management (`model_helper.py`)

```bash
# Download ResNet-50
python tests/e2e/model_helper.py download-resnet50

# List cached models
python tests/e2e/model_helper.py list
```

### Result Validation (`validate_results.py`)

Automatically validates benchmark results:

- Checks for required fields
- Validates throughput and latency values
- Ensures data consistency

### PR Integration (`pr_comment.py`)

Generates markdown-formatted comments for pull requests with benchmark results:

```bash
python tests/e2e/pr_comment.py --api 30 --pr 123
```

## Artifacts

All test artifacts are stored in:

- `artifacts/` - Build outputs, packages, results
- `ovmb_cache/` - Downloaded models and SDKs

Artifacts are automatically uploaded in CI and retained for 7 days.

## Extending E2E Tests

To add new test scenarios:

1. Create a new configuration in `tests/e2e/configs/`
2. Add model download logic to `model_helper.py` if needed
3. Update the CI matrix in `.github/workflows/e2e-android-test.yml`
4. Add validation logic to `validate_results.py`

## Troubleshooting

### Common Issues

1. **Emulator won't start**: Check KVM (Linux) or Hypervisor.framework (macOS) is enabled
2. **Model download fails**: Check network connectivity and cache permissions
3. **Build fails**: Ensure NDK r26d is installed and ANDROID_NDK_HOME is set
4. **Deployment fails**: Verify device/emulator is connected with `adb devices`

### Debug Commands

```bash
# Check Android SDK setup
python -m ovmobilebench.cli setup-android --verbose

# List available devices
python -m ovmobilebench.cli list-devices

# Run with dry-run to preview actions
python -m ovmobilebench.cli all -c config.yaml --dry-run
```

## Integration with Regular Testing

E2E tests are excluded from regular test runs:

- `make test` - Runs unit and integration tests only
- `make test-e2e` - Runs E2E tests only
- `pytest tests/ --ignore=tests/e2e` - Skip E2E tests (default)
- `pytest tests/e2e/` - Run only E2E tests
