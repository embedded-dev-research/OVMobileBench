# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with OVBench.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Build Errors](#build-errors)
3. [Device Connection Issues](#device-connection-issues)
4. [Benchmark Execution Errors](#benchmark-execution-errors)
5. [Performance Issues](#performance-issues)
6. [Configuration Problems](#configuration-problems)
7. [CI/CD Issues](#cicd-issues)
8. [Common Error Messages](#common-error-messages)

## Installation Issues

### Python Version Mismatch

**Problem**: `ERROR: ovbench requires Python 3.11+`

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.11
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# macOS
brew install python@3.11

# Create virtual environment with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate
```

### Missing Dependencies

**Problem**: `ModuleNotFoundError: No module named 'typer'`

**Solution**:
```bash
# Install all dependencies
pip install -e .[dev]

# Or install specific missing module
pip install typer pydantic pyyaml
```

### Poetry Installation Issues

**Problem**: `Poetry: command not found`

**Solution**:
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

## Build Errors

### Android NDK Not Found

**Problem**: `CMake Error: Android NDK not found`

**Solution**:
```bash
# Set NDK environment variable
export ANDROID_NDK_HOME=/path/to/android-ndk-r26d

# Or specify in config
```
```yaml
build:
  toolchain:
    android_ndk: "/path/to/android-ndk-r26d"
```

### Unsupported NDK Version

**Problem**: `ERROR: NDK version r25 is not supported`

**Solution**:
```bash
# Download correct NDK version
wget https://dl.google.com/android/repository/android-ndk-r26d-linux.zip
unzip android-ndk-r26d-linux.zip -d /opt/

# Update configuration
export ANDROID_NDK_HOME=/opt/android-ndk-r26d
```

### CMake Configuration Failed

**Problem**: `CMake Error at CMakeLists.txt`

**Solution**:
```bash
# Clear CMake cache
rm -rf build/CMakeCache.txt build/CMakeFiles

# Verify CMake version
cmake --version  # Should be 3.24+

# Try verbose configuration
cmake -B build -S . \
  -DCMAKE_VERBOSE_MAKEFILE=ON \
  -DCMAKE_BUILD_TYPE=Debug \
  2>&1 | tee cmake.log
```

### Compilation Errors

**Problem**: `undefined reference to '__atomic_load_8'`

**Solution**:
```yaml
# Add atomic library in config
build:
  options:
    CMAKE_CXX_FLAGS: "-latomic"
    CMAKE_EXE_LINKER_FLAGS: "-latomic"
```

### Out of Memory During Build

**Problem**: `c++: fatal error: Killed signal terminated program`

**Solution**:
```bash
# Reduce parallel jobs
ninja -j2  # Instead of -j$(nproc)

# Or increase swap
sudo dd if=/dev/zero of=/swapfile bs=1G count=8
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab for persistence
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Device Connection Issues

### ADB Device Not Found

**Problem**: `error: no devices/emulators found`

**Solution**:
```bash
# Check USB connection
lsusb | grep -i google  # For Pixel devices

# Restart ADB server
adb kill-server
adb start-server

# Check device authorization
adb devices
# Accept RSA key on device if prompted

# Try different USB port/cable
# Use USB 2.0 port if USB 3.0 fails
```

### ADB Unauthorized

**Problem**: `device unauthorized`

**Solution**:
1. On device: Settings → Developer Options → Revoke USB debugging authorizations
2. Reconnect USB cable
3. Accept RSA fingerprint on device
4. Verify: `adb devices`

### SSH Connection Failed

**Problem**: `ssh: connect to host 192.168.1.100 port 22: Connection refused`

**Solution**:
```bash
# Check SSH service on target
sudo systemctl status ssh

# Start SSH if not running
sudo systemctl start ssh
sudo systemctl enable ssh

# Check firewall
sudo ufw status
sudo ufw allow 22/tcp

# Test connection
ssh -v user@host  # Verbose mode for debugging
```

### Permission Denied (Android)

**Problem**: `Permission denied` when accessing /data/local/tmp

**Solution**:
```bash
# Check SELinux status
adb shell getenforce

# If enforcing, try different directory
adb shell mkdir -p /sdcard/ovbench
# Update config
```
```yaml
device:
  push_dir: "/sdcard/ovbench"
```

## Benchmark Execution Errors

### benchmark_app Not Found

**Problem**: `sh: benchmark_app: not found`

**Solution**:
```bash
# Verify file exists
adb shell ls -la /data/local/tmp/ovbench/bin/benchmark_app

# Check execute permission
adb shell chmod +x /data/local/tmp/ovbench/bin/benchmark_app

# Verify architecture match
adb shell file /data/local/tmp/ovbench/bin/benchmark_app
adb shell getprop ro.product.cpu.abi
```

### Library Loading Error

**Problem**: `error while loading shared libraries: libopenvino.so`

**Solution**:
```bash
# Set library path
adb shell "export LD_LIBRARY_PATH=/data/local/tmp/ovbench/lib:\$LD_LIBRARY_PATH && benchmark_app"

# Or in config
```
```yaml
device:
  env_vars:
    LD_LIBRARY_PATH: "/data/local/tmp/ovbench/lib:$LD_LIBRARY_PATH"
```

### Model File Not Found

**Problem**: `Failed to read model`

**Solution**:
```bash
# Verify model files exist
adb shell ls -la /data/local/tmp/ovbench/models/

# Check both .xml and .bin files
# Ensure matching base names
model.xml
model.bin  # Must have same base name

# Update config with correct path
```
```yaml
models:
  - name: "model"
    path: "/data/local/tmp/ovbench/models/model.xml"
```

### Timeout During Execution

**Problem**: `Benchmark timeout after 600 seconds`

**Solution**:
```yaml
# Increase timeout in config
run:
  timeout_sec: 1200  # 20 minutes

# Or reduce workload
run:
  matrix:
    niter: [50]  # Fewer iterations
```

## Performance Issues

### Low Throughput

**Problem**: Throughput significantly lower than expected

**Diagnosis**:
```bash
# Check CPU frequency
adb shell "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"

# Check thermal throttling
adb shell "cat /sys/class/thermal/thermal_zone*/temp"

# Check background processes
adb shell top -n 1
```

**Solutions**:

1. **Thermal throttling**:
   ```bash
   # Add cooldown
   ```
   ```yaml
   run:
     cooldown_sec: 60
   ```

2. **CPU governor**:
   ```bash
   # Set performance governor (requires root)
   adb shell "echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
   ```

3. **Background apps**:
   ```bash
   # Stop unnecessary apps
   adb shell am force-stop com.android.chrome
   adb shell settings put global window_animation_scale 0
   ```

### Inconsistent Results

**Problem**: Large variance in benchmark results

**Solution**:
```yaml
# Increase statistical validity
run:
  repeats: 10  # More repetitions
  warmup_runs: 5  # More warmup
  cooldown_sec: 30  # Between runs

# Stabilize device
device:
  setup_commands:
    - "settings put global window_animation_scale 0"
    - "input keyevent 26"  # Screen off
```

### Memory Issues

**Problem**: `std::bad_alloc` or out of memory

**Solution**:
```bash
# Check available memory
adb shell free -h

# Reduce batch size
```
```yaml
run:
  matrix:
    batch: [1]  # Smaller batch

# Clear memory before run
device:
  setup_commands:
    - "sync && echo 3 > /proc/sys/vm/drop_caches"
```

## Configuration Problems

### YAML Parsing Error

**Problem**: `yaml.scanner.ScannerError`

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Common issues:
# - Incorrect indentation (use spaces, not tabs)
# - Missing quotes around special characters
# - Invalid list/dict syntax
```

### Schema Validation Error

**Problem**: `pydantic.ValidationError`

**Solution**:
```python
# Debug configuration
from ovbench.config.schema import Experiment

try:
    config = Experiment.from_yaml("config.yaml")
except ValidationError as e:
    print(e.json(indent=2))
```

Common fixes:
- Ensure required fields are present
- Check value types match schema
- Verify enum values are valid

### Path Not Found

**Problem**: `FileNotFoundError: /path/to/openvino`

**Solution**:
```bash
# Use absolute paths
realpath relative/path

# Or use environment variables
export OPENVINO_ROOT=/path/to/openvino
```
```yaml
build:
  openvino_repo: "${OPENVINO_ROOT}"
```

## CI/CD Issues

### Self-Hosted Runner Offline

**Problem**: GitHub Actions waiting for runner

**Solution**:
```bash
# Check runner status
cd actions-runner
./run.sh  # Run interactively to see errors

# Common fixes
sudo ./svc.sh stop
sudo ./svc.sh start

# Check logs
journalctl -u actions.runner.* -f
```

### Artifact Upload Failed

**Problem**: `Error: Artifact upload failed`

**Solution**:
```yaml
# Reduce artifact size
- uses: actions/upload-artifact@v4
  with:
    name: results
    path: |
      results/*.csv
      results/*.json
      !results/raw_logs/
    retention-days: 7
    compression-level: 9
```

### Docker Build Failed

**Problem**: Docker image build fails in CI

**Solution**:
```dockerfile
# Add error handling
RUN apt-get update || exit 1
RUN apt-get install -y cmake ninja-build || exit 1

# Use build cache
# In workflow:
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## Common Error Messages

### Error Reference Table

| Error | Cause | Solution |
|-------|-------|----------|
| `INSTALL_FAILED_INSUFFICIENT_STORAGE` | Device full | Clear space: `adb shell rm -rf /data/local/tmp/old_files` |
| `INSTALL_FAILED_NO_MATCHING_ABIS` | Wrong architecture | Build for correct ABI (arm64-v8a) |
| `cmake: command not found` | CMake not installed | Install: `apt install cmake` |
| `ninja: command not found` | Ninja not installed | Install: `apt install ninja-build` |
| `device offline` | USB issue | Reconnect cable, restart ADB |
| `Read-only file system` | Permission issue | Use different directory or root |
| `Segmentation fault` | Binary incompatibility | Rebuild for target architecture |
| `std::bad_alloc` | Out of memory | Reduce batch size or model size |

## Debug Commands

### Diagnostic Script

```bash
#!/bin/bash
# diagnose.sh - Run diagnostics

echo "=== System Info ==="
uname -a
python --version
cmake --version
ninja --version

echo "=== Android Info ==="
adb devices
adb shell getprop ro.product.model
adb shell getprop ro.product.cpu.abi

echo "=== Device State ==="
adb shell free -h
adb shell df -h
adb shell top -n 1 | head -20

echo "=== Temperature ==="
adb shell "cat /sys/class/thermal/thermal_zone*/temp"

echo "=== CPU Info ==="
adb shell "cat /proc/cpuinfo | grep processor"
adb shell "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"
```

### Verbose Logging

```yaml
# Enable verbose output
run:
  custom_args:
    - "-d"  # Debug mode
    - "--log_level=DEBUG"
```

```python
# Python debugging
import logging
logging.basicConfig(level=logging.DEBUG)

from ovbench.pipeline import Pipeline
pipeline = Pipeline("config.yaml")
```

## Getting Help

If you're still experiencing issues:

1. **Check existing issues**: [GitHub Issues](https://github.com/embedded-dev-research/openvino_remote_benchmark/issues)
2. **Search discussions**: [GitHub Discussions](https://github.com/embedded-dev-research/openvino_remote_benchmark/discussions)
3. **File a bug report** with:
   - OVBench version: `ovbench --version`
   - Python version: `python --version`
   - Full error message and stack trace
   - Configuration file (sanitized)
   - Steps to reproduce
4. **Community support**: Email nesterov.alexander@outlook.com

## Next Steps

- [Architecture](architecture.md) - Understanding the system
- [API Reference](api-reference.md) - Programming interface
- [FAQ](user-guide.md#faq) - Frequently asked questions