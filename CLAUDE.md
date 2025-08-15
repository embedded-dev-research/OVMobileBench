# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OVBench is an end-to-end benchmarking pipeline for OpenVINO on mobile devices, primarily targeting Android platforms. It automates the complete workflow from building OpenVINO runtime, packaging models, deploying to devices, running benchmarks, and generating reports.

## Commands

### Installation and Setup
```bash
# Install dependencies
poetry install

# List available Android devices
poetry run ovbench list-devices
# or
make devices
```

### Running Benchmarks
```bash
# Run complete pipeline
make all CFG=experiments/android_example.yaml

# Run individual stages
make build CFG=experiments/android_example.yaml
make package CFG=experiments/android_example.yaml
make deploy CFG=experiments/android_example.yaml
make run CFG=experiments/android_example.yaml
make report CFG=experiments/android_example.yaml
```

### Development
```bash
# Run linters
make lint

# Run tests
make test

# Clean artifacts
make clean
```

## Architecture

### Core Modules

1. **config/** - Configuration schema and loaders using Pydantic
   - `schema.py`: Defines configuration models
   - `loader.py`: YAML configuration loading

2. **devices/** - Device abstraction layer
   - `base.py`: Abstract device interface
   - `android.py`: Android device implementation via ADB

3. **builders/** - Build system for OpenVINO
   - `openvino.py`: Handles CMake configuration and building for Android

4. **packaging/** - Bundle creation for deployment
   - `packager.py`: Creates tar.gz bundles with runtime and models

5. **runners/** - Benchmark execution
   - `benchmark.py`: Runs benchmark_app with various configurations

6. **parsers/** - Output parsing
   - `benchmark_parser.py`: Extracts metrics from benchmark_app output

7. **report/** - Report generation
   - `sink.py`: Outputs to JSON/CSV formats

8. **pipeline.py** - Main orchestration logic

## Key Configuration Fields

The YAML configuration must specify:
- `build.openvino_repo`: Path to OpenVINO source
- `build.toolchain.android_ndk`: Path to Android NDK
- `device.serials`: List of device serials from `adb devices`
- `models[].path`: Paths to model XML files

## Android-Specific Notes

- Default deployment path: `/data/local/tmp/ovbench`
- Requires Android NDK r26d or newer
- Target ABI: arm64-v8a
- Minimum API level: 24 (Android 7.0)

## Common Development Tasks

### Adding a new device type
1. Create new class in `devices/` inheriting from `Device`
2. Implement all abstract methods
3. Update `pipeline._get_device()` to support new type

### Adding a new report format
1. Create new sink class in `report/` inheriting from `ReportSink`
2. Implement `write()` method
3. Update `pipeline.report()` to handle new type

### Modifying benchmark parameters
Edit `config/schema.py`:
- Add fields to `RunMatrix` for new parameters
- Update `runners/benchmark.py` to use new parameters

## Testing Considerations

- Mock ADB commands when testing Android functionality
- Use dry-run mode for testing pipeline without actual execution
- Validate YAML configurations before running