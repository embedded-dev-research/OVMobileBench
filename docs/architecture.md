# OVMobileBench Architecture

## Overview

OVMobileBench is an end-to-end benchmarking pipeline for OpenVINO on mobile devices. It automates the complete workflow from obtaining OpenVINO runtime, packaging models and libraries, deploying to devices, running benchmarks, and generating comprehensive reports.

## System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI via Typer]
        Config[YAML Configuration]
    end

    subgraph "Pipeline Orchestration"
        Pipeline[Pipeline Controller]
        OVMode{OpenVINO Mode}
    end

    subgraph "OpenVINO Distribution"
        Build[Build from Source]
        Install[Use Installation]
        Link[Download Archive]
    end

    subgraph "Pipeline Stages"
        Package[Package Bundle]
        Deploy[Deploy to Devices]
        Run[Run Benchmarks]
        Parse[Parse Results]
        Report[Generate Reports]
    end

    subgraph "Device Layer"
        Android[Android/ADB]
        Linux[Linux/SSH]
        iOS[iOS/USB]
    end

    subgraph "Storage"
        Artifacts[Artifacts Storage]
        Results[Results Database]
    end

    CLI --> Pipeline
    Config --> Pipeline
    Pipeline --> OVMode

    OVMode -->|mode=build| Build
    OVMode -->|mode=install| Install
    OVMode -->|mode=link| Link

    Build --> Package
    Install --> Package
    Link --> Package

    Package --> Deploy
    Deploy --> Run
    Run --> Parse
    Parse --> Report

    Deploy --> Android
    Deploy --> Linux
    Deploy --> iOS

    Package --> Artifacts
    Report --> Results
```

## High-Level Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Pipeline
    participant OpenVINO
    participant Device
    participant Report

    User->>CLI: ovmobilebench all -c config.yaml
    CLI->>Pipeline: Load configuration
    Pipeline->>Pipeline: Validate config

    alt Build Mode
        Pipeline->>OpenVINO: Build from source
    else Install Mode
        Pipeline->>OpenVINO: Use existing install
    else Link Mode
        Pipeline->>OpenVINO: Download archive
    end

    Pipeline->>Pipeline: Package bundle
    Pipeline->>Device: Deploy bundle
    Pipeline->>Device: Execute benchmarks
    Device-->>Pipeline: Return results
    Pipeline->>Report: Parse & aggregate
    Report-->>User: Generate outputs
```

## Component Architecture

```mermaid
graph LR
    subgraph "Core Components"
        direction TB
        Config[Configuration<br/>Pydantic Schemas]
        Pipeline[Pipeline<br/>Orchestration]
        Device[Device<br/>Abstraction]
        Builder[Builder<br/>OpenVINO]
        Packager[Packager<br/>Bundle Creation]
        Runner[Runner<br/>Benchmark Exec]
        Parser[Parser<br/>Result Extract]
        Reporter[Reporter<br/>Output Gen]
    end

    subgraph "Utilities"
        Shell[Shell<br/>Commands]
        FS[FileSystem<br/>Operations]
        Log[Logging<br/>Structured]
        Error[Error<br/>Handling]
    end

    Config --> Pipeline
    Pipeline --> Builder
    Pipeline --> Packager
    Pipeline --> Runner
    Runner --> Device
    Runner --> Parser
    Parser --> Reporter

    Builder --> Shell
    Device --> Shell
    Packager --> FS
    Reporter --> FS
```

## Core Components

### 1. Configuration System (`ovmobilebench/config/`)

**Purpose**: Define and validate experiment configurations with strong typing.

```mermaid
classDiagram
    class Experiment {
        +ProjectConfig project
        +OpenVINOConfig openvino
        +DeviceConfig device
        +ModelsConfig models
        +RunConfig run
        +ReportConfig report
        +validate()
    }

    class OpenVINOConfig {
        +mode: build|install|link
        +source_dir: Optional[str]
        +install_dir: Optional[str]
        +archive_url: Optional[str]
        +validate_mode()
    }

    class DeviceConfig {
        +kind: android|linux_ssh|ios
        +serials: List[str]
        +host: Optional[str]
        +validate_device()
    }

    Experiment --> OpenVINOConfig
    Experiment --> DeviceConfig
```

### 2. OpenVINO Distribution System

**Three flexible modes for obtaining OpenVINO runtime:**

```mermaid
stateDiagram-v2
    [*] --> ConfigLoad
    ConfigLoad --> ModeCheck

    ModeCheck --> BuildMode: mode="build"
    ModeCheck --> InstallMode: mode="install"
    ModeCheck --> LinkMode: mode="link"

    BuildMode --> CloneRepo
    CloneRepo --> Configure
    Configure --> Compile
    Compile --> CollectArtifacts

    InstallMode --> ValidateDir
    ValidateDir --> CollectArtifacts

    LinkMode --> CheckURL
    CheckURL --> Download: URL provided
    CheckURL --> DetectLatest: URL="latest"
    DetectLatest --> Download
    Download --> Extract
    Extract --> CollectArtifacts

    CollectArtifacts --> [*]
```

