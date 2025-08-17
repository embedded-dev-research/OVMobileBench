# Architecture Specification: `ovmobilebench.android.installer` — Android SDK/NDK Module
_Generated: 2025-08-17 19:30:51_

> This document proposes a concrete, code-level architecture for the **Android SDK/NDK installer** module inside the OVMobileBench project.
> It is based on the public repository layout and README, which confirm the CLI entrypoint `ovmobilebench all -c ...` and the presence of Android setup docs and a single helper script `scripts/setup_android_tools.py`.
> The goal: move from a standalone script to a maintainable Python package module with testable interfaces and CI-first ergonomics.

---

## 0. Source context (what we know from the repo)
- The repository **OVMobileBench** exists on GitHub and exposes a CLI: `ovmobilebench all -c experiments/...yaml` in README Quick Start. citeturn1view0
- The README links include **Android SDK/NDK Setup** documentation (file `docs/android-setup.md`). citeturn1view0turn6view0
- The repo is licensed under **Apache-2.0**. citeturn1view0
- There is a **single script** under `scripts/`— the user confirmed it has a `--help`; the file path is `scripts/setup_android_tools.py`. citeturn4view0

**Purpose of this spec**: design and document the package **`ovmobilebench.android.installer`** that encapsulates Android tooling setup (SDK, NDK, AVD images) so workflows (local & CI) can call it directly or reuse its API from other OVMobileBench subsystems.

---

## 1. High-level responsibilities
1. Ensure Android **cmdline-tools** and **platform-tools** exist at a configured SDK root.
2. Ensure **platforms;android-<API>** and **system-images;android-<API>;<target>;<arch>** are installed when requested.
3. Ensure **NDK** is available (resolve as version alias like `r26d` or as an absolute path).
4. Optionally **create AVD** for headless emulator runs.
5. Export **`ANDROID_SDK_ROOT`** and **`ANDROID_NDK`** to environment (stdout or `$GITHUB_ENV`).
6. Keep operations **idempotent** and **observable** (structured logs, dry-run).
7. Provide clean **exceptions** and **return codes** for CI.

---

## 2. Package layout
```text
ovmobilebench/
  android/
    __init__.py
    installer/
      __init__.py
      api.py             # public functions & facades
      core.py            # high-level orchestration (Installer class)
      sdkmanager.py      # thin wrapper around sdkmanager
      avd.py             # AVD create/list utils
      ndk.py             # NDK resolution (alias/path), downloads if needed
      env.py             # export to $GITHUB_ENV / stdout, load/save state
      detect.py          # host detection (OS/arch, KVM presence)
      errors.py          # typed exceptions
      logging.py         # structured logging helpers (jsonl + readable)
      plan.py            # Dry-run planner & validators
      types.py           # dataclasses / TypedDict / enums for API/Target/Arch
      cli.py             # `ovmobilebench android setup ...` subcommand
      __main__.py        # optional - python -m ovmobilebench.android.installer
```

---

## 3. Public Python API (stable surface)
```python
from pathlib import Path
from typing import Optional
from ovmobilebench.android.installer.types import SystemImageSpec, NdkSpec
from ovmobilebench.android.installer.api import (
    ensure_android_tools,
    export_android_env,
    InstallerResult,
)

# Core one-shot call used by CI and local scripts:
result: InstallerResult = ensure_android_tools(
    sdk_root=Path("/opt/android-sdk"),
    api=30,
    target="google_atd",
    arch="arm64-v8a",
    ndk=NdkSpec(alias="r26d"),
    install_platform_tools=True,
    install_emulator=True,
    create_avd_name="ovb_api30_arm",
    accept_licenses=True,
    dry_run=False,
    verbose=True,
)

export_android_env(
    github_env=Path("/home/runner/work/_temp/_runner_file_commands/set_env_..."),
    print_stdout=True,
    sdk_root=result.sdk_root,
    ndk_path=result.ndk_path,
)
```
**Design notes**:
- Thin, explicit function with dataclass return type avoids leaky details and decouples callers from CLI nuances.
- The same API powers the CLI subcommand to avoid divergence with scripts.

---

