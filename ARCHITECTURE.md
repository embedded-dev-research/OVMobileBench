# OVMobileBench Architecture

## Overview

OVMobileBench is an end-to-end benchmarking pipeline for OpenVINO on mobile devices. It automates the complete workflow from building OpenVINO runtime, packaging models and libraries, deploying to devices, running benchmarks, and generating reports.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│                  (CLI via Typer)                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                     Pipeline                             │
│              (Orchestration Layer)                       │
└─────┬──────┬──────┬──────┬──────┬──────┬──────────────┘
      │      │      │      │      │      │
┌─────▼──┐ ┌▼─────┐┌▼─────┐┌▼─────┐┌▼─────┐┌▼──────┐
│ Build  │ │Pack  ││Deploy││ Run  ││Parse ││Report│
│        │ │      ││      ││      ││      ││      │
└────────┘ └──────┘└──────┘└──────┘└──────┘└──────┘
     │         │       │       │       │       │
┌────▼─────────▼───────▼───────▼───────▼───────▼─────┐
│              Device Abstraction Layer               │
│         (Android/ADB, Linux/SSH, iOS/stub)          │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration System (`ovmobilebench/config/`)

**Purpose**: Define and validate experiment configurations.

**Key Classes**:
- `Experiment`: Top-level configuration container
- `BuildConfig`: OpenVINO build settings
- `DeviceConfig`: Target device specifications
- `RunConfig`: Benchmark execution parameters
- `ReportConfig`: Output format and sinks

**Technology**: Pydantic for schema validation and type safety.

### 2. CLI Interface (`ovmobilebench/cli.py`)

**Purpose**: Command-line interface for user interaction.

**Commands**:
- `build`: Build OpenVINO from source
- `package`: Create deployment bundle
- `deploy`: Push to device(s)
- `run`: Execute benchmarks
- `report`: Generate reports
- `all`: Complete pipeline execution

**Technology**: Typer for modern CLI with auto-completion.

### 3. Pipeline Orchestrator (`ovmobilebench/pipeline.py`)

**Purpose**: Coordinate execution of all pipeline stages.

**Responsibilities**:
- Stage dependency management
- Error handling and recovery
- Progress tracking
- Resource cleanup

**Design Pattern**: Chain of Responsibility with stage isolation.

### 4. Device Abstraction (`ovmobilebench/devices/`)

**Purpose**: Uniform interface for different device types.

**Implementations**:
- `AndroidDevice`: ADB-based Android device control
- `LinuxDevice`: SSH-based Linux device control (planned)
- `iOSDevice`: iOS device control (stub)

**Interface**:
```python
class Device(ABC):
    def push(local, remote)
    def pull(remote, local)
    def shell(command)
    def exists(path)
    def mkdir(path)
    def rm(path)
    def info()
```

### 5. Build System (`ovmobilebench/builders/`)

**Purpose**: Build OpenVINO runtime for target platforms.

**Features**:
- CMake configuration generation
- Cross-compilation support (Android NDK)
- Build caching
- Artifact collection

**Supported Platforms**:
- Android (arm64-v8a)
- Linux ARM (aarch64)

### 6. Packaging System (`ovmobilebench/packaging/`)

**Purpose**: Bundle runtime, libraries, and models.

**Bundle Structure**:
```
ovbundle.tar.gz
├── bin/
│   └── benchmark_app
├── lib/
│   ├── libopenvino.so
│   └── ...
├── models/
│   ├── model.xml
│   └── model.bin
└── README.txt
```

### 7. Benchmark Runner (`ovmobilebench/runners/`)

**Purpose**: Execute benchmark_app with various configurations.

**Features**:
- Matrix expansion (device, threads, streams, precision)
- Timeout handling
- Cooldown between runs
- Warmup runs
- Progress tracking

### 8. Output Parser (`ovmobilebench/parsers/`)

**Purpose**: Extract metrics from benchmark_app output.

**Metrics**:
- Throughput (FPS)
- Latencies (avg, median, min, max)
- Device utilization
- Memory usage

### 9. Report Generation (`ovmobilebench/report/`)

