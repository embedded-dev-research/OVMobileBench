# OVBench — User Guide & Operations Manual


> **Version**: 1.0 · **Generated**: 2025-08-15 15:33:50  
> **Scope**: This manual consolidates all guidance shared so far (architecture, checklists, CI, repo bundle) 
> into a single, user-facing document. It explains how to install, configure, run, and operate OVBench — 
> an end‑to‑end automation pipeline for building OpenVINO, packaging runtime + models, deploying to mobile devices 
> (Android via ADB; optional Linux ARM via SSH), executing `benchmark_app`, parsing metrics, and producing reports.


## Table of Contents

1. [What is OVBench?](#what-is-ovbench)
2. [Key Features](#key-features)
3. [System Requirements](#system-requirements)
4. [Install & Setup](#install--setup)
   - 4.1 [From the All‑Files Markdown Bundle](#from-the-allfiles-markdown-bundle)
   - 4.2 [Fresh Repo Setup](#fresh-repo-setup)
   - 4.3 [Python Environment](#python-environment)
   - 4.4 [External Tooling](#external-tooling)
5. [Quickstart](#quickstart)
6. [Project Layout](#project-layout)
7. [Core Concepts](#core-concepts)
8. [Configuring Experiments (YAML)](#configuring-experiments-yaml)
   - 8.1 [Top‑Level Sections](#toplevel-sections)
   - 8.2 [Run Matrix](#run-matrix)
   - 8.3 [Example Configs](#example-configs)
9. [Models: Getting & Managing](#models-getting--managing)
10. [Build & Package OpenVINO for Android](#build--package-openvino-for-android)
11. [Deploy to Devices](#deploy-to-devices)
12. [Run Benchmarks](#run-benchmarks)
13. [Parse & Report](#parse--report)
14. [Interpreting Results](#interpreting-results)
15. [Stability & Performance Best Practices](#stability--performance-best-practices)
16. [Device Farm Usage](#device-farm-usage)
17. [CI/CD Integration](#cicd-integration)
18. [Security, Licensing & Compliance](#security-licensing--compliance)
19. [Troubleshooting](#troubleshooting)
20. [FAQ](#faq)
21. [Reference: CLI](#reference-cli)
22. [Reference: Config Schema](#reference-config-schema)
23. [Reference: JSON Result Schema](#reference-json-result-schema)
24. [Appendix A — Ready‑Made Files (Makefile, pyproject, tox, pre‑commit)](#appendix-a--readymade-files)
25. [Appendix B — GitHub Actions Workflow](#appendix-b--github-actions-workflow)
26. [Appendix C — HTML Report Template (Minimal)](#appendix-c--html-report-template-minimal)
27. [Appendix D — Regression Gates & Baselines](#appendix-d--regression-gates--baselines)
28. [Appendix E — Android Stabilization Cheatsheet](#appendix-e--android-stabilization-cheatsheet)
29. [Appendix F — Extended Checklists (RU/EN)](#appendix-f--extended-checklists-ruen)
30. [Changelog & Next Steps](#changelog--next-steps)


## What is OVBench?

**OVBench** is a Python project that automates the full pipeline for measuring inference performance of neural
networks using OpenVINO’s `benchmark_app` on **mobile devices**. It takes you from building the runtime and sample
on your host machine, to **packaging** binaries + libraries + models, **deploying** to devices (ADB/SSH),
**running** a test matrix, **parsing** metrics, and **reporting** results with rich metadata for traceability.

Typical flow:
1) **Build** (optional if using prebuilts)  
2) **Package** (runtime libs + `benchmark_app` + models)  
3) **Deploy** (push bundle to device run dir)  
4) **Run** (`benchmark_app` over a matrix of parameters)  
5) **Parse** stdout/stderr to structured metrics  
6) **Report** to CSV/JSON/SQLite and summarize  
7) **Trace** build flags, commit SHA, device info, timestamps


## Key Features

- One‑command pipeline (`ovbench all -c ...`) from build to report.
- Android (ADB, arm64‑v8a) first; Linux ARM via SSH optional; iOS stub for future.
- Clean separation of layers: builders, devices, runners, parsers, reporting.
- Strict provenance: commit SHA, CMake flags, NDK/ABI, device props, model checksums.
- Flexible **run matrix** (nireq, nstreams, threads, api, niter, device).
- Robust parser for `benchmark_app` throughput/latency; resilient to minor format changes.
- Multiple sinks: JSON, CSV (and optional SQLite).
- CI‑friendly: GitHub Actions workflow + self‑hosted device runner.
- Best practices for thermal/power stability and reproducibility.


## System Requirements

**Host OS**: Linux/macOS/Windows (for building, Linux/macOS recommended).  
**Python**: 3.11+  
**Android tooling** (primary target):
- Android **NDK r26d+**
- Android **platform‑tools** (`adb`)
- **CMake ≥ 3.24**, **Ninja ≥ 1.11**

**Optional**:
- SSH access to Linux ARM device (Paramiko)
- Open Model Zoo tools (`omz_downloader`, `omz_converter`) for model acquisition


## Install & Setup

### From the All‑Files Markdown Bundle
If you have `OVBench_All_Files_Bundle.md`, it contains a **Bootstrap Script** that materializes a full repo.

Steps:
1. Open the bundle and copy the entire **Bootstrap Script** block.
2. Paste into a terminal inside an empty directory:
   ```bash
   bash <(sed -n '/^```bash$/,/^```$/p' OVBench_All_Files_Bundle.md | sed '1d;$d')
   ```
   Or simply copy the shown script and run it.
3. A new `repo/` folder will be created with all files.

### Fresh Repo Setup
```bash
git clone <your-repo-url> ovbench
cd ovbench
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
pre-commit install   # optional but recommended
```

### Python Environment
- Use a virtual environment (venv/conda).  
- `pip install -e .[dev]` installs runtime + dev tooling (pytest, mypy, ruff, black).

### External Tooling
Ensure the following are installed and on PATH:
- `adb` (Android platform‑tools)
- Android NDK (e.g., `/opt/android-ndk-r26d`)
- `cmake`, `ninja`

Mac:
```bash
brew install cmake ninja android-platform-tools
```


## Quickstart

1. **Prepare an experiment YAML**, e.g. `experiments/android_mcpu_fp16.yaml`:
   ```yaml
   project:
     name: "ovbench-mobile"
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
     extra_files: []

   device:
     kind: "android"
     serials: ["R3CN30XXXX"]
     push_dir: "/data/local/tmp/ovbench"
     use_root: false

   models:
     - name: "resnet50"
       path: "models/resnet50_fp16.xml"
       precision: "FP16"

   run:
     repeats: 3
     matrix:
       niter: [200]
       api: ["sync"]
       nireq: [1, 2, 4]
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
   ```

2. **Run the pipeline**:
   ```bash
   ovbench all -c experiments/android_mcpu_fp16.yaml --verbose
   ```

3. **Inspect results** under `experiments/out/` (CSV/JSON), and logs under `artifacts/`.


## Project Layout

```
ovbench/
  cli.py                # Typer CLI (ovbench ...)
  pipeline.py           # Orchestrator
  config/
    schema.py           # Pydantic models for YAML config
  core/
    shell.py            # Safe command runner
    fs.py               # Filesystem helpers
    artifacts.py        # Artifact identifiers & helpers
  builders/             # CMake/NDK build wrappers (OpenVINO + benchmark_app)
  packaging/            # Bundle packager
  devices/
    base.py
    android.py          # ADB push/shell/info
    linux_ssh.py        # (optional) SSH device
    ios_stub.py         # (stub)
  runners/
    benchmark.py        # Command builder for benchmark_app
  parsers/
    benchmark_parser.py # Extract throughput/latency
  report/
    sink.py             # JSON/CSV/SQLite sinks
    summarize.py        # Aggregations (medians, etc.)
    render.py           # Charts/tables (optional)
experiments/            # YAML configs
models/                 # IR models (*.xml + *.bin)
artifacts/              # Build cache & device bundles (git-ignored)
.github/workflows/      # CI
```


## Core Concepts

- **Bundle**: tar.gz with `bin/benchmark_app`, `lib/*.so*`, `models/*.xml/.bin`, and optional notes.
- **Device**: abstraction for ADB/SSH operations (push, pull, shell, info).
- **Run Matrix**: Cartesian product of parameters to test (`nireq`, `nstreams`, `threads`, `api`, `niter`, `device`).
- **Repeat**: each spec can be repeated N times; medians commonly reported.
- **Provenance**: store build commit, flags, NDK/ABI, device props, model checksums.


## Configuring Experiments (YAML)

### Top‑Level Sections
- `project`: name, `run_id`
- `build`: whether to build; repo/commit; toolchain; cmake options
- `package`: include symbols; extra files
- `device`: kind (`android`, `linux_ssh`), serials/host, push_dir
- `models`: list of IR models (`.xml` + `.bin`)
- `run`: repeats, matrix (see below)
- `report`: sinks (JSON/CSV/SQLite) + tags (metadata)

### Run Matrix
Common knobs:
- `niter`: number of iterations per run
- `api`: `sync` or `async`
- `nireq`: number of infer requests
- `nstreams`: number of streams (plugin‑specific)
- `device`: plugin target (e.g., `CPU`)
- `threads`: CPU threads for plugin
- `infer_precision`: desired inference precision label

### Example Configs
Besides the Android FP16 example (see Quickstart), a Linux ARM config may look like:

```yaml
project:
  name: "ovbench-linux-arm"
  run_id: "2025-08-14_ov_linux_fp32"
build:
  enabled: false              # use prebuilts
  openvino_repo: "/opt/prebuilts/openvino"
  openvino_commit: "v2025.1"
  build_type: "Release"
  toolchain:
    cmake: "/usr/bin/cmake"
    ninja: "/usr/bin/ninja"
package:
  include_symbols: true
device:
  kind: "linux_ssh"
  host: "jetson.local"
  user: "ubuntu"
  key_path: "~/.ssh/id_rsa"
  push_dir: "/home/ubuntu/ovbench"
models:
  - name: "mobilenet_v2"
    path: "models/mobilenet_v2_fp32.xml"
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
```


## Models: Getting & Managing

Use **Open Model Zoo (OMZ)** for permissively licensed models:

```bash
omz_downloader --name resnet-50-tf
omz_converter --name resnet-50-tf --precision FP16
cp public/resnet-50-tf/FP16/resnet-50-tf.xml models/resnet50_fp16.xml
cp public/resnet-50-tf/FP16/resnet-50-tf.bin models/resnet50_fp16.bin
```

Recommendations:
- Keep models out of git if large/proprietary (store in artifacts/buckets).
- Record `sha256` checksums in the bundle to ensure integrity.
- Ensure `.xml` and `.bin` are co‑located with matching base names.


## Build & Package OpenVINO for Android

**Prerequisites**: Android NDK, CMake, Ninja.  
**CMake outline**:
1. Configure with Android toolchain, ABI (`arm64-v8a`), API level (≥ 24).
2. Build `benchmark_app` target.
3. Collect required `.so` libs into `lib/`.

**Packaging layout**:
```
ovbundle/
  bin/benchmark_app
  lib/*.so*
  models/*.xml + *.bin
  README_device.txt (optional)
```
Archive as `ovbundle_android.tar.gz` and deploy to device.


## Deploy to Devices

**Android (ADB)**:
- Default run dir: `/data/local/tmp/ovbench`
- Example (performed by OVBench pipeline):
  ```bash
  adb -s <serial> push ovbundle_android.tar.gz /data/local/tmp/ovbench/bundle.tar.gz
  adb -s <serial> shell 'cd /data/local/tmp/ovbench && tar -xzf bundle.tar.gz && mv ovbundle/* .'
  adb -s <serial> shell 'export LD_LIBRARY_PATH=/data/local/tmp/ovbench/lib:$LD_LIBRARY_PATH'
  ```

**Linux ARM (SSH)**:
- Use SFTP for pushing files, and `ssh` to run commands.
- Ensure run dir is writable and your user has execution rights.


## Run Benchmarks

`ovbench run -c <yaml>` executes the matrix defined in `run.matrix` for each model and device.

Under the hood, it builds a `benchmark_app` command like:
```bash
/data/local/tmp/ovbench/bin/benchmark_app   -m /data/local/tmp/ovbench/models/resnet50_fp16.xml   -d CPU -api sync -niter 200 -nireq 2 -nstreams 2 -nthreads 4
```
OVBench repeats runs as configured, captures stdout/stderr, and parses metrics.


## Parse & Report

OVBench extracts:
- **Throughput** (FPS)
- **Latency**: min/avg/median/max (ms)
- **Iterations** (`count`)
- **Device info** line (if present)

Outputs:
- JSON (full per‑run records)
- CSV (flat table for analysis)
- (Optional) SQLite DB with query‑friendly schema


## Interpreting Results

- Prefer **median** throughput across repeats over single best/avg.
- Compare configurations (threads/nstreams/nireq) for scaling behavior.
- Record ambient/thermal context when possible for fair comparisons.
- Track build commit/flags to correlate changes with perf diffs.


## Stability & Performance Best Practices

- **Cooldown** between runs; add a **warm‑up** run not counted in statistics.
- Android stabilization (where permitted):
  - Disable animations:
    ```bash
    adb shell settings put global window_animation_scale 0
    adb shell settings put global transition_animation_scale 0
    adb shell settings put global animator_duration_scale 0
    ```
  - Turn screen off: `adb shell input keyevent 26`
  - Airplane mode (may require permissions/root).
- For rooted/test devices only: set CPU **governor** to `performance`; consider `taskset` for core affinity.
- Keep charging state consistent; reduce background load; avoid thermal throttling.


## Device Farm Usage

- Maintain an inventory (`devices.yaml`): serial → SoC/CPU/RAM/Android/tags.
- Shard scenarios by labels (e.g., only `armv8` + `Android 12`).
- Run devices **in parallel**, but serialize runs on a **single** device to simplify logs and thermals.
- Health checks (periodic `adb devices`, `adb shell true`); auto‑recover with `adb kill-server && adb start-server`.


## CI/CD Integration

A typical GitHub Actions flow:
- **Build job** (Ubuntu runner): build OpenVINO + `benchmark_app`, package the bundle, upload as artifact.
- **Run‑on‑device job** (self‑hosted with attached Android device): download bundle, deploy, run, report, upload results.

Workflow excerpt:
```yaml
jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -U pip poetry && poetry install
      - env: { ANDROID_NDK: ${{ secrets.ANDROID_NDK }} }
        run: |
          export PATH="$ANDROID_NDK:$PATH"
          poetry run ovbench build -c experiments/android_mcpu_fp16.yaml
          poetry run ovbench package -c experiments/android_mcpu_fp16.yaml
      - uses: actions/upload-artifact@v4
        with: { name: ovbundle-android, path: artifacts/**/*, if-no-files-found: error }

  run-on-device:
    needs: build-android
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/download-artifact@v4
        with: { name: ovbundle-android, path: artifacts }
      - run: pip install -U pip && pip install .
      - name: Deploy & Run matrix
        env: { ANDROID_SERIALS: "R3CN30XXXX,emulator-5554" }
        run: |
          python - <<'PY'
          import yaml
          with open('experiments/android_mcpu_fp16.yaml') as f:
              cfg = yaml.safe_load(f)
          cfg['device']['serials'] = "${{ env.ANDROID_SERIALS }}".split(',')
          with open('experiments/ci.yaml', 'w') as f:
              yaml.safe_dump(cfg, f)
          PY
          ovbench deploy -c experiments/ci.yaml
          ovbench run -c experiments/ci.yaml
          ovbench report -c experiments/ci.yaml
      - uses: actions/upload-artifact@v4
        with: { name: results, path: experiments/out/* }
```


## Security, Licensing & Compliance

- Choose a repository license (MIT/Apache‑2.0/BSD‑3/etc.).
- Do **not** commit secrets; use CI Secret storage (GitHub Secrets/Environments).
- Avoid PII in logs; record only necessary metadata (device serials are OK when required).
- Respect Open Model Zoo and model licenses; keep proprietary models outside git (artifacts only).
- (Optional) SBOM for bundles; dependency license scan.


## Troubleshooting

- **ADB timeouts/offline**: check cable/USB mode; `adb kill-server && adb start-server`; re‑enable Developer options/USB debugging.
- **`LD_LIBRARY_PATH` not set**: ensure env export before running `benchmark_app`.
- **Linker errors (`not found`)**: missing `.so` in `lib/`; verify bundle completeness.
- **Permissions**: `chmod +x bin/benchmark_app` after unpacking on device.
- **Low/unstable FPS**: add cooldown, disable animations/screen, stabilize power, check thermal throttling.
- **CMake configure errors**: confirm NDK path, ABI, API level; clean build dir and reconfigure.


## FAQ

**Q: Can I use prebuilt OpenVINO?**  
A: Yes. Set `build.enabled: false` and package your prebuilt runtime.

**Q: Which metrics are reported?**  
A: Throughput (FPS), latency (min/avg/median/max), count, device info, and full provenance.

**Q: Can I run on non‑Android devices?**  
A: Yes, via `linux_ssh` device type (e.g., Jetson/SBC). iOS is a stub for future app‑based runner.

**Q: How do I compare runs?**  
A: Use medians across repeats and compare by identical (model, device, threads, nstreams, nireq) tuples.


## Reference: CLI

Assuming `ovbench = "ovbench.cli:app"` entrypoint:

- `ovbench all -c <yaml> [--verbose]` — full pipeline
- `ovbench build -c <yaml>` — build OpenVINO + `benchmark_app`
- `ovbench package -c <yaml>` — assemble device bundle
- `ovbench deploy -c <yaml>` — push to device(s), prepare env
- `ovbench run -c <yaml>` — execute matrix + repeats
- `ovbench report -c <yaml>` — parse, aggregate, export sinks


## Reference: Config Schema

```python
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
    push_dir: str = "/data/local/tmp/ovbench"
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
```


## Reference: JSON Result Schema

A run record typically includes:

```json
{
  "timestamp": "2025-08-14T11:20:05Z",
  "project_name": "ovbench-mobile",
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
  "cmd": "/data/local/tmp/ovbench/bin/benchmark_app -m models/resnet50_fp16.xml -d CPU -api sync -niter 200 -nireq 2 -nstreams 2 -nthreads 4",
  "build_type": "RelWithDebInfo",
  "build_commit": "ab12cd34",
  "toolchain_versions": {"ndk":"r26d"},
  "device_info": {"os":"Android","serial":"R3CN30XXXX"},
  "tags": {"branch":"feature/arm-optim","owner":"alex"}
}
```


## Appendix A — Ready‑Made Files

- **Makefile** (targets: `build`, `package`, `deploy`, `run`, `report`, `all`, `lint`, `fmt`, `type`, `test`, `clean`)
- **pyproject.toml** (Poetry; runtime & dev deps, CLI entrypoint)
- **tox.ini** (quality gates)
- **.pre-commit-config.yaml** (Black, Ruff, Mypy, hooks)

> See the “All‑Files Bundle” or repo root for full text of these files.


## Appendix B — GitHub Actions Workflow

A complete `bench.yml` is provided in the All‑Files Bundle. It includes:
- `build-android` job (Ubuntu runner)
- `run-on-device` job (self‑hosted with ADB device)
- Artifact upload/download, PR‑friendly outputs


## Appendix C — HTML Report Template (Minimal)

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>OVBench Report</title></head>
<body>
<h1>OVBench Report — {{ run_id }}</h1>
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


## Appendix D — Regression Gates & Baselines

**Quality gates (YAML):**
```yaml
quality_gates:
  regression_allowed_pct: -0.03   # fail if drop < -3%
  min_throughput_fps: 5.0
```

**Gate function (pseudo‑Python):**
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
**Baseline diff script (sample):**
```python
import json, statistics as st

def median_fps(rows):
    vals = [r["throughput_fps"] for r in rows if r["throughput_fps"] is not None]
    return st.median(vals) if vals else None
```


## Appendix E — Android Stabilization Cheatsheet

- Disable animations:
  ```bash
  adb shell settings put global window_animation_scale 0
  adb shell settings put global transition_animation_scale 0
  adb shell settings put global animator_duration_scale 0
  ```
- Screen off: `adb shell input keyevent 26`  
- Airplane mode (may require permissions/root).  
- CPU governor (root): set `performance` for predictable runs.  
- Pinning (taskset): `adb shell taskset 0xF <cmd>` (adjust mask to your SoC).
- Thermals: `adb shell dumpsys thermalservice`  
- Power stats: `adb shell dumpsys batterystats`


## Appendix F — Extended Checklists (RU/EN)

Two comprehensive preflight checklists exist (Russian & English) covering repo policies,
CI gates, device farm, security & more. Use them before publishing or enabling CI:
- `OVBench_Project_Preflight_Checklist.md` (RU)
- `OVBench_Project_Preflight_Checklist_EN.md` (EN)


## Changelog & Next Steps

- **v1.0**: Initial consolidated user manual combining architecture, setup, CI, and ops guidance.
- **Planned**:
  - iOS runner integration (app‑based), power measurement hooks
  - SQLite sink + query CLI
  - Web UI for browsing historical runs
  - Built‑in ONNX→IR conversion stage
