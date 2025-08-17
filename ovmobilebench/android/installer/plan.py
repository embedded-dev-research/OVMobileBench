"""Installation planning and validation utilities."""

from pathlib import Path
from typing import Optional

from .errors import InvalidArgumentError
from .logging import StructuredLogger
from .ndk import NdkResolver
from .types import Arch, InstallerPlan, NdkSpec, Target


class Planner:
    """Plan Android tools installation."""

    # Valid combinations of (api, target, arch)
    VALID_COMBINATIONS = {
        # Google ATD (Automated Test Device) - optimized for testing
        (30, "google_atd", "arm64-v8a"),
        (30, "google_atd", "x86_64"),
        (31, "google_atd", "arm64-v8a"),
        (31, "google_atd", "x86_64"),
        (32, "google_atd", "arm64-v8a"),
        (32, "google_atd", "x86_64"),
        (33, "google_atd", "arm64-v8a"),
        (33, "google_atd", "x86_64"),
        (34, "google_atd", "arm64-v8a"),
        (34, "google_atd", "x86_64"),
        # Google APIs - includes Play Services
        (28, "google_apis", "arm64-v8a"),
        (28, "google_apis", "x86_64"),
        (29, "google_apis", "arm64-v8a"),
        (29, "google_apis", "x86_64"),
        (30, "google_apis", "arm64-v8a"),
        (30, "google_apis", "x86_64"),
        (31, "google_apis", "arm64-v8a"),
        (31, "google_apis", "x86_64"),
        (32, "google_apis", "arm64-v8a"),
        (32, "google_apis", "x86_64"),
        (33, "google_apis", "arm64-v8a"),
        (33, "google_apis", "x86_64"),
        (34, "google_apis", "arm64-v8a"),
        (34, "google_apis", "x86_64"),
        # Default (AOSP) images
        (24, "default", "arm64-v8a"),
        (24, "default", "x86_64"),
        (25, "default", "arm64-v8a"),
        (25, "default", "x86_64"),
        (26, "default", "arm64-v8a"),
        (26, "default", "x86_64"),
        (27, "default", "arm64-v8a"),
        (27, "default", "x86_64"),
        (28, "default", "arm64-v8a"),
        (28, "default", "x86_64"),
        (29, "default", "arm64-v8a"),
        (29, "default", "x86_64"),
        (30, "default", "arm64-v8a"),
        (30, "default", "x86_64"),
        # x86 variants for older APIs
        (24, "default", "x86"),
        (25, "default", "x86"),
        (26, "default", "x86"),
        (27, "default", "x86"),
        (28, "default", "x86"),
        (28, "google_apis", "x86"),
        (29, "google_apis", "x86"),
        (30, "google_apis", "x86"),
    }

    def __init__(self, sdk_root: Path, logger: Optional[StructuredLogger] = None):
        """Initialize planner.

        Args:
            sdk_root: Root directory for Android SDK
            logger: Optional logger instance
        """
        self.sdk_root = sdk_root.absolute()
        self.logger = logger

    def build_plan(
        self,
        *,
        api: int,
        target: Target,
        arch: Arch,
        install_platform_tools: bool,
        install_emulator: bool,
        ndk: NdkSpec,
        create_avd_name: Optional[str] = None,
    ) -> InstallerPlan:
        """Build installation plan.

        Args:
            api: API level
            target: System image target
            arch: Architecture
            install_platform_tools: Whether to install platform-tools
            install_emulator: Whether to install emulator
            ndk: NDK specification
            create_avd_name: Optional AVD name to create

        Returns:
            Installation plan

        Raises:
            InvalidArgumentError: If arguments are invalid
        """
        # Validate combination
        self._validate_combination(api, target, arch)

        # Validate AVD requirements
        if create_avd_name and not install_emulator:
            raise InvalidArgumentError(
                "create_avd_name",
                create_avd_name,
                "Cannot create AVD without installing emulator",
            )

        # Check what needs to be installed
        plan = InstallerPlan(
            need_cmdline_tools=self._need_cmdline_tools(),
            need_platform_tools=install_platform_tools and self._need_platform_tools(),
            need_platform=self._need_platform(api),
            need_system_image=install_emulator and self._need_system_image(api, target, arch),
            need_emulator=install_emulator and self._need_emulator(),
            need_ndk=self._need_ndk(ndk),
            create_avd_name=create_avd_name,
        )

        if self.logger:
            self.logger.debug(
                "Installation plan created",
                plan={
                    "need_cmdline_tools": plan.need_cmdline_tools,
                    "need_platform_tools": plan.need_platform_tools,
                    "need_platform": plan.need_platform,
                    "need_system_image": plan.need_system_image,
                    "need_emulator": plan.need_emulator,
                    "need_ndk": plan.need_ndk,
                    "create_avd": plan.create_avd_name,
                },
            )

        return plan

    def _validate_combination(self, api: int, target: Target, arch: Arch) -> None:
        """Validate API/target/arch combination.

        Args:
            api: API level
            target: System image target
            arch: Architecture

        Raises:
            InvalidArgumentError: If combination is invalid
        """
        # Check API level range
        if api < 21 or api > 35:
            raise InvalidArgumentError(
                "api", api, "API level must be between 21 and 35"
            )

        # Check if combination is valid
        if (api, target, arch) not in self.VALID_COMBINATIONS:
            # Provide helpful error message
            valid_targets = set()
            valid_archs = set()
            for combo_api, combo_target, combo_arch in self.VALID_COMBINATIONS:
                if combo_api == api:
                    valid_targets.add(combo_target)
                    if combo_target == target:
                        valid_archs.add(combo_arch)

            if not valid_targets:
                raise InvalidArgumentError(
                    "api", api, f"No valid targets available for API {api}"
                )
            elif target not in valid_targets:
                raise InvalidArgumentError(
                    "target",
                    target,
                    f"Invalid target for API {api}. Valid: {', '.join(sorted(valid_targets))}",
                )
            elif arch not in valid_archs:
                raise InvalidArgumentError(
                    "arch",
                    arch,
                    f"Invalid arch for API {api}/{target}. Valid: {', '.join(sorted(valid_archs))}",
                )
            else:
                raise InvalidArgumentError(
                    "combination",
                    f"{api}/{target}/{arch}",
                    "This combination is not available",
                )

    def _need_cmdline_tools(self) -> bool:
        """Check if command-line tools need to be installed."""
        cmdline_tools = self.sdk_root / "cmdline-tools" / "latest"
        sdkmanager = cmdline_tools / "bin" / "sdkmanager"
        return not (cmdline_tools.exists() and sdkmanager.exists())

    def _need_platform_tools(self) -> bool:
        """Check if platform-tools need to be installed."""
        platform_tools = self.sdk_root / "platform-tools"
        adb = platform_tools / "adb"
        return not (platform_tools.exists() and adb.exists())

    def _need_platform(self, api: int) -> bool:
        """Check if platform needs to be installed."""
        platform_dir = self.sdk_root / "platforms" / f"android-{api}"
        return not platform_dir.exists()

    def _need_system_image(self, api: int, target: Target, arch: Arch) -> bool:
        """Check if system image needs to be installed."""
        system_image_dir = (
            self.sdk_root / "system-images" / f"android-{api}" / target / arch
        )
        return not system_image_dir.exists()

    def _need_emulator(self) -> bool:
        """Check if emulator needs to be installed."""
        emulator_dir = self.sdk_root / "emulator"
        emulator_bin = emulator_dir / "emulator"
        return not (emulator_dir.exists() and emulator_bin.exists())

    def _need_ndk(self, ndk: NdkSpec) -> bool:
        """Check if NDK needs to be installed."""
        if ndk.path:
            # If path provided, just check it exists
            return not ndk.path.exists()

        # Try to resolve NDK
        resolver = NdkResolver(self.sdk_root, self.logger)
        try:
            resolver.resolve_path(ndk)
            return False  # Already installed
        except Exception:
            return True  # Needs installation

    def validate_dry_run(self, plan: InstallerPlan) -> None:
        """Validate plan for dry-run mode.

        Args:
            plan: Installation plan

        Raises:
            InvalidArgumentError: If plan has issues
        """
        if not plan.has_work():
            if self.logger:
                self.logger.info("All components already installed")

        # Check for AVD without emulator
        if plan.create_avd_name and not self._has_emulator():
            if not plan.need_emulator:
                raise InvalidArgumentError(
                    "create_avd_name",
                    plan.create_avd_name,
                    "Emulator not installed and not in plan",
                )

    def _has_emulator(self) -> bool:
        """Check if emulator is available."""
        emulator_dir = self.sdk_root / "emulator"
        return emulator_dir.exists()

    def estimate_size(self, plan: InstallerPlan) -> int:
        """Estimate download size in MB.

        Args:
            plan: Installation plan

        Returns:
            Estimated size in MB
        """
        size_mb = 0

        if plan.need_cmdline_tools:
            size_mb += 150  # ~150MB for command-line tools

        if plan.need_platform_tools:
            size_mb += 50  # ~50MB for platform-tools

        if plan.need_platform:
            size_mb += 100  # ~100MB per platform

        if plan.need_system_image:
            size_mb += 800  # ~800MB for system image (varies)

        if plan.need_emulator:
            size_mb += 300  # ~300MB for emulator

        if plan.need_ndk:
            size_mb += 1000  # ~1GB for NDK

        return size_mb