**Purpose**: Generate structured reports from results.

**Formats**:
- JSON: Machine-readable format
- CSV: Spreadsheet-compatible
- SQLite: Database format (planned)
- HTML: Visual reports (planned)

### 10. Core Utilities (`ovmobilebench/core/`)

**Shared Components**:
- `shell.py`: Command execution with timeout
- `fs.py`: File system operations
- `artifacts.py`: Artifact management
- `logging.py`: Structured logging
- `errors.py`: Custom exceptions

## Data Flow

### 1. Configuration Loading
```
YAML File → Pydantic Validation → Experiment Object
```

### 2. Build Flow
```
Git Checkout → CMake Configure → Ninja Build → Artifact Collection
```

### 3. Package Flow
```
Build Artifacts + Models → Tar Archive → Checksum Generation
```

### 4. Deployment Flow
```
Bundle → ADB/SSH Push → Remote Extraction → Permission Setup
```

### 5. Execution Flow
```
Matrix Expansion → Device Preparation → Benchmark Execution → Output Collection
```

### 6. Reporting Flow
```
Raw Output → Parsing → Aggregation → Format Conversion → Sink Writing
```

## Configuration Schema

### Experiment Configuration
```yaml
project:
  name: string
  run_id: string

build:
  openvino_repo: path
  toolchain:
    android_ndk: path

device:
  kind: android|linux_ssh
  serials: [string]

models:
  - name: string
    path: path

run:
  matrix:
    threads: [int]
    nstreams: [string]

report:
  sinks:
    - type: json|csv
      path: path
```

## Security Considerations

### Input Validation
- All user inputs validated via Pydantic
- Shell commands parameterized to prevent injection
- Path traversal prevention

### Secrets Management
- No hardcoded credentials
- Environment variables for sensitive data
- SSH key-based authentication

### Device Security
- ADB authorization required
- Limited command set execution
- Temporary file cleanup

## Performance Optimizations

### Build Caching
- CMake build cache
- ccache integration (planned)
- Incremental builds

### Parallel Execution
- Multiple device support
- Concurrent stage execution (where safe)
- Async I/O for file operations

### Resource Management
- Automatic cleanup of temporary files
- Connection pooling for SSH
- Memory-mapped file I/O for large files

## Extensibility Points

### Adding New Device Types
1. Inherit from `Device` base class
2. Implement required methods
3. Register in `pipeline.py`

### Adding New Report Formats
1. Inherit from `ReportSink`
2. Implement `write()` method
3. Register in configuration schema

### Adding New Benchmark Tools
1. Create runner in `runners/`
2. Create parser in `parsers/`
3. Update configuration schema

## Testing Strategy

### Unit Tests
- Configuration validation
- Parser accuracy
- Device command generation

### Integration Tests
- Pipeline stage transitions
- File operations
- Mock device operations

### System Tests
- End-to-end pipeline execution
- Real device testing (CI)
- Performance regression tests

## CI/CD Pipeline

### Build Stage
- Lint (Black, Ruff)
- Type check (MyPy)
- Unit tests (pytest)
- Coverage report

### Package Stage
- Build distribution
- Generate artifacts

### Test Stage
- Integration tests
- Dry-run validation

### Deploy Stage (manual)
- PyPI publishing
- Docker image creation
- Documentation update

## Future Enhancements

### Near Term
- SQLite report sink
- Linux SSH device support
- HTML report generation
- Docker development environment

### Long Term
- Web UI dashboard
- Real-time monitoring
- Cloud device farm integration
- Model optimization recommendations
- Performance regression detection
- Distributed execution

## Dependencies

### Runtime
- Python 3.11+
- typer: CLI framework
- pydantic: Data validation
- pyyaml: YAML parsing
- paramiko: SSH client
- pandas: Data manipulation
- rich: Terminal formatting

### Build
- Android NDK r26d+
- CMake 3.24+
- Ninja 1.11+

### Development
- pip: Dependency management
- pytest: Testing framework
- black: Code formatting
- ruff: Linting
- mypy: Type checking

## License

Apache License 2.0