### 3. Device Abstraction Layer

**Uniform interface for different device types:**

```mermaid
classDiagram
    class Device {
        <<abstract>>
        +push(local, remote)
        +pull(remote, local)
        +shell(command)
        +exists(path)
        +mkdir(path)
        +rm(path)
        +info()
        +is_available()
    }

    class AndroidDevice {
        -adb_client
        +install_apk()
        +screenshot()
        +get_temperature()
    }

    class LinuxSSHDevice {
        -ssh_client
        +connect()
        +disconnect()
    }

    class iOSDevice {
        -usb_client
        +install_app()
    }

    Device <|-- AndroidDevice
    Device <|-- LinuxSSHDevice
    Device <|-- iOSDevice
```

### 4. Pipeline Execution Flow

```mermaid
flowchart TB
    Start([Start]) --> LoadConfig[Load Configuration]
    LoadConfig --> ValidateConfig{Valid?}
    ValidateConfig -->|No| Error1[Configuration Error]
    ValidateConfig -->|Yes| CheckMode{OpenVINO Mode?}

    CheckMode -->|build| BuildOV[Build OpenVINO]
    CheckMode -->|install| UseInstall[Use Installation]
    CheckMode -->|link| DownloadOV[Download Archive]

    BuildOV --> Package
    UseInstall --> Package
    DownloadOV --> Package

    Package[Create Package] --> Deploy[Deploy to Devices]
    Deploy --> CheckDevices{Devices Available?}
    CheckDevices -->|No| Error2[Device Error]
    CheckDevices -->|Yes| RunBenchmark

    RunBenchmark[Run Benchmarks] --> ParseResults[Parse Results]
    ParseResults --> GenerateReport[Generate Reports]
    GenerateReport --> End([End])

    Error1 --> End
    Error2 --> End
```

## Data Flow Architecture

### Configuration to Execution

```mermaid
graph LR
    subgraph Input
        YAML[YAML Config]
        ENV[Environment Vars]
    end

    subgraph Processing
        Parse[Parse & Validate]
        Expand[Matrix Expansion]
        Schedule[Task Scheduling]
    end

    subgraph Execution
        Tasks[Task Queue]
        Workers[Worker Pool]
        Results[Result Queue]
    end

    subgraph Output
        JSON[JSON Report]
        CSV[CSV Report]
        HTML[HTML Report]
    end

    YAML --> Parse
    ENV --> Parse
    Parse --> Expand
    Expand --> Schedule
    Schedule --> Tasks
    Tasks --> Workers
    Workers --> Results
    Results --> JSON
    Results --> CSV
    Results --> HTML
```

### Artifact Management

```mermaid
graph TD
    subgraph "Artifact Storage Structure"
        Root[artifacts/run_id/]
        Root --> BuildDir[build/]
        Root --> OVDownload[openvino_download/]
        Root --> Packages[packages/]
        Root --> Results[results/]
        Root --> Reports[reports/]

        BuildDir --> CMakeCache[CMakeCache.txt]
        BuildDir --> BinDir[bin/]
        BuildDir --> LibDir[lib/]

        OVDownload --> Archive[openvino.tar.gz]
        OVDownload --> Extracted[extracted/]

        Packages --> Bundle[bundle.tar.gz]
        Packages --> Manifest[manifest.json]

        Results --> RawOutput[raw_output/]
        Results --> ParsedData[parsed_data/]

        Reports --> JSONReport[report.json]
        Reports --> CSVReport[report.csv]
    end
```

## Performance Architecture

### Parallel Execution Strategy

```mermaid
graph TB
    subgraph "Matrix Expansion"
        Config[Run Configuration]
        Config --> Matrix{Parameter Matrix}
        Matrix --> C1[Config 1]
        Matrix --> C2[Config 2]
        Matrix --> C3[Config N]
    end

    subgraph "Device Pool"
        D1[Device 1]
        D2[Device 2]
        D3[Device M]
    end

    subgraph "Execution"
        Queue[Task Queue]
        Scheduler[Scheduler]

        C1 --> Queue
        C2 --> Queue
        C3 --> Queue

        Queue --> Scheduler

        Scheduler --> D1
        Scheduler --> D2
        Scheduler --> D3
    end

    subgraph "Aggregation"
        D1 --> Collector[Result Collector]
        D2 --> Collector
        D3 --> Collector
        Collector --> Aggregator[Aggregator]
        Aggregator --> Report[Final Report]
    end
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        Input[User Input]
        Input --> Validation[Input Validation<br/>Pydantic Schemas]
        Validation --> Sanitization[Command Sanitization<br/>Parameter Escaping]
        Sanitization --> Execution[Safe Execution<br/>Subprocess Controls]

        Secrets[Secrets Management]
        Secrets --> EnvVars[Environment Variables]
        Secrets --> SSHKeys[SSH Keys]
        Secrets --> NoHardcode[No Hardcoded Creds]

        Device[Device Security]
        Device --> USBAuth[USB Debug Auth]
        Device --> SSHAuth[SSH Auth]
        Device --> TempClean[Temp Cleanup]
    end
```