## 4. CLI surface (replacing `scripts/setup_android_tools.py`)
### 4.1 Subcommand wiring
Expose a new subcommand under the main CLI (declared in `pyproject.toml` entry points):
```text
ovmobilebench android setup [OPTIONS]
```
### 4.2 Example usage
```bash
ovmobilebench android setup \
  --sdk-root /opt/android-sdk \
  --api 30 \
  --target google_atd \
  --arch arm64-v8a \
  --ndk r26d \
  --with-platform-tools \
  --with-emulator \
  --create-avd ovb_api30_arm \
  --accept-licenses \
  --export-env "$GITHUB_ENV" \
  --print-env \
  --verbose
```
**Rationale**: align with README’s CLI-first workflow where users run a single `ovmobilebench` command to kick off E2E. citeturn1view0

---

## 5. Data model and enums
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal

Target = Literal["google_atd", "google_apis"]
Arch = Literal["arm64-v8a", "x86_64"]

@dataclass(frozen=True)
class SystemImageSpec:
    api: int
    target: Target
    arch: Arch

@dataclass(frozen=True)
class NdkSpec:
    alias: Optional[str] = None   # e.g. "r26d" or "26.1.10909125"
    path: Optional[Path] = None   # absolute path overrides alias if provided

@dataclass(frozen=True)
class InstallerPlan:
    need_cmdline_tools: bool
    need_platform_tools: bool
    need_platform: bool
    need_system_image: bool
    need_emulator: bool
    need_ndk: bool
    create_avd_name: Optional[str] = None

@dataclass(frozen=True)
class InstallerResult:
    sdk_root: Path
    ndk_path: Path
    avd_created: bool
    performed: dict
```

---

## 6. Core orchestration (`core.py`)
```python
class AndroidInstaller:
    def __init__(self, sdk_root: Path, *, logger, verbose: bool = False):
        self.sdk_root = sdk_root
        self.logger = logger
        self.verbose = verbose
        # lazily construct helpers
        self.sdk = SdkManager(sdk_root, logger=logger)
        self.ndk = NdkResolver(sdk_root, logger=logger)
        self.avd = AvdManager(sdk_root, logger=logger)
        self.env = EnvExporter(logger=logger)
        self.planner = Planner(sdk_root, logger=logger)

    def ensure(self, *, api: int, target: Target, arch: Arch, ndk: NdkSpec,
               install_platform_tools: bool, install_emulator: bool,
               create_avd_name: str | None, accept_licenses: bool, dry_run: bool) -> InstallerResult:
        plan = self.planner.build_plan(api=api, target=target, arch=arch,
                                       install_platform_tools=install_platform_tools,
                                       install_emulator=install_emulator, ndk=ndk)
        if dry_run:
            self.logger.info({"plan": plan})
            return InstallerResult(self.sdk_root, self.ndk.resolve_path(ndk), False, {"dry_run": True})

        if accept_licenses:
            self.sdk.accept_licenses()
        if plan.need_cmdline_tools:
            self.sdk.ensure_cmdline_tools()
        if plan.need_platform_tools and install_platform_tools:
            self.sdk.ensure_platform_tools()
        if plan.need_platform:
            self.sdk.ensure_platform(api)
        if plan.need_system_image and install_emulator:
            self.sdk.ensure_system_image(api, target, arch)
        ndk_path = self.ndk.ensure(ndk)
        avd_created = False
        if create_avd_name:
            avd_created = self.avd.create(create_avd_name, api, target, arch)
        return InstallerResult(sdk_root=self.sdk_root, ndk_path=ndk_path, avd_created=avd_created,
                               performed={"plan": plan})
```
**Notes**:
- `Planner` computes idempotent actions; every `ensure_*` checks disk before executing downloads.
- All sub-steps log JSON lines for audit and reproducibility.

---

## 7. SDK Manager wrapper (`sdkmanager.py`)
Responsibilities:
- Locate `sdkmanager` binary under `cmdline-tools/latest/bin/`.
- Provide `install(packages: list[str])` and `accept_licenses()` helpers.
- Build package IDs: `platforms;android-{api}` and `system-images;android-{api};{target};{arch}`.
- Validate results (check directories after install).
```python
class SdkManager:
    def __init__(self, sdk_root: Path, *, logger):
        self.sdk_root = sdk_root
        self.logger = logger

    def ensure_cmdline_tools(self) -> Path: ...
    def ensure_platform_tools(self) -> Path: ...
    def ensure_platform(self, api: int) -> Path: ...
    def ensure_system_image(self, api: int, target: Target, arch: Arch) -> Path: ...
    def accept_licenses(self) -> None: ...
