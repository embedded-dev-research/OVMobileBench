# OVMobileBench Mobile — End-to-End Benchmarking Pipeline for OpenVINO on Mobile Devices
> **Summary**: This document describes a Python project that automates the full pipeline
> from building OpenVINO Runtime and `benchmark_app`, packaging runtime and models,
> deploying the bundle to mobile devices (Android via ADB, with optional Linux/SSH, iOS stub),
> executing performance runs, parsing metrics, and producing structured reports (CSV/JSON/SQLite),
> while capturing comprehensive build and device provenance for traceability and reproducibility.

> **Scope**: Architecture, directory layout, configuration schema, CLI design, build & packaging,
> device abstractions, runners, parsers, reporting, CI, reliability & reproducibility strategies,
> examples, troubleshooting, FAQs, and extensibility roadmap.
- **Document Version**: 1.0
- **Generated**: 2025-08-15 14:04:42
- **Project Codename**: `ovmobilebench`
- **Primary Target**: Android (ADB, arm64-v8a)
- **Secondary Targets**: Linux ARM (SSH), iOS (stub/interface)
- **Authoring Tool**: ChatGPT (programmatic generation)
## Table of Contents
1. [Goals and Principles](#goals-and-principles)
2. [High-Level Flow](#high-level-flow)
3. [Directory Structure](#directory-structure)
4. [Configuration Model](#configuration-model)
5. [CLI Commands](#cli-commands)
6. [Core Utilities](#core-utilities)
7. [Build System](#build-system)
8. [Packaging](#packaging)
9. [Device Abstractions](#device-abstractions)
10. [Runners](#runners)
11. [Parsers](#parsers)
12. [Reporting](#reporting)
13. [Orchestration Pipeline](#orchestration-pipeline)
14. [Reliability and Reproducibility](#reliability-and-reproducibility)
15. [Performance Methodology](#performance-methodology)
16. [Thermals and Power](#thermals-and-power)
17. [Security Considerations](#security-considerations)
18. [CI/CD Integration](#cicd-integration)
19. [Examples and Walkthroughs](#examples-and-walkthroughs)
20. [Troubleshooting](#troubleshooting)
21. [FAQs](#faqs)
22. [Change Management](#change-management)
23. [Extensibility Roadmap](#extensibility-roadmap)
24. [Appendix A — Config Schemas](#appendix-a--config-schemas)
25. [Appendix B — Code Skeletons](#appendix-b--code-skeletons)
26. [Appendix C — Example Experiment Files](#appendix-c--example-experiment-files)
27. [Appendix D — Data Model for Results](#appendix-d--data-model-for-results)
28. [Appendix E — Glossary](#appendix-e--glossary)
29. [Appendix F — Device Notes (Android/Linux/iOS)](#appendix-f--device-notes-androidlinuxios)
30. [License and Attribution](#license-and-attribution)
## Goals and Principles

- **End-to-end automation**: One command to build, package, deploy, run, parse, and report.
- **Deterministic outputs**: Strict capture of build flags, commit SHA, device info, and environment.
- **Portability**: Primary target Android (arm64-v8a), optional Linux ARM via SSH, iOS as stub for future.
- **Extensibility**: Clean boundaries between layers — builders, devices, runners, parsers, reports.
- **Observability**: Structured logs, error codes, retries, cooldowns, thermal/CPU telemetry (optional).
- **Reproducibility**: Versioned artifacts, pinned toolchains, hermetic packaging of runtime + models.
- **Safety-by-default**: No hidden state; all inputs/outputs serialized to experiment artifact folders.
- **Simplicity in use**: YAML experiments + ergonomic CLI with sane defaults.
## High-Level Flow

1. **Build** OpenVINO Runtime and `benchmark_app` for the target ABI (Android NDK or native/SSH).
2. **Package** the resulting binaries and required libraries with selected IR models.
3. **Deploy** the prepared bundle to the device (ADB or SSH), prepare run directory, set env vars.
4. **Run** `benchmark_app` using a test matrix (nireq, nstreams, threads, api, niter, device).
5. **Parse** stdout / stderr to extract throughput and latency metrics with a robust parser.
6. **Report** results into CSV/JSON (and optionally SQLite), including all metadata and tags.
7. **Trace** everything: commits, flags, device props, temperature (optional), and timestamps.
## Directory Structure

```text
ovmobilebench/
  pyproject.toml
  README.md
  ovmobilebench/
    __init__.py
    cli.py
    pipeline.py
    config/
      schema.py
      loader.py
      defaults/
        android.yaml
        linux_arm.yaml
    core/
      shell.py
      fs.py
      artifacts.py
      device_info.py
      logging.py
      errors.py
      retry.py
      timeutils.py
    builders/
      openvino.py
      benchmark.py
    packaging/
      packager.py
    devices/
      base.py
      android.py
      linux_ssh.py
      ios_stub.py
    runners/
      benchmark.py
    parsers/
      benchmark_parser.py
    report/
      sink.py
      summarize.py
      render.py
  models/
  artifacts/
  experiments/
  .github/workflows/
    bench.yml
```
## Configuration Model

Configurations are authored as YAML and validated with Pydantic models.
They describe the build options, devices, models, and run matrix, as well as reporting sinks and tags.

**Key sections**:
- `project`: name and run identifier.
- `build`: whether to build, what repo/commit to use, toolchain, and options.
- `package`: packaging flags and additional files.
- `device`: the target device kind and connection details (ADB serials, SSH host).
- `models`: a list of models (IR XML + BIN assumed) and metadata (precision, name).
- `run`: execution matrix, repeats, and other parameters.
- `report`: sinks (CSV/JSON/SQLite) and custom tags.
## CLI Commands

- `ovmobilebench build -c <yaml>` — Build runtime and benchmark_app for the target.
- `ovmobilebench package -c <yaml>` — Create a device-ready bundle with libs and models.
- `ovmobilebench deploy -c <yaml>` — Push to device(s) and prepare run directory.
- `ovmobilebench run -c <yaml>` — Execute the test matrix and collect raw outputs.
- `ovmobilebench report -c <yaml>` — Parse, aggregate, and save formatted results.
- `ovmobilebench all -c <yaml>` — Perform the entire pipeline in one go.
- Common flags: `--dry-run`, `--verbose`, `--timeout <sec>`, `--cooldown-sec <sec>`.
## Core Utilities

### `core.shell`
- Safe subprocess execution with timeouts, live logging, and retry policies.
- Captures `returncode`, `stdout`, `stderr` and duration.
- Optional `env` and `cwd` control.

### `core.fs`
- Helpers for atomic writes, temporary dirs, cross-platform path handling.
- Digest-based caching and artifact versioning helpers.

### `core.artifacts`
- Identifiers for artifacts: `<platform>/<commit>/<build_type>`.
- Layout helpers mapping build outputs into a bundle structure.

### `core.device_info`
- Collects system information (Android: `getprop`, `/proc/cpuinfo`, etc.).
- Normalizes CPU, cores, frequencies where possible.

### `core.logging`
- Structured logging (JSON lines) and human-readable logs simultaneously.

### `core.retry`
- Exponential backoff with jitter for flaky ADB/SSH calls.

### `core.errors`
- Exception hierarchy for predictable error handling across layers.
## Build System

### OpenVINO + benchmark_app for Android
- Toolchain: Android NDK (r26d or newer recommended).
- CMake + Ninja, `android.toolchain.cmake`, ABI `arm64-v8a`, API level ≥ 24.
- Build flags intentionally minimal for runtime + samples.

### Example Steps
1. Configure with CMake: set toolchain, ABI, platform, build type.
2. Disable tests that aren't needed on device.
3. Build `benchmark_app` target and copy required shared libraries.
4. Version the build using `git rev-parse HEAD` for traceability.

### Non-Android (Linux ARM)
- Native or cross-compilation depending on host/target.
- SSH-based deployment; otherwise identical pipeline.
## Packaging

- Bundle layout:
  - `bin/benchmark_app`
  - `lib/*.so*` (runtime and dependencies)
  - `models/*.xml` + `*.bin`
  - `README_device.txt` (optional hints)
- Compressed as `ovbundle_<platform>_<commit>.tar.gz`.
- Integrity check by verifying expected files on unpacking.
## Device Abstractions

### Base Interface
```python
class Device(ABC):
    def push(self, local: Path, remote: str) -> None: ...
    def shell(self, cmd: str, timeout: int | None = None) -> tuple[int, str, str]: ...
    def exists(self, remote_path: str) -> bool: ...
    def pull(self, remote: str, local: Path) -> None: ...
    def info(self) -> dict: ...
```
### Android (ADB)
- `adb -s <serial> push/pull/shell`
- Run directory: `/data/local/tmp/ovmobilebench`
- Env: `LD_LIBRARY_PATH` includes `lib/` within run directory
- Optional: thermal and CPU governor inspection

### Linux (SSH)
- Paramiko-based `push` via SFTP, `shell` via exec
- Env and run directory configurable
- Useful for SBCs/Jetson when Android is not applicable

### iOS (Stub)
- Interface and constraints documented; app-based runner typically required
## Runners

- The benchmark runner forms the command line based on a `RunSpec`:
  - `-m` model
  - `-d` device (e.g., CPU)
  - `-api` sync/async
  - `-niter`, `-nireq`
  - `-nstreams`, `-nthreads` (optional, CPU-specific)
- Matrix expansion: `models × nireq × nstreams × threads × api × niter`.
- Repeats: for each spec, run multiple times and collect per-run metrics for aggregation.
## Parsers

- Regex-based extraction of:
  - `Throughput: <value> FPS`
  - `Average latency: <ms>`
  - `Min latency: <ms>` / `Max latency: <ms>` / `Median latency: <ms>`
  - `count: <n>`
  - Device line (if present)
- Normalization of units and robust handling of missing values.
- Optionally preserve the last N KB of raw logs for diagnostics.
## Reporting

- Sinks:
  - JSON: full records per run
  - CSV: flat table for spreadsheets/BI
  - SQLite (optional): structured tables for queries
- Aggregations:
  - Median/best-of across repeats
  - Group by model/device/params
- Provenance:
  - Commit hash, build flags, toolchain versions, device info, tags
## Orchestration Pipeline

The `pipeline.py` module coordinates the stages:

1. **Build** (optional if prebuilts are used)
2. **Package**
3. **Deploy** (to each device)
4. **Run** (across matrix, with repeats and cooldowns)
5. **Parse & Aggregate**
6. **Report** (to configured sinks)

Errors are captured with specific exception types and retried when safe.
All intermediate artifacts and logs are stored beneath `artifacts/`.
## Reliability and Reproducibility

- Timeouts and retries for ADB/SSH commands
- Cooldown between runs to reduce thermal bias
- Optional preconditioning/warmup run
- Pinned toolchain versions and flags, stored in JSON metadata
- Model checksums recorded to guarantee inputs match
## Performance Methodology

- Prefer **median** throughput and latency across repeats
- Record ambient conditions (if available) and test durations
- Control background load: airplane mode, disable animations (Android dev options), close apps
- Standardize power source (battery level or charging policy)
## Thermals and Power

- Optional capture: `dumpsys thermalservice`, `/sys/class/thermal/*`
- If throttling detected, annotate results and optionally retry after cooldown
- For power-sensitive tests, maintain consistent charging state and screen-off policy
## Security Considerations

- Bundles may contain proprietary models; support encrypted model distribution (future work)
- Avoid storing secrets in configs; use environment variables for sensitive paths
- Sanitize logs by default (no accidental PII or internal paths where not required)
## CI/CD Integration

- GitHub Actions workflow (`.github/workflows/bench.yml`):
  - Build job: compiles runtime and benchmark_app; uploads bundle as artifact
  - Device job (self-hosted runner with attached device): downloads artifact, deploys, runs matrix
  - Publishes results as artifacts and/or pushes to storage (S3/GCS)
- Nightly and per-commit modes possible with differing matrices and models
## Examples and Walkthroughs

### 1) Minimal Android Run (single device, FP16)
- Prepare `experiments/android_minimal.yaml`
- Run: `ovmobilebench all -c experiments/android_minimal.yaml`
- Inspect outputs: `experiments/out/*.json` and `*.csv`

### 2) Multi-Device Matrix
- Provide multiple serials to `device.serials`
- Matrix expands per device; reports include serial identifiers

### 3) SSH to Linux ARM
- Switch `device.kind` to `linux_ssh` and provide host/user/key
- Otherwise identical pipeline
## Troubleshooting

- **ADB timeouts**: Check USB cable, enable developer options/USB debugging, increase command timeout.
- **`LD_LIBRARY_PATH` not set**: Ensure runner exports the path before executing `benchmark_app`.
- **Missing `.bin` next to `.xml`**: Packaging step expects both; verify model paths.
- **Low/unstable FPS**: Add cooldowns, fix charging state, reduce background load, check thermal throttling.
- **CMake configure errors**: Confirm NDK path, ABI, API level; delete build cache and reconfigure.
## FAQs

**Q: Can I use prebuilt OpenVINO?**  
A: Yes. Set `build.enabled: false` and point packaging to existing binaries.

**Q: How are repeats aggregated?**  
A: By default, medians are reported; raw per-run metrics are preserved.

**Q: What devices are supported?**  
A: Android via ADB out of the box; Linux ARM via SSH optional; iOS is stubbed for future work.

**Q: How do I add a new runner (e.g., custom app)?**  
A: Implement a device-agnostic `Runner` that produces comparable metrics, and plug it into the pipeline.
## Change Management

- Versioning via tags in `report.tags` and artifact directory structure
- Schema evolution handled by Pydantic models with `version` keys
- Changelog driven by PRs; CI validates sample experiments and parsing logic
## Extensibility Roadmap

- iOS app-based runner integration
- Power measurement hooks and energy-per-inference metrics
- Built-in ONNX→IR conversion stage
- Web UI for browsing historical runs
- SQLite sink and lightweight query CLI
## Appendix A — Config Schemas

```python
# ovmobilebench/config/schema.py
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional, Dict, Any

class Toolchain(BaseModel):
    android_ndk: Optional[str] = None
    abi: Optional[str] = None
    api_level: Optional[int] = None
    cmake: str = "cmake"
    ninja: str = "ninja"

class BuildOptions(BaseModel):
    ENABLE_INTEL_GPU: Optional[Literal["ON", "OFF"]] = "OFF"
    ENABLE_ONEDNN_FOR_ARM: Optional[Literal["ON", "OFF"]] = "OFF"
    ENABLE_PYTHON: Optional[Literal["ON", "OFF"]] = "OFF"
    # Extend as needed

class BuildConfig(BaseModel):
    enabled: bool = True
    openvino_repo: str
    openvino_commit: str = "HEAD"
    build_type: Literal["Release", "RelWithDebInfo", "Debug"] = "RelWithDebInfo"
    toolchain: Toolchain
    options: BuildOptions = BuildOptions()

class PackageConfig(BaseModel):
    include_symbols: bool = False
    extra_files: List[str] = []

class DeviceConfig(BaseModel):
    kind: Literal["android", "linux_ssh", "ios"]
    serials: List[str] = []
    host: Optional[str] = None
    user: Optional[str] = None
    key_path: Optional[str] = None
    push_dir: str = "/data/local/tmp/ovmobilebench"
    use_root: bool = False

class ModelItem(BaseModel):
    name: str
    path: str
    precision: Optional[str] = None
    tags: Dict[str, Any] = {}

class RunMatrix(BaseModel):
    niter: List[int] = [200]
    api: List[Literal["sync", "async"]] = ["sync"]
    nireq: List[int] = [1]
    nstreams: List[str] = ["1"]
    device: List[str] = ["CPU"]
    infer_precision: List[str] = ["FP16"]
    threads: List[int] = [4]

class RunConfig(BaseModel):
    repeats: int = 3
    matrix: RunMatrix
    cooldown_sec: int = 0
    timeout_sec: Optional[int] = None

class SinkItem(BaseModel):
    type: Literal["json", "csv", "sqlite"]
    path: str

class ReportConfig(BaseModel):
    sinks: List[SinkItem]
    tags: Dict[str, Any] = {}

class ProjectConfig(BaseModel):
    name: str
    run_id: str

class Experiment(BaseModel):
    project: ProjectConfig
    build: BuildConfig
    package: PackageConfig
    device: DeviceConfig
    models: List[ModelItem]
    run: RunConfig
    report: ReportConfig

    def expand_matrix_for_model(self, model_path: str):
        # Example expansion
        combos = []
        for dev in self.run.matrix.device:
            for api in self.run.matrix.api:
                for niter in self.run.matrix.niter:
                    for nireq in self.run.matrix.nireq:
                        for nstreams in self.run.matrix.nstreams:
                            for threads in self.run.matrix.threads:
                                combos.append({
                                    "model_xml": model_path,
                                    "device": dev,
                                    "api": api,
                                    "niter": niter,
                                    "nireq": nireq,
                                    "nstreams": nstreams,
                                    "threads": threads
                                })
        return combos
```
## Appendix B — Code Skeletons

### `ovmobilebench/core/shell.py`
```python
import subprocess, shlex, time
from dataclasses import dataclass

@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    duration_sec: float

def run(cmd, timeout=None, env=None, cwd=None) -> CommandResult:
    start = time.time()
    if isinstance(cmd, (list, tuple)):
        args = list(cmd)
    else:
        args = shlex.split(cmd)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=cwd)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return CommandResult(124, out, "TIMEOUT: " + err, time.time() - start)
    return CommandResult(proc.returncode, out, err, time.time() - start)
```

### `ovmobilebench/devices/android.py`
```python
import subprocess
from pathlib import Path
from .base import Device

class AndroidDevice(Device):
    def __init__(self, serial: str, push_dir: str):
        super().__init__(name=serial)
        self.serial = serial
        self.push_dir = push_dir

    def _adb(self, args):
        return subprocess.run(["adb", "-s", self.serial] + args, capture_output=True, text=True, check=False)

    def push(self, local: Path, remote: str) -> None:
        self._adb(["push", str(local), remote])

    def shell(self, cmd: str, timeout: int | None = None):
        # Basic wrapper; for production, add timeout handling
        cp = self._adb(["shell", cmd])
        return cp.returncode, cp.stdout, cp.stderr

    def exists(self, remote_path: str) -> bool:
        rc, out, _ = self.shell(f"ls {remote_path}")
        return rc == 0

    def pull(self, remote: str, local: Path) -> None:
        self._adb(["pull", remote, str(local)])

    def info(self) -> dict:
        rc, props, _ = self.shell("getprop")
        return {"os": "Android", "props": props, "serial": self.serial}
```
## Appendix C — Example Experiment Files

### `experiments/android_mcpu_fp16.yaml`
```yaml
project:
  name: "ovmobilebench-mobile"
  run_id: "2025-08-14_ov_arm_fp16"

build:
  enabled: true
  openvino_repo: "/path/to/openvino"
  openvino_commit: "HEAD"
  build_type: "RelWithDebInfo"
  toolchain:
    android_ndk: "/opt/android-ndk-r26d"
    abi: "arm64-v8a"
    api_level: 24
    cmake: "/usr/bin/cmake"
    ninja: "/usr/bin/ninja"
  options:
    ENABLE_INTEL_GPU: OFF
    ENABLE_ONEDNN_FOR_ARM: OFF
    ENABLE_PYTHON: OFF

package:
  include_symbols: false
  extra_files:
    - "README_device.txt"

device:
  kind: "android"
  serials: ["R3CN30XXXX"]
  push_dir: "/data/local/tmp/ovmobilebench"
  use_root: false

models:
  - name: "resnet50"
    path: "models/resnet50_fp16.xml"
    precision: "FP16"

run:
  repeats: 5
  matrix:
    niter: [200]
    api: ["sync"]
    nireq: [1,2,4]
    nstreams: ["1", "2"]
    device: ["CPU"]
    infer_precision: ["FP16"]
    threads: [1, 4]

report:
  sinks:
    - type: "json"
      path: "experiments/out/android_fp16.json"
    - type: "csv"
      path: "experiments/out/android_fp16.csv"
  tags:
    branch: "feature/arm-optim"
    owner: "alex"
```

### `experiments/linux_arm_fp32.yaml`
```yaml
project:
  name: "ovmobilebench-linux-arm"
  run_id: "2025-08-14_ov_linux_fp32"

build:
  enabled: false   # use prebuilts
  openvino_repo: "/opt/prebuilts/openvino"
  openvino_commit: "v2025.1"
  build_type: "Release"
  toolchain:
    cmake: "/usr/bin/cmake"
    ninja: "/usr/bin/ninja"

package:
  include_symbols: true
  extra_files: []

device:
  kind: "linux_ssh"
  serials: []
  host: "jetson.local"
  user: "ubuntu"
  key_path: "~/.ssh/id_rsa"
  push_dir: "/home/ubuntu/ovmobilebench"
  use_root: false

models:
  - name: "mobilenet_v2"
    path: "models/mobilenet_v2_fp32.xml"
    precision: "FP32"

run:
  repeats: 3
  matrix:
    niter: [100]
    api: ["sync", "async"]
    nireq: [1, 2]
    nstreams: ["1"]
    device: ["CPU"]
    infer_precision: ["FP32"]
    threads: [2, 4]

report:
  sinks:
    - type: "json"
      path: "experiments/out/linux_fp32.json"
    - type: "csv"
      path: "experiments/out/linux_fp32.csv"
  tags:
    scenario: "jetson-eval"
```
## Appendix D — Data Model for Results

Each run produces a flattened record with the following fields:

```text
timestamp, project_name, run_id, serial, device_name,
model, model_path, precision, device, api,
niter, nireq, nstreams, threads,
throughput_fps, latency_avg_ms, latency_min_ms, latency_max_ms, latency_med_ms,
iterations, return_code, cmd,
build_type, build_commit, toolchain_versions, device_info, tags (JSON)
```

Example (JSON):
```json
{
  "timestamp": "2025-08-14T11:20:05Z",
  "project_name": "ovmobilebench-mobile",
  "run_id": "2025-08-14_ov_arm_fp16",
  "serial": "R3CN30XXXX",
  "device_name": "R3CN30XXXX",
  "model": "resnet50",
  "model_path": "models/resnet50_fp16.xml",
  "precision": "FP16",
  "device": "CPU",
  "api": "sync",
  "niter": 200,
  "nireq": 2,
  "nstreams": "2",
  "threads": 4,
  "throughput_fps": 255.4,
  "latency_avg_ms": 7.8,
  "latency_min_ms": 7.2,
  "latency_max_ms": 8.9,
  "latency_med_ms": 7.6,
  "iterations": 200,
  "return_code": 0,
  "cmd": "/data/local/tmp/ovmobilebench/bin/benchmark_app -m models/resnet50_fp16.xml -d CPU -api sync -niter 200 -nireq 2 -nstreams 2 -nthreads 4",
  "build_type": "RelWithDebInfo",
  "build_commit": "ab12cd34",
  "toolchain_versions": {"ndk":"r26d"},
  "device_info": {"os":"Android","serial":"R3CN30XXXX"},
  "tags": {"branch":"feature/arm-optim","owner":"alex"}
}
```
## Appendix E — Glossary

- **ABI** — Application Binary Interface (e.g., `arm64-v8a` for Android 64-bit ARM).
- **ADB** — Android Debug Bridge, used for device communication.
- **API Level** — Android platform level (e.g., 24 corresponds to Android 7.0).
- **Benchmark_app** — OpenVINO sample measuring model inference performance.
- **Cooldown** — Time between runs to reduce thermal bias.
- **IR** — Intermediate Representation format of OpenVINO (XML + BIN files).
- **LD_LIBRARY_PATH** — Env var indicating where shared libraries are searched.
- **NDK** — Android Native Development Kit.
- **NIREQ** — Number of infer requests in benchmark_app.
- **NSTREAMS** — Number of execution streams for a device plugin.
- **OpenVINO** — Open Visual Inference and Neural network Optimization toolkit.
- **Paramiko** — Python SSH library for Linux remote execution.
- **Pydantic** — Python validation library for config schemas.
- **RelWithDebInfo** — Build type (Release with Debug Info).
- **Throughput (FPS)** — Inferences per second (frames per second).
- **Threads (nthreads)** — CPU thread count configured for plugin.
## Appendix F — Device Notes (Android/Linux/iOS)

### Android
- Enable Developer Options and USB Debugging.
- Confirm `adb devices` lists the serial.
- Ensure run directory permissions: `/data/local/tmp/ovmobilebench` is typically writable.

### Linux (SSH)
- Ensure SSH key-based auth; confirm SFTP is enabled.
- Confirm filesystem has enough space for bundles and outputs.

### iOS (Stub)
- Requires custom app wrapper around inference runnable.
- Future work: specify `xcrun simctl` or device-runner integration.
## License and Attribution

- This document and the scaffolding are provided for internal benchmarking workflows.
- Respect licenses of third-party tools and dependencies (OpenVINO, Android NDK, etc.).
- Models may have their own licenses; ensure compliance before distribution.
### Recipe 01 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #1.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `1`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_01.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 02 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #2.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `2`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_02.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 03 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #3.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `3`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_03.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 04 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #4.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `4`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_04.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 05 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #5.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `5`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_05.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 06 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #6.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `6`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_06.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 07 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #7.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `7`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_07.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 08 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #8.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `8`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_08.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 09 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #9.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `9`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_09.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 10 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #10.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `10`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_10.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 11 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #11.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `11`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_11.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 12 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #12.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `12`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_12.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 13 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #13.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `13`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_13.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 14 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #14.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `14`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_14.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 15 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #15.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `15`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_15.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 16 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #16.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `16`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_16.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 17 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #17.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `17`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_17.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 18 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #18.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `18`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_18.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 19 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #19.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `19`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_19.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 20 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #20.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `20`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_20.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 21 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #21.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `21`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_21.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 22 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #22.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `22`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_22.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 23 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #23.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `23`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_23.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 24 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #24.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `24`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_24.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 25 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #25.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `25`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_25.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 26 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #26.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `26`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_26.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 27 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #27.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `27`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_27.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 28 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #28.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `28`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_28.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 29 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #29.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `29`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_29.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 30 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #30.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `30`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_30.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 31 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #31.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `31`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_31.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 32 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #32.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `32`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_32.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 33 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #33.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `33`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_33.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 34 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #34.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `34`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_34.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 35 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #35.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `35`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_35.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 36 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #36.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `36`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_36.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 37 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #37.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `37`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_37.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 38 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #38.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `38`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_38.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 39 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #39.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `39`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_39.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.


### Recipe 40 — Scenario Pattern
- **Goal**: Describe a repeatable benchmarking scenario pattern #40.
- **Context**: Applies to a class of models/devices.
- **Inputs**: YAML config with variations in `nireq`, `nstreams`, `threads`.
- **Process**:
  1. Build/prebuilts selection.
  2. Package with given models.
  3. Deploy to device `40`.
  4. Execute matrix with repeats=3.
  5. Parse and report as CSV + JSON.
- **Outputs**: `experiments/out/recipe_40.csv` and `.json`.
- **Notes**: Adjust cooldowns to avoid thermal bias for longer models.
### Tip 01 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 02 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 03 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 04 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 05 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 06 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 07 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 08 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 09 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 10 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 11 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 12 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 13 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 14 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 15 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 16 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 17 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 18 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 19 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 20 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 21 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 22 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 23 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 24 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 25 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 26 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 27 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 28 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 29 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 30 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 31 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 32 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 33 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 34 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 35 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 36 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 37 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 38 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 39 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.


### Tip 40 — Practical Insight
- **Symptom**: Variation in throughput across repeats.
- **Likely Cause**: CPU governor scaling or background tasks.
- **Mitigation**: Fix governor (if possible), airplane mode, screen off, stabilize temperature.
- **Extra**: Increase `run.cooldown_sec` or add a warmup run.

# Supplemental Sections Added — 2025-08-15 14:15:15

> The following sections extend the original design with concrete, ready-to-use assets:
> GitHub Actions pipelines, Makefile, pyproject.toml project file, tox config, devcontainer/Dockerfile,
> unit tests (pytest) for parsers and devices, SQLite sink and schema, regression detection,
> parallel execution guidance, models acquisition, device farm design, baseline management,
> visualization cookbook, and advanced Android stabilization controls.

## Quickstart (Expanded)

### Prerequisites
- Python 3.11+
- Android SDK Platform Tools (`adb`), Android NDK r26d+
- CMake 3.24+, Ninja 1.11+
- Git, zip/tar
- On Linux ARM target (optional): SSH server and SFTP
- On macOS host (optional): `brew install cmake ninja android-platform-tools`

### Installation
```bash
# Install dependencies and package
python -m venv .venv && source .venv/bin/activate
pip install -U pip wheel
pip install -r requirements.txt
pip install -e .[dev]
ovmobilebench --help
```

### First Run
```bash
cp experiments/android_mcpu_fp16.yaml experiments/local.yaml
# Edit paths: openvino_repo, models/*.xml, ndk path, etc.
ovmobilebench all -c experiments/local.yaml --verbose
```

---

## pyproject.toml (Reference)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ovmobilebench"
version = "0.1.0"
description = "End-to-end benchmarking pipeline for OpenVINO on mobile devices"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {name = "Embedded Dev Research Team"},
]
dependencies = [
    "typer>=0.9.0",
    "click>=8.1.0",
    "pydantic>=2.8.2",
    "pyyaml>=6.0.2",
    "paramiko>=3.4.0",
    "pandas>=2.2.2",
    "rich>=13.7.1",
    "adbutils>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-cov>=5.0.0",
    "mypy>=1.10.0",
    "ruff>=0.5.0",
    "black>=24.4.2",
    "types-PyYAML>=6.0.12",
]

[project.scripts]
ovmobilebench = "ovmobilebench.cli:app"

[tool.setuptools.packages.find]
include = ["ovmobilebench*"]
```

---

## Makefile (Convenience Targets)

```makefile
.PHONY: help build package deploy run report all lint fmt test clean

help:
	@echo "Targets: build package deploy run report all lint fmt test clean"

build:
	ovmobilebench build -c $(CFG)

package:
	ovmobilebench package -c $(CFG)

deploy:
	ovmobilebench deploy -c $(CFG)

run:
	ovmobilebench run -c $(CFG)

report:
	ovmobilebench report -c $(CFG)

all:
	ovmobilebench all -c $(CFG)

lint:
	ruff check ovmobilebench
	mypy ovmobilebench

fmt:
	black ovmobilebench

test:
	pytest -q

clean:
	rm -rf artifacts/ .pytest_cache .mypy_cache .ruff_cache dist build
```

---

## tox.ini (Quality Gates)

```ini
[tox]
envlist = py311,lint,type
skipsdist = true

[testenv]
deps = pytest pytest-cov
commands = pytest --cov=ovmobilebench --cov-report=term-missing -q

[testenv:lint]
deps = ruff black
commands =
    ruff ovmobilebench
    black --check ovmobilebench

[testenv:type]
deps = mypy
commands = mypy ovmobilebench
```

---

## Devcontainer / Dockerfile (Reproducible Dev Env)

> Note: Android SDK/NDK licensing may require manual acceptance; keep them as bind mounts or build args.

```Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake ninja-build unzip curl wget zip && rm -rf /var/lib/apt/lists/*

# Install Android platform-tools (adb); NDK is mounted from host for licensing
RUN curl -sSL https://dl.google.com/android/repository/platform-tools-latest-linux.zip -o /tmp/pt.zip && \
    unzip /tmp/pt.zip -d /opt && rm /tmp/pt.zip && \
    ln -s /opt/platform-tools/adb /usr/local/bin/adb

WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY ovmobilebench ./ovmobilebench
RUN pip install -U pip && pip install .[dev]
```

---

## GitHub Actions — Build & Device Runs

### `.github/workflows/bench.yml`
```yaml
name: ovmobilebench-mobile

on:
  workflow_dispatch:
  push:
    branches: [ main ]
  schedule:
    - cron: "0 2 * * *"

jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e .
      - name: Build OpenVINO bundle
        env:
          ANDROID_NDK: ${{ secrets.ANDROID_NDK }}
        run: |
          export PATH="$ANDROID_NDK:$PATH"
          ovmobilebench build -c experiments/android_mcpu_fp16.yaml
          ovmobilebench package -c experiments/android_mcpu_fp16.yaml
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: ovbundle-android
          path: artifacts/**/*
          if-no-files-found: error

  run-on-device:
    needs: build-android
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Download bundle
        uses: actions/download-artifact@v4
        with:
          name: ovbundle-android
          path: artifacts
      - name: Install ovmobilebench
        run: |
          pip install -U pip
          pip install .
      - name: Deploy & Run matrix
        env:
          ANDROID_SERIALS: "R3CN30XXXX,emulator-5554"
        run: |
          python - <<'PY'
          import yaml
          with open('experiments/android_mcpu_fp16.yaml') as f:
              cfg = yaml.safe_load(f)
          cfg['device']['serials'] = "${{ env.ANDROID_SERIALS }}".split(',')
          with open('experiments/ci.yaml', 'w') as f:
              yaml.safe_dump(cfg, f)
          PY
          ovmobilebench deploy -c experiments/ci.yaml
          ovmobilebench run -c experiments/ci.yaml
          ovmobilebench report -c experiments/ci.yaml
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: results
          path: experiments/out/*
```

---

## SQLite Sink & Schema (Optional)

```sql
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  project_name TEXT,
  run_id TEXT,
  serial TEXT,
  device_name TEXT,
  model TEXT,
  model_path TEXT,
  precision TEXT,
  device TEXT,
  api TEXT,
  niter INTEGER,
  nireq INTEGER,
  nstreams TEXT,
  threads INTEGER,
  throughput_fps REAL,
  latency_avg_ms REAL,
  latency_min_ms REAL,
  latency_max_ms REAL,
  latency_med_ms REAL,
  iterations INTEGER,
  return_code INTEGER,
  cmd TEXT,
  build_type TEXT,
  build_commit TEXT,
  toolchain_versions TEXT,
  device_info TEXT,
  tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_runs_model ON runs(model, device, threads, nstreams, nireq);
CREATE INDEX IF NOT EXISTS idx_runs_runid ON runs(run_id);
```

**Example Queries**
```sql
SELECT model, device, threads, nstreams, nireq,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY throughput_fps) AS fps_median
FROM runs
GROUP BY model, device, threads, nstreams, nireq;

WITH L AS (SELECT * FROM runs WHERE run_id = :latest),
     B AS (SELECT * FROM runs WHERE run_id = :baseline)
SELECT L.model, L.device, L.threads, L.nstreams, L.nireq,
       L.throughput_fps AS latest_fps, B.throughput_fps AS base_fps,
       (L.throughput_fps - B.throughput_fps) / NULLIF(B.throughput_fps,0) AS rel_delta
FROM L JOIN B USING (model, device, threads, nstreams, nireq);
```

---

## Regression Detection (Threshold Gates)

```yaml
quality_gates:
  regression_allowed_pct: -0.03
  min_throughput_fps: 5.0
```

```python
def check_gates(latest: float, baseline: float | None, min_fps: float, allowed_pct: float) -> bool:
    if latest is None: 
        return False
    if latest < min_fps: 
        return False
    if baseline is not None:
        delta = (latest - baseline) / max(baseline, 1e-9)
        if delta < allowed_pct: 
            return False
    return True
```

---

## Unit Tests (pytest)

### `tests/test_parser.py`
```python
from ovmobilebench.parsers.benchmark_parser import parse_metrics

SAMPLE = """
[ INFO ] Throughput: 245.67 FPS
[ INFO ] Average latency: 8.12 ms
[ INFO ] Median latency: 7.98 ms
[ INFO ] Min latency: 7.45 ms
[ INFO ] Max latency: 9.01 ms
count: 200
Device: ARM CPU
"""

def test_parse_basic():
    m = parse_metrics(SAMPLE)
    assert m["throughput_fps"] == 245.67
    assert m["latency_avg_ms"] == 8.12
    assert m["latency_min_ms"] == 7.45
    assert m["latency_max_ms"] == 9.01
    assert m["latency_med_ms"] == 7.98
    assert m["iterations"] == 200
    assert "ARM CPU" in m["raw_device_line"]
```

### `tests/test_android_device.py`
```python
from ovmobilebench.devices.android import AndroidDevice

class FakeCP:
    returncode = 0
    stdout = "ok"
    stderr = ""

def fake_adb(self, args):
    return FakeCP()

def test_push_shell_exists(monkeypatch, tmp_path):
    dev = AndroidDevice(serial="TESTSERIAL", push_dir="/data/local/tmp/ovmobilebench")
    monkeypatch.setattr(AndroidDevice, "_adb", fake_adb)
    dev.push(tmp_path/"a", "/remote/a")  # does not raise
    rc, out, err = dev.shell("echo 1")
    assert rc == 0 and out == "ok"
    assert dev.exists("/remote/a") is True
```

---

## Visualization Cookbook (Matplotlib)

```python
import json
import matplotlib.pyplot as plt

with open("experiments/out/android_fp16.json") as f:
    rows = json.load(f)

by_thr = {}
for r in rows:
    k = r["threads"]
    by_thr.setdefault(k, []).append(r["throughput_fps"])

xs = sorted(by_thr.keys())
ys = [sum(v)/len(v) for v in (by_thr[x] for x in xs)]

plt.figure()
plt.plot(xs, ys, marker="o")
plt.title("Average Throughput vs Threads")
plt.xlabel("Threads")
plt.ylabel("FPS")
plt.grid(True)
plt.show()
```

---

## Advanced Android Stabilization

- **Airplane mode** (may require permissions/root):  
  `adb shell settings put global airplane_mode_on 1 && adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true`
- **Disable animations**:  
  `adb shell settings put global window_animation_scale 0`  
  `adb shell settings put global transition_animation_scale 0`  
  `adb shell settings put global animator_duration_scale 0`
- **Screen off**: `adb shell input keyevent 26`
- **CPU governor** (root): echo `performance` to `/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`
- **Affinity**: `adb shell taskset 0xF <cmd>`
- **Thermals**: `adb shell dumpsys thermalservice`
- **Power stats**: `adb shell dumpsys batterystats`

---

## Device Farm Design

- Inventory: YAML mapping serial → labels (SoC, RAM, Android version).
- Sharding: assign scenarios to devices by label selectors.
- Concurrency: run devices in parallel; single-run serialized per device.
- Health: periodic pings; auto-recover ADB server if offline.

---

## Baseline Management

- Store a `baseline_run_id` and results snapshot.
- Compare in CI; update baseline only after review.

---

## Models Acquisition (Open Model Zoo)

```bash
omz_downloader --name resnet-50-tf
omz_converter --name resnet-50-tf --precision FP16
cp public/resnet-50-tf/FP16/resnet-50-tf.xml models/resnet50_fp16.xml
cp public/resnet-50-tf/FP16/resnet-50-tf.bin models/resnet50_fp16.bin
```

---

## Logging and Telemetry

- JSONL logs per stage under `artifacts/logs/`.
- Optional shipping if env vars configured.
- Redact sensitive values in structured logs.

---

## HTML Report Template (Minimal)

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>OVMobileBench Report</title></head>
<body>
<h1>OVMobileBench Report — {{ run_id }}</h1>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Model</th><th>Device</th><th>Threads</th><th>nstreams</th><th>FPS median</th></tr>
{% for row in rows %}
<tr>
<td>{{ row.model }}</td><td>{{ row.device }}</td><td>{{ row.threads }}</td>
<td>{{ row.nstreams }}</td><td>{{ row.fps_median }}</td>
</tr>
{% endfor %}
</table>
</body></html>
```

---

## Concurrency & Parallel Runs

- Parallelize across devices; avoid parallel long-running `adb shell` per device.
- Implement backpressure and graceful shutdown handlers.

---

## Data Retention and Compliance

- Retain artifacts for 90 days; prune older.
- Restrict access to proprietary bundles.
- Keep metrics and metadata only; avoid data samples.

---

## Security & Supply Chain

- Record repo URL and commit; optional commit verification.
- SBOM generation and license scan where applicable.
- Verify library dependencies; avoid unexpected system libs.

---

## Extended Troubleshooting

- `Permission denied`: `chmod +x bin/benchmark_app`
- `linker: not found`: missing deps; check `LD_LIBRARY_PATH`
- `device offline`: restart ADB server, replug USB, check developer options
- Performance drops: reboot device, close apps, check thermals

---

## Appendix G — Sample Baseline Diff Script

```python
import json, statistics as st

def median_fps(rows):
    vals = [r["throughput_fps"] for r in rows if r["throughput_fps"] is not None]
    return st.median(vals) if vals else None

latest = json.load(open("experiments/out/android_fp16.json"))
base   = json.load(open("baselines/android_fp16.json"))

def key_of(r): 
    return (r["model"], r["device"], r["threads"], r["nstreams"], r["nireq"])

L = {}
for r in latest: L.setdefault(key_of(r), []).append(r)
B = {}
for r in base:   B.setdefault(key_of(r), []).append(r)

for k in sorted(set(L.keys()) | set(B.keys())):
    m_latest = median_fps(L.get(k, []))
    m_base   = median_fps(B.get(k, []))
    if m_latest is None or m_base is None: 
        continue
    rel = (m_latest - m_base) / max(m_base, 1e-9)
    print(k, f"{m_latest:.1f} vs {m_base:.1f} => {rel:+.1%}")
```

---

## Appendix H — Example CLI (Typer) Skeleton

```python
import typer
from ovmobilebench.pipeline import run_all
from ovmobilebench.config.loader import load_experiment

app = typer.Typer(add_completion=False)

@app.command()
def all(c: str, verbose: bool = False):
    cfg = load_experiment(c)
    run_all(cfg)

@app.command()
def build(c: str):
    cfg = load_experiment(c)
    # call builders
    ...

if __name__ == "__main__":
    app()
```

---

## Appendix I — Config Loader with Overrides

```python
def deep_set(dct, path, value):
    keys = path.split(".")
    cur = dct
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = value
    return dct
```

---

## Appendix J — Result JSON Schema Stub

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OVMobileBench Run Record",
  "type": "object",
  "properties": {
    "timestamp": { "type": "string", "format": "date-time" },
    "project_name": { "type": "string" },
    "run_id": { "type": "string" },
    "serial": { "type": "string" },
    "model": { "type": "string" },
    "device": { "type": "string" },
    "throughput_fps": { "type": ["number", "null"] },
    "latency_avg_ms": { "type": ["number", "null"] },
    "tags": { "type": "object", "additionalProperties": true }
  },
  "required": ["timestamp","project_name","run_id","serial","model","device"]
}
```

---

## Appendix K — Packaging Integrity & Checksums

```bash
sha256sum bin/benchmark_app lib/* models/* > checksums.txt
sha256sum -c checksums.txt
```

---

## Appendix L — Taskset and Core Mapping (Android)

```bash
adb shell cat /sys/devices/system/cpu/present
adb shell cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq
adb shell taskset 0xF ./bin/benchmark_app -m models/resnet50_fp16.xml -d CPU
```

---

## Appendix M — Sample `README_device.txt`

```
1) Export LD_LIBRARY_PATH before running:
   export LD_LIBRARY_PATH=$PWD/lib:$LD_LIBRARY_PATH

2) Run benchmark:
   ./bin/benchmark_app -m models/resnet50_fp16.xml -d CPU -niter 200 -nireq 2

3) Troubleshooting:
   - If "linker: not found": check lib path
   - If "Permission denied": chmod +x bin/benchmark_app
```

---

## Final Notes

This supplement provides immediately usable assets to bootstrap the project.
Adopt selectively, and pin versions across toolchains and dependencies to maintain repeatability.
