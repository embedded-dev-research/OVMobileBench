# OVMobileBench User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Advanced Usage](#advanced-usage)
6. [Working with Models](#working-with-models)
7. [Device Management](#device-management)
8. [Performance Optimization](#performance-optimization)
9. [Analyzing Results](#analyzing-results)
10. [Best Practices](#best-practices)
11. [FAQ](#faq)

## Introduction

OVMobileBench is a comprehensive benchmarking pipeline for OpenVINO inference on mobile devices. It automates the entire workflow from building the runtime to generating performance reports.

### Key Features

- **End-to-end automation**: From build to report in one command
- **Multi-device support**: Android (primary), Linux ARM, iOS (planned)
- **Flexible configuration**: YAML-based experiment definitions
- **Rich metrics**: Throughput, latency, device utilization
- **Reproducible results**: Full provenance tracking

## Core Concepts

### Pipeline Stages

1. **Build**: Compile OpenVINO runtime for target platform
2. **Package**: Bundle runtime, libraries, and models
3. **Deploy**: Transfer bundle to target device(s)
4. **Run**: Execute benchmarks with specified parameters
5. **Parse**: Extract metrics from benchmark output
6. **Report**: Generate structured reports

### Configuration

All experiments are defined in YAML files with these sections:
- `project`: Experiment metadata
- `build`: OpenVINO build configuration
- `device`: Target device settings
- `models`: Neural network models to benchmark
- `run`: Benchmark execution parameters
- `report`: Output format and destinations

### Run Matrix

The run matrix defines parameter combinations to test:
- `niter`: Number of iterations
- `api`: Sync or async execution
- `nireq`: Number of inference requests
- `nstreams`: Number of parallel streams
- `threads`: CPU thread count
- `device`: Target plugin (CPU, GPU, etc.)

## Installation

### System Requirements

- Python 3.11+
- Git
- CMake 3.24+
- Ninja 1.11+
- Android NDK r26d+ (for Android targets)
- Android SDK Platform Tools

### Install Options

#### From Source
```bash
git clone https://github.com/embedded-dev-research/OVMobileBench.git
cd OVMobileBench
pip install -e .[dev]
```

#### Using pip with requirements
```bash
pip install -r requirements.txt
pip install -e .
```

### Environment Setup

```bash
# Android development
export ANDROID_NDK_HOME=/path/to/android-ndk-r26d
export ANDROID_HOME=/path/to/android-sdk
export PATH=$ANDROID_HOME/platform-tools:$PATH

# OpenVINO (if using prebuilt)
export INTEL_OPENVINO_DIR=/opt/intel/openvino
source $INTEL_OPENVINO_DIR/setupvars.sh
```

## Basic Usage

### Running a Complete Pipeline

```bash
ovmobilebench all -c experiments/config.yaml --verbose
```

### Running Individual Stages

```bash
# Build OpenVINO
ovmobilebench build -c experiments/config.yaml

# Create deployment package
ovmobilebench package -c experiments/config.yaml

# Deploy to devices
ovmobilebench deploy -c experiments/config.yaml

# Run benchmarks
ovmobilebench run -c experiments/config.yaml

# Generate reports
ovmobilebench report -c experiments/config.yaml
```

### Command-Line Options

```bash
ovmobilebench --help                    # Show help
ovmobilebench all --help                # Show help for 'all' command
ovmobilebench all -c config.yaml        # Run with config
ovmobilebench all -c config.yaml -v     # Verbose output
ovmobilebench all -c config.yaml --dry-run  # Preview without execution
```

## Advanced Usage

### Using Prebuilt OpenVINO

```yaml
build:
  enabled: false
  openvino_repo: "/path/to/prebuilt/openvino"
```

### Custom Build Options

```yaml
build:
  enabled: true
  openvino_repo: "/path/to/openvino/source"
  build_type: "Release"
  options:
    ENABLE_INTEL_GPU: "OFF"
    ENABLE_ONEDNN_FOR_ARM: "ON"
    ENABLE_PYTHON: "OFF"
    CMAKE_CXX_FLAGS: "-march=armv8.2-a"
```

### Multi-Device Benchmarking

```yaml
device:
  kind: "android"
  serials: ["device1", "device2", "device3"]
  push_dir: "/data/local/tmp/ovmobilebench"
```

### Complex Run Matrices

```yaml
run:
  repeats: 5
  cooldown_sec: 30
  matrix:
    niter: [100, 200, 500]
    api: ["sync", "async"]
    nireq: [1, 2, 4, 8]
    nstreams: ["1", "2", "AUTO"]
    device: ["CPU", "GPU"]
    threads: [1, 2, 4, 8, 16]
    infer_precision: ["FP32", "FP16", "INT8"]
```

### Custom Report Tags

```yaml
report:
  tags:
    branch: "feature/optimization"
    experiment: "thread-scaling"
    hardware: "snapdragon-888"
    owner: "maintainer"
```

## Working with Models

### Model Sources

#### Open Model Zoo
```bash
# Download model
omz_downloader --name resnet-50-tf -o models/

# Convert to IR format
omz_converter --name resnet-50-tf --precision FP16 -d models/
```

#### Custom Models
```bash
# Convert ONNX model
mo --input_model model.onnx --output_dir models/ --data_type FP16
```

### Model Configuration

```yaml
models:
  - name: "resnet50"
    path: "models/resnet50_fp16.xml"
    precision: "FP16"
    tags:
      dataset: "imagenet"
      accuracy: "76.1%"
  
  - name: "mobilenet_v2"
    path: "models/mobilenet_v2_int8.xml"
    precision: "INT8"
    tags:
      dataset: "imagenet"
      compressed: true
```

### Model Management

```bash
# List available models
ls -la models/

# Verify model files
ovmobilebench validate-models -c experiments/config.yaml

# Calculate checksums
sha256sum models/*.xml models/*.bin > models/checksums.txt
```

## Device Management

### Android Devices

#### Setup
```bash
# Enable Developer Options and USB Debugging
# Connect device via USB

# Verify connection
adb devices

# Get device information
adb shell getprop ro.product.model
adb shell getprop ro.board.platform
```

#### Configuration
```yaml
device:
  kind: "android"
  serials: ["R3CN30XXXX"]
  push_dir: "/data/local/tmp/ovmobilebench"
  use_root: false
```

### Linux ARM Devices

#### Setup
```bash
# Set up SSH key authentication
ssh-copy-id user@device.local

# Test connection
ssh user@device.local uname -a
```

#### Configuration
```yaml
device:
  kind: "linux_ssh"
  host: "192.168.1.100"
  user: "ubuntu"
  key_path: "~/.ssh/id_rsa"
  push_dir: "/home/ubuntu/ovmobilebench"
```

### Device Stabilization

```bash
# Android: Disable animations
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0

# Turn screen off
adb shell input keyevent 26

# Set CPU governor (requires root)
adb shell "echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
```

## Performance Optimization

### Thermal Management

```yaml
run:
  cooldown_sec: 60  # Wait between runs
  warmup_runs: 2    # Discard initial runs
```

### CPU Affinity

```bash
# Pin to big cores (device-specific)
export TASKSET_MASK="0xF0"  # Cores 4-7
```

### Memory Optimization

```yaml
build:
  options:
    ENABLE_LTO: "ON"  # Link-time optimization
    CMAKE_BUILD_TYPE: "Release"
```

### Thread Tuning

```yaml
run:
  matrix:
    threads: [1, 2, 4, 8]  # Test different thread counts
    nstreams: ["AUTO"]      # Let OpenVINO optimize
```

## Analyzing Results

### Understanding Metrics

- **Throughput (FPS)**: Inferences per second
- **Latency (ms)**: Time per inference
  - Average: Mean across all iterations
  - Median: Middle value (robust to outliers)
  - Min/Max: Range of values
- **Efficiency**: FPS per thread
- **Scaling**: Performance vs. resource usage

### Viewing Results

```bash
# Quick view
cat experiments/results/output.csv

# Pretty JSON
python -m json.tool experiments/results/output.json

# Import to pandas
python -c "import pandas as pd; df = pd.read_csv('output.csv'); print(df.describe())"
```

### Comparing Configurations

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load results
df = pd.read_csv('results.csv')

# Group by configuration
grouped = df.groupby(['threads', 'nstreams'])['throughput_fps'].median()

# Plot
grouped.plot(kind='bar')
plt.ylabel('Throughput (FPS)')
plt.title('Performance by Configuration')
plt.show()
```

### Regression Detection

```python
# Compare with baseline
baseline = pd.read_csv('baseline.csv')
current = pd.read_csv('current.csv')

# Calculate regression
regression = (current['throughput_fps'] - baseline['throughput_fps']) / baseline['throughput_fps'] * 100

# Flag regressions > 5%
regressions = regression[regression < -5]
if not regressions.empty:
    print(f"Performance regressions detected: {regressions}")
```

## Best Practices

### Experiment Design

1. **Start simple**: Single model, single device
2. **Isolate variables**: Change one parameter at a time
3. **Multiple runs**: Use repeats ≥ 3 for statistical validity
4. **Document context**: Record temperature, battery, background apps

### Reproducibility

1. **Version control**: Track configurations in git
2. **Record metadata**: Build flags, device info, timestamps
3. **Use checksums**: Verify model integrity
4. **Archive results**: Keep raw outputs

### Performance

1. **Warm up**: Discard initial runs
2. **Cool down**: Prevent thermal throttling
3. **Stable power**: Use consistent charging state
4. **Minimize noise**: Disable unnecessary services

### Security

1. **No secrets in configs**: Use environment variables
2. **Validate inputs**: Check model sources
3. **Limit permissions**: Avoid root when possible
4. **Clean up**: Remove temporary files

## FAQ

### Q: Can I use prebuilt OpenVINO packages?

Yes, set `build.enabled: false` and point to your prebuilt OpenVINO directory.

### Q: How do I benchmark on multiple devices simultaneously?

List multiple device serials in the configuration:
```yaml
device:
  serials: ["device1", "device2", "device3"]
```

### Q: What's the difference between sync and async API?

- **Sync**: Blocking inference, simpler, good for single-request scenarios
- **Async**: Non-blocking, allows parallel requests, better throughput

### Q: How do I optimize for latency vs throughput?

- **Latency**: Use sync API, nireq=1, optimize single-thread performance
- **Throughput**: Use async API, multiple nireq, optimize parallelism

### Q: Can I benchmark custom layers?

Yes, ensure your custom layers are built into OpenVINO and the model uses them correctly.

### Q: How do I handle thermal throttling?

- Increase cooldown time between runs
- Use external cooling if available
- Monitor temperature during benchmarks
- Run shorter iterations

### Q: What's the recommended matrix for initial testing?

Start with:
```yaml
run:
  matrix:
    niter: [100]
    api: ["sync"]
    nireq: [1]
    nstreams: ["1"]
    threads: [4]
```

### Q: How do I debug failed runs?

1. Use `--verbose` flag
2. Check logs in `artifacts/` directory
3. Run individual stages separately
4. Verify device connectivity
5. Check available disk space

### Q: Can I export results to Excel?

Yes, CSV output can be opened directly in Excel or converted:
```python
import pandas as pd
df = pd.read_csv('results.csv')
df.to_excel('results.xlsx', index=False)
```

### Q: How do I benchmark INT8 models?

1. Quantize your model to INT8
2. Specify precision in model config
3. Ensure CPU plugin supports INT8 (ARM may have limitations)

## Getting Help

- [GitHub Issues](https://github.com/embedded-dev-research/OVMobileBench/issues) - Bug reports and feature requests
- [Documentation](https://github.com/embedded-dev-research/OVMobileBench/tree/main/docs) - This guide and API reference
- [Discussions](https://github.com/embedded-dev-research/OVMobileBench/discussions) - Project discussions
- Email: nesterov.alexander@outlook.com