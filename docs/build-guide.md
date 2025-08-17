# Build Guide

This guide covers building OpenVINO and benchmark_app for mobile platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Building for Android](#building-for-android)
3. [Building for Linux ARM](#building-for-linux-arm)
4. [Using Prebuilt OpenVINO](#using-prebuilt-openvino)
5. [Build Optimization](#build-optimization)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Common Requirements

- Git
- CMake 3.24+
- Ninja 1.11+ (recommended) or Make
- Python 3.8+
- C++14 compatible compiler

### Platform-Specific Requirements

#### Android
- Android NDK r26d or later
- Android SDK (for adb)
- Java JDK 8+ (for Android SDK)

#### Linux ARM
- Cross-compilation toolchain (for cross-compiling)
- OR native build environment (when building on target)

## Building for Android

### Step 1: Install Android NDK

```bash
# Download NDK
wget https://dl.google.com/android/repository/android-ndk-r26d-linux.zip

# Extract
unzip android-ndk-r26d-linux.zip -d /opt/

# Set environment variable
export ANDROID_NDK_HOME=/opt/android-ndk-r26d
```

### Step 2: Clone OpenVINO

```bash
# Clone repository
git clone https://github.com/openvinotoolkit/openvino.git
cd openvino

# Checkout specific version
git checkout releases/2024/3

# Initialize submodules
git submodule update --init --recursive
```

### Step 3: Configure Build

Create build configuration in your experiment YAML:

```yaml
build:
  enabled: true
  openvino_repo: "/path/to/openvino"
  openvino_commit: "releases/2024/3"
  build_type: "Release"
  toolchain:
    android_ndk: "/opt/android-ndk-r26d"
    abi: "arm64-v8a"
    api_level: 24
    cmake: "cmake"
    ninja: "ninja"
  options:
    ENABLE_INTEL_CPU: "ON"
    ENABLE_INTEL_GPU: "OFF"
    ENABLE_ARM_COMPUTE: "OFF"
    ENABLE_ONEDNN_FOR_ARM: "ON"
    ENABLE_PYTHON: "OFF"
    ENABLE_SAMPLES: "ON"
    CMAKE_CXX_FLAGS: "-march=armv8.2-a+fp16"
```

### Step 4: Build with OVMobileBench

```bash
# Build using OVMobileBench
ovmobilebench build -c experiments/android_build.yaml --verbose
```

### Manual Build Process

If you prefer manual building:

```bash
# Set up environment
export ANDROID_NDK=/opt/android-ndk-r26d
export ANDROID_ABI=arm64-v8a
export ANDROID_PLATFORM=24

# Create build directory
mkdir build-android && cd build-android

# Configure with CMake
cmake \
    -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK/build/cmake/android.toolchain.cmake \
    -DANDROID_ABI=$ANDROID_ABI \
    -DANDROID_PLATFORM=$ANDROID_PLATFORM \
    -DANDROID_STL=c++_shared \
    -DENABLE_INTEL_CPU=ON \
    -DENABLE_INTEL_GPU=OFF \
    -DENABLE_ONEDNN_FOR_ARM=ON \
    -DENABLE_PYTHON=OFF \
    -DENABLE_SAMPLES=ON \
    ..

# Build
ninja benchmark_app

# Package libraries
mkdir -p package/lib package/bin
cp bin/arm64-v8a/benchmark_app package/bin/
cp lib/arm64-v8a/*.so package/lib/
```

### Android ABI Options

| ABI | Architecture | Devices |
|-----|-------------|---------|
| arm64-v8a | 64-bit ARM | Most modern Android devices |
| armeabi-v7a | 32-bit ARM | Older Android devices |
| x86_64 | 64-bit x86 | Emulators, some tablets |
| x86 | 32-bit x86 | Older emulators |

### Android API Levels

| API Level | Android Version | Recommended |
|-----------|----------------|-------------|
| 21 | Android 5.0 (Lollipop) | Minimum |
| 24 | Android 7.0 (Nougat) | Good compatibility |
| 28 | Android 9 (Pie) | Modern features |
| 30 | Android 11 | Latest stable |

## Building for Linux ARM

### Option 1: Cross-Compilation

#### Install Cross-Compiler

```bash
# For Ubuntu/Debian
sudo apt-get install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

# For Fedora
sudo dnf install gcc-aarch64-linux-gnu gcc-c++-aarch64-linux-gnu
```

#### Configure Build

```yaml
build:
  enabled: true
  openvino_repo: "/path/to/openvino"
  build_type: "Release"
  toolchain:
    cmake: "cmake"
    ninja: "ninja"
  options:
    CMAKE_C_COMPILER: "aarch64-linux-gnu-gcc"
    CMAKE_CXX_COMPILER: "aarch64-linux-gnu-g++"
    CMAKE_SYSTEM_NAME: "Linux"
    CMAKE_SYSTEM_PROCESSOR: "aarch64"
    ENABLE_INTEL_CPU: "ON"
    ENABLE_INTEL_GPU: "OFF"
    ENABLE_PYTHON: "OFF"
```

#### Manual Cross-Compilation

```bash
# Create toolchain file
cat > toolchain-aarch64.cmake << EOF
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
EOF

# Configure
cmake -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_TOOLCHAIN_FILE=toolchain-aarch64.cmake \
    -DENABLE_INTEL_CPU=ON \
    -DENABLE_PYTHON=OFF \
    ..

# Build
ninja benchmark_app
```

### Option 2: Native Build on ARM Device

```bash
# On ARM device (e.g., Raspberry Pi)
# Install dependencies
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    ninja-build

# Clone and build
git clone https://github.com/openvinotoolkit/openvino.git
cd openvino
git submodule update --init --recursive

mkdir build && cd build
cmake -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_INTEL_CPU=ON \
    -DENABLE_PYTHON=OFF \
    ..

ninja benchmark_app
```

## Using Prebuilt OpenVINO

### Download Prebuilt Packages

```bash
# Download from OpenVINO releases
wget https://storage.openvinotoolkit.org/repositories/openvino/packages/2024.3/linux/l_openvino_toolkit_ubuntu20_2024.3.0.16041.1e3b88e4e3f_arm64.tgz

# Extract
tar -xzf l_openvino_toolkit_*.tgz
```

### Configure for Prebuilt

```yaml
build:
  enabled: false  # Don't build from source
  openvino_repo: "/opt/intel/openvino_2024.3"

package:
  # Package will use prebuilt binaries
  extra_files:
    - "/opt/intel/openvino_2024.3/runtime/lib/arm64/*.so"
    - "/opt/intel/openvino_2024.3/tools/benchmark_app/benchmark_app"
```

## Build Optimization

### Compiler Optimizations

```yaml
build:
  options:
    CMAKE_CXX_FLAGS: "-O3 -march=native -mtune=native"
    CMAKE_C_FLAGS: "-O3 -march=native -mtune=native"
    CMAKE_BUILD_TYPE: "Release"
    ENABLE_LTO: "ON"  # Link-time optimization
```

### ARM-Specific Optimizations

```yaml
build:
  options:
    # For ARMv8.2-A with FP16
    CMAKE_CXX_FLAGS: "-march=armv8.2-a+fp16+dotprod"

    # Enable ARM Compute Library
    ENABLE_ARM_COMPUTE: "ON"

    # Enable oneDNN for ARM
    ENABLE_ONEDNN_FOR_ARM: "ON"
```

### Build Caching

```yaml
build:
  # Use ccache for faster rebuilds
  options:
    CMAKE_C_COMPILER_LAUNCHER: "ccache"
    CMAKE_CXX_COMPILER_LAUNCHER: "ccache"
```

### Parallel Build

```bash
# Use all available cores
ninja -j$(nproc)

# Or with make
make -j$(nproc)
```

## Advanced Build Options

### Custom Plugins

```yaml
build:
  options:
    # Disable unused plugins
    ENABLE_INTEL_GPU: "OFF"
    ENABLE_INTEL_NPU: "OFF"
    ENABLE_INTEL_GNA: "OFF"

    # Enable specific features
    ENABLE_OPENCV: "OFF"  # Disable if not needed
    ENABLE_PYTHON: "OFF"  # Disable for smaller size
```

### Debug Build

```yaml
build:
  build_type: "Debug"
  options:
    CMAKE_BUILD_TYPE: "Debug"
    CMAKE_CXX_FLAGS: "-g -O0"
    ENABLE_DEBUG_SYMBOLS: "ON"
```

### Static Linking

```yaml
build:
  options:
    BUILD_SHARED_LIBS: "OFF"
    CMAKE_EXE_LINKER_FLAGS: "-static"
```

## Build Artifacts

### Expected Output Structure

```
build/
├── bin/
│   └── arm64-v8a/
│       └── benchmark_app
├── lib/
│   └── arm64-v8a/
│       ├── libopenvino.so
│       ├── libopenvino_c.so
│       ├── libopenvino_intel_cpu_plugin.so
│       └── ...
└── cmake/
    └── ...
```

### Packaging Build Output

```bash
# Create package directory
mkdir -p ovbundle/{bin,lib}

# Copy binaries
cp build/bin/*/benchmark_app ovbundle/bin/

# Copy libraries
cp build/lib/*/*.so* ovbundle/lib/

# Create archive
tar -czf ovbundle.tar.gz ovbundle/
```

## Troubleshooting

### Common Build Errors

#### CMake Configuration Errors

```bash
# Error: Could not find NDK
# Solution: Set ANDROID_NDK environment variable
export ANDROID_NDK=/path/to/ndk

# Error: Unsupported NDK version
# Solution: Use NDK r26d or later
```

#### Compilation Errors

```bash
# Error: undefined reference to '__atomic_*'
# Solution: Add atomic library
CMAKE_CXX_FLAGS="-latomic"

# Error: C++ standard library issues
# Solution: Ensure correct STL
-DANDROID_STL=c++_shared
```

#### Linking Errors

```bash
# Error: cannot find -llog
# Solution: Add Android system libraries
CMAKE_EXE_LINKER_FLAGS="-llog -landroid"
```

### Build Performance Issues

#### Slow Build

```bash
# Use ninja instead of make
cmake -GNinja ...

# Enable parallel compilation
ninja -j$(nproc)

# Use ccache
export CCACHE_DIR=/path/to/ccache
ccache -M 10G
```

#### Out of Memory

```bash
# Reduce parallel jobs
ninja -j2

# Increase swap
sudo dd if=/dev/zero of=/swapfile bs=1G count=4
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Validation

#### Verify Build

```bash
# Check binary architecture
file ovbundle/bin/benchmark_app

# Check library dependencies
readelf -d ovbundle/bin/benchmark_app

# For Android
$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf -d benchmark_app
```

#### Test Locally

```bash
# Test with emulator
adb push ovbundle /data/local/tmp/
adb shell "cd /data/local/tmp/ovbundle && \
    LD_LIBRARY_PATH=./lib ./bin/benchmark_app -h"
```

## CI/CD Integration

### GitHub Actions Build

```yaml
name: Build OpenVINO for Android

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup NDK
        run: |
          wget https://dl.google.com/android/repository/android-ndk-r26d-linux.zip
          unzip -q android-ndk-r26d-linux.zip
          echo "ANDROID_NDK=$PWD/android-ndk-r26d" >> $GITHUB_ENV

      - name: Build
        run: |
          ovmobilebench build -c config.yaml

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ovbundle-android
          path: artifacts/
```

### Docker Build Environment

```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    wget \
    unzip

# Install Android NDK
RUN wget https://dl.google.com/android/repository/android-ndk-r26d-linux.zip && \
    unzip -q android-ndk-r26d-linux.zip -d /opt/ && \
    rm android-ndk-r26d-linux.zip

ENV ANDROID_NDK=/opt/android-ndk-r26d

# Clone OpenVINO
RUN git clone https://github.com/openvinotoolkit/openvino.git /openvino

WORKDIR /openvino
```

## Next Steps

- [Benchmarking Guide](benchmarking.md) - Running benchmarks
- [Device Setup](device-setup.md) - Preparing target devices
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