## Extensibility Architecture

### Plugin System Design

```mermaid
classDiagram
    class PluginInterface {
        <<interface>>
        +name: str
        +version: str
        +initialize()
        +execute()
        +cleanup()
    }

    class DevicePlugin {
        +connect()
        +disconnect()
        +execute_command()
    }

    class ReportPlugin {
        +format_data()
        +write_output()
    }

    class BenchmarkPlugin {
        +prepare()
        +run()
        +parse_output()
    }

    PluginInterface <|-- DevicePlugin
    PluginInterface <|-- ReportPlugin
    PluginInterface <|-- BenchmarkPlugin

    class PluginManager {
        -plugins: Dict
        +register(plugin)
        +get(name)
        +list_available()
    }

    PluginManager --> PluginInterface
```

## Error Handling Architecture

```mermaid
stateDiagram-v2
    [*] --> Normal
    Normal --> Error: Exception

    Error --> Recoverable
    Error --> NonRecoverable

    Recoverable --> Retry: Retry Logic
    Retry --> Normal: Success
    Retry --> NonRecoverable: Max Retries

    NonRecoverable --> Cleanup
    Cleanup --> Report
    Report --> [*]

    state Recoverable {
        NetworkError
        DeviceTimeout
        ResourceBusy
    }

    state NonRecoverable {
        ConfigError
        BuildError
        FatalError
    }
```

## CI/CD Integration

```mermaid
graph LR
    subgraph "GitHub Actions Workflow"
        Push[Code Push]
        Push --> Lint[Lint & Format]
        Lint --> Test[Unit Tests]
        Test --> Build[Build Pipeline]
        Build --> Integration[Integration Tests]
        Integration --> Coverage[Coverage Report]
        Coverage --> Deploy{Deploy?}
        Deploy -->|Yes| PyPI[PyPI Release]
        Deploy -->|No| End[End]
    end

    subgraph "Quality Gates"
        Coverage --> CovCheck{Coverage > 80%?}
        CovCheck -->|No| Fail[Build Failed]
        CovCheck -->|Yes| Pass[Build Passed]
    end
```

## Monitoring & Observability

```mermaid
graph TB
    subgraph "Metrics Collection"
        Runtime[Runtime Metrics]
        Performance[Performance Metrics]
        Device[Device Metrics]
    end

    subgraph "Logging"
        Structured[Structured Logs]
        Debug[Debug Logs]
        Error[Error Logs]
    end

    subgraph "Reporting"
        Dashboard[Dashboard]
        Alerts[Alerts]
        Trends[Trend Analysis]
    end

    Runtime --> Dashboard
    Performance --> Dashboard
    Device --> Dashboard

    Structured --> Alerts
    Error --> Alerts

    Dashboard --> Trends
```

## Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Core implementation |
| CLI | Typer | Command-line interface |
| Validation | Pydantic | Configuration validation |
| Android | adbutils | Device communication |
| SSH | Paramiko | Linux device access |
| Data | Pandas | Result processing |
| Testing | Pytest | Test framework |
| Formatting | Black | Code formatting |
| Linting | Ruff | Code quality |
| Types | MyPy | Type checking |

### Build Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| Android NDK | r26d+ | Android cross-compilation |
| CMake | 3.24+ | Build configuration |
| Ninja | 1.11+ | Build execution |
| Python | 3.11+ | Runtime requirement |

## Future Enhancements

### Roadmap

```mermaid
timeline
    title OVMobileBench Development Roadmap

    section Q1 2025
        OpenVINO Modes     : Three distribution modes
        Test Coverage      : 80%+ coverage
        Documentation      : Complete docs

    section Q2 2025
        Web Dashboard      : Real-time monitoring
        Cloud Integration  : AWS Device Farm
        Auto-optimization  : Model tuning

    section Q3 2025
        Distributed Exec   : Multi-host support
        ML Insights        : Performance prediction
        Enterprise Features: LDAP, audit logs
```

## License

Apache License 2.0 - See [LICENSE](../LICENSE) for details.