```
**Key invariant**: every ensure checks for existing dirs first (idempotency) and logs version information from `sdkmanager --version` and `adb version`.

---

## 8. NDK resolver (`ndk.py`)
- If `NdkSpec.path` is given, validate and return it.
- If alias is given (e.g., `r26d`), map to concrete version (`26.1.10909125`) and ensure it is present under `<sdk_root>/ndk/<ver>` (download/unpack if missing).
- Expose `resolve_path(NdkSpec) -> Path` and `ensure(NdkSpec) -> Path`.
```python
class NdkResolver:
    def __init__(self, sdk_root: Path, *, logger):
        self.sdk_root = sdk_root
        self.logger = logger

    def resolve_path(self, spec: NdkSpec) -> Path: ...
    def ensure(self, spec: NdkSpec) -> Path: ...
```
---

## 9. AVD utilities (`avd.py`)
- Construct package id from `(api, target, arch)` and call `avdmanager create avd -n <NAME> -k <PACKAGE>` if AVD doesn’t exist.
- Provide `list_avd() -> list[str]` for diagnostics.
- (Optional) `boot_headless(name)` helper for local smoke checks in tests.
```python
class AvdManager:
    def __init__(self, sdk_root: Path, *, logger): ...
    def list(self) -> list[str]: ...
    def create(self, name: str, api: int, target: Target, arch: Arch, profile: str | None = None) -> bool: ...
```
---

## 10. Environment export (`env.py`)
- Write `ANDROID_SDK_ROOT` and `ANDROID_NDK` into a given `$GITHUB_ENV` file if provided.
- Also support `print_stdout=True` to echo lines like `ANDROID_SDK_ROOT=/path` (used by shell eval).
```python
class EnvExporter:
    def __init__(self, *, logger): ...
    def export(self, github_env: Path | None, *, print_stdout: bool, sdk_root: Path, ndk_path: Path) -> None: ...
```
---

## 11. Planner & validators (`plan.py`)
- Decide which components are missing and produce `InstallerPlan`.
- Validate `(api, target, arch)` combination and NDK spec before execution.
- Support `--dry-run` mode: print plan and exit zero without changes.
```python
class Planner:
    def __init__(self, sdk_root: Path, *, logger): ...
    def build_plan(self, *, api: int, target: Target, arch: Arch, install_platform_tools: bool,
                   install_emulator: bool, ndk: NdkSpec) -> InstallerPlan: ...
```
---

## 12. Error model (`errors.py`)
- `InstallerError` (base)
- `InvalidArgumentError` (bad api/target/arch/ndk)
- `DownloadError`, `UnpackError`, `SdkManagerError`, `AvdManagerError`
- `PermissionError` (insufficient rights / path not writable)

---

## 13. Structured logging (`logging.py`)
- Human-readable INFO lines plus a JSONL sink (e.g., `.ovmb/logs/installer.jsonl`).
- Each step logs: component, action, args, start/finish, duration, outcome, error (if any).
- Make it trivial to attach logs as **CI artifacts**.

---

## 14. Host detection (`detect.py`)
- Detect host OS and architecture, presence of `/dev/kvm` (Linux) to hint best AVD (ARM64 on ARM runners).
- Not strictly required for install, but useful for warnings and defaults.

---

## 15. Integration points with the rest of OVMobileBench
- **Build stage**: the `toolchain.android_ndk` path in experiments YAML should be set from the exported `ANDROID_NDK`.
- **Device stage**: Android ADB tools (`platform-tools`) must be on PATH for deploy/run.
- **CI**: call `ovmobilebench android setup ...` before `ovmobilebench all -c ...`. citeturn1view0

---

## 16. CLI help (spec)
```text
Usage: ovmobilebench android setup [OPTIONS]

