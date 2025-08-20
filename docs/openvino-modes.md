# OpenVINO Distribution Modes

OVMobileBench supports three flexible modes for obtaining OpenVINO runtime, making it easy to integrate into different workflows.

## Overview

The `openvino` section in your configuration file determines how the OpenVINO runtime is obtained:

```yaml
openvino:
  mode: build|install|link  # Choose one of three modes
```

## Mode 1: Build from Source

Build OpenVINO from source code with custom configurations.

### When to Use

- Need specific optimizations or features
- Testing unreleased versions
- Custom patches or modifications
- CI/CD pipeline with source control

### Configuration

```yaml
openvino:
  mode: "build"
  source_dir: "/path/to/openvino"  # Path to OpenVINO source
  commit: "HEAD"                   # Git commit/tag/branch
  build_type: "Release"             # CMAKE_BUILD_TYPE

  toolchain:
    android_ndk: "/opt/android-ndk-r26d"
    abi: "arm64-v8a"
    api_level: 24
    cmake: "cmake"
    ninja: "ninja"

  options:
    ENABLE_INTEL_GPU: "OFF"
    ENABLE_ONEDNN_FOR_ARM: "ON"
    BUILD_SHARED_LIBS: "ON"
```

### Example: Android ARM64

```yaml
openvino:
  mode: "build"
  source_dir: "${HOME}/openvino"
  commit: "releases/2024/3"
  build_type: "Release"
  toolchain:
    android_ndk: "${ANDROID_NDK_HOME}"
    abi: "arm64-v8a"
    api_level: 24
  options:
    ENABLE_INTEL_GPU: "OFF"
    ENABLE_ONEDNN_FOR_ARM: "ON"
    ENABLE_PYTHON: "OFF"
```

### Example: Linux ARM64

```yaml
openvino:
  mode: "build"
  source_dir: "/workspace/openvino"
  commit: "master"
  build_type: "RelWithDebInfo"
  toolchain:
    cmake: "/usr/bin/cmake"
    ninja: "/usr/bin/ninja"
  options:
    ENABLE_ARM_COMPUTE: "ON"
    CMAKE_CXX_FLAGS: "-march=armv8.2-a+fp16"
```

## Mode 2: Use Existing Installation

Use a pre-built OpenVINO installation directory.

### When to Use

- Already have OpenVINO built
- Using official OpenVINO packages
- Faster iteration during development
- Consistent runtime across tests

### Configuration

```yaml
openvino:
  mode: "install"
  install_dir: "/path/to/openvino/install"  # Path to install directory
```

### Example: Using Official Package

```yaml
openvino:
  mode: "install"
  install_dir: "/opt/intel/openvino_2024.3"
```

### Example: Using Custom Build

```yaml
openvino:
  mode: "install"
  install_dir: "${HOME}/builds/openvino-arm64/install"
```

## Mode 3: Download Archive

Download OpenVINO archives from a URL or automatically fetch the latest build.

### When to Use

- Quick setup without building
- Testing nightly builds
- CI/CD with ephemeral environments
- Cross-platform testing

### Configuration

```yaml
openvino:
  mode: "link"
  archive_url: "URL or 'latest'"  # Archive URL or "latest" keyword
```

### Example: Specific Archive

```yaml
openvino:
  mode: "link"
  archive_url: "https://storage.openvinotoolkit.org/repositories/openvino/packages/nightly/2025.4.0-19820-4671c012da0/openvino_toolkit_rhel8_2025.4.0.dev20250820_aarch64.tgz"
```

### Example: Auto-detect Latest

```yaml
openvino:
  mode: "link"
  archive_url: "latest"  # Automatically selects for your platform
```

### Platform Detection

When using `archive_url: "latest"`, OVMobileBench automatically selects the appropriate build:

| Device Type | Platform | Selected Build |
|------------|----------|---------------|
| Android | Any | Linux ARM64 |
| Linux SSH | Linux ARM64 | RHEL8 ARM64 |
| Linux SSH | Linux x86_64 | Ubuntu 22 x86_64 |
| Host | macOS ARM64 | macOS ARM64 |
| Host | macOS x86_64 | macOS x86_64 |
| Host | Windows | Windows x86_64 |

### Available Archives

Latest builds are fetched from:

```
https://storage.openvinotoolkit.org/repositories/openvino/packages/nightly/latest.json
```

Common archive patterns:

