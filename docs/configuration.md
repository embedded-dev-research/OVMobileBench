# Configuration Reference

## Overview

OVMobileBench uses YAML configuration files to define experiments. This document provides a complete reference for all configuration options.

## Configuration Structure

```yaml
project:      # Project metadata
build:        # OpenVINO build settings
package:      # Bundle packaging options
device:       # Target device configuration
models:       # Model definitions
run:          # Benchmark execution parameters
report:       # Output configuration
```

## Schema Reference

### Project Section

Defines experiment metadata and identification.

```yaml
project:
  name: string           # Project name (required)
  run_id: string        # Unique run identifier (required)
  description: string   # Optional description
  version: string       # Optional version
```

**Example:**

```yaml
project:
  name: "mobile-benchmark"
  run_id: "exp-2025-01-15-001"
  description: "Thread scaling analysis on Snapdragon 888"
  version: "1.0.0"
```

### Build Section

Controls OpenVINO build process.

```yaml
build:
  enabled: boolean                    # Whether to build (default: true)
  openvino_repo: path                # Path to OpenVINO source (required)
  openvino_commit: string            # Git commit/tag (default: "HEAD")
  build_type: string                 # CMAKE_BUILD_TYPE (default: "Release")
  build_dir: path                    # Build directory (optional)
  clean_build: boolean               # Clean before build (default: false)

  toolchain:
    android_ndk: path                # Android NDK path (Android only)
    abi: string                      # Target ABI (default: "arm64-v8a")
    api_level: integer               # Android API level (default: 24)
    cmake: path                      # CMake executable (default: "cmake")
    ninja: path                      # Ninja executable (default: "ninja")
    compiler: string                 # Compiler choice (optional)

  options:                           # CMake options
    ENABLE_INTEL_CPU: ON|OFF
    ENABLE_INTEL_GPU: ON|OFF
    ENABLE_ARM_COMPUTE: ON|OFF
    ENABLE_ONEDNN_FOR_ARM: ON|OFF
    ENABLE_PYTHON: ON|OFF
    ENABLE_SAMPLES: ON|OFF
    ENABLE_TESTS: ON|OFF
    ENABLE_LTO: ON|OFF
    CMAKE_CXX_FLAGS: string
    CMAKE_C_FLAGS: string
    # Any other CMake options...
```

**Examples:**

Android build:

```yaml
build:
  enabled: true
  openvino_repo: "/home/user/openvino"
  openvino_commit: "releases/2024/3"
  build_type: "Release"
  toolchain:
    android_ndk: "/opt/android-ndk-r26d"
    abi: "arm64-v8a"
    api_level: 24
  options:
    ENABLE_INTEL_GPU: "OFF"
    ENABLE_ONEDNN_FOR_ARM: "ON"
```

Linux ARM build:

```yaml
build:
  enabled: true
  openvino_repo: "/home/user/openvino"
  build_type: "RelWithDebInfo"
  toolchain:
    cmake: "/usr/bin/cmake"
    ninja: "/usr/bin/ninja"
    compiler: "aarch64-linux-gnu-g++"
  options:
    CMAKE_CXX_FLAGS: "-march=armv8.2-a+fp16"
```

Using prebuilt:

```yaml
build:
  enabled: false
  openvino_repo: "/opt/intel/openvino_2024.3"
```

### Package Section

Controls bundle creation.

```yaml
package:
  include_symbols: boolean           # Include debug symbols (default: false)
  strip_binaries: boolean           # Strip binaries (default: true)
  compression: string               # Compression type (default: "gzip")
  extra_files: [path]              # Additional files to include
  exclude_patterns: [string]       # Patterns to exclude
  output_dir: path                 # Output directory (optional)
  bundle_name: string              # Bundle filename (optional)
```

**Example:**

```yaml
package:
  include_symbols: false
  strip_binaries: true
  compression: "gzip"
  extra_files:
    - "configs/plugin.xml"
    - "scripts/setup.sh"
  exclude_patterns:
    - "*.pdb"
    - "test_*"
```

### Device Section

Defines target device(s) for deployment.

```yaml
device:
  kind: android|linux_ssh|ios      # Device type (required)

  # Android-specific
  serials: [string]                # Device serials from 'adb devices'
  use_root: boolean                # Use root access (default: false)

  # Linux SSH-specific
  host: string                     # Hostname or IP
  port: integer                    # SSH port (default: 22)
  user: string                     # SSH username
  password: string                 # SSH password (not recommended)
  key_path: path                   # SSH private key path

  # Common options
  push_dir: path                   # Remote directory (required)
  env_vars: {string: string}       # Environment variables
  setup_commands: [string]         # Commands to run before benchmark
  cleanup_commands: [string]       # Commands to run after benchmark
```

