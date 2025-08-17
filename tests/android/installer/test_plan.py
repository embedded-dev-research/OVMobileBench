"""Tests for installation planning and validation."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ovmobilebench.android.installer.errors import InvalidArgumentError
from ovmobilebench.android.installer.plan import Planner
from ovmobilebench.android.installer.types import InstallerPlan, NdkSpec


class TestPlanner:
    """Test Planner class."""

    def setup_method(self):
        """Set up test environment."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sdk_root = Path(self.tmpdir.name) / "sdk"
        self.sdk_root.mkdir()
        self.planner = Planner(self.sdk_root)

    def teardown_method(self):
        """Clean up test environment."""
        self.tmpdir.cleanup()

    def test_init(self):
        """Test Planner initialization."""
        logger = Mock()
        planner = Planner(self.sdk_root, logger=logger)
        assert planner.sdk_root == self.sdk_root.absolute()
        assert planner.logger == logger

    def test_validate_combination_valid(self):
        """Test validating valid API/target/arch combination."""
        # Should not raise exception
        self.planner._validate_combination(30, "google_atd", "arm64-v8a")
        self.planner._validate_combination(34, "google_apis", "x86_64")
        self.planner._validate_combination(28, "default", "x86")

    def test_validate_combination_invalid_api(self):
        """Test validating invalid API level."""
        with pytest.raises(InvalidArgumentError, match="API level must be between"):
            self.planner._validate_combination(20, "google_atd", "arm64-v8a")
        
        with pytest.raises(InvalidArgumentError, match="API level must be between"):
            self.planner._validate_combination(99, "google_atd", "arm64-v8a")

    def test_validate_combination_invalid_target(self):
        """Test validating invalid target for API."""
        with pytest.raises(InvalidArgumentError, match="Invalid target"):
            self.planner._validate_combination(30, "invalid_target", "arm64-v8a")

    def test_validate_combination_invalid_arch(self):
        """Test validating invalid architecture for API/target."""
        # google_atd doesn't support armeabi-v7a
        with pytest.raises(InvalidArgumentError, match="Invalid arch"):
            self.planner._validate_combination(30, "google_atd", "armeabi-v7a")

    def test_validate_combination_unavailable(self):
        """Test validating unavailable combination."""
        # API 35 with default target is not in VALID_COMBINATIONS
        with pytest.raises(InvalidArgumentError):
            self.planner._validate_combination(35, "default", "arm64-v8a")

    def test_build_plan_all_needed(self):
        """Test building plan when all components needed."""
        plan = self.planner.build_plan(
            api=30,
            target="google_atd",
            arch="arm64-v8a",
            install_platform_tools=True,
            install_emulator=True,
            ndk=NdkSpec(alias="r26d"),
            create_avd_name="test_avd",
        )

        assert plan.need_cmdline_tools is True
        assert plan.need_platform_tools is True
        assert plan.need_platform is True
        assert plan.need_system_image is True
        assert plan.need_emulator is True
        assert plan.need_ndk is True
        assert plan.create_avd_name == "test_avd"

    def test_build_plan_some_installed(self):
        """Test building plan when some components are installed."""
        # Create some directories to simulate installed components
        (self.sdk_root / "cmdline-tools" / "latest" / "bin").mkdir(parents=True)
        (self.sdk_root / "cmdline-tools" / "latest" / "bin" / "sdkmanager").touch()
        (self.sdk_root / "platform-tools").mkdir()
        (self.sdk_root / "platform-tools" / "adb").touch()

        plan = self.planner.build_plan(
            api=30,
            target="google_atd",
            arch="arm64-v8a",
            install_platform_tools=True,
            install_emulator=True,
            ndk=NdkSpec(alias="r26d"),
        )

        assert plan.need_cmdline_tools is False  # Already installed
        assert plan.need_platform_tools is False  # Already installed
        assert plan.need_platform is True
        assert plan.need_system_image is True
        assert plan.need_emulator is True
        assert plan.need_ndk is True

    def test_build_plan_ndk_only(self):
        """Test building plan for NDK only."""
        plan = self.planner.build_plan(
            api=30,
            target="google_atd",
            arch="arm64-v8a",
            install_platform_tools=False,
            install_emulator=False,
            ndk=NdkSpec(alias="r26d"),
        )

        assert plan.need_platform_tools is False
        assert plan.need_system_image is False
        assert plan.need_emulator is False
        assert plan.need_ndk is True

    def test_build_plan_avd_without_emulator_fails(self):
        """Test that creating AVD without emulator fails."""
        with pytest.raises(InvalidArgumentError, match="Cannot create AVD without installing emulator"):
            self.planner.build_plan(
                api=30,
                target="google_atd",
                arch="arm64-v8a",
                install_platform_tools=False,
                install_emulator=False,  # No emulator
                ndk=NdkSpec(alias="r26d"),
                create_avd_name="test_avd",  # But want AVD
            )

    def test_need_cmdline_tools(self):
        """Test checking if command-line tools needed."""
        assert self.planner._need_cmdline_tools() is True

        # Create cmdline-tools
        (self.sdk_root / "cmdline-tools" / "latest" / "bin").mkdir(parents=True)
        (self.sdk_root / "cmdline-tools" / "latest" / "bin" / "sdkmanager").touch()

        assert self.planner._need_cmdline_tools() is False

    def test_need_platform_tools(self):
        """Test checking if platform-tools needed."""
        assert self.planner._need_platform_tools() is True

        # Create platform-tools
        (self.sdk_root / "platform-tools").mkdir()
        (self.sdk_root / "platform-tools" / "adb").touch()

        assert self.planner._need_platform_tools() is False

    def test_need_platform(self):
        """Test checking if platform needed."""
        assert self.planner._need_platform(30) is True

        # Create platform
        (self.sdk_root / "platforms" / "android-30").mkdir(parents=True)

        assert self.planner._need_platform(30) is False

    def test_need_system_image(self):
        """Test checking if system image needed."""
        assert self.planner._need_system_image(30, "google_atd", "arm64-v8a") is True

        # Create system image
        (self.sdk_root / "system-images" / "android-30" / "google_atd" / "arm64-v8a").mkdir(parents=True)

        assert self.planner._need_system_image(30, "google_atd", "arm64-v8a") is False

    def test_need_emulator(self):
        """Test checking if emulator needed."""
        assert self.planner._need_emulator() is True

        # Create emulator
        (self.sdk_root / "emulator").mkdir()
        (self.sdk_root / "emulator" / "emulator").touch()

        assert self.planner._need_emulator() is False

    @patch("ovmobilebench.android.installer.plan.NdkResolver")
    def test_need_ndk_with_path(self, mock_resolver_class):
        """Test checking if NDK needed when path provided."""
        ndk_path = Path("/opt/android-ndk")
        ndk_spec = NdkSpec(path=ndk_path)

        # Path doesn't exist
        with patch.object(Path, "exists", return_value=False):
            assert self.planner._need_ndk(ndk_spec) is True

        # Path exists
        with patch.object(Path, "exists", return_value=True):
            assert self.planner._need_ndk(ndk_spec) is False

    @patch("ovmobilebench.android.installer.plan.NdkResolver")
    def test_need_ndk_with_alias(self, mock_resolver_class):
        """Test checking if NDK needed when alias provided."""
        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver

        ndk_spec = NdkSpec(alias="r26d")

        # NDK not installed
        mock_resolver.resolve_path.side_effect = Exception("Not found")
        assert self.planner._need_ndk(ndk_spec) is True

        # NDK installed
        mock_resolver.resolve_path.side_effect = None
        mock_resolver.resolve_path.return_value = Path("/opt/ndk")
        assert self.planner._need_ndk(ndk_spec) is False

    def test_validate_dry_run_no_work(self):
        """Test validating dry-run with no work."""
        plan = InstallerPlan(
            need_cmdline_tools=False,
            need_platform_tools=False,
            need_platform=False,
            need_system_image=False,
            need_emulator=False,
            need_ndk=False,
        )

        # Should not raise
        self.planner.validate_dry_run(plan)

    def test_validate_dry_run_avd_without_emulator(self):
        """Test validating dry-run with AVD but no emulator."""
        plan = InstallerPlan(
            need_cmdline_tools=False,
            need_platform_tools=False,
            need_platform=False,
            need_system_image=False,
            need_emulator=False,  # Not installing emulator
            need_ndk=False,
            create_avd_name="test_avd",  # But want to create AVD
        )

        # Emulator not available
        with pytest.raises(InvalidArgumentError, match="Emulator not installed"):
            self.planner.validate_dry_run(plan)

        # Emulator available but not in plan - OK
        (self.sdk_root / "emulator").mkdir()
        plan_with_emulator = InstallerPlan(
            need_cmdline_tools=False,
            need_platform_tools=False,
            need_platform=False,
            need_system_image=False,
            need_emulator=False,
            need_ndk=False,
            create_avd_name="test_avd",
        )
        # Should not raise
        self.planner.validate_dry_run(plan_with_emulator)

    def test_estimate_size(self):
        """Test estimating download size."""
        plan = InstallerPlan(
            need_cmdline_tools=True,  # ~150MB
            need_platform_tools=True,  # ~50MB
            need_platform=True,  # ~100MB
            need_system_image=True,  # ~800MB
            need_emulator=True,  # ~300MB
            need_ndk=True,  # ~1000MB
        )

        size_mb = self.planner.estimate_size(plan)
        assert size_mb == 150 + 50 + 100 + 800 + 300 + 1000  # 2400MB

    def test_estimate_size_partial(self):
        """Test estimating download size for partial installation."""
        plan = InstallerPlan(
            need_cmdline_tools=True,  # ~150MB
            need_platform_tools=False,
            need_platform=False,
            need_system_image=False,
            need_emulator=False,
            need_ndk=True,  # ~1000MB
        )

        size_mb = self.planner.estimate_size(plan)
        assert size_mb == 150 + 1000  # 1150MB

    def test_known_combinations(self):
        """Test some known valid combinations."""
        valid_combinations = [
            (30, "google_atd", "arm64-v8a"),
            (30, "google_atd", "x86_64"),
            (33, "google_apis", "arm64-v8a"),
            (28, "default", "x86"),
            (24, "default", "arm64-v8a"),
        ]

        for api, target, arch in valid_combinations:
            # Should not raise
            self.planner._validate_combination(api, target, arch)