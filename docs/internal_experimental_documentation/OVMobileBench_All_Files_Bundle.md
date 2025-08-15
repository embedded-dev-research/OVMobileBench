# OVMobileBench — Complete Repo Bundle (All Files in One Markdown)

_Generated: 2025-08-15T15:24:59_

This Markdown contains every file needed to create a working OVMobileBench repo. 
Copy the **Bootstrap Script** to a shell and run it; it will materialize all files.

## Bootstrap Script

```bash
set -euo pipefail
mkdir -p repo && cd repo
mkdir -p '.github/workflows'
mkdir -p 'docs'
mkdir -p 'experiments'
mkdir -p 'models'
mkdir -p 'ovmobilebench'
mkdir -p 'ovmobilebench/config'
mkdir -p 'ovmobilebench/core'
mkdir -p 'ovmobilebench/devices'
mkdir -p 'ovmobilebench/parsers'
mkdir -p 'ovmobilebench/report'
mkdir -p 'ovmobilebench/runners'
mkdir -p 'tests'
cat > 'README.md' << '__OVBENCH_EOF_1__'
# OVMobileBench

OVMobileBench automates building OpenVINO and running `benchmark_app` on mobile devices (Android via ADB), packaging,
deployment, execution, parsing, and reporting — end-to-end.

- Quickstart: see `experiments/android_mcpu_fp16.yaml`
- Full design: `ARCHITECTURE.md`
- Preflight checklists: `docs/CHECKLIST_RU.md`, `docs/CHECKLIST_EN.md`

```bash
ovmobilebench all -c experiments/android_mcpu_fp16.yaml
```

__OVBENCH_EOF_1__
cat > 'ARCHITECTURE.md' << '__OVBENCH_EOF_2__'
# Architecture

*(Placeholder: file was not found at generation time.)*

__OVBENCH_EOF_2__
cat > 'docs/CHECKLIST_RU.md' << '__OVBENCH_EOF_3__'
# Checklist (RU)

*(Placeholder: file was not found at generation time.)*

__OVBENCH_EOF_3__
cat > 'docs/CHECKLIST_EN.md' << '__OVBENCH_EOF_4__'
# OVMobileBench — Repository Preflight Checklist for Publication and CI Launch

> **Purpose**: This document is a detailed preflight checklist to prepare the **OVMobileBench**
> repository (automation for building OpenVINO, packaging, deploying to mobile devices,
> and running `benchmark_app`) for public/internal release and stable CI/CD operation.
>
> **Includes**: repo structure, licensing, versioning policy, Python packaging,
> code quality tooling, secrets and access, CI pipelines, artifacts and retention,
> testing, security & compliance, performance methodology, device farm,
> releases, issue/PR templates, rollback/incident playbooks, and extended appendices.
>
> **Date**: 2025-08-15 15:07:02
> **Primary Target**: Android (ADB, arm64-v8a). Also: Linux ARM (SSH), iOS (stub).

## Table of Contents

1. [Principles & Readiness Metrics](#principles--readiness-metrics)
2. [Fast Start: Top 10 Must-Haves](#fast-start-top-10-must-haves)
3. [Strategic Choices (License, Versioning, Branding)](#strategic-choices-license-versioning-branding)
4. [Repository Initialization](#repository-initialization)
5. [Directory Structure & Required Files](#directory-structure--required-files)
6. [Python Package: pyproject, Dependencies, Extras](#python-package-pyproject-dependencies-extras)
7. [Code Quality: Formatting, Linting, Typing, Hooks](#code-quality-formatting-linting-typing-hooks)
8. [External Tooling: NDK/SDK, CMake/Ninja, ADB, OMZ](#external-tooling-ndksdk-cmakeninja-adb-omz)
9. [Secrets, Access, Environment Variables](#secrets-access-environment-variables)
10. [CI/CD: Pipelines, Artifacts, Gates, Caching](#cicd-pipelines-artifacts-gates-caching)
11. [Artifacts, Storage, Retention, Data Layout](#artifacts-storage-retention-data-layout)
12. [Testing: Unit, Integration, System Runs](#testing-unit-integration-system-runs)
13. [Device Farm: Inventory, Scheduling, Health](#device-farm-inventory-scheduling-health)
14. [Performance & Stability Methodology](#performance--stability-methodology)
15. [Models & Data Licensing](#models--data-licensing)
16. [Security & Compliance](#security--compliance)
17. [Documentation: README, CONTRIBUTING, ARCH, CHECKLIST](#documentation-readme-contributing-arch-checklist)
18. [Releases & Versioning](#releases--versioning)
19. [Issue/PR Templates, CODEOWNERS, Labels & Workflow Policies](#issuepr-templates-codeowners-labels--workflow-policies)
20. [Rollback Plan & Incident Management](#rollback-plan--incident-management)
21. [Extended Checklists (by Roles and Phases)](#extended-checklists-by-roles-and-phases)
22. [Appendices: File Templates & Examples](#appendices-file-templates--examples)

## Principles & Readiness Metrics

- [ ] **Consistency**: same structure, tooling and commands locally and in CI.
- [ ] **Reproducibility**: pin NDK, CMake, Python deps, and model versions.
- [ ] **Observability**: JSONL logs, artifacts, build/device metadata.
- [ ] **Simplicity**: `ovmobilebench all -c <yaml>` should work without manual steps.
- [ ] **Least privilege**: secrets and access are locked down to minimum.
- [ ] **Transparency**: docs cover end-to-end scenarios and incident SOPs.
- [ ] **Quality-by-default**: linters, formatters, typing, tests — mandatory and fast.
- [ ] **Readiness metrics**:
  - TTR (Time To Run) < 10 min for minimal run;
  - CI flake-rate < 2%;
  - Unit test coverage ≥ 70% for `core`;
  - Cross-device reproducibility: ≤ 5% median FPS delta.

## Fast Start: Top 10 Must-Haves

1. [ ] License chosen and added (MIT/Apache-2.0/etc.).
2. [ ] `pyproject.toml` + `ovmobilebench` package with `ovmobilebench.cli:app` entrypoint.
3. [ ] `pre-commit` with Black, Ruff, Mypy, end-of-file-fixer.
4. [ ] CI badges in README, working `bench.yml` workflow.
5. [ ] `.gitignore`, `.gitattributes`, `CODEOWNERS`, `CONTRIBUTING.md`.
6. [ ] Issue/PR templates, label set, PR gates (lint/tests).
7. [ ] Minimal `experiments/local.yaml` for “first run” out of the box.
8. [ ] Artifact/retention policy (S3/GCS/Actions artifacts) documented.
9. [ ] Secrets encrypted; onboarding steps for ADB/NDK/CMake in README.
10. [ ] Add “ARCHITECTURE.md” and this “CHECKLIST.md”.

## Strategic Choices (License, Versioning, Branding)

- [ ] License: MIT / Apache-2.0 / BSD-3 / Proprietary (document rationale).
- [ ] Versioning: SemVer (0.y for early releases) / CalVer (YYYY.MM).
- [ ] Branding: name, logo (if any), disclaimers (mention OpenVINO appropriately).
- [ ] External models policy: what can be in git vs artifacts/buckets.
- [ ] Privacy/PII: do not log user IDs or sensitive paths unless required.

## Repository Initialization

- [ ] `git init` or create on GitHub/GitLab.
- [ ] Set `main` as protected; forbid direct pushes; require PR reviews.
- [ ] **Branch protection**:
  - [ ] required checks (lint, type, tests, build);
  - [ ] required reviews (≥1/2);
  - [ ] no merge on red statuses.
- [ ] **Sign-off** (DCO) or GPG-signed commits policy.
- [ ] Enable **secret scanning** (GH Advanced Security/Trufflehog if available).
- [ ] Define **CODEOWNERS** for critical dirs (`ovmobilebench/core`, `devices/*`, workflows).
- [ ] Add `SECURITY.md` (contacts, vulnerability disclosure policy).

## Directory Structure & Required Files

- [ ] `ovmobilebench/` — sources
  - [ ] `cli.py` — Typer/Click CLI
  - [ ] `pipeline.py` — orchestrator
  - [ ] `config/` — schemas/loader/defaults
  - [ ] `core/` — shell/fs/artifacts/logging/errors/retry
  - [ ] `builders/` — openvino/benchmark
  - [ ] `packaging/` — packager
  - [ ] `devices/` — base/android/linux_ssh/ios_stub
  - [ ] `runners/` — benchmark runner
  - [ ] `parsers/` — benchmark_parser
  - [ ] `report/` — sink/summarize/render
- [ ] `experiments/` — YAML scenarios (at least `local.yaml`)
- [ ] `models/` — empty or `.gitkeep` (if models are not in git)
- [ ] `artifacts/` — git-ignored; generated at runtime
- [ ] `tests/` — pytest; at minimum: parser and device wrappers
- [ ] `.github/workflows/bench.yml` — CI pipeline
- [ ] `README.md` — quickstart, commands, requirements
- [ ] `ARCHITECTURE.md` — detailed design (1000+ lines)
- [ ] `CHECKLIST.md` — this file
- [ ] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `LICENSE`, `SECURITY.md`
- [ ] `.gitignore`, `.gitattributes`, `pyproject.toml`, `Makefile`, `tox.ini`

## Python Package: pyproject, Dependencies, Extras

- [ ] Package via `pyproject.toml` (Poetry or PEP 621):
  - [ ] `name = "ovmobilebench"`, `version`, `readme`, `scripts`.
  - [ ] Runtime deps: `typer`, `pydantic`, `pyyaml`, `paramiko`, `pandas`, `rich`.
  - [ ] Dev deps: `pytest`, `pytest-cov`, `mypy`, `ruff`, `black`.
  - [ ] Extras: `[dev]`, `[ssh]`, `[viz]` as needed.
- [ ] Minimum Python version: 3.11 (pinned in CI).
- [ ] Dependency pinning strategy: `^` / `~` / exact.
- [ ] Commands: `ovmobilebench build|package|deploy|run|report|all`.
- [ ] `entry_points`: `ovmobilebench = "ovmobilebench.cli:app"`.

## Code Quality: Formatting, Linting, Typing, Hooks

- [ ] **Black** (formatting) and **Ruff** (linting) configured.
- [ ] **Mypy** (strict options for `ovmobilebench/core`, `devices/*`).
- [ ] `pre-commit` with black, ruff, mypy, trailing-whitespace, end-of-file-fixer.
- [ ] Quality badges in README (lint/type/test).
- [ ] Ruff profiles for excluding dirs (e.g., `artifacts/`).
- [ ] Fast unit tests (≤ 1 min locally) for core modules.

## External Tooling: NDK/SDK, CMake/Ninja, ADB, OMZ

- [ ] Android **NDK r26d+** installed (path documented in README and CI).
- [ ] **CMake ≥ 3.24** and **Ninja ≥ 1.11** installed.
- [ ] **ADB** available locally and on self-hosted runner.
- [ ] Optional: **OMZ** (Open Model Zoo) for model download/convert.
- [ ] Installation docs included for Linux/macOS/Windows.

## Secrets, Access, Environment Variables

- [ ] Document environment variables for CI (examples):
  - [ ] `ANDROID_NDK` (path on runner or secret/mount)
  - [ ] `SSH_KEY` / `SSH_KNOWN_HOSTS` (Linux ARM)
  - [ ] `S3_*` / `GCS_*` (if exporting artifacts)
- [ ] **Never** commit secrets in YAML/repo.
- [ ] Use GitHub Secrets/Environments; restrict scope to teams/branches.
- [ ] Secret updates through DevOps/Infra with audit logs.

## CI/CD: Pipelines, Artifacts, Gates, Caching

- [ ] `bench.yml` with two jobs:
  - [ ] **build-android**: build & package; upload artifact.
  - [ ] **run-on-device** (self-hosted): download artifact, deploy, run, report.
- [ ] PR gates: lint → type → unit → build → (opt) smoke run on device.
- [ ] Caching: pip/poetry and CMake/Ninja (actions/cache).
- [ ] Artifact retention: ≥ 7–30 days; name with `run_id` and `commit`.
- [ ] Publishing results: artifacts, S3/GCS, PR comments with FPS tables.
- [ ] Parallelism control: `concurrency.group` to avoid race conditions.

## Artifacts, Storage, Retention, Data Layout

- [ ] Artifacts:
  - [ ] `ovbundle_<platform>_<commit>.tar.gz`
  - [ ] `experiments/out/*.json` and `.csv`
  - [ ] JSONL stage logs and device metadata
  - [ ] (opt) SQLite DB with results
- [ ] Standardized record fields (timestamp, model, device, params, metrics).
- [ ] Retention and access defined (repo settings/S3 lifecycle).
- [ ] Local cleanup policy for `artifacts/` (`make clean`).

## Testing: Unit, Integration, System Runs

- [ ] Unit tests: metrics parser, command generation, device wrappers.
- [ ] Integration: bundle packaging (without real NDK), pipeline dry-run.
- [ ] System: minimal run nightly on a “test” device.
- [ ] Coverage: target ≥ 70%; report in CI.
- [ ] Pytest markers: `slow`, `device`, `ssh` — off by default.

## Device Farm: Inventory, Scheduling, Health

- [ ] Inventory (`devices.yaml`): serial → SoC/CPU/RAM/Android/tags.
- [ ] Scheduling by labels (e.g., armv8 + Android 12 only).
- [ ] Parallel across devices; serialize runs within a single device.
- [ ] Health checks: `adb devices`, `adb shell true`, auto-reconnect.
- [ ] SOP documented: replace device, update firmware, factory reset.

## Performance & Stability Methodology

- [ ] Fix **LD_LIBRARY_PATH** and ensure dependencies are co-packaged.
- [ ] **Cooldown** between runs; **warm-up** run (excluded from stats).
- [ ] Android stabilization: disable animations, screen off, airplane mode (if permitted).
- [ ] Governor/affinity only on allowed/rooted devices.
- [ ] Metrics: medians across repeats; keep raw log tail for diagnostics.

## Models & Data Licensing

- [ ] OMZ/open models — OK; proprietary models via artifacts/private buckets only.
- [ ] Record `sha256` and model version; consider excluding `.bin/.xml` from git.
- [ ] Respect model licenses; document in README/NOTICE.

## Security & Compliance

- [ ] `SECURITY.md`: how to report vulnerabilities.
- [ ] Secret scanning and dependency CVE tracking in place.
- [ ] Avoid PII in logs; redact sensitive paths.
- [ ] (Opt) SBOM for bundle; dependency license scanning.

## Documentation: README, CONTRIBUTING, ARCH, CHECKLIST

- [ ] README: crisp, badges, requirements, commands, “first run”.
- [ ] ARCHITECTURE.md: full design & rationale.
- [ ] CONTRIBUTING.md: how to run tests/lint, PR process, branching.
- [ ] CHECKLIST.md: this preflight registry.
- [ ] CHANGELOG.md: manual or Conventional Commits + tooling.

## Releases & Versioning

- [ ] Choose scheme: SemVer/CalVer, pre-releases (`-alpha.1`).
- [ ] Tags and release notes (auto-generated from PRs/commits).
- [ ] Release artifacts: signed hashes, bundle archive, baseline results.
- [ ] Version support policy and EOL.

## Issue/PR Templates, CODEOWNERS, Labels & Workflow Policies

- [ ] `.github/ISSUE_TEMPLATE/*.md` — bug/feature/perf/regression.
- [ ] `.github/pull_request_template.md` — what/why/how tested/screenshots.
- [ ] `CODEOWNERS` — by directories and critical files.
- [ ] Labels: `perf`, `infra`, `bug`, `good-first-issue`, `help-wanted`, etc.
- [ ] Branch policy: `main`, `feature/*`, `release/*`, `hotfix/*`.

## Rollback Plan & Incident Management

- [ ] Document release rollback (revert tags/releases, close artifacts).
- [ ] On-call/owners; SLA for CI outage or regression.
- [ ] Post-mortem template (what happened, root cause, action items).

### Extended Checklist: Core Engineer

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: CI/CD Engineer

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: ML Engineer

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: DevRel/Documentation

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: Security Owner

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: Release Manager

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Phase Bootstrap: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Build: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Package: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Deploy: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Run: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Parse: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Report: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Release: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

## Appendices: File Templates & Examples

### .gitignore (minimal)
```
.artifacts/
artifacts/
models/*
!models/.gitkeep
.venv/
__pycache__/
dist/
build/
*.egg-info/
.env
*.tar.gz
```

### CODEOWNERS (example)
```
*                 @team/owners
/ovmobilebench/core/    @team/core
/ovmobilebench/devices/ @team/devices
/.github/         @team/ci
```

### Pull Request Template (example)
```
## What & Why
-

## How Tested
-

## Author Checklist
- [ ] Lint/types/tests green
- [ ] Docs updated
- [ ] No secrets/PII in logs
```

### Issue Template — Performance Regression
```
### Description
Performance regression (model/device/params).

### Steps to Reproduce
1) 
2) 
3) 

### Expected / Actual
-

### Attachments
- Logs, JSON/CSV, tooling versions
```


## Expanded Task Index

- [ ] Check #001: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #002: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #003: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #004: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #005: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #006: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #007: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #008: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #009: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #010: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #011: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #012: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #013: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #014: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #015: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #016: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #017: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #018: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #019: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #020: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #021: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #022: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #023: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #024: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #025: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #026: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #027: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #028: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #029: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #030: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #031: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #032: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #033: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #034: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #035: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #036: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #037: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #038: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #039: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #040: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #041: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #042: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #043: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #044: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #045: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #046: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #047: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #048: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #049: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #050: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #051: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #052: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #053: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #054: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #055: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #056: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #057: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #058: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #059: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #060: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #061: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #062: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #063: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #064: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #065: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #066: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #067: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #068: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #069: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #070: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #071: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #072: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #073: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #074: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #075: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #076: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #077: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #078: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #079: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #080: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #081: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #082: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #083: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #084: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #085: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #086: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #087: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #088: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #089: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #090: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #091: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #092: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #093: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #094: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #095: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #096: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #097: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #098: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #099: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #100: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #101: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #102: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #103: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #104: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #105: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #106: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #107: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #108: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #109: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #110: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #111: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #112: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #113: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #114: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #115: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #116: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #117: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #118: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #119: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #120: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #121: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #122: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #123: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #124: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #125: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #126: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #127: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #128: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #129: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #130: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #131: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #132: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #133: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #134: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #135: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #136: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #137: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #138: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #139: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #140: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #141: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #142: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #143: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #144: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #145: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #146: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #147: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #148: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #149: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #150: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #151: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #152: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #153: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #154: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #155: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #156: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #157: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #158: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #159: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #160: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #161: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #162: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #163: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #164: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #165: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #166: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #167: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #168: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #169: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #170: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #171: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #172: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #173: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #174: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #175: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #176: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #177: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #178: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #179: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #180: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #181: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #182: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #183: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #184: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #185: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #186: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #187: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #188: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #189: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #190: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #191: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #192: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #193: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #194: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #195: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #196: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #197: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #198: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #199: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #200: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #201: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #202: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #203: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #204: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #205: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #206: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #207: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #208: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #209: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #210: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #211: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #212: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #213: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #214: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #215: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #216: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #217: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #218: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #219: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #220: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #221: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #222: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #223: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #224: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #225: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #226: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #227: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #228: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #229: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #230: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #231: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #232: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #233: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #234: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #235: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #236: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #237: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #238: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #239: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #240: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #241: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #242: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #243: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #244: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #245: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #246: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #247: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #248: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #249: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #250: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #251: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #252: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #253: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #254: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #255: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #256: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #257: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #258: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #259: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #260: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #261: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #262: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #263: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #264: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #265: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #266: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #267: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #268: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #269: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #270: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #271: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #272: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #273: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #274: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #275: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #276: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #277: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #278: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #279: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #280: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #281: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #282: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #283: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #284: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #285: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #286: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #287: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #288: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #289: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #290: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #291: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #292: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #293: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #294: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #295: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #296: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #297: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #298: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #299: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #300: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #301: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #302: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #303: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #304: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #305: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #306: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #307: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #308: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #309: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #310: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #311: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #312: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #313: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #314: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #315: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #316: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #317: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #318: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #319: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #320: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #321: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #322: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #323: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #324: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #325: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #326: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #327: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #328: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #329: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #330: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #331: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #332: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #333: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #334: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #335: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #336: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #337: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #338: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #339: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #340: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #341: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #342: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #343: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #344: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #345: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #346: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #347: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #348: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #349: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #350: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #351: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #352: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #353: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #354: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #355: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #356: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #357: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #358: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #359: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #360: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #361: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #362: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #363: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #364: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #365: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #366: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #367: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #368: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #369: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #370: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #371: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #372: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #373: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #374: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #375: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #376: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #377: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #378: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #379: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #380: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #381: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #382: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #383: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #384: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #385: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #386: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #387: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #388: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #389: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #390: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #391: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #392: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #393: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #394: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #395: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #396: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #397: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #398: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #399: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #400: See CI/CD, Security, Testing, and Device Farm sections.
__OVBENCH_EOF_4__
cat > 'LICENSE' << '__OVBENCH_EOF_5__'
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
... (standard MIT text shortened for brevity in this snippet; include full text in real repo) ...

__OVBENCH_EOF_5__
cat > 'SECURITY.md' << '__OVBENCH_EOF_6__'
# Security Policy

## Reporting
Please report vulnerabilities privately via security@example.com. We will acknowledge within 72 hours.

## Scope
Source under /ovmobilebench/**, CI workflows, and published artifacts.

__OVBENCH_EOF_6__
cat > 'CODE_OF_CONDUCT.md' << '__OVBENCH_EOF_7__'
# Code of Conduct
We follow the Contributor Covenant. Be respectful, inclusive, and constructive.

__OVBENCH_EOF_7__
cat > 'CONTRIBUTING.md' << '__OVBENCH_EOF_8__'
# Contributing

## Dev Setup
- Python 3.11+, Poetry or pip
- `poetry install` or `pip install -e .[dev]`

## Tests & Lint
- `pytest -q`
- `ruff ovmobilebench && black --check ovmobilebench && mypy ovmobilebench`

__OVBENCH_EOF_8__
cat > '.gitignore' << '__OVBENCH_EOF_9__'
.artifacts/
artifacts/
models/*
!models/.gitkeep
.venv/
__pycache__/
dist/
build/
*.egg-info/
.env
*.tar.gz

__OVBENCH_EOF_9__
cat > '.gitattributes' << '__OVBENCH_EOF_10__'
* text=auto eol=lf

__OVBENCH_EOF_10__
cat > '.pre-commit-config.yaml' << '__OVBENCH_EOF_11__'
repos:
- repo: https://github.com/psf/black
  rev: 24.4.2
  hooks:
    - id: black
      args: [--line-length=100]

- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.5.0
  hooks:
    - id: ruff
      args: [--fix]

- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.10.0
  hooks:
    - id: mypy
      additional_dependencies: ["types-PyYAML"]
      args: ["--strict", "--ignore-missing-imports"]

- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.6.0
  hooks:
    - id: end-of-file-fixer
    - id: trailing-whitespace

__OVBENCH_EOF_11__
cat > 'pyproject.toml' << '__OVBENCH_EOF_12__'
[tool.poetry]
name = "ovmobilebench"
version = "0.1.0"
description = "End-to-end benchmarking pipeline for OpenVINO on mobile devices"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
packages = [{ include = "ovmobilebench" }]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.3"
pydantic = "^2.8.2"
pyyaml = "^6.0.2"
paramiko = "^3.4.0"
pandas = "^2.2.2"
rich = "^13.7.1"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.0"
pytest-cov = "^5.0.0"
mypy = "^1.10.0"
ruff = "^0.5.0"
black = "^24.4.2"
pre-commit = "^3.7.1"

[tool.poetry.scripts]
ovmobilebench = "ovmobilebench.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

__OVBENCH_EOF_12__
cat > 'Makefile' << '__OVBENCH_EOF_13__'
#.PHONY targets
.PHONY: help build package deploy run report all lint fmt type test clean

help:
	@echo "Targets: build package deploy run report all lint fmt type test clean"

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
	ruff ovmobilebench

fmt:
	black ovmobilebench

type:
	mypy ovmobilebench

test:
	pytest -q

clean:
	rm -rf artifacts/ .pytest_cache .mypy_cache .ruff_cache dist build

__OVBENCH_EOF_13__
cat > 'tox.ini' << '__OVBENCH_EOF_14__'
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

__OVBENCH_EOF_14__
cat > 'Dockerfile.dev' << '__OVBENCH_EOF_15__'
FROM mcr.microsoft.com/devcontainers/python:3.11
RUN apt-get update && apt-get install -y --no-install-recommends \    git cmake ninja-build unzip curl wget zip && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://dl.google.com/android/repository/platform-tools-latest-linux.zip -o /tmp/pt.zip && \    unzip /tmp/pt.zip -d /opt && rm /tmp/pt.zip && \    ln -s /opt/platform-tools/adb /usr/local/bin/adb
WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY ovmobilebench ./ovmobilebench
RUN pip install -U pip && pip install .[dev]

__OVBENCH_EOF_15__
cat > '.github/workflows/bench.yml' << '__OVBENCH_EOF_16__'
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
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -U pip poetry && poetry install
      - name: Build & Package
        env:
          ANDROID_NDK: ${{ secrets.ANDROID_NDK }}
        run: |
          export PATH="$ANDROID_NDK:$PATH"
          poetry run ovmobilebench build -c experiments/android_mcpu_fp16.yaml
          poetry run ovmobilebench package -c experiments/android_mcpu_fp16.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: ovbundle-android
          path: artifacts/**/*
          if-no-files-found: error
  run-on-device:
    needs: build-android
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: actions/download-artifact@v4
        with:
          name: ovbundle-android
          path: artifacts
      - run: pip install -U pip && pip install .
      - name: Deploy & Run
        env:
          ANDROID_SERIALS: "R3CN30XXXX"
        run: |
          python - <<'PY'
          import yaml
          with open('experiments/android_mcpu_fp16.yaml') as f:
            cfg = yaml.safe_load(f)
          cfg['device']['serials'] = "${{ env.ANDROID_SERIALS }}".split(',')
          with open('experiments/ci.yaml','w') as f:
            yaml.safe_dump(cfg, f)
          PY
          ovmobilebench deploy -c experiments/ci.yaml
          ovmobilebench run -c experiments/ci.yaml
          ovmobilebench report -c experiments/ci.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: results
          path: experiments/out/*

__OVBENCH_EOF_16__
cat > 'experiments/android_mcpu_fp16.yaml' << '__OVBENCH_EOF_17__'
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
  extra_files: []
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
  repeats: 3
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

__OVBENCH_EOF_17__
cat > 'models/.gitkeep' << '__OVBENCH_EOF_18__'

__OVBENCH_EOF_18__
cat > 'ovmobilebench/__init__.py' << '__OVBENCH_EOF_19__'
__all__ = []

__OVBENCH_EOF_19__
cat > 'ovmobilebench/cli.py' << '__OVBENCH_EOF_20__'
import typer
from ovmobilebench.pipeline import run_all
from ovmobilebench.config.schema import Experiment
import yaml

app = typer.Typer(add_completion=False)

def load_experiment(path: str) -> Experiment:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Experiment(**data)

@app.command()
def all(c: str, verbose: bool = False):
    cfg = load_experiment(c)
    run_all(cfg)

@app.command()
def build(c: str):
    cfg = load_experiment(c)
    # TODO: call builders — placeholder
    typer.echo("Build stage placeholder")

@app.command()
def package(c: str):
    typer.echo("Package stage placeholder")

@app.command()
def deploy(c: str):
    typer.echo("Deploy stage placeholder")

@app.command()
def run(c: str):
    typer.echo("Run stage placeholder")

@app.command()
def report(c: str):
    typer.echo("Report stage placeholder")

if __name__ == "__main__":
    app()

__OVBENCH_EOF_20__
cat > 'ovmobilebench/pipeline.py' << '__OVBENCH_EOF_21__'
from ovmobilebench.config.schema import Experiment

def run_all(cfg: Experiment):
    # Placeholder orchestrator to be replaced with real steps
    print("Running full pipeline for", cfg.project.name, "run_id:", cfg.project.run_id)

__OVBENCH_EOF_21__
cat > 'ovmobilebench/config/schema.py' << '__OVBENCH_EOF_22__'

from pydantic import BaseModel, Field
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

__OVBENCH_EOF_22__
cat > 'ovmobilebench/devices/base.py' << '__OVBENCH_EOF_23__'
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple

class Device(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def push(self, local: Path, remote: str) -> None: ...
    @abstractmethod
    def shell(self, cmd: str, timeout: int | None = None) -> Tuple[int, str, str]: ...
    @abstractmethod
    def exists(self, remote_path: str) -> bool: ...
    @abstractmethod
    def pull(self, remote: str, local: Path) -> None: ...
    @abstractmethod
    def info(self) -> dict: ...

__OVBENCH_EOF_23__
cat > 'ovmobilebench/devices/android.py' << '__OVBENCH_EOF_24__'
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
        cp = self._adb(["shell", cmd])
        return cp.returncode, cp.stdout, cp.stderr

    def exists(self, remote_path: str) -> bool:
        rc, _, _ = self.shell(f"ls {remote_path}")
        return rc == 0

    def pull(self, remote: str, local: Path) -> None:
        self._adb(["pull", remote, str(local)])

    def info(self) -> dict:
        rc, props, _ = self.shell("getprop")
        return {"os": "Android", "props": props, "serial": self.serial}

__OVBENCH_EOF_24__
cat > 'ovmobilebench/parsers/benchmark_parser.py' << '__OVBENCH_EOF_25__'
import re

RE = {
  "throughput": re.compile(r"Throughput:\s*([\d.]+)\s*(FPS|fps)"),
  "lat_avg":    re.compile(r"Average latency:\s*([\d.]+)\s*ms"),
  "lat_min":    re.compile(r"Min latency:\s*([\d.]+)\s*ms"),
  "lat_max":    re.compile(r"Max latency:\s*([\d.]+)\s*ms"),
  "lat_med":    re.compile(r"Median latency:\s*([\d.]+)\s*ms"),
  "count":      re.compile(r"count:\s*(\d+)"),
  "device_full":re.compile(r"Device:\s*(.+)"),
}

def _get(pat, text, cast=float):
    m = RE[pat].search(text)
    return cast(m.group(1)) if m else None

def parse_metrics(text: str) -> dict:
    return {
        "throughput_fps": _get("throughput", text),
        "latency_avg_ms": _get("lat_avg", text),
        "latency_min_ms": _get("lat_min", text),
        "latency_max_ms": _get("lat_max", text),
        "latency_med_ms": _get("lat_med", text),
        "iterations": _get("count", text, int),
        "raw_device_line": (RE["device_full"].search(text).group(1)
                            if RE["device_full"].search(text) else None),
        "raw": text[-2000:],
    }

__OVBENCH_EOF_25__
cat > 'ovmobilebench/runners/benchmark.py' << '__OVBENCH_EOF_26__'
from dataclasses import dataclass
from pathlib import Path

@dataclass
class RunSpec:
    model_xml: str
    device: str
    api: str
    niter: int
    nireq: int
    nstreams: str | None
    threads: int | None

def build_cmd(push_dir: str, spec: RunSpec) -> str:
    parts = [
        f"{push_dir}/bin/benchmark_app",
        f"-m {push_dir}/models/{Path(spec.model_xml).name}",
        f"-d {spec.device}", f"-api {spec.api}", f"-niter {spec.niter}",
        f"-nireq {spec.nireq}"
    ]
    if spec.nstreams: parts += [f"-nstreams {spec.nstreams}"]
    if spec.threads:  parts += [f"-nthreads {spec.threads}"]
    return " ".join(parts)

__OVBENCH_EOF_26__
cat > 'ovmobilebench/report/sink.py' << '__OVBENCH_EOF_27__'
import json, csv
from pathlib import Path

def write_json(rows: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f: json.dump(rows, f, ensure_ascii=False, indent=2)

def write_csv(rows: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

__OVBENCH_EOF_27__
cat > 'ovmobilebench/core/shell.py' << '__OVBENCH_EOF_28__'
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
    args = cmd if isinstance(cmd, (list, tuple)) else shlex.split(cmd)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=cwd)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return CommandResult(124, out, "TIMEOUT: " + err, time.time() - start)
    return CommandResult(proc.returncode, out, err, time.time() - start)

__OVBENCH_EOF_28__
cat > 'ovmobilebench/core/fs.py' << '__OVBENCH_EOF_29__'
from pathlib import Path
def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

__OVBENCH_EOF_29__
cat > 'ovmobilebench/core/artifacts.py' << '__OVBENCH_EOF_30__'
from dataclasses import dataclass

@dataclass
class ArtifactRef:
    platform: str
    commit: str
    build_type: str

__OVBENCH_EOF_30__
cat > 'tests/test_parser.py' << '__OVBENCH_EOF_31__'
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

__OVBENCH_EOF_31__
cat > 'CODEOWNERS' << '__OVBENCH_EOF_32__'
*                 @team/owners
/ovmobilebench/core/    @team/core
/ovmobilebench/devices/ @team/devices
/.github/         @team/ci

__OVBENCH_EOF_32__
echo 'Repo files created.'
ls -la
```

## File Tree

```
.gitattributes
.github/workflows/bench.yml
.gitignore
.pre-commit-config.yaml
ARCHITECTURE.md
CODEOWNERS
CODE_OF_CONDUCT.md
CONTRIBUTING.md
Dockerfile.dev
LICENSE
Makefile
README.md
SECURITY.md
docs/CHECKLIST_EN.md
docs/CHECKLIST_RU.md
experiments/android_mcpu_fp16.yaml
models/.gitkeep
ovmobilebench/__init__.py
ovmobilebench/cli.py
ovmobilebench/config/schema.py
ovmobilebench/core/artifacts.py
ovmobilebench/core/fs.py
ovmobilebench/core/shell.py
ovmobilebench/devices/android.py
ovmobilebench/devices/base.py
ovmobilebench/parsers/benchmark_parser.py
ovmobilebench/pipeline.py
ovmobilebench/report/sink.py
ovmobilebench/runners/benchmark.py
pyproject.toml
tests/test_parser.py
tox.ini
```

## Files — Embedded Content

### `README.md`

```markdown
# OVMobileBench

OVMobileBench automates building OpenVINO and running `benchmark_app` on mobile devices (Android via ADB), packaging,
deployment, execution, parsing, and reporting — end-to-end.

- Quickstart: see `experiments/android_mcpu_fp16.yaml`
- Full design: `ARCHITECTURE.md`
- Preflight checklists: `docs/CHECKLIST_RU.md`, `docs/CHECKLIST_EN.md`

```bash
ovmobilebench all -c experiments/android_mcpu_fp16.yaml
```

```
### `ARCHITECTURE.md`

```markdown
# Architecture

*(Placeholder: file was not found at generation time.)*

```
### `docs/CHECKLIST_RU.md`

```markdown
# Checklist (RU)

*(Placeholder: file was not found at generation time.)*

```
### `docs/CHECKLIST_EN.md`

```markdown
# OVMobileBench — Repository Preflight Checklist for Publication and CI Launch

> **Purpose**: This document is a detailed preflight checklist to prepare the **OVMobileBench**
> repository (automation for building OpenVINO, packaging, deploying to mobile devices,
> and running `benchmark_app`) for public/internal release and stable CI/CD operation.
>
> **Includes**: repo structure, licensing, versioning policy, Python packaging,
> code quality tooling, secrets and access, CI pipelines, artifacts and retention,
> testing, security & compliance, performance methodology, device farm,
> releases, issue/PR templates, rollback/incident playbooks, and extended appendices.
>
> **Date**: 2025-08-15 15:07:02
> **Primary Target**: Android (ADB, arm64-v8a). Also: Linux ARM (SSH), iOS (stub).

## Table of Contents

1. [Principles & Readiness Metrics](#principles--readiness-metrics)
2. [Fast Start: Top 10 Must-Haves](#fast-start-top-10-must-haves)
3. [Strategic Choices (License, Versioning, Branding)](#strategic-choices-license-versioning-branding)
4. [Repository Initialization](#repository-initialization)
5. [Directory Structure & Required Files](#directory-structure--required-files)
6. [Python Package: pyproject, Dependencies, Extras](#python-package-pyproject-dependencies-extras)
7. [Code Quality: Formatting, Linting, Typing, Hooks](#code-quality-formatting-linting-typing-hooks)
8. [External Tooling: NDK/SDK, CMake/Ninja, ADB, OMZ](#external-tooling-ndksdk-cmakeninja-adb-omz)
9. [Secrets, Access, Environment Variables](#secrets-access-environment-variables)
10. [CI/CD: Pipelines, Artifacts, Gates, Caching](#cicd-pipelines-artifacts-gates-caching)
11. [Artifacts, Storage, Retention, Data Layout](#artifacts-storage-retention-data-layout)
12. [Testing: Unit, Integration, System Runs](#testing-unit-integration-system-runs)
13. [Device Farm: Inventory, Scheduling, Health](#device-farm-inventory-scheduling-health)
14. [Performance & Stability Methodology](#performance--stability-methodology)
15. [Models & Data Licensing](#models--data-licensing)
16. [Security & Compliance](#security--compliance)
17. [Documentation: README, CONTRIBUTING, ARCH, CHECKLIST](#documentation-readme-contributing-arch-checklist)
18. [Releases & Versioning](#releases--versioning)
19. [Issue/PR Templates, CODEOWNERS, Labels & Workflow Policies](#issuepr-templates-codeowners-labels--workflow-policies)
20. [Rollback Plan & Incident Management](#rollback-plan--incident-management)
21. [Extended Checklists (by Roles and Phases)](#extended-checklists-by-roles-and-phases)
22. [Appendices: File Templates & Examples](#appendices-file-templates--examples)

## Principles & Readiness Metrics

- [ ] **Consistency**: same structure, tooling and commands locally and in CI.
- [ ] **Reproducibility**: pin NDK, CMake, Python deps, and model versions.
- [ ] **Observability**: JSONL logs, artifacts, build/device metadata.
- [ ] **Simplicity**: `ovmobilebench all -c <yaml>` should work without manual steps.
- [ ] **Least privilege**: secrets and access are locked down to minimum.
- [ ] **Transparency**: docs cover end-to-end scenarios and incident SOPs.
- [ ] **Quality-by-default**: linters, formatters, typing, tests — mandatory and fast.
- [ ] **Readiness metrics**:
  - TTR (Time To Run) < 10 min for minimal run;
  - CI flake-rate < 2%;
  - Unit test coverage ≥ 70% for `core`;
  - Cross-device reproducibility: ≤ 5% median FPS delta.

## Fast Start: Top 10 Must-Haves

1. [ ] License chosen and added (MIT/Apache-2.0/etc.).
2. [ ] `pyproject.toml` + `ovmobilebench` package with `ovmobilebench.cli:app` entrypoint.
3. [ ] `pre-commit` with Black, Ruff, Mypy, end-of-file-fixer.
4. [ ] CI badges in README, working `bench.yml` workflow.
5. [ ] `.gitignore`, `.gitattributes`, `CODEOWNERS`, `CONTRIBUTING.md`.
6. [ ] Issue/PR templates, label set, PR gates (lint/tests).
7. [ ] Minimal `experiments/local.yaml` for “first run” out of the box.
8. [ ] Artifact/retention policy (S3/GCS/Actions artifacts) documented.
9. [ ] Secrets encrypted; onboarding steps for ADB/NDK/CMake in README.
10. [ ] Add “ARCHITECTURE.md” and this “CHECKLIST.md”.

## Strategic Choices (License, Versioning, Branding)

- [ ] License: MIT / Apache-2.0 / BSD-3 / Proprietary (document rationale).
- [ ] Versioning: SemVer (0.y for early releases) / CalVer (YYYY.MM).
- [ ] Branding: name, logo (if any), disclaimers (mention OpenVINO appropriately).
- [ ] External models policy: what can be in git vs artifacts/buckets.
- [ ] Privacy/PII: do not log user IDs or sensitive paths unless required.

## Repository Initialization

- [ ] `git init` or create on GitHub/GitLab.
- [ ] Set `main` as protected; forbid direct pushes; require PR reviews.
- [ ] **Branch protection**:
  - [ ] required checks (lint, type, tests, build);
  - [ ] required reviews (≥1/2);
  - [ ] no merge on red statuses.
- [ ] **Sign-off** (DCO) or GPG-signed commits policy.
- [ ] Enable **secret scanning** (GH Advanced Security/Trufflehog if available).
- [ ] Define **CODEOWNERS** for critical dirs (`ovmobilebench/core`, `devices/*`, workflows).
- [ ] Add `SECURITY.md` (contacts, vulnerability disclosure policy).

## Directory Structure & Required Files

- [ ] `ovmobilebench/` — sources
  - [ ] `cli.py` — Typer/Click CLI
  - [ ] `pipeline.py` — orchestrator
  - [ ] `config/` — schemas/loader/defaults
  - [ ] `core/` — shell/fs/artifacts/logging/errors/retry
  - [ ] `builders/` — openvino/benchmark
  - [ ] `packaging/` — packager
  - [ ] `devices/` — base/android/linux_ssh/ios_stub
  - [ ] `runners/` — benchmark runner
  - [ ] `parsers/` — benchmark_parser
  - [ ] `report/` — sink/summarize/render
- [ ] `experiments/` — YAML scenarios (at least `local.yaml`)
- [ ] `models/` — empty or `.gitkeep` (if models are not in git)
- [ ] `artifacts/` — git-ignored; generated at runtime
- [ ] `tests/` — pytest; at minimum: parser and device wrappers
- [ ] `.github/workflows/bench.yml` — CI pipeline
- [ ] `README.md` — quickstart, commands, requirements
- [ ] `ARCHITECTURE.md` — detailed design (1000+ lines)
- [ ] `CHECKLIST.md` — this file
- [ ] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `LICENSE`, `SECURITY.md`
- [ ] `.gitignore`, `.gitattributes`, `pyproject.toml`, `Makefile`, `tox.ini`

## Python Package: pyproject, Dependencies, Extras

- [ ] Package via `pyproject.toml` (Poetry or PEP 621):
  - [ ] `name = "ovmobilebench"`, `version`, `readme`, `scripts`.
  - [ ] Runtime deps: `typer`, `pydantic`, `pyyaml`, `paramiko`, `pandas`, `rich`.
  - [ ] Dev deps: `pytest`, `pytest-cov`, `mypy`, `ruff`, `black`.
  - [ ] Extras: `[dev]`, `[ssh]`, `[viz]` as needed.
- [ ] Minimum Python version: 3.11 (pinned in CI).
- [ ] Dependency pinning strategy: `^` / `~` / exact.
- [ ] Commands: `ovmobilebench build|package|deploy|run|report|all`.
- [ ] `entry_points`: `ovmobilebench = "ovmobilebench.cli:app"`.

## Code Quality: Formatting, Linting, Typing, Hooks

- [ ] **Black** (formatting) and **Ruff** (linting) configured.
- [ ] **Mypy** (strict options for `ovmobilebench/core`, `devices/*`).
- [ ] `pre-commit` with black, ruff, mypy, trailing-whitespace, end-of-file-fixer.
- [ ] Quality badges in README (lint/type/test).
- [ ] Ruff profiles for excluding dirs (e.g., `artifacts/`).
- [ ] Fast unit tests (≤ 1 min locally) for core modules.

## External Tooling: NDK/SDK, CMake/Ninja, ADB, OMZ

- [ ] Android **NDK r26d+** installed (path documented in README and CI).
- [ ] **CMake ≥ 3.24** and **Ninja ≥ 1.11** installed.
- [ ] **ADB** available locally and on self-hosted runner.
- [ ] Optional: **OMZ** (Open Model Zoo) for model download/convert.
- [ ] Installation docs included for Linux/macOS/Windows.

## Secrets, Access, Environment Variables

- [ ] Document environment variables for CI (examples):
  - [ ] `ANDROID_NDK` (path on runner or secret/mount)
  - [ ] `SSH_KEY` / `SSH_KNOWN_HOSTS` (Linux ARM)
  - [ ] `S3_*` / `GCS_*` (if exporting artifacts)
- [ ] **Never** commit secrets in YAML/repo.
- [ ] Use GitHub Secrets/Environments; restrict scope to teams/branches.
- [ ] Secret updates through DevOps/Infra with audit logs.

## CI/CD: Pipelines, Artifacts, Gates, Caching

- [ ] `bench.yml` with two jobs:
  - [ ] **build-android**: build & package; upload artifact.
  - [ ] **run-on-device** (self-hosted): download artifact, deploy, run, report.
- [ ] PR gates: lint → type → unit → build → (opt) smoke run on device.
- [ ] Caching: pip/poetry and CMake/Ninja (actions/cache).
- [ ] Artifact retention: ≥ 7–30 days; name with `run_id` and `commit`.
- [ ] Publishing results: artifacts, S3/GCS, PR comments with FPS tables.
- [ ] Parallelism control: `concurrency.group` to avoid race conditions.

## Artifacts, Storage, Retention, Data Layout

- [ ] Artifacts:
  - [ ] `ovbundle_<platform>_<commit>.tar.gz`
  - [ ] `experiments/out/*.json` and `.csv`
  - [ ] JSONL stage logs and device metadata
  - [ ] (opt) SQLite DB with results
- [ ] Standardized record fields (timestamp, model, device, params, metrics).
- [ ] Retention and access defined (repo settings/S3 lifecycle).
- [ ] Local cleanup policy for `artifacts/` (`make clean`).

## Testing: Unit, Integration, System Runs

- [ ] Unit tests: metrics parser, command generation, device wrappers.
- [ ] Integration: bundle packaging (without real NDK), pipeline dry-run.
- [ ] System: minimal run nightly on a “test” device.
- [ ] Coverage: target ≥ 70%; report in CI.
- [ ] Pytest markers: `slow`, `device`, `ssh` — off by default.

## Device Farm: Inventory, Scheduling, Health

- [ ] Inventory (`devices.yaml`): serial → SoC/CPU/RAM/Android/tags.
- [ ] Scheduling by labels (e.g., armv8 + Android 12 only).
- [ ] Parallel across devices; serialize runs within a single device.
- [ ] Health checks: `adb devices`, `adb shell true`, auto-reconnect.
- [ ] SOP documented: replace device, update firmware, factory reset.

## Performance & Stability Methodology

- [ ] Fix **LD_LIBRARY_PATH** and ensure dependencies are co-packaged.
- [ ] **Cooldown** between runs; **warm-up** run (excluded from stats).
- [ ] Android stabilization: disable animations, screen off, airplane mode (if permitted).
- [ ] Governor/affinity only on allowed/rooted devices.
- [ ] Metrics: medians across repeats; keep raw log tail for diagnostics.

## Models & Data Licensing

- [ ] OMZ/open models — OK; proprietary models via artifacts/private buckets only.
- [ ] Record `sha256` and model version; consider excluding `.bin/.xml` from git.
- [ ] Respect model licenses; document in README/NOTICE.

## Security & Compliance

- [ ] `SECURITY.md`: how to report vulnerabilities.
- [ ] Secret scanning and dependency CVE tracking in place.
- [ ] Avoid PII in logs; redact sensitive paths.
- [ ] (Opt) SBOM for bundle; dependency license scanning.

## Documentation: README, CONTRIBUTING, ARCH, CHECKLIST

- [ ] README: crisp, badges, requirements, commands, “first run”.
- [ ] ARCHITECTURE.md: full design & rationale.
- [ ] CONTRIBUTING.md: how to run tests/lint, PR process, branching.
- [ ] CHECKLIST.md: this preflight registry.
- [ ] CHANGELOG.md: manual or Conventional Commits + tooling.

## Releases & Versioning

- [ ] Choose scheme: SemVer/CalVer, pre-releases (`-alpha.1`).
- [ ] Tags and release notes (auto-generated from PRs/commits).
- [ ] Release artifacts: signed hashes, bundle archive, baseline results.
- [ ] Version support policy and EOL.

## Issue/PR Templates, CODEOWNERS, Labels & Workflow Policies

- [ ] `.github/ISSUE_TEMPLATE/*.md` — bug/feature/perf/regression.
- [ ] `.github/pull_request_template.md` — what/why/how tested/screenshots.
- [ ] `CODEOWNERS` — by directories and critical files.
- [ ] Labels: `perf`, `infra`, `bug`, `good-first-issue`, `help-wanted`, etc.
- [ ] Branch policy: `main`, `feature/*`, `release/*`, `hotfix/*`.

## Rollback Plan & Incident Management

- [ ] Document release rollback (revert tags/releases, close artifacts).
- [ ] On-call/owners; SLA for CI outage or regression.
- [ ] Post-mortem template (what happened, root cause, action items).

### Extended Checklist: Core Engineer

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: CI/CD Engineer

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: ML Engineer

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: DevRel/Documentation

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: Security Owner

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Extended Checklist: Release Manager

- [ ] Review architecture and current decisions.
- [ ] Verify your domain meets this CHECKLIST requirements.
- [ ] Keep README/ARCH/CONTRIBUTING sections up to date.
- [ ] Maintain/run SOPs for your area.
- [ ] Provide test scenario and minimal examples for review.
- [ ] Raise risks, blockers, and tooling needs.
- [ ] Keep pipelines green and minimize flake-rate.
- [ ] Participate in periodic perf/quality reviews.

### Phase Bootstrap: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Build: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Package: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Deploy: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Run: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Parse: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Report: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

### Phase Release: Control Checklist

- [ ] CLI entrypoints documented and tested.
- [ ] Logs and artifacts written to expected directories.
- [ ] Errors categorized and propagated clearly.
- [ ] Execution time within SLO.
- [ ] Idempotency: reruns do not corrupt results/environment.
- [ ] Phase docs updated alongside code changes.

## Appendices: File Templates & Examples

### .gitignore (minimal)
```
.artifacts/
artifacts/
models/*
!models/.gitkeep
.venv/
__pycache__/
dist/
build/
*.egg-info/
.env
*.tar.gz
```

### CODEOWNERS (example)
```
*                 @team/owners
/ovmobilebench/core/    @team/core
/ovmobilebench/devices/ @team/devices
/.github/         @team/ci
```

### Pull Request Template (example)
```
## What & Why
-

## How Tested
-

## Author Checklist
- [ ] Lint/types/tests green
- [ ] Docs updated
- [ ] No secrets/PII in logs
```

### Issue Template — Performance Regression
```
### Description
Performance regression (model/device/params).

### Steps to Reproduce
1) 
2) 
3) 

### Expected / Actual
-

### Attachments
- Logs, JSON/CSV, tooling versions
```


## Expanded Task Index

- [ ] Check #001: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #002: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #003: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #004: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #005: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #006: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #007: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #008: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #009: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #010: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #011: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #012: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #013: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #014: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #015: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #016: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #017: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #018: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #019: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #020: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #021: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #022: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #023: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #024: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #025: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #026: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #027: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #028: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #029: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #030: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #031: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #032: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #033: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #034: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #035: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #036: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #037: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #038: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #039: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #040: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #041: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #042: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #043: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #044: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #045: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #046: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #047: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #048: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #049: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #050: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #051: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #052: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #053: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #054: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #055: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #056: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #057: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #058: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #059: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #060: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #061: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #062: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #063: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #064: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #065: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #066: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #067: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #068: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #069: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #070: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #071: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #072: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #073: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #074: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #075: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #076: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #077: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #078: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #079: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #080: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #081: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #082: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #083: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #084: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #085: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #086: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #087: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #088: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #089: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #090: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #091: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #092: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #093: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #094: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #095: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #096: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #097: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #098: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #099: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #100: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #101: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #102: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #103: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #104: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #105: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #106: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #107: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #108: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #109: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #110: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #111: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #112: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #113: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #114: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #115: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #116: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #117: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #118: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #119: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #120: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #121: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #122: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #123: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #124: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #125: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #126: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #127: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #128: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #129: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #130: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #131: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #132: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #133: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #134: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #135: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #136: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #137: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #138: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #139: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #140: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #141: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #142: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #143: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #144: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #145: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #146: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #147: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #148: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #149: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #150: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #151: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #152: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #153: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #154: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #155: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #156: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #157: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #158: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #159: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #160: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #161: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #162: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #163: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #164: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #165: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #166: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #167: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #168: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #169: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #170: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #171: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #172: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #173: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #174: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #175: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #176: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #177: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #178: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #179: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #180: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #181: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #182: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #183: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #184: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #185: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #186: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #187: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #188: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #189: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #190: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #191: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #192: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #193: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #194: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #195: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #196: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #197: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #198: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #199: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #200: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #201: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #202: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #203: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #204: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #205: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #206: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #207: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #208: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #209: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #210: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #211: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #212: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #213: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #214: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #215: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #216: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #217: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #218: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #219: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #220: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #221: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #222: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #223: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #224: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #225: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #226: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #227: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #228: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #229: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #230: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #231: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #232: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #233: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #234: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #235: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #236: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #237: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #238: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #239: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #240: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #241: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #242: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #243: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #244: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #245: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #246: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #247: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #248: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #249: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #250: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #251: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #252: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #253: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #254: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #255: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #256: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #257: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #258: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #259: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #260: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #261: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #262: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #263: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #264: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #265: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #266: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #267: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #268: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #269: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #270: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #271: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #272: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #273: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #274: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #275: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #276: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #277: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #278: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #279: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #280: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #281: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #282: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #283: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #284: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #285: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #286: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #287: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #288: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #289: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #290: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #291: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #292: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #293: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #294: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #295: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #296: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #297: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #298: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #299: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #300: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #301: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #302: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #303: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #304: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #305: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #306: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #307: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #308: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #309: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #310: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #311: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #312: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #313: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #314: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #315: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #316: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #317: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #318: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #319: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #320: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #321: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #322: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #323: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #324: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #325: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #326: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #327: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #328: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #329: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #330: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #331: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #332: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #333: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #334: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #335: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #336: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #337: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #338: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #339: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #340: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #341: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #342: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #343: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #344: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #345: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #346: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #347: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #348: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #349: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #350: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #351: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #352: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #353: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #354: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #355: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #356: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #357: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #358: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #359: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #360: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #361: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #362: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #363: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #364: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #365: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #366: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #367: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #368: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #369: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #370: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #371: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #372: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #373: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #374: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #375: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #376: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #377: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #378: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #379: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #380: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #381: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #382: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #383: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #384: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #385: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #386: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #387: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #388: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #389: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #390: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #391: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #392: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #393: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #394: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #395: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #396: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #397: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #398: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #399: See CI/CD, Security, Testing, and Device Farm sections.
- [ ] Check #400: See CI/CD, Security, Testing, and Device Farm sections.
```
### `LICENSE`

```text
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
... (standard MIT text shortened for brevity in this snippet; include full text in real repo) ...

```
### `SECURITY.md`

```markdown
# Security Policy

## Reporting
Please report vulnerabilities privately via security@example.com. We will acknowledge within 72 hours.

## Scope
Source under /ovmobilebench/**, CI workflows, and published artifacts.

```
### `CODE_OF_CONDUCT.md`

```markdown
# Code of Conduct
We follow the Contributor Covenant. Be respectful, inclusive, and constructive.

```
### `CONTRIBUTING.md`

```markdown
# Contributing

## Dev Setup
- Python 3.11+, Poetry or pip
- `poetry install` or `pip install -e .[dev]`

## Tests & Lint
- `pytest -q`
- `ruff ovmobilebench && black --check ovmobilebench && mypy ovmobilebench`

```
### `.gitignore`

```text
.artifacts/
artifacts/
models/*
!models/.gitkeep
.venv/
__pycache__/
dist/
build/
*.egg-info/
.env
*.tar.gz

```
### `.gitattributes`

```text
* text=auto eol=lf

```
### `.pre-commit-config.yaml`

```yaml
repos:
- repo: https://github.com/psf/black
  rev: 24.4.2
  hooks:
    - id: black
      args: [--line-length=100]

- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.5.0
  hooks:
    - id: ruff
      args: [--fix]

- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.10.0
  hooks:
    - id: mypy
      additional_dependencies: ["types-PyYAML"]
      args: ["--strict", "--ignore-missing-imports"]

- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.6.0
  hooks:
    - id: end-of-file-fixer
    - id: trailing-whitespace

```
### `pyproject.toml`

```toml
[tool.poetry]
name = "ovmobilebench"
version = "0.1.0"
description = "End-to-end benchmarking pipeline for OpenVINO on mobile devices"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
packages = [{ include = "ovmobilebench" }]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.3"
pydantic = "^2.8.2"
pyyaml = "^6.0.2"
paramiko = "^3.4.0"
pandas = "^2.2.2"
rich = "^13.7.1"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.0"
pytest-cov = "^5.0.0"
mypy = "^1.10.0"
ruff = "^0.5.0"
black = "^24.4.2"
pre-commit = "^3.7.1"

[tool.poetry.scripts]
ovmobilebench = "ovmobilebench.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

```
### `Makefile`

```makefile
#.PHONY targets
.PHONY: help build package deploy run report all lint fmt type test clean

help:
	@echo "Targets: build package deploy run report all lint fmt type test clean"

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
	ruff ovmobilebench

fmt:
	black ovmobilebench

type:
	mypy ovmobilebench

test:
	pytest -q

clean:
	rm -rf artifacts/ .pytest_cache .mypy_cache .ruff_cache dist build

```
### `tox.ini`

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
### `Dockerfile.dev`

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.11
RUN apt-get update && apt-get install -y --no-install-recommends \    git cmake ninja-build unzip curl wget zip && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://dl.google.com/android/repository/platform-tools-latest-linux.zip -o /tmp/pt.zip && \    unzip /tmp/pt.zip -d /opt && rm /tmp/pt.zip && \    ln -s /opt/platform-tools/adb /usr/local/bin/adb
WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY ovmobilebench ./ovmobilebench
RUN pip install -U pip && pip install .[dev]

```
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
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -U pip poetry && poetry install
      - name: Build & Package
        env:
          ANDROID_NDK: ${{ secrets.ANDROID_NDK }}
        run: |
          export PATH="$ANDROID_NDK:$PATH"
          poetry run ovmobilebench build -c experiments/android_mcpu_fp16.yaml
          poetry run ovmobilebench package -c experiments/android_mcpu_fp16.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: ovbundle-android
          path: artifacts/**/*
          if-no-files-found: error
  run-on-device:
    needs: build-android
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: actions/download-artifact@v4
        with:
          name: ovbundle-android
          path: artifacts
      - run: pip install -U pip && pip install .
      - name: Deploy & Run
        env:
          ANDROID_SERIALS: "R3CN30XXXX"
        run: |
          python - <<'PY'
          import yaml
          with open('experiments/android_mcpu_fp16.yaml') as f:
            cfg = yaml.safe_load(f)
          cfg['device']['serials'] = "${{ env.ANDROID_SERIALS }}".split(',')
          with open('experiments/ci.yaml','w') as f:
            yaml.safe_dump(cfg, f)
          PY
          ovmobilebench deploy -c experiments/ci.yaml
          ovmobilebench run -c experiments/ci.yaml
          ovmobilebench report -c experiments/ci.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: results
          path: experiments/out/*

```
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
  extra_files: []
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
  repeats: 3
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

```
### `models/.gitkeep`

```text

```
### `ovmobilebench/__init__.py`

```python
__all__ = []

```
### `ovmobilebench/cli.py`

```python
import typer
from ovmobilebench.pipeline import run_all
from ovmobilebench.config.schema import Experiment
import yaml

app = typer.Typer(add_completion=False)

def load_experiment(path: str) -> Experiment:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Experiment(**data)

@app.command()
def all(c: str, verbose: bool = False):
    cfg = load_experiment(c)
    run_all(cfg)

@app.command()
def build(c: str):
    cfg = load_experiment(c)
    # TODO: call builders — placeholder
    typer.echo("Build stage placeholder")

@app.command()
def package(c: str):
    typer.echo("Package stage placeholder")

@app.command()
def deploy(c: str):
    typer.echo("Deploy stage placeholder")

@app.command()
def run(c: str):
    typer.echo("Run stage placeholder")

@app.command()
def report(c: str):
    typer.echo("Report stage placeholder")

if __name__ == "__main__":
    app()

```
### `ovmobilebench/pipeline.py`

```python
from ovmobilebench.config.schema import Experiment

def run_all(cfg: Experiment):
    # Placeholder orchestrator to be replaced with real steps
    print("Running full pipeline for", cfg.project.name, "run_id:", cfg.project.run_id)

```
### `ovmobilebench/config/schema.py`

```python

from pydantic import BaseModel, Field
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

```
### `ovmobilebench/devices/base.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple

class Device(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def push(self, local: Path, remote: str) -> None: ...
    @abstractmethod
    def shell(self, cmd: str, timeout: int | None = None) -> Tuple[int, str, str]: ...
    @abstractmethod
    def exists(self, remote_path: str) -> bool: ...
    @abstractmethod
    def pull(self, remote: str, local: Path) -> None: ...
    @abstractmethod
    def info(self) -> dict: ...

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
        cp = self._adb(["shell", cmd])
        return cp.returncode, cp.stdout, cp.stderr

    def exists(self, remote_path: str) -> bool:
        rc, _, _ = self.shell(f"ls {remote_path}")
        return rc == 0

    def pull(self, remote: str, local: Path) -> None:
        self._adb(["pull", remote, str(local)])

    def info(self) -> dict:
        rc, props, _ = self.shell("getprop")
        return {"os": "Android", "props": props, "serial": self.serial}

```
### `ovmobilebench/parsers/benchmark_parser.py`

```python
import re

RE = {
  "throughput": re.compile(r"Throughput:\s*([\d.]+)\s*(FPS|fps)"),
  "lat_avg":    re.compile(r"Average latency:\s*([\d.]+)\s*ms"),
  "lat_min":    re.compile(r"Min latency:\s*([\d.]+)\s*ms"),
  "lat_max":    re.compile(r"Max latency:\s*([\d.]+)\s*ms"),
  "lat_med":    re.compile(r"Median latency:\s*([\d.]+)\s*ms"),
  "count":      re.compile(r"count:\s*(\d+)"),
  "device_full":re.compile(r"Device:\s*(.+)"),
}

def _get(pat, text, cast=float):
    m = RE[pat].search(text)
    return cast(m.group(1)) if m else None

def parse_metrics(text: str) -> dict:
    return {
        "throughput_fps": _get("throughput", text),
        "latency_avg_ms": _get("lat_avg", text),
        "latency_min_ms": _get("lat_min", text),
        "latency_max_ms": _get("lat_max", text),
        "latency_med_ms": _get("lat_med", text),
        "iterations": _get("count", text, int),
        "raw_device_line": (RE["device_full"].search(text).group(1)
                            if RE["device_full"].search(text) else None),
        "raw": text[-2000:],
    }

```
### `ovmobilebench/runners/benchmark.py`

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class RunSpec:
    model_xml: str
    device: str
    api: str
    niter: int
    nireq: int
    nstreams: str | None
    threads: int | None

def build_cmd(push_dir: str, spec: RunSpec) -> str:
    parts = [
        f"{push_dir}/bin/benchmark_app",
        f"-m {push_dir}/models/{Path(spec.model_xml).name}",
        f"-d {spec.device}", f"-api {spec.api}", f"-niter {spec.niter}",
        f"-nireq {spec.nireq}"
    ]
    if spec.nstreams: parts += [f"-nstreams {spec.nstreams}"]
    if spec.threads:  parts += [f"-nthreads {spec.threads}"]
    return " ".join(parts)

```
### `ovmobilebench/report/sink.py`

```python
import json, csv
from pathlib import Path

def write_json(rows: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f: json.dump(rows, f, ensure_ascii=False, indent=2)

def write_csv(rows: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

```
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
    args = cmd if isinstance(cmd, (list, tuple)) else shlex.split(cmd)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=cwd)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return CommandResult(124, out, "TIMEOUT: " + err, time.time() - start)
    return CommandResult(proc.returncode, out, err, time.time() - start)

```
### `ovmobilebench/core/fs.py`

```python
from pathlib import Path
def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

```
### `ovmobilebench/core/artifacts.py`

```python
from dataclasses import dataclass

@dataclass
class ArtifactRef:
    platform: str
    commit: str
    build_type: str

```
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
### `CODEOWNERS`

```text
*                 @team/owners
/ovmobilebench/core/    @team/core
/ovmobilebench/devices/ @team/devices
/.github/         @team/ci

```