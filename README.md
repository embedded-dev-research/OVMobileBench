# OVBench - OpenVINO™ Mobile Benchmarking Pipeline

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

End-to-end benchmarking pipeline for OpenVINO on mobile devices (Android, Linux ARM). Automates building, packaging, deployment, execution, and reporting of benchmark_app performance metrics.

## Features

- 🔨 **Automated Build**: Build OpenVINO runtime and benchmark_app for Android (arm64-v8a)
- 📦 **Smart Packaging**: Bundle runtime, libraries, and models into deployable packages
- 🚀 **Easy Deployment**: Deploy to devices via ADB (Android) or SSH (Linux)
- ⚡ **Matrix Testing**: Run benchmarks with multiple configurations (threads, streams, batch sizes)
- 📊 **Rich Reports**: Generate CSV/JSON reports with performance metrics
- 🌡️ **Device Optimization**: Automatic device preparation (disable animations, screen off, temperature monitoring)

## Requirements

- Python 3.11+
- Android NDK r26d+ (for building)
- Android SDK Platform Tools (adb)
- CMake 3.24+
- Ninja 1.11+
- OpenVINO source code
- Android device with USB debugging enabled

## Installation

```bash
# Install with Poetry
poetry install

# Or with pip
pip install -e .
```

## Quick Start

1. **Configure your experiment** by editing `experiments/android_example.yaml`:
   - Set path to OpenVINO repository
   - Set path to Android NDK
   - Add your device serial (from `adb devices`)
   - Specify model paths

2. **Run the complete pipeline**:
```bash
make all CFG=experiments/android_example.yaml
```

Or run individual stages:
```bash
make build    # Build OpenVINO
make package  # Create deployment bundle
make deploy   # Deploy to device
make run      # Execute benchmarks
make report   # Generate reports
```

## CLI Commands

```bash
# List available devices
ovbench list-devices

# Run complete pipeline
ovbench all -c experiments/android_example.yaml

# Run individual stages
ovbench build -c config.yaml
ovbench package -c config.yaml
ovbench deploy -c config.yaml
ovbench run -c config.yaml
ovbench report -c config.yaml
```

## Configuration

See `experiments/android_example.yaml` for a complete configuration example. Key settings:

```yaml
build:
  openvino_repo: /path/to/openvino
  toolchain:
    android_ndk: /path/to/android-ndk-r26d

device:
  serials: ["YOUR_DEVICE_SERIAL"]

models:
  - name: resnet50
    path: models/resnet50_fp16.xml

run:
  matrix:
    threads: [2, 4]
    nstreams: ["1", "2"]
```

## Project Structure

```
ovbench/
├── cli.py           # CLI interface
├── pipeline.py      # Main orchestration
├── config/          # Configuration schemas
├── devices/         # Device abstractions (Android, Linux)
├── builders/        # OpenVINO build system
├── packaging/       # Bundle creation
├── runners/         # Benchmark execution
├── parsers/         # Output parsing
└── report/          # Report generation
```

## Development

```bash
# Run linters
make lint

# Run tests
make test

# Clean artifacts
make clean
```

## License

Apache License 2.0. See [LICENSE](LICENSE) file.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## Support

For issues and questions, please use GitHub Issues.
