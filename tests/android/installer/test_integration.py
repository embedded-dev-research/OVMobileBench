"""Integration tests for Android installer module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ovmobilebench.android.installer.api import (
    ensure_android_tools,
    export_android_env,
    verify_installation,
)
from ovmobilebench.android.installer.core import AndroidInstaller
from ovmobilebench.android.installer.errors import InstallerError, InvalidArgumentError
from ovmobilebench.android.installer.types import HostInfo, NdkSpec


@pytest.mark.integration
class TestAndroidInstallerIntegration:
    """Integration tests for Android installer."""

    def setup_method(self):
        """Set up test environment."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sdk_root = Path(self.tmpdir.name) / "sdk"
        self.sdk_root.mkdir()

    def teardown_method(self):
        """Clean up test environment."""
        self.tmpdir.cleanup()

    @patch("subprocess.run")
    @patch("ovmobilebench.android.installer.detect.detect_host")
    @patch("ovmobilebench.android.installer.detect.check_disk_space")
    def test_full_installation_flow(self, mock_check_disk, mock_detect_host, mock_subprocess):
        """Test complete installation flow."""
        # Mock host detection
        mock_detect_host.return_value = HostInfo(
            os="linux", arch="x86_64", has_kvm=True, java_version="17"
        )
        mock_check_disk.return_value = True

        # Mock subprocess to avoid actual command execution
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        # Create mock components
        self._create_cmdline_tools()
        self._create_platform_tools()
        self._create_platform(30)
        self._create_system_image(30, "google_atd", "arm64-v8a")
        self._create_emulator()
        self._create_ndk("26.3.11579264")
        self._create_cmake()

        installer = AndroidInstaller(self.sdk_root)

        # Mock license acceptance to avoid actual sdkmanager call
        with patch.object(installer.sdk, "accept_licenses") as mock_accept:
            mock_accept.return_value = None

            # Mock AVD creation
            with patch.object(installer.avd, "create") as mock_avd_create:
                mock_avd_create.return_value = True

                result = installer.ensure(
                    api=30,
                    target="google_atd",
                    arch="arm64-v8a",
                    ndk=NdkSpec(alias="r26d"),
                    create_avd_name="test_avd",
                    dry_run=False,
                )

                assert isinstance(result, dict)
                assert result["sdk_root"] == self.sdk_root
                assert result["avd_created"] is True

    @patch("subprocess.run")
    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_ndk_only_installation(self, mock_detect_host, mock_subprocess):
        """Test NDK-only installation flow."""
        mock_detect_host.return_value = HostInfo(os="linux", arch="x86_64", has_kvm=False)

        # Mock subprocess to avoid actual command execution
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        self._create_cmdline_tools()
        ndk_path = self._create_ndk("26.3.11579264")
        # Also create cmake and platform as they're checked
        self._create_cmake()
        (self.sdk_root / "platforms" / "android-30").mkdir(parents=True)
        (self.sdk_root / "system-images" / "android-30" / "google_atd" / "arm64-v8a").mkdir(
            parents=True
        )

        installer = AndroidInstaller(self.sdk_root)

        result = installer.ensure(
            api=30,
            target="google_atd",
            arch="arm64-v8a",
            ndk=NdkSpec(alias="r26d"),
            install_platform_tools=False,
            install_emulator=False,
            dry_run=False,
        )

        assert result["ndk_path"] == ndk_path
        assert result["avd_created"] is False

    def test_verify_complete_installation(self):
        """Test verification of complete installation."""
        # Create all components
        self._create_cmdline_tools()
        self._create_platform_tools()
        self._create_emulator()
        self._create_ndk("26.3.11579264")

        installer = AndroidInstaller(self.sdk_root)

        # Mock AVD list
        with patch.object(installer.avd, "list_avds") as mock_avd_list:
            with patch.object(installer.sdk, "list_installed") as mock_sdk_list:
                mock_avd_list.return_value = ["test_avd"]
                mock_sdk_list.return_value = []

                results = installer.verify()

                assert results["sdk_root_exists"] is True
                assert results["cmdline_tools"] is True
                assert results["platform_tools"] is True
                assert results["emulator"] is True
                assert results["ndk"] is True
                assert "26.3.11579264" in results["ndk_versions"]
                assert "test_avd" in results["avds"]

    def test_cleanup_operations(self):
        """Test cleanup of temporary files."""
        # Create temporary files
        zip_file = self.sdk_root / "tools.zip"
        zip_file.touch()
        tar_file = self.sdk_root / "ndk.tar.gz"
        tar_file.touch()
        temp_dir = self.sdk_root / "temp"
        temp_dir.mkdir()
        (temp_dir / "file.tmp").touch()

        installer = AndroidInstaller(self.sdk_root)
        installer.cleanup(remove_downloads=True, remove_temp=True)

        assert not zip_file.exists()
        assert not tar_file.exists()
        assert not temp_dir.exists()

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_environment_export(self, mock_detect_host):
        """Test environment variable export."""
        mock_detect_host.return_value = HostInfo(os="linux", arch="x86_64", has_kvm=True)

        self._create_cmdline_tools()
        self._create_platform_tools()
        ndk_path = self._create_ndk("26.3.11579264")

        installer = AndroidInstaller(self.sdk_root)

        # Export to dict
        env_dict = installer.env.export(sdk_root=self.sdk_root, ndk_path=ndk_path)

        assert env_dict["ANDROID_HOME"] == str(self.sdk_root)
        assert env_dict["ANDROID_SDK_ROOT"] == str(self.sdk_root)
        assert env_dict["ANDROID_NDK_HOME"] == str(ndk_path)
        # PATH is not returned by export method, only set in environment

    @patch("ovmobilebench.android.installer.detect.detect_host")
    @patch("ovmobilebench.android.installer.detect.check_disk_space")
    def test_dry_run_mode(self, mock_check_disk, mock_detect_host):
        """Test dry-run mode doesn't make changes."""
        mock_detect_host.return_value = HostInfo(os="linux", arch="x86_64", has_kvm=True)
        mock_check_disk.return_value = True

        installer = AndroidInstaller(self.sdk_root)

        with patch.object(installer.sdk, "ensure_cmdline_tools") as mock_ensure:
            result = installer.ensure(
                api=30,
                target="google_atd",
                arch="arm64-v8a",
                ndk=NdkSpec(alias="r26d"),
                dry_run=True,
            )

            # Should not call any installation methods
            mock_ensure.assert_not_called()
            assert result["performed"]["dry_run"] is True

    def test_invalid_configuration_detection(self):
        """Test detection of invalid configurations."""
        installer = AndroidInstaller(self.sdk_root)

        with pytest.raises(InvalidArgumentError):
            installer.ensure(
                api=99,  # Invalid API level
                target="invalid_target",
                arch="invalid_arch",
                ndk=NdkSpec(alias="r26d"),
                dry_run=False,
            )

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_api_function_ensure(self, mock_detect_host):
        """Test the public API ensure function."""
        mock_detect_host.return_value = HostInfo(os="linux", arch="x86_64", has_kvm=True)

        self._create_cmdline_tools()

        with patch("ovmobilebench.android.installer.api.AndroidInstaller") as MockInstaller:
            mock_instance = Mock()
            MockInstaller.return_value = mock_instance
            mock_instance.ensure.return_value = {
                "sdk_root": self.sdk_root,
                "ndk_path": None,
                "avd_created": False,
                "performed": {},
            }

            result = ensure_android_tools(
                sdk_root=self.sdk_root,
                api=30,
                target="google_atd",
                arch="arm64-v8a",
                ndk="r26d",
                dry_run=True,
            )

            assert isinstance(result, dict)
            MockInstaller.assert_called_once()
            mock_instance.ensure.assert_called_once()

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_api_function_export(self, mock_detect_host):
        """Test the public API export function."""
        mock_detect_host.return_value = HostInfo(os="linux", arch="x86_64", has_kvm=True)

        ndk_path = self._create_ndk("26.3.11579264")

        env_vars = export_android_env(
            sdk_root=self.sdk_root,
            ndk_path=ndk_path,
        )

        assert isinstance(env_vars, dict)
        assert "ANDROID_HOME" in env_vars
        assert "ANDROID_SDK_ROOT" in env_vars
        assert "ANDROID_NDK" in env_vars

    def test_api_function_verify(self):
        """Test the public API verify function."""
        self._create_cmdline_tools()

        with patch("ovmobilebench.android.installer.api.AndroidInstaller") as MockInstaller:
            mock_instance = Mock()
            MockInstaller.return_value = mock_instance
            mock_instance.verify.return_value = {
                "sdk_root_exists": True,
                "cmdline_tools": True,
                "platform_tools": False,
                "emulator": False,
                "ndk": False,
                "avds": [],
            }

            results = verify_installation(sdk_root=self.sdk_root)

            assert isinstance(results, dict)
            assert results["cmdline_tools"] is True
            assert results["platform_tools"] is False

    @patch("subprocess.run")
    @patch("ovmobilebench.android.installer.detect.detect_host")
    @patch("ovmobilebench.android.installer.detect.check_disk_space")
    def test_concurrent_component_installation(
        self, mock_check_disk, mock_detect_host, mock_subprocess
    ):
        """Test that components can be installed concurrently."""
        mock_detect_host.return_value = HostInfo(os="linux", arch="x86_64", has_kvm=True)
        mock_check_disk.return_value = True

        # Mock subprocess to avoid actual command execution
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        installer = AndroidInstaller(self.sdk_root)

        # Mock license acceptance to avoid actual sdkmanager call
        with patch.object(installer.sdk, "accept_licenses") as mock_accept:
            mock_accept.return_value = None

            # Mock multiple components needing installation
            with patch.object(installer.sdk, "ensure_platform_tools") as mock_platform:
                with patch.object(installer.sdk, "ensure_emulator") as mock_emulator:
                    with patch.object(installer.sdk, "ensure_build_tools") as mock_build:
                        with patch.object(installer.ndk, "ensure") as mock_ndk:
                            # Create cmdline tools and mock components first
                            self._create_cmdline_tools()

                            # Create the directories that would be created
                            (self.sdk_root / "platforms" / "android-30").mkdir(parents=True)
                            (
                                self.sdk_root
                                / "system-images"
                                / "android-30"
                                / "google_atd"
                                / "arm64-v8a"
                            ).mkdir(parents=True)
                            (self.sdk_root / "cmake" / "3.22.1").mkdir(parents=True)

                            # Set up return values
                            mock_platform.return_value = self.sdk_root / "platform-tools"
                            mock_emulator.return_value = self.sdk_root / "emulator"
                            mock_build.return_value = self.sdk_root / "build-tools" / "34.0.0"
                            mock_ndk.return_value = self.sdk_root / "ndk" / "26.3.11579264"

                            installer.ensure(
                                api=30,
                                target="google_atd",
                                arch="arm64-v8a",
                                ndk=NdkSpec(alias="r26d"),
                                install_build_tools="34.0.0",
                                dry_run=False,
                            )

                            # All should be called
                            mock_platform.assert_called_once()
                            mock_emulator.assert_called_once()
                            mock_build.assert_called_once_with("34.0.0")

    # Helper methods to create mock components

    def _create_cmdline_tools(self):
        """Create mock cmdline-tools."""
        cmdline_dir = self.sdk_root / "cmdline-tools" / "latest" / "bin"
        cmdline_dir.mkdir(parents=True)
        (cmdline_dir / "sdkmanager").touch()
        (cmdline_dir / "avdmanager").touch()
        return cmdline_dir.parent

    def _create_platform_tools(self):
        """Create mock platform-tools."""
        platform_dir = self.sdk_root / "platform-tools"
        platform_dir.mkdir()
        (platform_dir / "adb").touch()
        return platform_dir

    def _create_platform(self, api):
        """Create mock platform."""
        platform_dir = self.sdk_root / "platforms" / f"android-{api}"
        platform_dir.mkdir(parents=True)
        return platform_dir

    def _create_system_image(self, api, target, arch):
        """Create mock system image."""
        image_dir = self.sdk_root / "system-images" / f"android-{api}" / target / arch
        image_dir.mkdir(parents=True)
        return image_dir

    def _create_emulator(self):
        """Create mock emulator."""
        emulator_dir = self.sdk_root / "emulator"
        emulator_dir.mkdir()
        (emulator_dir / "emulator").touch()
        return emulator_dir

    def _create_ndk(self, version):
        """Create mock NDK."""
        ndk_dir = self.sdk_root / "ndk" / version
        ndk_dir.mkdir(parents=True)
        (ndk_dir / "ndk-build").touch()
        (ndk_dir / "toolchains").mkdir()
        return ndk_dir

    def _create_cmake(self):
        """Create mock cmake."""
        cmake_dir = self.sdk_root / "cmake" / "3.22.1"
        cmake_dir.mkdir(parents=True)
        (cmake_dir / "bin" / "cmake").parent.mkdir(parents=True, exist_ok=True)
        (cmake_dir / "bin" / "cmake").touch()
        return cmake_dir


