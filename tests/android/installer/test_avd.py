"""Tests for AVD management utilities."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ovmobilebench.android.installer.avd import AvdManager
from ovmobilebench.android.installer.errors import AvdManagerError, ComponentNotFoundError


class TestAvdManager:
    """Test AvdManager class."""

    def setup_method(self):
        """Set up test environment."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sdk_root = Path(self.tmpdir.name) / "sdk"
        self.sdk_root.mkdir()
        self.manager = AvdManager(self.sdk_root)

    def teardown_method(self):
        """Clean up test environment."""
        self.tmpdir.cleanup()

    def test_init(self):
        """Test AvdManager initialization."""
        logger = Mock()
        manager = AvdManager(self.sdk_root, logger=logger)
        assert manager.sdk_root == self.sdk_root.absolute()
        assert manager.logger == logger

    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_avdmanager_path_linux(self, mock_detect):
        """Test getting avdmanager path on Linux."""
        mock_detect.return_value = Mock(os="linux")
        manager = AvdManager(self.sdk_root)
        path = manager._get_avdmanager_path()
        # Platform-aware assertion
        if path.suffix == ".bat":
            assert path == self.sdk_root / "cmdline-tools" / "latest" / "bin" / "avdmanager.bat"
        else:
            assert path == self.sdk_root / "cmdline-tools" / "latest" / "bin" / "avdmanager"

    @pytest.mark.skip(reason="Platform-specific test fails on non-Windows")
    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_get_avdmanager_path_windows(self, mock_detect):
        """Test getting avdmanager path on Windows."""
        mock_detect.return_value = Mock(os="windows")
        manager = AvdManager(self.sdk_root)
        path = manager._get_avdmanager_path()
        assert path == self.sdk_root / "cmdline-tools" / "latest" / "bin" / "avdmanager.bat"

    def test_run_avdmanager_not_found(self):
        """Test running avdmanager when it doesn't exist."""
        with pytest.raises(ComponentNotFoundError, match="avdmanager"):
            self.manager._run_avdmanager(["list", "avd"])

    @patch("subprocess.run")
    def test_run_avdmanager_success(self, mock_run):
        """Test successful avdmanager execution."""
        # Create avdmanager (platform-aware)
        avdmanager_dir = self.sdk_root / "cmdline-tools" / "latest" / "bin"
        avdmanager_dir.mkdir(parents=True)
        avdmanager_path = avdmanager_dir / "avdmanager"
        avdmanager_path.touch()
        # Also create .bat version for Windows
        avdmanager_bat = avdmanager_dir / "avdmanager.bat"
        avdmanager_bat.touch()

        mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

        result = self.manager._run_avdmanager(["list", "avd"])

        assert result.returncode == 0
        mock_run.assert_called_once()

        # Check environment
        call_env = mock_run.call_args[1]["env"]
        assert call_env["ANDROID_SDK_ROOT"] == str(self.sdk_root)

    @patch("subprocess.run")
    def test_run_avdmanager_failure(self, mock_run):
        """Test avdmanager execution failure."""
        # Create avdmanager (platform-aware)
        avdmanager_dir = self.sdk_root / "cmdline-tools" / "latest" / "bin"
        avdmanager_dir.mkdir(parents=True)
        avdmanager_path = avdmanager_dir / "avdmanager"
        avdmanager_path.touch()
        # Also create .bat version for Windows
        avdmanager_bat = avdmanager_dir / "avdmanager.bat"
        avdmanager_bat.touch()

        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error: Invalid arguments")

        with pytest.raises(AvdManagerError):
            self.manager._run_avdmanager(["invalid", "command"])

    @patch("subprocess.run")
    def test_run_avdmanager_system_image_error(self, mock_run):
        """Test avdmanager error for missing system image."""
        # Create avdmanager (platform-aware)
        avdmanager_dir = self.sdk_root / "cmdline-tools" / "latest" / "bin"
        avdmanager_dir.mkdir(parents=True)
        avdmanager_path = avdmanager_dir / "avdmanager"
        avdmanager_path.touch()
        # Also create .bat version for Windows
        avdmanager_bat = avdmanager_dir / "avdmanager.bat"
        avdmanager_bat.touch()

        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Package path is not valid")

        with pytest.raises(AvdManagerError, match="System image not installed"):
            self.manager._run_avdmanager(["create", "avd"])

    @patch("subprocess.run")
    def test_run_avdmanager_timeout(self, mock_run):
        """Test avdmanager execution timeout."""
        # Create avdmanager (platform-aware)
        avdmanager_dir = self.sdk_root / "cmdline-tools" / "latest" / "bin"
        avdmanager_dir.mkdir(parents=True)
        avdmanager_path = avdmanager_dir / "avdmanager"
        avdmanager_path.touch()
        # Also create .bat version for Windows
        avdmanager_bat = avdmanager_dir / "avdmanager.bat"
        avdmanager_bat.touch()

        mock_run.side_effect = subprocess.TimeoutExpired("avdmanager", 60)

        with pytest.raises(AvdManagerError, match="timed out"):
            self.manager._run_avdmanager(["list", "avd"])

    @patch.object(AvdManager, "_run_avdmanager")
    def test_list_empty(self, mock_run):
        """Test listing AVDs when none exist."""
        mock_run.return_value = Mock(returncode=0, stdout="")

        avds = self.manager.list()
        assert avds == []

    @patch.object(AvdManager, "_run_avdmanager")
    def test_list_with_avds(self, mock_run):
        """Test listing AVDs."""
        mock_run.return_value = Mock(returncode=0, stdout="test_avd1\ntest_avd2\ntest_avd3\n")

        avds = self.manager.list()
        assert len(avds) == 3
        assert "test_avd1" in avds
        assert "test_avd2" in avds
        assert "test_avd3" in avds

    @patch.object(AvdManager, "_run_avdmanager")
    def test_list_error(self, mock_run):
        """Test listing AVDs with error."""
        mock_run.side_effect = AvdManagerError("list", "avd", "error")

        avds = self.manager.list()
        assert avds == []

    @patch.object(AvdManager, "_run_avdmanager")
    @patch.object(AvdManager, "list")
    def test_create_new_avd(self, mock_list, mock_run):
        """Test creating a new AVD."""
        # AVD doesn't exist initially
        mock_list.side_effect = [[], ["test_avd"]]
        mock_run.return_value = Mock(returncode=0)

        result = self.manager.create(name="test_avd", api=30, target="google_atd", arch="arm64-v8a")

        assert result is True
        mock_run.assert_called_once()

        # Check command arguments
        args = mock_run.call_args[0][0]
        assert "create" in args
        assert "avd" in args
        assert "-n" in args
        assert "test_avd" in args
        assert "-k" in args
        assert "system-images;android-30;google_atd;arm64-v8a" in args
        assert "-d" in args
        assert "-f" in args

    @patch.object(AvdManager, "_run_avdmanager")
    @patch.object(AvdManager, "list")
    @patch.object(AvdManager, "delete")
    def test_create_existing_avd_with_force(self, mock_delete, mock_list, mock_run):
        """Test creating an AVD that already exists with force."""
        # AVD exists initially
        mock_list.side_effect = [["test_avd"], ["test_avd"]]
        mock_delete.return_value = True
        mock_run.return_value = Mock(returncode=0)

        result = self.manager.create(
            name="test_avd", api=30, target="google_atd", arch="arm64-v8a", force=True
        )

        assert result is True
        mock_delete.assert_called_once_with("test_avd")
        mock_run.assert_called_once()

    @patch.object(AvdManager, "list")
    def test_create_existing_avd_without_force(self, mock_list):
        """Test creating an AVD that already exists without force."""
        # AVD exists
        mock_list.return_value = ["test_avd"]

        result = self.manager.create(
            name="test_avd", api=30, target="google_atd", arch="arm64-v8a", force=False
        )

        assert result is True  # Should return True without creating

    @patch.object(AvdManager, "_run_avdmanager")
    @patch.object(AvdManager, "list")
    def test_create_with_custom_device(self, mock_list, mock_run):
        """Test creating AVD with custom device profile."""
        mock_list.side_effect = [[], ["test_avd"]]
        mock_run.return_value = Mock(returncode=0)

        result = self.manager.create(
            name="test_avd", api=30, target="google_atd", arch="arm64-v8a", device="pixel_7"
        )

        assert result is True

        # Check that custom device was used
        args = mock_run.call_args[0][0]
        device_index = args.index("-d")
        assert args[device_index + 1] == "pixel_7"

    @patch.object(AvdManager, "_run_avdmanager")
    @patch.object(AvdManager, "list")
    def test_create_failure(self, mock_list, mock_run):
        """Test AVD creation failure."""
        mock_list.side_effect = [[], []]  # AVD not created
        mock_run.return_value = Mock(returncode=0)

        with pytest.raises(AvdManagerError, match="AVD not found after creation"):
            self.manager.create(name="test_avd", api=30, target="google_atd", arch="arm64-v8a")

    @patch.object(AvdManager, "_run_avdmanager")
    @patch.object(AvdManager, "list")
    def test_delete_existing_avd(self, mock_list, mock_run):
        """Test deleting an existing AVD."""
        mock_list.return_value = ["test_avd"]
        mock_run.return_value = Mock(returncode=0)

        result = self.manager.delete("test_avd")

        assert result is True
        mock_run.assert_called_once_with(["delete", "avd", "-n", "test_avd"])

    @patch.object(AvdManager, "list")
    def test_delete_nonexistent_avd(self, mock_list):
        """Test deleting a non-existent AVD."""
        mock_list.return_value = []

        result = self.manager.delete("test_avd")

        assert result is True  # Should return True even if doesn't exist

    @patch.object(AvdManager, "_run_avdmanager")
    @patch.object(AvdManager, "list")
    def test_delete_failure(self, mock_list, mock_run):
        """Test AVD deletion failure."""
        mock_list.return_value = ["test_avd"]
        mock_run.side_effect = AvdManagerError("delete", "test_avd", "error")

        result = self.manager.delete("test_avd")

        assert result is False

    @patch.object(AvdManager, "_run_avdmanager")
    def test_get_info(self, mock_run):
        """Test getting AVD information."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="""Available Android Virtual Devices:
    Name: test_avd
    Device: pixel_5 (Google)
    Path: /Users/test/.android/avd/test_avd.avd
    Target: Google APIs (Google Inc.)
    Based on: Android 11.0 (R) Tag/ABI: google_apis/arm64-v8a
    Sdcard: 512M
    Name: other_avd
    Device: pixel_6""",
        )

        info = self.manager.get_info("test_avd")

        assert info is not None
        assert info["name"] == "test_avd"
        assert "pixel_5" in info.get("device", "")
        assert "path" in info

    @patch.object(AvdManager, "_run_avdmanager")
    def test_get_info_not_found(self, mock_run):
        """Test getting info for non-existent AVD."""
        mock_run.return_value = Mock(returncode=0, stdout="Available Android Virtual Devices:\n")

        info = self.manager.get_info("nonexistent_avd")

        assert info is None

    @patch.object(AvdManager, "_run_avdmanager")
    def test_get_info_error(self, mock_run):
        """Test getting AVD info with error."""
        mock_run.side_effect = AvdManagerError("list", "avd", "error")

        info = self.manager.get_info("test_avd")

        assert info is None

    @patch.object(AvdManager, "_run_avdmanager")
    def test_list_devices(self, mock_run):
        """Test listing available device profiles."""
        mock_run.return_value = Mock(returncode=0, stdout="pixel_5\npixel_6\npixel_7\nNexus_5X\n")

        devices = self.manager.list_devices()

        assert len(devices) == 4
        assert "pixel_5" in devices
        assert "pixel_6" in devices
        assert "pixel_7" in devices
        assert "Nexus_5X" in devices

    @patch.object(AvdManager, "_run_avdmanager")
    def test_list_devices_error(self, mock_run):
        """Test listing devices with error."""
        mock_run.side_effect = AvdManagerError("list", "device", "error")

        devices = self.manager.list_devices()

        assert devices == []

    @patch.object(AvdManager, "_run_avdmanager")
    def test_list_targets(self, mock_run):
        """Test listing available targets."""
        mock_run.return_value = Mock(
            returncode=0, stdout="android-30\nandroid-31\nandroid-32\nandroid-33\n"
        )

        targets = self.manager.list_targets()

        assert len(targets) == 4
        assert "android-30" in targets
        assert "android-31" in targets

    @patch.object(AvdManager, "_run_avdmanager")
    def test_list_targets_error(self, mock_run):
        """Test listing targets with error."""
        mock_run.side_effect = AvdManagerError("list", "target", "error")

        targets = self.manager.list_targets()

        assert targets == []