- `linux_aarch64` - Linux ARM64 generic
- `rhel8_aarch64` - RHEL8 ARM64
- `ubuntu22_x86_64` - Ubuntu 22.04 x86_64
- `macos_arm64` - macOS Apple Silicon
- `windows_x86_64` - Windows x86_64

## Mode Comparison

| Feature | Build | Install | Link |
|---------|-------|---------|------|
| Setup time | Slow (compile) | Fast | Medium (download) |
| Customization | Full | None | None |
| Storage space | Large | Medium | Medium |
| Network required | No* | No | Yes |
| Reproducibility | High | High | Medium |
| Version control | Git | Manual | URL-based |

*Except for initial clone

## Best Practices

### Development Workflow

1. **Initial Development**: Use Mode 2 (install) with a local build
2. **Testing Changes**: Use Mode 1 (build) with specific commits
3. **CI/CD**: Use Mode 3 (link) with "latest" or pinned URLs

### CI/CD Pipeline

```yaml
# CI configuration for automated testing
openvino:
  mode: "link"
  archive_url: "latest"  # Always test with latest build
```

### Production Benchmarking

```yaml
# Production configuration with pinned version
openvino:
  mode: "link"
  archive_url: "https://storage.openvinotoolkit.org/.../openvino_2024.3.0_aarch64.tgz"
```

### Local Development

```yaml
# Development configuration with local build
openvino:
  mode: "install"
  install_dir: "${HOME}/openvino-builds/current"
```

## Caching

### Download Cache

Mode 3 (link) caches downloaded archives:

- Location: `artifacts/{run_id}/openvino_download/`
- Archive: `openvino.tar.gz`
- Extracted: `openvino_download/`

### Build Cache

Mode 1 (build) uses CMake cache:

- Location: `artifacts/{run_id}/build/`
- Incremental builds supported

## Troubleshooting

### Common Issues

1. **Mode 1: Build fails**
   - Check toolchain paths
   - Verify NDK version compatibility
   - Review CMake options

2. **Mode 2: Install directory not found**
   - Verify path exists
   - Check for `benchmark_app` in directory
   - Ensure correct architecture

3. **Mode 3: Download fails**
   - Check network connectivity
   - Verify URL is accessible
   - Try specific URL instead of "latest"

### Validation

OVMobileBench validates the configuration:

```python
# Mode-specific validation
if mode == "build" and not source_dir:
    raise ValueError("source_dir required for build mode")
elif mode == "install" and not install_dir:
    raise ValueError("install_dir required for install mode")
elif mode == "link" and not archive_url:
    raise ValueError("archive_url required for link mode")
```

## Migration Guide

### From Old Format

Old format (pre-1.0):

```yaml
build:
  openvino_repo: "/path/to/openvino"
  enabled: true
```

New format:

```yaml
openvino:
  mode: "build"
  source_dir: "/path/to/openvino"
```

### Switching Modes

To switch between modes, only change the `mode` field and corresponding options:

```yaml
# From build mode
openvino:
  mode: "build"
  source_dir: "/workspace/openvino"

# To install mode
openvino:
  mode: "install"
  install_dir: "/workspace/openvino/install"

# To link mode
openvino:
  mode: "link"
  archive_url: "latest"
```

## Examples

### Complete Android Example

```yaml
project:
  name: "android-benchmark"
  run_id: "test-001"

openvino:
  mode: "link"
  archive_url: "latest"

device:
  kind: "android"
  serials: ["device1"]
  push_dir: "/data/local/tmp/ovmobilebench"

models:
  - name: "resnet50"
    path: "models/resnet50.xml"

run:
  matrix:
    threads: [1, 2, 4]

report:
  sinks:
    - type: "json"
      path: "results.json"
```

### Complete Raspberry Pi Example

```yaml
project:
  name: "rpi-benchmark"
  run_id: "test-002"

openvino:
  mode: "build"
  source_dir: "${OPENVINO_ROOT}"
  commit: "releases/2024/3"
  build_type: "Release"
  options:
    ENABLE_ONEDNN_FOR_ARM: "ON"

device:
  kind: "linux_ssh"
  host: "192.168.1.100"
  username: "pi"
  push_dir: "/home/pi/benchmark"

models:
  - name: "mobilenet"
    path: "models/mobilenet.xml"

run:
  matrix:
    threads: [1, 4]

report:
  sinks:
    - type: "csv"
      path: "results.csv"
```