Options:
  --sdk-root PATH             SDK root destination (default: $HOME/Android/Sdk)
  --api INTEGER               Android API level (e.g., 30)
  --target [google_atd|google_apis]
  --arch [arm64-v8a|x86_64]
  --ndk TEXT|PATH             NDK alias (e.g., r26d) or absolute path
  --with-platform-tools       Install platform-tools (adb/fastboot)
  --with-emulator             Install emulator & system image
  --create-avd TEXT           Create AVD with this name (optional)
  --profile TEXT              AVD hardware profile (e.g., pixel_5)
  --accept-licenses           Accept licenses non-interactively
  --export-env PATH           Write ANDROID_SDK_ROOT/ANDROID_NDK to $GITHUB_ENV
  --print-env                 Also print env lines to stdout
  --dry-run                   Show planned actions only
  --verbose                   Verbose logging
  --help                      Show this message and exit
```
---

## 17. YAML glue (how experiments consume the env)
```yaml
build:
  toolchain:
    android_ndk: "${ env.ANDROID_NDK }"
    abi: "arm64-v8a"
    api_level: 30
    cmake: "cmake"
    ninja: "ninja"
```
**This lets the pipeline stay configuration-driven while the installer determines actual paths.**

---

## 18. Test strategy
### 18.1 Unit tests
- Mock subprocess calls to `sdkmanager`, `avdmanager`, `emulator`, `adb`.
- Validate parser, planner, and idempotent `ensure_*` logic on fake filesystem (tmp dirs).
- Verify `EnvExporter.export` writes correct lines and supports `print_stdout`.

### 18.2 Integration tests
- On self-hosted or containerized ARM/Linux with KVM:
  - `android setup --api 30 --target google_atd --arch arm64-v8a --with-platform-tools --with-emulator --ndk r26d`
  - Assert presence of folders and versions; optionally boot AVD headless and check `sys.boot_completed`.

### 18.3 Negative tests
- Network unavailable, disk full, invalid alias, conflicting flags (e.g., `--create-avd` without `--with-emulator`).

---

## 19. Code skeletons (selected files)
### 19.1 `api.py`
```python
from pathlib import Path
from typing import Optional
from .core import AndroidInstaller
from .types import NdkSpec
from .logging import get_logger
from .env import EnvExporter

class InstallerResult(TypedDict):
    sdk_root: Path
    ndk_path: Path
    avd_created: bool
    performed: dict

def ensure_android_tools(*, sdk_root: Path, api: int, target: str, arch: str, ndk: NdkSpec,
                         install_platform_tools: bool = True, install_emulator: bool = True,
                         create_avd_name: Optional[str] = None, accept_licenses: bool = True,
                         dry_run: bool = False, verbose: bool = False) -> InstallerResult:
    logger = get_logger(verbose=verbose)
    inst = AndroidInstaller(sdk_root, logger=logger, verbose=verbose)
    res = inst.ensure(api=api, target=target, arch=arch, ndk=ndk,
                      install_platform_tools=install_platform_tools, install_emulator=install_emulator,
                      create_avd_name=create_avd_name, accept_licenses=accept_licenses, dry_run=dry_run)
    return res

def export_android_env(*, github_env: Path | None, print_stdout: bool, sdk_root: Path, ndk_path: Path) -> None:
    EnvExporter(logger=get_logger()).export(github_env, print_stdout=print_stdout, sdk_root=sdk_root, ndk_path=ndk_path)
```

### 19.2 `cli.py` (Click/typer skeleton)
```python
import typer
from pathlib import Path
from .api import ensure_android_tools, export_android_env
from .types import NdkSpec

app = typer.Typer(name="android", help="Android tooling helpers")

