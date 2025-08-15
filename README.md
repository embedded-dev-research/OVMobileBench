# OVBench - OpenVINO™ Mobile Benchmarking Pipeline

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/embedded-dev-research/openvino_remote_benchmark/actions/workflows/bench.yml/badge.svg)](https://github.com/embedded-dev-research/openvino_remote_benchmark/actions)

**OVBench** is an end-to-end automation pipeline for benchmarking OpenVINO inference performance on mobile devices. It handles the complete workflow from building OpenVINO runtime, packaging models, deploying to devices, executing benchmarks, and generating comprehensive reports.

## 🚀 Quick Start

```bash
# Install from source
git clone https://github.com/embedded-dev-research/openvino_remote_benchmark.git
cd openvino_remote_benchmark
pip install -e .

# Run complete benchmark pipeline
ovbench all -c experiments/android_example.yaml

# View results
cat experiments/results/*.csv
```

## 📚 Documentation

- **[Getting Started Guide](docs/getting-started.md)** - Installation and first benchmark
- **[User Guide](docs/user-guide.md)** - Complete usage documentation
- **[Configuration Reference](docs/configuration.md)** - YAML configuration schema
- **[Device Setup](docs/device-setup.md)** - Android/Linux device preparation
- **[Build Guide](docs/build-guide.md)** - Building OpenVINO for mobile
- **[Benchmarking Guide](docs/benchmarking.md)** - Running and interpreting benchmarks
- **[CI/CD Integration](docs/ci-cd.md)** - GitHub Actions and automation
- **[API Reference](docs/api-reference.md)** - Python API documentation
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## ✨ Key Features

- 🔨 **Automated Build** - Cross-compile OpenVINO for Android/Linux ARM
- 📦 **Smart Packaging** - Bundle runtime, libraries, and models
- 🚀 **Multi-Device** - Deploy via ADB (Android) or SSH (Linux)
- ⚡ **Matrix Testing** - Test multiple configurations automatically
- 📊 **Rich Reports** - JSON/CSV output with detailed metrics
- 🌡️ **Device Control** - Temperature monitoring, performance tuning
- 🔄 **CI/CD Ready** - GitHub Actions integration included
- 📈 **Reproducible** - Full provenance tracking of builds and runs

## 🔧 Supported Platforms

| Platform | Architecture | Transport | Status |
|----------|-------------|-----------|--------|
| Android | ARM64 (arm64-v8a) | ADB | ✅ Stable |
| Linux | ARM64/ARM32 | SSH | ✅ Stable |
| iOS | ARM64 | USB | 🚧 Planned |

## 📋 Requirements

- **Python**: 3.11+
- **For Android targets**:
  - Android NDK r26d+
  - Android SDK Platform Tools (adb)
  - CMake 3.24+
  - Ninja 1.11+
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

- [Architecture Overview](docs/architecture.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 💬 Support

- 📝 [GitHub Issues](https://github.com/embedded-dev-research/openvino_remote_benchmark/issues) - Bug reports and feature requests
- 💡 [Discussions](https://github.com/embedded-dev-research/openvino_remote_benchmark/discussions) - Questions and ideas
- 📧 Contact: nesterov.alexander@outlook.com
