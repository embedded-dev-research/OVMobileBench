"""Main orchestration pipeline."""

import logging
import os
from pathlib import Path
from typing import Any

from ovmobilebench.builders.openvino import OpenVINOBuilder
from ovmobilebench.config.schema import Experiment
from ovmobilebench.core.errors import ConfigError, DeviceError, OVMobileBenchError
from ovmobilebench.core.fs import ensure_dir
from ovmobilebench.devices.android import AndroidDevice
from ovmobilebench.packaging.packager import Packager
from ovmobilebench.parsers.benchmark_parser import BenchmarkParser
from ovmobilebench.report.sink import CSVSink, JSONSink
from ovmobilebench.runners.benchmark import BenchmarkRunner

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
        self.results: list[dict[str, Any]] = []

    def build(self) -> Path | None:
        """Build or prepare OpenVINO runtime based on mode."""
        openvino_config = self.config.openvino

        if self.dry_run:
            logger.info(f"[DRY RUN] Would prepare OpenVINO in '{openvino_config.mode}' mode")
            return None

        if openvino_config.mode == "build":
            logger.info("Building OpenVINO from source")
            build_dir = self.artifacts_dir / "build"
            builder = OpenVINOBuilder(openvino_config, build_dir, self.verbose)
            return builder.build()

        elif openvino_config.mode == "install":
            logger.info(f"Using existing OpenVINO install from: {openvino_config.install_dir}")
            # Just return the install directory
            if openvino_config.install_dir is None:
                raise ValueError("install_dir must be specified when mode is 'install'")
            return Path(openvino_config.install_dir)

        elif openvino_config.mode == "link":
            logger.info(f"Downloading OpenVINO from: {openvino_config.archive_url}")
            if openvino_config.archive_url is None:
                raise ValueError("archive_url must be specified when mode is 'link'")
            return self._download_and_extract_openvino(openvino_config.archive_url)

        else:
            raise ValueError(f"Unknown OpenVINO mode: {openvino_config.mode}")

    def package(self) -> Path | None:
        """Create deployment package."""
        if self.dry_run:
            logger.info("[DRY RUN] Would create package")
            return None

        # Get OpenVINO artifacts based on mode
        artifacts = {}
        openvino_config = self.config.openvino

        if openvino_config.mode == "build":
            build_dir = self.artifacts_dir / "build"
            builder = OpenVINOBuilder(openvino_config, build_dir, self.verbose)
            artifacts = builder.get_artifacts()
        elif openvino_config.mode == "install":
            # Use existing install directory
            if openvino_config.install_dir is None:
                raise ValueError("install_dir must be specified when mode is 'install'")
            install_dir = Path(openvino_config.install_dir)
            artifacts = self._get_install_artifacts(install_dir)
        elif openvino_config.mode == "link":
            # Artifacts should be already downloaded in build() step
            download_dir = self.artifacts_dir / "openvino_download"
            artifacts = self._get_install_artifacts(download_dir)

        # Create package
        packager = Packager(
            self.config.package,
            self.config.get_model_list(),
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
        timeout: int | None = None,
        cooldown: int | None = None,
    ) -> list[dict[str, Any]]:
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
            for model in self.config.get_model_list():
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

            sink: JSONSink | CSVSink
            if sink_config.type == "json":
                sink = JSONSink()
            elif sink_config.type == "csv":
                sink = CSVSink()
            else:
                logger.warning(f"Unknown sink type: {sink_config.type}")
                continue

            sink.write(aggregated, path)
            logger.info(f"Report written to: {path}")

    def _download_and_extract_openvino(self, archive_url: str) -> Path:
        """Download and extract OpenVINO archive."""
        import json
        import platform
        import tarfile
        import urllib.request

        download_dir = self.artifacts_dir / "openvino_download"
        download_dir.mkdir(parents=True, exist_ok=True)

        # Handle 'latest' URL
        if archive_url == "latest":
            # Fetch latest.json to get actual URL
            latest_url = "https://storage.openvinotoolkit.org/repositories/openvino/packages/nightly/latest.json"
            logger.info(f"Fetching latest OpenVINO URL from: {latest_url}")

            with urllib.request.urlopen(latest_url) as response:
                latest_data = json.loads(response.read())

                # Auto-select based on platform and device config
                system = platform.system().lower()
                machine = platform.machine().lower()
                device_kind = self.config.device.kind

                # Determine the key to use
                if device_kind == "android":
                    # For Android, prefer ARM64 builds
                    if "linux_aarch64" in latest_data:
                        selected_key = "linux_aarch64"
                    elif "ubuntu22_arm64" in latest_data:
                        selected_key = "ubuntu22_arm64"
                    else:
                        logger.warning(
                            f"No ARM64 build found for Android. Available: {list(latest_data.keys())}"
                        )
                        # Fallback to first available
                        selected_key = list(latest_data.keys())[0]
                elif device_kind == "linux_ssh":
                    # For Linux SSH (e.g., Raspberry Pi), use ARM64
                    if "linux_aarch64" in latest_data:
                        selected_key = "linux_aarch64"
                    elif "rhel8_aarch64" in latest_data:
                        selected_key = "rhel8_aarch64"
                    elif "ubuntu22_arm64" in latest_data:
                        selected_key = "ubuntu22_arm64"
                    else:
                        logger.warning(
                            f"No ARM64 build found. Available: {list(latest_data.keys())}"
                        )
                        selected_key = list(latest_data.keys())[0]
                else:
                    # For host system, match current platform
                    selected_key = None
                    if "darwin" in system and "macos" in str(latest_data.keys()).lower():
                        selected_key = next(
                            (k for k in latest_data.keys() if "macos" in k.lower()), None
                        )
                    elif "linux" in system:
                        if "x86_64" in machine or "amd64" in machine:
                            ubuntu_key = next(
                                (
                                    k
                                    for k in latest_data.keys()
                                    if "ubuntu" in k.lower() and "arm" not in k.lower()
                                ),
                                None,
                            )
                            if ubuntu_key:
                                selected_key = ubuntu_key
                        else:
                            arm_key = next(
                                (
                                    k
                                    for k in latest_data.keys()
                                    if "arm" in k.lower() or "aarch" in k.lower()
                                ),
                                None,
                            )
                            if arm_key:
                                selected_key = arm_key

                    if not selected_key:
                        selected_key = list(latest_data.keys())[0]

                logger.info(f"Selected build: {selected_key}")
                archive_url = latest_data[selected_key]["url"]
                logger.info(f"Using archive URL: {archive_url}")

        # Download archive
        archive_path = download_dir / "openvino.tgz"
        if not archive_path.exists():
            logger.info(f"Downloading OpenVINO archive to: {archive_path}")
            urllib.request.urlretrieve(archive_url, archive_path)
        else:
            logger.info(f"Using cached archive: {archive_path}")

        # Extract archive
        extract_dir = download_dir / "extracted"
        if not extract_dir.exists():
            logger.info(f"Extracting archive to: {extract_dir}")
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(extract_dir)
        else:
            logger.info(f"Using already extracted archive: {extract_dir}")

        # Find install directory in extracted archive
        # Try different patterns
        patterns = [
            "*/runtime",
            "*/install",
            "*_package*/runtime",
            "l_openvino_toolkit*/runtime",
            "*",
        ]

        for pattern in patterns:
            install_dirs = list(extract_dir.glob(pattern))
            if install_dirs and install_dirs[0].is_dir():
                logger.info(f"Found OpenVINO directory: {install_dirs[0]}")
                return install_dirs[0]

        raise ValueError(
            f"Could not find OpenVINO install directory in archive. Contents: {list(extract_dir.iterdir())}"
        )

    def _get_install_artifacts(self, install_dir: Path) -> dict[str, Path]:
        """Get artifacts from an install directory."""
        artifacts = {}

        # Look for benchmark_app
        benchmark_apps = list(install_dir.glob("**/benchmark_app"))
        if benchmark_apps:
            artifacts["benchmark_app"] = benchmark_apps[0]

        # Look for libraries
        lib_dirs = list(install_dir.glob("**/lib"))
        if lib_dirs:
            artifacts["lib_dir"] = lib_dirs[0]

        # Look for plugins
        plugin_dirs = list(install_dir.glob("**/plugins.xml"))
        if plugin_dirs:
            artifacts["plugins_xml"] = plugin_dirs[0]

        return artifacts

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
                mock_mode=self.dry_run,  # Use mock mode in dry-run
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