@pytest.mark.integration
class TestEndToEndScenarios:
    """Test end-to-end scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sdk_root = Path(self.tmpdir.name) / "sdk"

    def teardown_method(self):
        """Clean up test environment."""
        self.tmpdir.cleanup()

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_ci_environment_setup(self, mock_detect_host):
        """Test setup in CI environment."""
        mock_detect_host.return_value = HostInfo(os="linux", arch="x86_64", has_kvm=False)

        # Set CI environment variables
        with patch.dict(os.environ, {"CI": "true", "GITHUB_ACTIONS": "true"}):
            result = ensure_android_tools(
                sdk_root=self.sdk_root,
                api=30,
                target="google_atd",
                arch="arm64-v8a",
                ndk=NdkSpec(alias="r26d"),
                create_avd_name=None,  # No AVD in CI without KVM
                dry_run=True,
            )

            assert result is not None

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_development_environment_setup(self, mock_detect_host):
        """Test setup in development environment."""
        mock_detect_host.return_value = HostInfo(os="darwin", arch="arm64", has_kvm=False)

        result = ensure_android_tools(
            sdk_root=self.sdk_root,
            api=33,
            target="google_apis",
            arch="arm64-v8a",
            ndk=NdkSpec(alias="r26d"),
            create_avd_name="dev_avd",
            install_build_tools="34.0.0",
            dry_run=True,
        )

        assert result is not None

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_windows_environment_setup(self, mock_detect_host):
        """Test setup on Windows."""
        mock_detect_host.return_value = HostInfo(os="windows", arch="x86_64", has_kvm=True)

        result = ensure_android_tools(
            sdk_root=self.sdk_root,
            api=30,
            target="google_atd",
            arch="x86_64",  # x86_64 for Windows with HAXM
            ndk=NdkSpec(alias="r26d"),
            create_avd_name="win_avd",
            dry_run=True,
        )

        assert result is not None

    def test_incremental_updates(self):
        """Test incremental updates to existing installation."""
        # First installation
        self.sdk_root.mkdir()
        installer = AndroidInstaller(self.sdk_root)

        # Create some existing components
        cmdline_dir = self.sdk_root / "cmdline-tools" / "latest" / "bin"
        cmdline_dir.mkdir(parents=True)
        (cmdline_dir / "sdkmanager").touch()

        platform_dir = self.sdk_root / "platform-tools"
        platform_dir.mkdir()
        (platform_dir / "adb").touch()

        # Verify shows partial installation
        results = installer.verify()
        assert results["cmdline_tools"] is True
        assert results["platform_tools"] is True
        assert results["emulator"] is False

        # Now "install" emulator
        emulator_dir = self.sdk_root / "emulator"
        emulator_dir.mkdir()
        (emulator_dir / "emulator").touch()

        # Verify shows updated installation
        results = installer.verify()
        assert results["emulator"] is True

    @patch("ovmobilebench.android.installer.detect.detect_host")
    @patch("ovmobilebench.android.installer.detect.check_disk_space")
    def test_error_recovery(self, mock_check_disk, mock_detect_host):
        """Test error recovery during installation."""
        mock_detect_host.return_value = HostInfo(os="linux", arch="x86_64", has_kvm=True)
        mock_check_disk.return_value = True

        installer = AndroidInstaller(self.sdk_root)

        # Simulate error during platform installation
        with patch.object(installer.sdk, "ensure_platform") as mock_platform:
            mock_platform.side_effect = InstallerError("Failed to install platform")

            with pytest.raises(InstallerError):
                installer.ensure(
                    api=30,
                    target="google_atd",
                    arch="arm64-v8a",
                    ndk=NdkSpec(alias="r26d"),
                    dry_run=False,
                )

            # Cleanup should still work
            installer.cleanup(remove_downloads=True)

    def test_multiple_ndk_versions(self):
        """Test managing multiple NDK versions."""
        self.sdk_root.mkdir()
        installer = AndroidInstaller(self.sdk_root)

        # Create multiple NDK versions
        ndk1 = self.sdk_root / "ndk" / "26.3.11579264"
        ndk1.mkdir(parents=True)
        (ndk1 / "ndk-build").touch()
        (ndk1 / "toolchains").mkdir()

        ndk2 = self.sdk_root / "ndk" / "25.2.9519653"
        ndk2.mkdir(parents=True)
        (ndk2 / "ndk-build").touch()
        (ndk2 / "toolchains").mkdir()

        # List should show both
        ndk_versions = installer.ndk.list_installed()
        assert len(ndk_versions) == 2
        versions = [v for v, _ in ndk_versions]
        assert "26.3.11579264" in versions
        assert "25.2.9519653" in versions
