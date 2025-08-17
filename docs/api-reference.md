# API Reference

Complete API documentation for OVMobileBench Python modules.

## Table of Contents

1. [Pipeline API](#pipeline-api)
2. [Configuration API](#configuration-api)
3. [Device API](#device-api)
4. [Builder API](#builder-api)
5. [Runner API](#runner-api)
6. [Parser API](#parser-api)
7. [Report API](#report-api)
8. [Android Installer API](#android-installer-api)
9. [Utilities](#utilities)

## Pipeline API

### `ovmobilebench.pipeline`

Main orchestration module for running benchmarks.

#### `Pipeline`

```python
class Pipeline:
    """Main pipeline orchestrator"""

    def __init__(self, config: Union[str, Path, Experiment]):
        """
        Initialize pipeline with configuration.

        Args:
            config: Path to YAML config file or Experiment object
        """

    def run(self, stages: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run pipeline stages.

        Args:
            stages: List of stages to run. If None, runs all stages.
                   Valid stages: ['build', 'package', 'deploy', 'run', 'report']

        Returns:
            Dictionary with results from each stage

        Raises:
            PipelineError: If any stage fails
        """

    def build(self) -> BuildResult:
        """Build OpenVINO from source"""

    def package(self) -> PackageResult:
        """Create deployment bundle"""

    def deploy(self) -> DeployResult:
        """Deploy to target devices"""

    def run_benchmarks(self) -> BenchmarkResult:
        """Execute benchmarks"""

    def report(self) -> ReportResult:
        """Generate reports"""
```

#### Example Usage

```python
from ovmobilebench.pipeline import Pipeline

# Create pipeline from config file
pipeline = Pipeline("experiments/config.yaml")

# Run complete pipeline
results = pipeline.run()

# Run specific stages
results = pipeline.run(stages=["deploy", "run", "report"])

# Access individual stages
build_result = pipeline.build()
benchmark_result = pipeline.run_benchmarks()
```

## Configuration API

### `ovmobilebench.config.schema`

Pydantic models for configuration validation.

#### `Experiment`

```python
class Experiment(BaseModel):
    """Top-level experiment configuration"""

    project: ProjectConfig
    build: BuildConfig
    package: PackageConfig
    device: DeviceConfig
    models: List[ModelItem]
    run: RunConfig
    report: ReportConfig

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "Experiment":
        """Load configuration from YAML file"""

    def to_yaml(self, path: Union[str, Path]) -> None:
        """Save configuration to YAML file"""

    def override(self, overrides: Dict[str, Any]) -> "Experiment":
        """Apply overrides to configuration"""
```

#### `BuildConfig`

```python
class BuildConfig(BaseModel):
    """Build configuration"""

    enabled: bool = True
    openvino_repo: str
    openvino_commit: str = "HEAD"
    build_type: Literal["Release", "Debug", "RelWithDebInfo"] = "Release"
    toolchain: Toolchain
    options: Dict[str, str] = {}

    def validate_paths(self) -> None:
        """Validate that all paths exist"""

    def get_cmake_args(self) -> List[str]:
        """Generate CMake arguments"""
```

#### `RunConfig`

```python
class RunConfig(BaseModel):
    """Benchmark execution configuration"""

    repeats: int = 3
    warmup_runs: int = 0
    cooldown_sec: int = 0
    timeout_sec: Optional[int] = None
    matrix: RunMatrix

    def expand_matrix(self) -> List[Dict[str, Any]]:
        """Expand matrix into individual configurations"""

    def estimate_duration(self) -> timedelta:
        """Estimate total execution time"""
```

#### Example Usage

```python
from ovmobilebench.config.schema import Experiment

# Load configuration
config = Experiment.from_yaml("config.yaml")

# Access configuration
print(config.project.name)
print(config.run.matrix.threads)

# Modify configuration
config.run.repeats = 5
config.models.append(ModelItem(
    name="new_model",
    path="models/new.xml"
))

# Save modified configuration
config.to_yaml("modified_config.yaml")

# Apply overrides
overrides = {
    "run.matrix.threads": [1, 2, 4],
    "device.serials": ["device1", "device2"]
}
modified = config.override(overrides)
```

## Device API

### `ovmobilebench.devices.base`

Base class for device implementations.

#### `Device`

```python
class Device(ABC):
    """Abstract base class for devices"""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to device"""

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to device"""

    @abstractmethod
    def push(self, local: Path, remote: str) -> None:
        """Push file to device"""

    @abstractmethod
    def pull(self, remote: str, local: Path) -> None:
        """Pull file from device"""

    @abstractmethod
    def shell(self, command: str, timeout: Optional[int] = None) -> ShellResult:
        """Execute command on device"""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if path exists on device"""

    @abstractmethod
    def mkdir(self, path: str, parents: bool = True) -> None:
        """Create directory on device"""

    @abstractmethod
    def rm(self, path: str, recursive: bool = False) -> None:
        """Remove file/directory on device"""

    @abstractmethod
    def info(self) -> DeviceInfo:
        """Get device information"""
```

### `ovmobilebench.devices.android`

Android device implementation using **adbutils** library for direct Python-based device control.

#### `AndroidDevice`

```python
class AndroidDevice(Device):
    """Android device via adbutils Python library"""

    def __init__(self, serial: str, use_root: bool = False):
        """
        Initialize Android device.

        Args:
            serial: Device serial number
            use_root: Whether to use root access
        """

    def get_temperature(self) -> float:
        """Get device temperature in Celsius"""

    def get_cpu_info(self) -> CPUInfo:
        """Get CPU information"""

    def set_cpu_governor(self, governor: str) -> None:
        """Set CPU frequency governor (requires root)"""

    def screenshot(self, path: Path) -> None:
        """Take screenshot and save to path"""
```

### `ovmobilebench.devices.linux_ssh`

Linux device implementation using **paramiko** library for secure SSH connections and operations.

#### `LinuxSSHDevice`

```python
class LinuxSSHDevice(Device):
    """Linux device via SSH using paramiko"""

    def __init__(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        port: int = 22,
        push_dir: str = "/tmp/ovmobilebench"
    ):
        """
        Initialize SSH connection to Linux device.

        Args:
            host: Hostname or IP address
            username: SSH username
            password: SSH password (optional if using key)
            key_filename: Path to SSH private key
            port: SSH port (default 22)
            push_dir: Remote directory for deployment
        """

    def get_env(self) -> Dict[str, str]:
        """Get environment variables for benchmark execution"""
```

#### Example Usage

```python
# Example 1: Android Device
from ovmobilebench.devices.android import AndroidDevice

# Create device connection
device = AndroidDevice("R3CN30XXXX")
device.connect()

# Transfer files
device.push(Path("model.xml"), "/data/local/tmp/model.xml")
device.mkdir("/data/local/tmp/ovmobilebench")

# Execute commands
result = device.shell("ls -la /data/local/tmp")
print(result.stdout)

# Get device info
info = device.info()
print(f"Model: {info.model}")
print(f"CPU: {info.cpu}")

# Monitor temperature
temp = device.get_temperature()
print(f"Temperature: {temp}°C")

device.disconnect()

# Example 2: Linux SSH Device
from ovmobilebench.devices.linux_ssh import LinuxSSHDevice

# Connect via SSH with key authentication
device = LinuxSSHDevice(
    host="192.168.1.100",
    username="ubuntu",
    key_filename="~/.ssh/id_rsa",
    push_dir="/home/ubuntu/ovmobilebench"
)

# Transfer files via SFTP
device.push(Path("model.xml"), "/home/ubuntu/ovmobilebench/model.xml")

# Execute remote commands
ret, stdout, stderr = device.shell("uname -a")
print(f"System: {stdout}")

# Get device info
info = device.info()
print(f"Hostname: {info['hostname']}")
print(f"CPU cores: {info['cpu_cores']}")
```

## Builder API

### `ovmobilebench.builders.openvino`

OpenVINO build management.

#### `OpenVINOBuilder`

```python
class OpenVINOBuilder:
    """Build OpenVINO from source"""

    def __init__(self, config: BuildConfig):
        """Initialize builder with configuration"""

    def configure(self) -> None:
        """Run CMake configuration"""

    def build(self, targets: List[str] = None) -> None:
        """
        Build specified targets.

        Args:
            targets: List of CMake targets. If None, builds all.
        """

    def clean(self) -> None:
        """Clean build directory"""

    def package(self, output_dir: Path) -> PackageInfo:
        """Package build artifacts"""
```

#### Example Usage

```python
from ovmobilebench.builders.openvino import OpenVINOBuilder
from ovmobilebench.config.schema import BuildConfig

config = BuildConfig(
    openvino_repo="/path/to/openvino",
    toolchain=Toolchain(
        android_ndk="/opt/android-ndk",
        abi="arm64-v8a"
    )
)

builder = OpenVINOBuilder(config)
builder.configure()
builder.build(targets=["benchmark_app"])
package = builder.package(Path("output"))
```

## Runner API

### `ovmobilebench.runners.benchmark`

Benchmark execution management.

#### `BenchmarkRunner`

```python
class BenchmarkRunner:
    """Execute benchmark_app"""

    def __init__(self, device: Device, config: RunConfig):
        """
        Initialize runner.

        Args:
            device: Target device
            config: Run configuration
        """

    def run_single(self, params: Dict[str, Any]) -> BenchmarkResult:
        """Run single benchmark with given parameters"""

    def run_matrix(self, model: ModelItem) -> List[BenchmarkResult]:
        """Run complete parameter matrix for a model"""

    def run_all(self, models: List[ModelItem]) -> List[BenchmarkResult]:
        """Run benchmarks for all models"""
```

#### `BenchmarkResult`

```python
@dataclass
class BenchmarkResult:
    """Result from single benchmark run"""

    model: str
    device: str
    parameters: Dict[str, Any]
    throughput_fps: float
    latency_avg_ms: float
    latency_min_ms: float
    latency_max_ms: float
    latency_median_ms: float
    stdout: str
    stderr: str
    return_code: int
    duration_sec: float
    timestamp: datetime
```

#### Example Usage

```python
from ovmobilebench.runners.benchmark import BenchmarkRunner
from ovmobilebench.devices.android import AndroidDevice

device = AndroidDevice("R3CN30XXXX")
runner = BenchmarkRunner(device, run_config)

# Run single benchmark
result = runner.run_single({
    "model": "model.xml",
    "niter": 100,
    "api": "sync",
    "threads": 4
})

print(f"Throughput: {result.throughput_fps} FPS")
print(f"Latency: {result.latency_avg_ms} ms")

# Run full matrix
results = runner.run_matrix(model_item)
```

## Parser API

### `ovmobilebench.parsers.benchmark_parser`

Parse benchmark_app output.

#### `BenchmarkParser`

```python
class BenchmarkParser:
    """Parse benchmark_app output"""

    def parse(self, stdout: str, stderr: str = "") -> ParsedMetrics:
        """
        Parse benchmark output.

        Args:
            stdout: Standard output from benchmark_app
            stderr: Standard error from benchmark_app

        Returns:
            Parsed metrics

        Raises:
            ParserError: If output cannot be parsed
        """

    def extract_throughput(self, text: str) -> float:
        """Extract throughput in FPS"""

    def extract_latencies(self, text: str) -> LatencyMetrics:
        """Extract latency metrics"""
```

#### Example Usage

```python
from ovmobilebench.parsers.benchmark_parser import BenchmarkParser

parser = BenchmarkParser()

stdout = """
[Step 11/11] Dumping statistics report
Count:      100 iterations
Duration:   1547.52 ms
Latency:
    Median:  15.34 ms
    Average: 15.48 ms
    Min:     14.92 ms
    Max:     18.21 ms
Throughput: 64.65 FPS
"""

metrics = parser.parse(stdout)
print(f"Throughput: {metrics.throughput_fps}")
print(f"Median latency: {metrics.latency_median_ms}")
```

## Report API

### `ovmobilebench.report.sink`

Report generation and output.

#### `ReportSink`

```python
class ReportSink(ABC):
    """Abstract base class for report sinks"""

    @abstractmethod
    def write(self, results: List[BenchmarkResult]) -> None:
        """Write results to sink"""
```

#### `JSONSink`

```python
class JSONSink(ReportSink):
    """Write results to JSON file"""

    def __init__(self, path: Path, indent: int = 2):
        """Initialize JSON sink"""

    def write(self, results: List[BenchmarkResult]) -> None:
        """Write results as JSON"""
```

#### `CSVSink`

```python
class CSVSink(ReportSink):
    """Write results to CSV file"""

    def __init__(self, path: Path, columns: Optional[List[str]] = None):
        """Initialize CSV sink"""

    def write(self, results: List[BenchmarkResult]) -> None:
        """Write results as CSV"""
```

### `ovmobilebench.report.summarize`

Statistical summarization of results.

#### `Summarizer`

```python
class Summarizer:
    """Summarize benchmark results"""

    def summarize(self, results: List[BenchmarkResult]) -> Summary:
        """Generate statistical summary"""

    def group_by(self, results: List[BenchmarkResult],
                 keys: List[str]) -> Dict[tuple, List[BenchmarkResult]]:
        """Group results by specified keys"""

    def compare(self, baseline: List[BenchmarkResult],
                current: List[BenchmarkResult]) -> Comparison:
        """Compare two sets of results"""
```

#### Example Usage

```python
from ovmobilebench.report import JSONSink, CSVSink, Summarizer

# Write to different formats
json_sink = JSONSink(Path("results.json"))
json_sink.write(results)

csv_sink = CSVSink(Path("results.csv"))
csv_sink.write(results)

# Generate summary
summarizer = Summarizer()
summary = summarizer.summarize(results)
print(f"Mean throughput: {summary.throughput_mean}")
print(f"Std deviation: {summary.throughput_std}")

# Compare results
comparison = summarizer.compare(baseline_results, current_results)
print(f"Performance change: {comparison.throughput_change:.1%}")
```

## Android Installer API

### `ovmobilebench.android.installer`

Automated Android SDK/NDK installation and management.

#### Main Functions

##### `ensure_android_tools`

```python
def ensure_android_tools(
    sdk_root: Union[str, Path],
    api: int,
    target: str = "google_atd",
    arch: str = "arm64-v8a",
    ndk: Optional[Union[str, Path, NdkSpec]] = None,
    create_avd_name: Optional[str] = None,
    install_platform_tools: bool = True,
    install_emulator: bool = True,
    install_build_tools: Optional[str] = None,
    accept_licenses: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
    jsonl_path: Optional[Path] = None
) -> InstallerResult:
    """
    Install and configure Android SDK/NDK.

    Args:
        sdk_root: Android SDK installation directory
        api: Android API level (e.g., 30, 31, 33)
        target: System image target (google_atd, google_apis, default)
        arch: Architecture (arm64-v8a, x86_64, x86, armeabi-v7a)
        ndk: NDK specification (alias like "r26d" or path)
        create_avd_name: Name for AVD creation (None to skip)
        install_platform_tools: Install ADB and platform tools
        install_emulator: Install Android Emulator
        install_build_tools: Build tools version (e.g., "34.0.0")
        accept_licenses: Automatically accept SDK licenses
        dry_run: Preview without making changes
        verbose: Enable detailed logging
        jsonl_path: Path for JSON Lines log output

    Returns:
        Dictionary with installation results

    Raises:
        InstallerError: If installation fails
    """
```

##### `export_android_env`

```python
def export_android_env(
    sdk_root: Union[str, Path],
    ndk_path: Optional[Union[str, Path]] = None,
    format: str = "dict"
) -> Union[Dict[str, str], str]:
    """
    Export Android environment variables.

    Args:
        sdk_root: Android SDK root directory
        ndk_path: NDK installation path
        format: Output format (dict, bash, fish, windows, github)

    Returns:
        Environment variables as dictionary or formatted string
    """
```

##### `verify_installation`

```python
def verify_installation(
    sdk_root: Union[str, Path],
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Verify Android tools installation.

    Args:
        sdk_root: Android SDK root directory
        verbose: Print verification results

    Returns:
        Dictionary with installation status
    """
```

#### Classes

##### `AndroidInstaller`

```python
class AndroidInstaller:
    """Main installer orchestrator"""

    def __init__(self, sdk_root: Path, logger: Optional[StructuredLogger] = None):
        """Initialize installer with SDK root"""

    def ensure(self, api: int, target: str, arch: str,
               ndk: Optional[NdkSpec] = None, **kwargs) -> InstallerResult:
        """Install Android tools with specified configuration"""

    def verify(self) -> Dict[str, Any]:
        """Verify installation status"""

    def cleanup(self, remove_downloads: bool = True,
                remove_temp: bool = True) -> None:
        """Clean up temporary files"""
```

#### Data Types

##### `NdkSpec`

```python
class NdkSpec:
    """NDK specification"""
    alias: Optional[str] = None  # e.g., "r26d"
    path: Optional[Path] = None  # Absolute path to NDK
```

##### `InstallerResult`

```python
class InstallerResult(TypedDict):
    """Installation result"""
    sdk_root: Path
    ndk_path: Optional[Path]
    avd_created: bool
    performed: Dict[str, Any]
```

#### Example Usage

```python
from ovmobilebench.android import ensure_android_tools, export_android_env

# Install Android tools
result = ensure_android_tools(
    sdk_root="/opt/android-sdk",
    api=30,
    target="google_atd",
    arch="arm64-v8a",
    ndk="r26d",
    create_avd_name="test_device"
)

# Export environment variables
env = export_android_env(
    sdk_root=result["sdk_root"],
    ndk_path=result["ndk_path"],
    format="bash"
)
print(env)

# Verify installation
from ovmobilebench.android import verify_installation
status = verify_installation("/opt/android-sdk")
```

For complete documentation, see [Android Installer Module Documentation](android_installer.md).

## Utilities

### `ovmobilebench.core.shell`

Shell command execution utilities.

#### `run_command`

```python
def run_command(
    command: Union[str, List[str]],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    capture_output: bool = True
) -> CommandResult:
    """
    Execute shell command.

    Args:
        command: Command to execute
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        Command result with output and return code
    """
```

### `ovmobilebench.core.fs`

File system utilities.

#### Functions

```python
def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist"""

def safe_remove(path: Path) -> None:
    """Remove file/directory safely"""

def copy_tree(src: Path, dst: Path) -> None:
    """Copy directory tree"""

def calculate_checksum(path: Path) -> str:
    """Calculate SHA256 checksum of file"""

def find_files(root: Path, pattern: str) -> List[Path]:
    """Find files matching pattern"""
```

### `ovmobilebench.core.artifacts`

Artifact management utilities.

#### `ArtifactManager`

```python
class ArtifactManager:
    """Manage build and benchmark artifacts"""

    def __init__(self, base_dir: Path):
        """Initialize artifact manager"""

    def create_artifact(self, name: str, content: Any) -> Artifact:
        """Create new artifact"""

    def get_artifact(self, artifact_id: str) -> Artifact:
        """Retrieve artifact by ID"""

    def list_artifacts(self, filter_type: Optional[str] = None) -> List[Artifact]:
        """List all artifacts"""

    def cleanup(self, older_than: timedelta) -> int:
        """Clean up old artifacts"""
```

#### Example Usage

```python
from ovmobilebench.core import shell, fs, artifacts

# Execute command
result = shell.run_command("cmake --version")
print(result.stdout)

# File operations
fs.ensure_dir(Path("output"))
checksum = fs.calculate_checksum(Path("model.xml"))

# Artifact management
manager = artifacts.ArtifactManager(Path("artifacts"))
artifact = manager.create_artifact("build_output", build_result)
```

## Custom Extensions

### Creating Custom Device

```python
from ovmobilebench.devices.base import Device, DeviceInfo

class CustomDevice(Device):
    """Custom device implementation"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def connect(self) -> None:
        # Implement connection logic
        pass

    def shell(self, command: str, timeout: Optional[int] = None) -> ShellResult:
        # Implement command execution
        pass

    # Implement other required methods...
```

### Creating Custom Parser

```python
from ovmobilebench.parsers.base import Parser

class CustomParser(Parser):
    """Custom output parser"""

    def parse(self, output: str) -> Dict[str, Any]:
        # Implement parsing logic
        metrics = {}
        # Parse output...
        return metrics
```

### Creating Custom Report Format

```python
from ovmobilebench.report.sink import ReportSink

class HTMLSink(ReportSink):
    """Generate HTML reports"""

    def __init__(self, template_path: Path):
        self.template = load_template(template_path)

    def write(self, results: List[BenchmarkResult]) -> None:
        html = self.template.render(results=results)
        # Save HTML...
```

## Error Handling

All API methods may raise these exceptions:

```python
class OVMobileBenchError(Exception):
    """Base exception for OVMobileBench"""

class ConfigurationError(OVMobileBenchError):
    """Configuration validation error"""

class DeviceError(OVMobileBenchError):
    """Device operation error"""

class BuildError(OVMobileBenchError):
    """Build process error"""

class BenchmarkError(OVMobileBenchError):
    """Benchmark execution error"""

class ParserError(OVMobileBenchError):
    """Output parsing error"""
```

Example error handling:

```python
from ovmobilebench.exceptions import DeviceError, BenchmarkError

try:
    device = AndroidDevice("invalid_serial")
    device.connect()
except DeviceError as e:
    print(f"Failed to connect: {e}")
    # Handle error...

try:
    result = runner.run_single(params)
except BenchmarkError as e:
    print(f"Benchmark failed: {e}")
    # Retry or skip...
```

## Next Steps

- [Troubleshooting](troubleshooting.md) - Common issues
- [Architecture](architecture.md) - System design
- [Examples](https://github.com/embedded-dev-research/OVMobileBench/tree/main/examples) - Code examples
