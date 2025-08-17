"""Tests for host detection utilities."""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch


from ovmobilebench.android.installer.detect import (
    detect_host,
    detect_java_version,
    get_platform_suffix,
    get_sdk_tools_filename,
    get_ndk_filename,
    get_best_emulator_arch,
    check_disk_space,
    is_ci_environment,
    get_recommended_settings,
)


class TestDetectHost:
    """Test host detection."""

    @patch("platform.system")
    @patch("platform.machine")
    @patch("pathlib.Path.exists")
    def test_detect_linux_x86_64_with_kvm(self, mock_exists, mock_machine, mock_system):
        """Test detecting Linux x86_64 with KVM."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        mock_exists.return_value = True  # /dev/kvm exists

        host = detect_host()
        assert host.os == "linux"
        assert host.arch == "x86_64"
        assert host.has_kvm is True

    @patch("platform.system")
    @patch("platform.machine")
    @patch("pathlib.Path.exists")
    def test_detect_linux_arm64_without_kvm(self, mock_exists, mock_machine, mock_system):
        """Test detecting Linux ARM64 without KVM."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "aarch64"
        mock_exists.return_value = False  # /dev/kvm doesn't exist

        host = detect_host()
        assert host.os == "linux"
        assert host.arch == "arm64"
        assert host.has_kvm is False

    @patch("platform.system")
    @patch("platform.machine")
    def test_detect_macos_arm64(self, mock_machine, mock_system):
        """Test detecting macOS ARM64."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"

        host = detect_host()
        assert host.os == "darwin"
        assert host.arch == "arm64"
        assert host.has_kvm is False  # KVM is Linux-only

    @patch("platform.system")
    @patch("platform.machine")
    def test_detect_windows_x86_64(self, mock_machine, mock_system):
        """Test detecting Windows x86_64."""
        mock_system.return_value = "Windows"
        mock_machine.return_value = "AMD64"

        host = detect_host()
        assert host.os == "windows"
        assert host.arch == "x86_64"
        assert host.has_kvm is False


class TestDetectJavaVersion:
    """Test Java version detection."""

    @patch("subprocess.run")
    def test_detect_java_17(self, mock_run):
        """Test detecting Java 17."""
        mock_run.return_value = Mock(
            stderr='openjdk version "17.0.8" 2023-07-18\nOpenJDK Runtime Environment'
        )

        version = detect_java_version()
        assert version == "17.0.8"

    @patch("subprocess.run")
    def test_detect_java_8(self, mock_run):
        """Test detecting Java 8."""
        mock_run.return_value = Mock(
            stderr='java version "1.8.0_381"\nJava(TM) SE Runtime Environment'
        )

        version = detect_java_version()
        assert version == "1.8.0_381"

    @patch("subprocess.run")
    def test_detect_java_not_found(self, mock_run):
        """Test when Java is not found."""
        mock_run.side_effect = FileNotFoundError()

        version = detect_java_version()
        assert version is None

    @patch("subprocess.run")
    def test_detect_java_timeout(self, mock_run):
        """Test when Java detection times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("java", 5)

        version = detect_java_version()
        assert version is None


class TestPlatformFunctions:
    """Test platform-specific functions."""

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_platform_suffix_linux(self, mock_detect):
        """Test getting platform suffix for Linux."""
        mock_detect.return_value = Mock(os="linux")
        assert get_platform_suffix() == "linux"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_platform_suffix_macos(self, mock_detect):
        """Test getting platform suffix for macOS."""
        mock_detect.return_value = Mock(os="darwin")
        assert get_platform_suffix() == "darwin"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_sdk_tools_filename_linux(self, mock_detect):
        """Test getting SDK tools filename for Linux."""
        mock_detect.return_value = Mock(os="linux")
        filename = get_sdk_tools_filename("11076708")
        assert filename == "commandlinetools-linux-11076708_latest.zip"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_sdk_tools_filename_macos(self, mock_detect):
        """Test getting SDK tools filename for macOS."""
        mock_detect.return_value = Mock(os="darwin")
        filename = get_sdk_tools_filename("11076708")
        assert filename == "commandlinetools-mac-11076708_latest.zip"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_sdk_tools_filename_windows(self, mock_detect):
        """Test getting SDK tools filename for Windows."""
        mock_detect.return_value = Mock(os="windows")
        filename = get_sdk_tools_filename("11076708")
        assert filename == "commandlinetools-win-11076708_latest.zip"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_ndk_filename_linux(self, mock_detect):
        """Test getting NDK filename for Linux."""
        mock_detect.return_value = Mock(os="linux")
        filename = get_ndk_filename("r26d")
        assert filename == "android-ndk-r26d-linux.zip"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_ndk_filename_macos(self, mock_detect):
        """Test getting NDK filename for macOS."""
        mock_detect.return_value = Mock(os="darwin")
        filename = get_ndk_filename("r26d")
        assert filename == "android-ndk-r26d-darwin.dmg"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_ndk_filename_windows(self, mock_detect):
        """Test getting NDK filename for Windows."""
        mock_detect.return_value = Mock(os="windows")
        filename = get_ndk_filename("r26d")
        assert filename == "android-ndk-r26d-windows.zip"


