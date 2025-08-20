# OVMobileBench - OpenVINO™ Mobile Benchmarking Pipeline

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/embedded-dev-research/OVMobileBench/actions/workflows/bench.yml/badge.svg)](https://github.com/embedded-dev-research/OVMobileBench/actions)
[![codecov](https://codecov.io/gh/embedded-dev-research/OVMobileBench/branch/main/graph/badge.svg)](https://codecov.io/gh/embedded-dev-research/OVMobileBench)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

**OVMobileBench** is an end-to-end automation pipeline for benchmarking OpenVINO inference performance on mobile devices. It handles the complete workflow from building OpenVINO runtime, packaging models, deploying to devices, executing benchmarks, and generating comprehensive reports.

## 🚀 Quick Start

```bash
# Install from source
git clone https://github.com/embedded-dev-research/OVMobileBench.git
cd OVMobileBench
pip install -e .

# Run complete benchmark pipeline
ovmobilebench all -c experiments/android_example.yaml

# View results
cat experiments/results/*.csv
```

### OpenVINO Distribution Modes

OVMobileBench supports three flexible ways to obtain OpenVINO:

1. **Build Mode** - Build OpenVINO from source
2. **Install Mode** - Use pre-built OpenVINO installation
3. **Link Mode** - Download OpenVINO archive (supports "latest" for auto-detection)

See [Configuration Reference](docs/configuration.md) for details.

## 📚 Documentation

- **[Getting Started Guide](docs/getting-started.md)** - Installation and first benchmark
- **[OpenVINO Modes Guide](docs/openvino-modes.md)** - Three ways to obtain OpenVINO runtime
- **[User Guide](docs/user-guide.md)** - Complete usage documentation
- **[Configuration Reference](docs/configuration.md)** - YAML configuration schema
- **[Device Setup](docs/device-setup.md)** - Android/Linux device preparation
- **[Android Installer Module](docs/android_installer.md)** - Automated Android SDK/NDK setup
- **[Build Guide](docs/build-guide.md)** - Building OpenVINO for mobile
- **[Benchmarking Guide](docs/benchmarking.md)** - Running and interpreting benchmarks
- **[CI/CD Integration](docs/ci-cd.md)** - GitHub Actions and automation
- **[API Reference](docs/api-reference.md)** - Python API documentation
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## ✨ Key Features

- 🔨 **Flexible OpenVINO Distribution** - Three modes: build from source, use existing install, or download archives
- 📦 **Smart Packaging** - Bundle runtime, libraries, and models
- 🚀 **Multi-Device** - Deploy via ADB (Android) or SSH (Linux using paramiko)
- ⚡ **Matrix Testing** - Test multiple configurations automatically
- 📊 **Rich Reports** - JSON/CSV output with detailed metrics
- 🌡️ **Device Control** - Temperature monitoring, performance tuning
- 🔄 **CI/CD Ready** - GitHub Actions integration included
- 📈 **Reproducible** - Full provenance tracking of builds and runs
- 🤖 **Android SDK/NDK Installer** - Automated setup of Android development tools
- 🔗 **Auto-Download** - Fetch latest OpenVINO builds for your platform

## 🔧 Supported Platforms

| Host OS | Host Arch    | Device OS | Device Arch  | Transport | Library   | Status     |
|---------|--------------|-----------|--------------|-----------|-----------|------------|
| Linux   | x86_64/ARM64 | Android   | x86_64/ARM64 | ADB       | adbutils  | ✅ Stable  |
| macOS   | x86_64/ARM64 | Android   | x86_64/ARM64 | ADB       | adbutils  | ✅ Stable  |
| Windows | x86_64/ARM64 | Android   | x86_64/ARM64 | ADB       | adbutils  | ✅ Stable  |
| Linux   | x86_64       | Linux     | ARM64/ARM32  | SSH       | paramiko  | ✅ Stable  |
| macOS   | x86_64/ARM64 | Linux     | ARM64/ARM32  | SSH       | paramiko  | ✅ Stable  |
| Windows | x86_64/ARM64 | Linux     | ARM64/ARM32  | SSH       | paramiko  | ✅ Stable  |
| Any     | Any          | iOS       | ARM64        | USB       | -         | 🚧 Planned |

## 📋 Requirements

- **Python**: 3.11+
- **For Android targets**:
  - Android NDK r26d+
  - CMake 3.24+
  - Ninja 1.11+
  - Android device with USB debugging enabled
- **For Linux ARM targets**:
  - SSH access to device
  - Cross-compilation toolchain

## 🎯 Use Cases

- **Performance Testing** - Measure inference speed across devices
- **Regression Detection** - Track performance changes over time
- **Hardware Evaluation** - Compare different SoCs and configurations
- **Model Optimization** - Find optimal runtime parameters
- **CI/CD Integration** - Automated testing in development pipelines

## 📖 Learn More

- [Getting Started Guide](docs/getting-started.md)
- [Android SDK/NDK Setup](docs/android-setup.md)
- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 💬 Support

- 📝 [GitHub Issues](https://github.com/embedded-dev-research/OVMobileBench/issues) - Bug reports and feature requests
- 💡 [Discussions](https://github.com/embedded-dev-research/OVMobileBench/discussions) - Questions and ideas
- 📧 Contact: <nesterov.alexander@outlook.com>
