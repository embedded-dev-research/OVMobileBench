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
8. [Utilities](#utilities)

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

Android device implementation using Python adbutils library for direct device control.

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

#### Example Usage

```python
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