@app.command("setup")
def setup(
    sdk_root: Path = typer.Option(Path.home() / "Android" / "Sdk", help="SDK root"),
    api: int = typer.Option(30, help="Android API"),
    target: str = typer.Option("google_atd", help="System image target"),
    arch: str = typer.Option("arm64-v8a", help="System image arch"),
    ndk: str = typer.Option("r26d", help="NDK version alias or absolute path"),
    with_platform_tools: bool = typer.Option(True, help="Install platform-tools"),
    with_emulator: bool = typer.Option(True, help="Install emulator & system image"),
    create_avd: str | None = typer.Option(None, help="Create AVD with this name"),
    accept_licenses: bool = typer.Option(True, help="Accept licenses"),
    export_env: Path | None = typer.Option(None, help="Path to $GITHUB_ENV"),
    print_env: bool = typer.Option(True, help="Also print env to stdout"),
) -> None:
    res = ensure_android_tools(
        sdk_root=sdk_root, api=api, target=target, arch=arch,
        ndk=NdkSpec(alias=ndk if not Path(ndk).exists() else None, path=Path(ndk) if Path(ndk).exists() else None),
        install_platform_tools=with_platform_tools, install_emulator=with_emulator,
        create_avd_name=create_avd, accept_licenses=accept_licenses,
    )
    export_android_env(github_env=export_env, print_stdout=print_env,
                       sdk_root=res["sdk_root"], ndk_path=res["ndk_path"])
```
---

## 20. Observability (what to log)
- **Inputs:** api, target, arch, ndk alias/path, sdk_root, flags.
- **Host:** OS, arch, `/dev/kvm` existence, Java version.
- **Actions:** package IDs, install durations, exit codes, directory sizes.
- **Outputs:** resolved NDK path, exported env, created AVD name.

---

## 21. Security & supply-chain
- Download from official Android sources; allow mirror override via env/opts.
- (Optional) SHA256 verification for archives.
- Avoid logging secrets; sanitize environment in logs.

---

## 22. Failure semantics
- Installer raises typed errors; CLI converts them to non-zero exit codes and user-readable hints.
- Always print last actions and remediation tips (e.g., disk free, proxy settings).
- Keep a *state file* with timestamps and versions to ease retries.

---

## 23. Example CI usage (ARM runner)
```yaml
- name: Android setup
  run: |
    ovmobilebench android setup \
      --sdk-root "$RUNNER_TEMP/android-sdk" \
      --api 30 --target google_atd --arch arm64-v8a \
      --ndk r26d --with-platform-tools --with-emulator \
      --accept-licenses --export-env "$GITHUB_ENV" --print-env
- name: Run pipeline
  run: ovmobilebench all -c experiments/android_emulator_arm64.yaml
```
**Why ARM64 AVD on ARM runners:** natively accelerated via KVM → fast CPU benchmarks for OpenVINO. citeturn1view0

---

## 24. Extended diagnostics & tips
- `sdkmanager --list` to confirm available packages.
- `adb version` and `emulator -version` to record versions in artifacts.
- Use `--dry-run` first in new environments to preview actions.
- If AVD boot time fluctuates, disable animations and wait for `sys.boot_completed`.

---

## 25. Roadmap for deprecating `scripts/setup_android_tools.py`
1. Introduce `ovmobilebench android setup` using this module.
2. Make `scripts/setup_android_tools.py` a thin shim that imports and calls the module functions.
3. Update docs/CI to prefer the subcommand.
4. After two minor releases, deprecate and remove the standalone script.

---

## 26. Appendix — Formal CLI grammar (EBNF-ish)
```text
setup := 'ovmobilebench' 'android' 'setup' (option)*
option :=
    '--sdk-root' PATH | '--api' INT | '--target' TARGET | '--arch' ARCH |
    '--ndk' (ALIAS|PATH) | '--with-platform-tools' | '--with-emulator' |
    '--create-avd' NAME | '--profile' STR | '--accept-licenses' |
    '--export-env' PATH | '--print-env' | '--dry-run' | '--verbose'
TARGET := 'google_atd' | 'google_apis'
ARCH   := 'arm64-v8a' | 'x86_64'
```
---

## 27. Checklist (succinct)
- [ ] Idempotent ensures for cmdline-tools, platform-tools, platform, system-images, emulator, NDK
- [ ] Validated `(api, target, arch)` and NDK spec
- [ ] Exported env to `$GITHUB_ENV` and/or stdout
- [ ] JSONL + human logs; CI artifacts
- [ ] Unit tests + smoke integration test
- [ ] Backwards-compatible shim for `scripts/setup_android_tools.py`

---