**Examples:**

Android devices:

```yaml
device:
  kind: "android"
  serials: ["R3CN30XXXX", "emulator-5554"]
  push_dir: "/data/local/tmp/ovmobilebench"
  use_root: false
  env_vars:
    LD_LIBRARY_PATH: "/data/local/tmp/ovmobilebench/lib"
```

Linux SSH device:

```yaml
device:
  kind: "linux_ssh"
  host: "192.168.1.100"
  user: "ubuntu"
  key_path: "~/.ssh/id_rsa"
  push_dir: "/home/ubuntu/ovmobilebench"
  setup_commands:
    - "sudo cpupower frequency-set -g performance"
```

### Models Section

Defines models to benchmark.

```yaml
models:
  - name: string                    # Model name (required)
    path: path                      # Path to .xml file (required)
    precision: string               # Precision (FP32/FP16/INT8)
    input_shape: [integer]          # Override input shape (optional)
    layout: string                  # Input layout (optional)
    mean_values: [float]            # Preprocessing mean (optional)
    scale_values: [float]           # Preprocessing scale (optional)
    tags: {string: any}             # Custom metadata
```

**Example:**

```yaml
models:
  - name: "resnet50"
    path: "models/resnet50_fp16.xml"
    precision: "FP16"
    input_shape: [1, 3, 224, 224]
    layout: "NCHW"
    mean_values: [123.68, 116.78, 103.94]
    scale_values: [58.624, 57.12, 57.375]
    tags:
      dataset: "imagenet"
      accuracy_top1: 76.1

  - name: "yolo_v5"
    path: "models/yolov5s.xml"
    precision: "INT8"
    input_shape: [1, 3, 640, 640]
    tags:
      task: "detection"
      map: 0.367
```

### Run Section

Controls benchmark execution.

```yaml
run:
  enabled: boolean                  # Enable benchmarking (default: true)
  repeats: integer                  # Number of repetitions (default: 3)
  warmup_runs: integer              # Warmup iterations (default: 0)
  cooldown_sec: integer             # Cooldown between runs (default: 0)
  timeout_sec: integer              # Timeout per run (optional)

  matrix:                           # Parameter combinations to test
    niter: [integer]                # Iterations per run
    api: [sync|async]               # Inference API
    nireq: [integer]                # Number of inference requests
    nstreams: [string]              # Number of streams ("AUTO" allowed)
    device: [string]                # Target device (CPU/GPU/etc)
    threads: [integer]              # Number of threads
    infer_precision: [string]       # Inference precision hint
    batch: [integer]                # Batch size (optional)

  advanced:                         # Advanced options
    pin_threads: boolean            # Pin threads to cores
    numa_node: integer              # NUMA node affinity
    enable_profiling: boolean       # Enable performance profiling
    cache_dir: path                 # Model cache directory

  custom_args: [string]             # Additional benchmark_app arguments
```

**Examples:**

Simple matrix:

```yaml
run:
  repeats: 3
  matrix:
    niter: [100]
    api: ["sync"]
    threads: [4]
```

Complex matrix:

```yaml
run:
  repeats: 5
  warmup_runs: 2
  cooldown_sec: 30
  timeout_sec: 600
  matrix:
    niter: [100, 200, 500]
    api: ["sync", "async"]
    nireq: [1, 2, 4, 8]
    nstreams: ["1", "2", "AUTO"]
    device: ["CPU", "GPU"]
    threads: [1, 2, 4, 8]
    infer_precision: ["FP32", "FP16"]
    batch: [1, 4, 8]
  advanced:
    pin_threads: true
    enable_profiling: true
  custom_args:
    - "-hint LATENCY"
    - "-pc"
```

### Report Section

Configures output generation.

```yaml
report:
  enabled: boolean                  # Enable reporting (default: true)

  sinks:                           # Output destinations
    - type: json|csv|sqlite|html   # Sink type
      path: path                    # Output file path
      options: {}                   # Type-specific options

  aggregation:                      # Statistical aggregation
    metrics: [string]               # Metrics to compute
    percentiles: [float]            # Percentiles to calculate

  filters:                          # Result filtering
    min_throughput: float           # Minimum FPS threshold
    max_latency: float              # Maximum latency threshold

  comparison:                       # Baseline comparison
    baseline_path: path             # Path to baseline results
    regression_threshold: float     # Regression threshold (%)

  tags: {string: any}               # Metadata tags

  artifacts:                        # Additional artifacts
    save_logs: boolean              # Save raw logs
    save_stdout: boolean            # Save benchmark stdout
    save_profiling: boolean         # Save profiling data
```

