"""Core orchestration for Android tools installation."""

from pathlib import Path
from typing import Optional

from .avd import AvdManager
from .detect import check_disk_space, detect_host
from .env import EnvExporter
from .errors import PermissionError as InstallerPermissionError
from .logging import StructuredLogger
from .ndk import NdkResolver
from .plan import Planner
from .sdkmanager import SdkManager
from .types import Arch, InstallerResult, NdkSpec, Target


class AndroidInstaller:
    """Main orchestrator for Android tools installation."""

    def __init__(
        self, sdk_root: Path, *, logger: Optional[StructuredLogger] = None, verbose: bool = False
    ):
        """Initialize Android installer.

        Args:
            sdk_root: Root directory for Android SDK
            logger: Optional logger instance
            verbose: Enable verbose logging
        """
        self.sdk_root = sdk_root.absolute()
        self.logger = logger
        self.verbose = verbose

        # Initialize components
        self.sdk = SdkManager(sdk_root, logger=logger)
        self.ndk = NdkResolver(sdk_root, logger=logger)
        self.avd = AvdManager(sdk_root, logger=logger)
        self.env = EnvExporter(logger=logger)
        self.planner = Planner(sdk_root, logger=logger)

    def ensure(
        self,
        *,
        api: int,
        target: Target,
        arch: Arch,
        ndk: NdkSpec,
        install_platform_tools: bool = True,
        install_emulator: bool = True,
        install_build_tools: Optional[str] = None,
        create_avd_name: Optional[str] = None,
        accept_licenses: bool = True,
        dry_run: bool = False,
    ) -> InstallerResult:
        """Ensure Android tools are installed.

        Args:
            api: API level
            target: System image target
            arch: Architecture
            ndk: NDK specification
            install_platform_tools: Install platform-tools
            install_emulator: Install emulator and system image
            install_build_tools: Optional build-tools version to install
            create_avd_name: Optional AVD name to create
            accept_licenses: Accept SDK licenses
            dry_run: Only show what would be done

        Returns:
            Installation result

        Raises:
            InstallerError: If installation fails
        """
        # Log host information
        if self.logger:
            host = detect_host()
            self.logger.info(
                f"Host: {host.os} {host.arch}",
                os=host.os,
                arch=host.arch,
                has_kvm=host.has_kvm,
                java_version=host.java_version,
            )

        # Check disk space
        if not check_disk_space(self.sdk_root, required_gb=15.0):
            if self.logger:
                self.logger.warning("Low disk space detected (< 15GB free)")

        # Build installation plan
        plan = self.planner.build_plan(
            api=api,
            target=target,
            arch=arch,
            install_platform_tools=install_platform_tools,
            install_emulator=install_emulator,
            ndk=ndk,
            create_avd_name=create_avd_name,
        )

        # Log the plan
        if self.logger:
            estimated_size = self.planner.estimate_size(plan)
            self.logger.info(
                f"Installation plan (estimated size: {estimated_size}MB)",
                plan={
                    "cmdline_tools": plan.need_cmdline_tools,
                    "platform_tools": plan.need_platform_tools,
                    "platform": plan.need_platform,
                    "system_image": plan.need_system_image,
                    "emulator": plan.need_emulator,
                    "ndk": plan.need_ndk,
                    "avd": plan.create_avd_name,
                },
                estimated_size_mb=estimated_size,
            )

        # Dry run mode - just show plan
        if dry_run:
            self.planner.validate_dry_run(plan)
            if self.logger:
                self.logger.info("Dry run complete (no changes made)")
            return InstallerResult(
                sdk_root=self.sdk_root,
                ndk_path=self.ndk.resolve_path(ndk) if not plan.need_ndk else Path("/placeholder"),
                avd_created=False,
                performed={"dry_run": True, "plan": plan.__dict__},
            )

        # Check permissions
        try:
            self._check_permissions()
        except PermissionError:
            raise InstallerPermissionError(self.sdk_root, "write")

        # Execute installation
        performed = {}

        # Accept licenses if needed
        if accept_licenses and (plan.need_cmdline_tools or plan.has_work()):
            # Ensure cmdline-tools first if needed
            if plan.need_cmdline_tools:
                self.sdk.ensure_cmdline_tools()
                performed["cmdline_tools"] = True

            self.sdk.accept_licenses()
            performed["licenses_accepted"] = True

        # Install components
        if plan.need_cmdline_tools and "cmdline_tools" not in performed:
            self.sdk.ensure_cmdline_tools()
            performed["cmdline_tools"] = True

        if plan.need_platform_tools:
            self.sdk.ensure_platform_tools()
            performed["platform_tools"] = True

        if plan.need_platform:
            self.sdk.ensure_platform(api)
            performed[f"platform_{api}"] = True

        if install_build_tools:
            self.sdk.ensure_build_tools(install_build_tools)
            performed[f"build_tools_{install_build_tools}"] = True

        if plan.need_emulator:
            self.sdk.ensure_emulator()
            performed["emulator"] = True

        if plan.need_system_image:
            self.sdk.ensure_system_image(api, target, arch)
            performed[f"system_image_{api}_{target}_{arch}"] = True

        # Install NDK
        ndk_path = self.ndk.ensure(ndk)
        if plan.need_ndk:
            performed["ndk"] = True

        # Create AVD if requested
        avd_created = False
        if create_avd_name:
            avd_created = self.avd.create(create_avd_name, api, target, arch)
            performed[f"avd_{create_avd_name}"] = avd_created

        # Log summary
        if self.logger:
            self.logger.success(
                "Installation complete",
                sdk_root=str(self.sdk_root),
                ndk_path=str(ndk_path),
                avd_created=avd_created,
                components_installed=list(performed.keys()),
            )

        return InstallerResult(
            sdk_root=self.sdk_root,
            ndk_path=ndk_path,
            avd_created=avd_created,
            performed=performed,
        )

    def _check_permissions(self) -> None:
        """Check if we have write permissions to SDK root.

        Raises:
            PermissionError: If no write permissions
        """
        # Create SDK root if it doesn't exist
        try:
            self.sdk_root.mkdir(parents=True, exist_ok=True)

            # Try to create a test file
            test_file = self.sdk_root / ".permission_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, IOError) as e:
            raise PermissionError(f"No write permission for {self.sdk_root}: {e}")

    def cleanup(self, remove_downloads: bool = True, remove_temp: bool = True) -> None:
        """Clean up temporary files and downloads.

        Args:
            remove_downloads: Remove downloaded archives
            remove_temp: Remove temporary directories
        """
        if self.logger:
            self.logger.info("Cleaning up temporary files")

        cleanup_count = 0

        # Remove downloaded archives
        if remove_downloads:
            patterns = ["*.zip", "*.tar.gz", "*.dmg"]
            for pattern in patterns:
                for file in self.sdk_root.glob(pattern):
                    if self.logger:
                        self.logger.debug(f"Removing: {file.name}")
                    file.unlink()
                    cleanup_count += 1

        # Remove temp directories
        if remove_temp:
            temp_dirs = ["temp", "tmp", ".temp"]
            for dir_name in temp_dirs:
                temp_dir = self.sdk_root / dir_name
                if temp_dir.exists():
                    if self.logger:
                        self.logger.debug(f"Removing directory: {temp_dir.name}")
                    import shutil

                    shutil.rmtree(temp_dir)
                    cleanup_count += 1

        if self.logger:
            self.logger.info(f"Cleaned up {cleanup_count} items")

    def verify(self) -> dict:
        """Verify installation status.

        Returns:
            Dictionary with verification results
        """
        results = {
            "sdk_root_exists": self.sdk_root.exists(),
            "cmdline_tools": False,
            "platform_tools": False,
            "emulator": False,
            "ndk": False,
            "avds": [],
        }

        # Check cmdline-tools
        sdkmanager = self.sdk_root / "cmdline-tools" / "latest" / "bin" / "sdkmanager"
        results["cmdline_tools"] = sdkmanager.exists()

        # Check platform-tools
        adb = self.sdk_root / "platform-tools" / "adb"
        results["platform_tools"] = adb.exists()

        # Check emulator
        emulator = self.sdk_root / "emulator" / "emulator"
        results["emulator"] = emulator.exists()

        # Check NDK
        ndk_installations = self.ndk.list_installed()
        results["ndk"] = len(ndk_installations) > 0
        results["ndk_versions"] = [version for version, _ in ndk_installations]

        # Check AVDs
        try:
            results["avds"] = self.avd.list()
        except Exception:
            results["avds"] = []

        # List installed components
        try:
            results["components"] = [comp.package_id for comp in self.sdk.list_installed()]
        except Exception:
            results["components"] = []

        if self.logger:
            self.logger.info("Verification complete", results=results)

        return results
