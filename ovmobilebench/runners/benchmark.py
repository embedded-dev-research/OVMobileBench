"""Benchmark runner implementation."""

import logging
import time
from collections.abc import Callable
from typing import Any

from ovmobilebench.config.schema import RunConfig
from ovmobilebench.devices.base import Device

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Execute benchmark_app on device."""

    def __init__(
        self,
        device: Device,
        config: RunConfig,
        remote_dir: str = "/data/local/tmp/ovmobilebench",
    ):
        self.device = device
        self.config = config
        self.remote_dir = remote_dir

    def run_single(
        self,
        spec: dict[str, Any],
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Run single benchmark configuration."""
        cmd = self._build_command(spec)

        logger.info(f"Running: {cmd}")

        start_time = time.time()
        rc, stdout, stderr = self.device.shell(cmd, timeout=timeout or self.config.timeout_sec)
        duration = time.time() - start_time

        result = {
            "spec": spec,
            "command": cmd,
            "returncode": rc,
            "stdout": stdout,
            "stderr": stderr,
            "duration_sec": duration,
            "timestamp": time.time(),
        }

        if rc != 0:
            error_msg = stderr if stderr else stdout
            logger.error(f"Benchmark failed with rc={rc}: {error_msg}")

        return result

    def run_matrix(
        self,
        matrix_specs: list[dict[str, Any]],
        progress_callback: Callable | None = None,
    ) -> list[dict[str, Any]]:
        """Run complete matrix of configurations."""
        results = []
        total = len(matrix_specs) * self.config.repeats
        completed = 0

        for spec in matrix_specs:
            for repeat in range(self.config.repeats):
                logger.info(
                    f"Running {spec['model_name']} - repeat {repeat + 1}/{self.config.repeats}"
                )

                # Cooldown between runs
                if completed > 0 and self.config.cooldown_sec > 0:
                    logger.info(f"Cooldown for {self.config.cooldown_sec}s")
                    time.sleep(self.config.cooldown_sec)

                # Run benchmark
                result = self.run_single(spec)
                result["repeat"] = repeat
                results.append(result)

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        return results

    def _build_command(self, spec: dict[str, Any]) -> str:
        """Build benchmark_app command line."""
        cmd_parts = [
            f"cd {self.remote_dir} &&",
            f"export LD_LIBRARY_PATH={self.remote_dir}/lib:$LD_LIBRARY_PATH &&",
            "./bin/benchmark_app",
            f"-m models/{spec['model_name']}.xml",
            f"-d {spec['device']}",
            f"-api {spec['api']}",
            f"-niter {spec['niter']}",
        ]

        # Performance hint (latency, throughput, or none)
        if "hint" in spec:
            cmd_parts.append(f"-hint {spec['hint']}")

        # If hint is "none", we can use the fine-tuning options
        if spec.get("hint") == "none":
            if "nireq" in spec:
                cmd_parts.append(f"-nireq {spec['nireq']}")
            if "nstreams" in spec:
                cmd_parts.append(f"-nstreams {spec['nstreams']}")
            if "threads" in spec:
                cmd_parts.append(f"-nthreads {spec['threads']}")

        # Inference precision
        if "infer_precision" in spec:
            cmd_parts.append(f"-infer_precision {spec['infer_precision']}")

        return " ".join(cmd_parts)

    def warmup(self, model_name: str):
        """Perform warmup run."""
        spec = {
            "model_name": model_name,
            "device": "CPU",
            "api": "sync",
            "niter": 10,
            "hint": "latency",
        }

        logger.info(f"Warmup run for {model_name}")
        self.run_single(spec, timeout=30)