**Examples:**

Multiple output formats:

```yaml
report:
  sinks:
    - type: "json"
      path: "results/output.json"
      options:
        indent: 2

    - type: "csv"
      path: "results/output.csv"
      options:
        sep: ","
        index: false

    - type: "html"
      path: "results/report.html"
      options:
        template: "templates/report.html"
```

With aggregation and filtering:

```yaml
report:
  aggregation:
    metrics: ["mean", "median", "std", "min", "max"]
    percentiles: [0.25, 0.5, 0.75, 0.95, 0.99]
  filters:
    min_throughput: 10.0
    max_latency: 100.0
  comparison:
    baseline_path: "baselines/v1.0.json"
    regression_threshold: -5.0
```

## Complete Example

```yaml
# Full configuration example
project:
  name: "snapdragon-benchmark"
  run_id: "2025-01-15-thread-scaling"
  description: "Analyze thread scaling on Snapdragon 888"

build:
  enabled: true
  openvino_repo: "/home/user/openvino"
  openvino_commit: "releases/2024/3"
  build_type: "Release"
  toolchain:
    android_ndk: "/opt/android-ndk-r26d"
    abi: "arm64-v8a"
    api_level: 24
  options:
    ENABLE_INTEL_GPU: "OFF"
    ENABLE_ONEDNN_FOR_ARM: "ON"
    ENABLE_LTO: "ON"

package:
  include_symbols: false
  strip_binaries: true
  extra_files:
    - "configs/plugins.xml"

device:
  kind: "android"
  serials: ["R3CN30XXXX"]
  push_dir: "/data/local/tmp/ovmobilebench"
  env_vars:
    LD_LIBRARY_PATH: "/data/local/tmp/ovmobilebench/lib"
  setup_commands:
    - "settings put global window_animation_scale 0"
    - "input keyevent 26"  # Screen off

models:
  - name: "resnet50"
    path: "models/resnet50_fp16.xml"
    precision: "FP16"
    tags:
      dataset: "imagenet"

  - name: "mobilenet_v2"
    path: "models/mobilenet_v2_int8.xml"
    precision: "INT8"
    tags:
      compressed: true

run:
  repeats: 5
  warmup_runs: 2
  cooldown_sec: 30
  matrix:
    niter: [200]
    api: ["sync", "async"]
    nireq: [1, 2, 4]
    nstreams: ["1", "2", "AUTO"]
    device: ["CPU"]
    threads: [1, 2, 4, 8]
    infer_precision: ["FP16"]

report:
  sinks:
    - type: "json"
      path: "results/snapdragon_888.json"
    - type: "csv"
      path: "results/snapdragon_888.csv"
  aggregation:
    metrics: ["median", "mean", "std"]
  tags:
    device: "Snapdragon 888"
    os: "Android 12"
    experiment: "thread-scaling"
  artifacts:
    save_logs: true
```

## Environment Variables

Configuration values can reference environment variables:

```yaml
build:
  openvino_repo: "${OPENVINO_ROOT}"
  toolchain:
    android_ndk: "${ANDROID_NDK_HOME}"

device:
  serials: ["${ANDROID_SERIAL}"]
```

## Configuration Validation

OVMobileBench validates configurations using Pydantic schemas. Common validation errors:

- **Missing required fields**: Ensure all required fields are present
- **Invalid types**: Check that values match expected types
- **Path validation**: Ensure paths exist and are accessible
- **Value constraints**: Some fields have min/max or enum constraints

## Tips and Best Practices

1. **Version control**: Keep configurations in git for reproducibility
2. **Use comments**: YAML supports comments with `#`
3. **Modular configs**: Use YAML anchors for repeated sections
4. **Environment-specific**: Use separate configs for different environments
5. **Incremental testing**: Start simple, add complexity gradually

## Configuration Templates

Find example configurations in the `experiments/` directory:

- `android_basic.yaml` - Minimal Android configuration
- `android_matrix.yaml` - Complex parameter matrix
- `linux_ssh.yaml` - Linux device via SSH
- `prebuilt.yaml` - Using prebuilt OpenVINO
- `ci_template.yaml` - CI/CD optimized configuration
