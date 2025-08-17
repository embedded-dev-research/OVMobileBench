"""Main orchestration pipeline."""

import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from ovmobilebench.config.schema import Experiment
from ovmobilebench.devices.android import AndroidDevice
from ovmobilebench.builders.openvino import OpenVINOBuilder
from ovmobilebench.packaging.packager import Packager
from ovmobilebench.runners.benchmark import BenchmarkRunner
from ovmobilebench.parsers.benchmark_parser import BenchmarkParser
from ovmobilebench.report.sink import JSONSink, CSVSink
from ovmobilebench.core.fs import ensure_dir
from ovmobilebench.core.errors import OVMobileBenchError, DeviceError, ConfigError

logger = logging.getLogger(__name__)


class Pipeline:
    """Main orchestration pipeline for benchmarking."""

    def __init__(
        self,
        config: Experiment,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        self.config = config
        self.verbose = verbose
        self.dry_run = dry_run
        self.artifacts_dir = ensure_dir(Path("artifacts") / config.project.run_id)
        self.results: List[Dict[str, Any]] = []

    def build(self) -> Optional[Path]:
        """Build OpenVINO runtime."""
        if not self.config.build.enabled:
            logger.info("Build disabled, skipping")
            return None

        if self.dry_run:
            logger.info("[DRY RUN] Would build OpenVINO")
            return None

        build_dir = self.artifacts_dir / "build"
        builder = OpenVINOBuilder(self.config.build, build_dir, self.verbose)

        return builder.build()

    def package(self) -> Optional[Path]:
        """Create deployment package."""
        if self.dry_run:
            logger.info("[DRY RUN] Would create package")
            return None

        # Get build artifacts
        build_dir = self.artifacts_dir / "build"
        artifacts = {}

        if self.config.build.enabled:
            builder = OpenVINOBuilder(self.config.build, build_dir, self.verbose)
            artifacts = builder.get_artifacts()

        # Create package
        packager = Packager(
            self.config.package,
            self.config.models,
            self.artifacts_dir / "packages",
        )

        bundle_name = f"ovbundle_{self.config.project.run_id}"
        return packager.create_bundle(artifacts, bundle_name)

    def deploy(self) -> None:
        """Deploy package to devices."""
        if self.dry_run:
            logger.info("[DRY RUN] Would deploy to devices")
            return

        bundle_path = self.artifacts_dir / "packages" / f"ovbundle_{self.config.project.run_id}"

        for serial in self.config.device.serials:
            logger.info(f"Deploying to device: {serial}")
            device = self._get_device(serial)

            if not device.is_available():
                raise DeviceError(f"Device not available: {serial}")

            # Clean and create remote directory
            device.cleanup(self.config.device.push_dir)
            device.mkdir(self.config.device.push_dir)

            # Push bundle
            device.push(bundle_path, self.config.device.push_dir)

            # Extract on device
            device.shell(f"cd {self.config.device.push_dir} && tar -xzf {bundle_path.name}")

            logger.info(f"Deployed to {serial}")

    def run(
        self,
        timeout: Optional[int] = None,
        cooldown: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Run benchmarks on devices."""
        if self.dry_run:
            logger.info("[DRY RUN] Would run benchmarks")
            return []

        all_results = []

        for serial in self.config.device.serials:
            logger.info(f"Running benchmarks on device: {serial}")
            device = self._get_device(serial)

            if not device.is_available():
                raise DeviceError(f"Device not available: {serial}")

            # Get device info
            device_info = device.info()

            # Prepare device for benchmarking
            self._prepare_device(device)

            # Create runner
            runner = BenchmarkRunner(
                device,
                self.config.run,
                f"{self.config.device.push_dir}/ovbundle_{self.config.project.run_id}",
            )

            # Run for each model
            for model in self.config.models:
                logger.info(f"Running model: {model.name}")

                # Warmup if enabled
                if self.config.run.warmup:
                    runner.warmup(model.name)

                # Expand matrix for model
                matrix_specs = self.config.expand_matrix_for_model(model)

                # Run matrix
                results = runner.run_matrix(matrix_specs)

                # Add metadata
                for result in results:
                    result["device_serial"] = serial
                    result["device_info"] = device_info
                    result["project"] = self.config.project.model_dump()
                    result["model_tags"] = model.tags

                all_results.extend(results)

        self.results = all_results
        return all_results

    def report(self) -> None:
        """Generate reports from results."""
        if not self.results:
            logger.warning("No results to report")
            return

        # Parse results
        parser = BenchmarkParser()
        parsed_results = [parser.parse_result(r) for r in self.results]

        # Aggregate if configured
        if self.config.report.aggregate:
            aggregated = parser.aggregate_results(parsed_results)
        else:
            aggregated = parsed_results

        # Add report tags
        for result in aggregated:
            result["tags"] = self.config.report.tags

        # Write to sinks
        for sink_config in self.config.report.sinks:
            path = Path(sink_config.path)

            sink: Union[JSONSink, CSVSink]
            if sink_config.type == "json":
                sink = JSONSink()
            elif sink_config.type == "csv":
                sink = CSVSink()
            else:
                logger.warning(f"Unknown sink type: {sink_config.type}")
                continue

            sink.write(aggregated, path)
            logger.info(f"Report written to: {path}")

    def _get_device(self, serial: str):
        """Get device instance."""
        if self.config.device.kind == "android":
            from .devices.android import AndroidDevice

            return AndroidDevice(serial, self.config.device.push_dir)
        elif self.config.device.type == "linux_ssh":
            from .devices.linux_ssh import LinuxSSHDevice

            # Parse SSH config from device section
            device_config = self.config.device.model_dump()
            host = device_config.get("host")
            if not host:
                raise ConfigError("SSH host must be specified in device configuration")
            return LinuxSSHDevice(
                host=host,
                username=device_config.get("username", os.environ.get("USER", "user")),
                password=device_config.get("password"),
                key_filename=device_config.get("key_filename"),
                port=device_config.get("port", 22),
                push_dir=device_config.get("push_dir", "/tmp/ovmobilebench"),
            )
        else:
            raise OVMobileBenchError(
                f"Unsupported device kind/type: {self.config.device.kind}/{getattr(self.config.device, 'type', 'unknown')}"
            )

    def _prepare_device(self, device: AndroidDevice) -> None:
        """Prepare device for benchmarking."""
        logger.info("Preparing device for benchmarking")

        # Disable animations
        device.disable_animations()

        # Screen off
        device.screen_off()

        # Log temperature
        temp = device.get_temperature()
        if temp:
            logger.info(f"Device temperature: {temp}°C")
