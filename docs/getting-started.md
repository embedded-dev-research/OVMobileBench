# Getting Started with OVMobileBench

Welcome to OVMobileBench! This guide will help you get up and running with your first benchmark in minutes.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Git** for cloning repositories
- **Android SDK Platform Tools** (for Android benchmarking)
- **Android NDK r26d+** (for building from source)
- **CMake 3.24+** and **Ninja 1.11+** (for building)

## Installation

### Method 1: Install from Source (Recommended)

```bash
git clone https://github.com/embedded-dev-research/openvino_remote_benchmark.git
cd openvino_remote_benchmark
pip install -e .[dev]
```

### Method 2: Using Poetry

```bash
git clone https://github.com/embedded-dev-research/openvino_remote_benchmark.git
cd openvino_remote_benchmark
poetry install
poetry shell
```

## Quick Setup

### 1. Set Up Environment Variables

```bash
export ANDROID_NDK_HOME=/path/to/android-ndk-r26d
export ANDROID_HOME=/path/to/android-sdk
export PATH=$ANDROID_HOME/platform-tools:$PATH
```

### 2. Verify Installation

```bash
# Check OVMobileBench installation
ovmobilebench --version

# Check Android tools
adb --version
cmake --version
ninja --version
```

### 3. Connect Your Device

For Android devices:

```bash
# Enable Developer Options and USB Debugging on your device
# Connect via USB
adb devices

# You should see your device listed
# Example output:
# List of devices attached
# R3CN30XXXX  device
```

## Your First Benchmark

### 1. Download a Test Model

```bash
# Create models directory
mkdir -p models

# Download a sample model (ResNet-50)
# You can use Open Model Zoo tools or download manually
omz_downloader --name resnet-50-tf -o models/
omz_converter --name resnet-50-tf --precision FP16 -d models/
```

### 2. Create a Configuration File

Create `experiments/quick_test.yaml`:

```yaml
project:
  name: "quick-test"
  run_id: "first-run"

build:
  enabled: false  # Use prebuilt OpenVINO if available
  openvino_repo: "/path/to/openvino"  # Update this path

device:
  kind: "android"
  serials: ["YOUR_DEVICE_SERIAL"]  # From 'adb devices'
  push_dir: "/data/local/tmp/ovmobilebench"

models:
  - name: "resnet50"
    path: "models/public/resnet-50-tf/FP16/resnet-50-tf.xml"
    precision: "FP16"

run:
  repeats: 3
  matrix:
    niter: [100]
    api: ["sync"]
    nireq: [1]
    nstreams: ["1"]
    device: ["CPU"]
    threads: [4]

report:
  sinks:
    - type: "csv"
      path: "experiments/results/quick_test.csv"
    - type: "json"
      path: "experiments/results/quick_test.json"
```

### 3. Run the Benchmark

```bash
# Run the complete pipeline
ovmobilebench all -c experiments/quick_test.yaml --verbose

# Or run individual stages
ovmobilebench build -c experiments/quick_test.yaml
ovmobilebench package -c experiments/quick_test.yaml
ovmobilebench deploy -c experiments/quick_test.yaml
ovmobilebench run -c experiments/quick_test.yaml
ovmobilebench report -c experiments/quick_test.yaml
```

### 4. View Results

```bash
# View CSV results
cat experiments/results/quick_test.csv

# View JSON results (pretty-printed)
python -m json.tool experiments/results/quick_test.json
```

## Understanding the Output

A typical benchmark result includes:

- **Throughput (FPS)**: Frames/inferences per second
- **Latency metrics**: Average, median, min, max (in milliseconds)
- **Device information**: Serial, SoC, memory
- **Configuration**: Threads, streams, precision used
- **Build provenance**: OpenVINO version, build flags

Example CSV output:
```
model,device,threads,nstreams,throughput_fps,latency_avg_ms
resnet50,CPU,4,1,25.3,39.5
resnet50,CPU,4,2,31.2,32.1
```

## Common Workflows

### Building OpenVINO from Source

If you need to build OpenVINO:

```bash
# Clone OpenVINO
git clone https://github.com/openvinotoolkit/openvino.git
cd openvino
git submodule update --init --recursive

# Update your config to enable building
# Set build.enabled: true in your YAML
```

### Using Multiple Devices

```yaml
device:
  kind: "android"
  serials: ["device1", "device2", "device3"]
```

### Testing Different Configurations

```yaml
run:
  matrix:
    threads: [1, 2, 4, 8]
    nstreams: ["1", "2", "AUTO"]
    api: ["sync", "async"]
```

## Next Steps

- [Device Setup Guide](device-setup.md) - Configure Android/Linux devices
- [Configuration Reference](configuration.md) - Full YAML schema
- [Build Guide](build-guide.md) - Building OpenVINO for mobile
- [User Guide](user-guide.md) - Complete usage documentation

## Getting Help

- Check the [Troubleshooting Guide](troubleshooting.md)
- File issues on [GitHub](https://github.com/embedded-dev-research/openvino_remote_benchmark/issues)
- See [FAQ](user-guide.md#faq) for common questions

## Tips for Success

1. **Start simple**: Begin with one model and one device
2. **Use prebuilt OpenVINO**: Avoid building from source initially
3. **Monitor thermals**: Let devices cool between runs
4. **Validate results**: Run benchmarks multiple times
5. **Keep logs**: Use `--verbose` flag for debugging

Happy benchmarking!