class TestGetBestEmulatorArch:
    """Test emulator architecture selection."""

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_arm64_host(self, mock_detect):
        """Test ARM64 host prefers ARM64 emulator."""
        mock_detect.return_value = Mock(os="linux", arch="arm64", has_kvm=False)
        assert get_best_emulator_arch() == "arm64-v8a"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_x86_64_host_without_kvm(self, mock_detect):
        """Test x86_64 host without KVM prefers x86_64."""
        mock_detect.return_value = Mock(os="darwin", arch="x86_64", has_kvm=False)
        assert get_best_emulator_arch() == "x86_64"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_x86_64_linux_with_kvm(self, mock_detect):
        """Test x86_64 Linux with KVM can use ARM64."""
        mock_detect.return_value = Mock(os="linux", arch="x86_64", has_kvm=True)
        assert get_best_emulator_arch() == "arm64-v8a"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_arm_32bit_host(self, mock_detect):
        """Test ARM 32-bit host prefers armeabi-v7a."""
        mock_detect.return_value = Mock(os="linux", arch="armv7l", has_kvm=False)
        assert get_best_emulator_arch() == "armeabi-v7a"

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_x86_32bit_host(self, mock_detect):
        """Test x86 32-bit host."""
        mock_detect.return_value = Mock(os="windows", arch="i686", has_kvm=False)
        assert get_best_emulator_arch() == "x86"


class TestCheckDiskSpace:
    """Test disk space checking."""

    @patch("shutil.disk_usage")
    def test_enough_space(self, mock_disk_usage):
        """Test when there's enough disk space."""
        mock_disk_usage.return_value = Mock(free=20 * 1024**3)  # 20 GB free
        assert check_disk_space(Path("/tmp"), required_gb=10.0) is True

    @patch("shutil.disk_usage")
    def test_not_enough_space(self, mock_disk_usage):
        """Test when there's not enough disk space."""
        mock_disk_usage.return_value = Mock(free=5 * 1024**3)  # 5 GB free
        assert check_disk_space(Path("/tmp"), required_gb=10.0) is False

    @patch("shutil.disk_usage")
    def test_disk_check_error(self, mock_disk_usage):
        """Test when disk check fails."""
        mock_disk_usage.side_effect = OSError("Permission denied")
        # Should return True (assume OK) when check fails
        assert check_disk_space(Path("/tmp"), required_gb=10.0) is True


class TestIsCiEnvironment:
    """Test CI environment detection."""

    def test_github_actions(self):
        """Test detecting GitHub Actions."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            assert is_ci_environment() is True

    def test_gitlab_ci(self):
        """Test detecting GitLab CI."""
        with patch.dict(os.environ, {"GITLAB_CI": "true"}):
            assert is_ci_environment() is True

    def test_jenkins(self):
        """Test detecting Jenkins."""
        with patch.dict(os.environ, {"JENKINS_URL": "http://jenkins.example.com"}):
            assert is_ci_environment() is True

    def test_generic_ci(self):
        """Test detecting generic CI."""
        with patch.dict(os.environ, {"CI": "true"}):
            assert is_ci_environment() is True

    def test_not_ci(self):
        """Test when not in CI environment."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_ci_environment() is False


class TestGetRecommendedSettings:
    """Test recommended settings generation."""

    @patch("ovmobilebench.android.installer.detect.is_ci_environment")
    @patch("ovmobilebench.android.installer.detect.get_best_emulator_arch")
    def test_local_linux_settings(self, mock_arch, mock_is_ci):
        """Test recommended settings for local Linux."""
        mock_is_ci.return_value = False
        mock_arch.return_value = "x86_64"

        host = Mock(os="linux", arch="x86_64", has_kvm=True)
        settings = get_recommended_settings(host)

        assert settings["api"] == 30
        assert settings["target"] == "google_atd"
        assert settings["arch"] == "x86_64"
        assert settings["ndk"] == "r26d"
        assert settings["install_emulator"] is True
        assert settings["create_avd"] is False  # Not in CI

    @patch("ovmobilebench.android.installer.detect.is_ci_environment")
    @patch("ovmobilebench.android.installer.detect.get_best_emulator_arch")
    def test_ci_settings(self, mock_arch, mock_is_ci):
        """Test recommended settings for CI environment."""
        mock_is_ci.return_value = True
        mock_arch.return_value = "arm64-v8a"

        settings = get_recommended_settings()

        assert settings["target"] == "google_atd"  # Optimized for testing
        assert settings["install_emulator"] is True
        assert settings["create_avd"] is True  # Auto-create in CI

    @patch("ovmobilebench.android.installer.detect.get_best_emulator_arch")
    def test_windows_settings(self, mock_arch):
        """Test recommended settings for Windows."""
        mock_arch.return_value = "x86_64"

        host = Mock(os="windows", arch="x86_64", has_kvm=False)
        settings = get_recommended_settings(host)

        assert settings["install_emulator"] is False  # Skip on Windows by default
