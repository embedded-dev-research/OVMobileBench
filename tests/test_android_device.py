"""Tests for AndroidDevice with adbutils."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ovmobilebench.core.errors import DeviceError
from ovmobilebench.devices.android import AndroidDevice, list_android_devices


class TestAndroidDevice:
    """Test AndroidDevice functionality."""

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_list_android_devices(self, mock_adb_client):
        """Test listing available Android devices."""
        # Setup mock
        mock_device1 = Mock()
        mock_device1.serial = "device1"
        mock_device1.get_state.return_value = "device"

        mock_device2 = Mock()
        mock_device2.serial = "device2"
        mock_device2.get_state.return_value = "offline"

        mock_client = Mock()
        mock_client.device_list.return_value = [mock_device1, mock_device2]
        mock_adb_client.return_value = mock_client

        # Test
        devices = list_android_devices()

        # Verify
        assert len(devices) == 2
        assert devices[0] == ("device1", "device")
        assert devices[1] == ("device2", "offline")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_device_connection(self, mock_adb_client):
        """Test device connection initialization."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")

        # Verify
        assert device.serial == "test_serial"
        assert device.push_dir == "/data/local/tmp/ovmobilebench"
        mock_client.device.assert_called_once_with("test_serial")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_push_file(self, mock_adb_client):
        """Test pushing a file to device."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        local_path = Path("/tmp/test.txt")
        device.push(local_path, "/data/local/tmp/test.txt")

        # Verify
        mock_device.push.assert_called_once_with(str(local_path), "/data/local/tmp/test.txt")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_pull_file(self, mock_adb_client):
        """Test pulling a file from device."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        local_path = Path("/tmp/test.txt")
        device.pull("/data/local/tmp/test.txt", local_path)

        # Verify
        mock_device.pull.assert_called_once_with("/data/local/tmp/test.txt", str(local_path))

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_shell_command(self, mock_adb_client):
        """Test executing shell command on device."""
        # Setup mock
        mock_device = Mock()
        mock_device.shell.return_value = "Hello World\n__EXIT_CODE__0"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        exit_code, stdout, stderr = device.shell("echo 'Hello World'")

        # Verify
        assert exit_code == 0
        assert stdout == "Hello World\n"
        assert stderr == ""

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_exists_file(self, mock_adb_client):
        """Test checking if file exists on device."""
        # Setup mock
        mock_device = Mock()
        mock_device.shell.return_value = "1"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        exists = device.exists("/data/local/tmp/test.txt")

        # Verify
        assert exists is True
        mock_device.shell.assert_called_once_with(
            "test -e /data/local/tmp/test.txt && echo 1 || echo 0"
        )

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_mkdir(self, mock_adb_client):
        """Test creating directory on device."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        device.mkdir("/data/local/tmp/test_dir")

        # Verify
        mock_device.shell.assert_called_once_with("mkdir -p /data/local/tmp/test_dir")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_rm_file(self, mock_adb_client):
        """Test removing file from device."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        device.rm("/data/local/tmp/test.txt")

        # Verify
        mock_device.shell.assert_called_once_with("rm -f /data/local/tmp/test.txt")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_rm_directory_recursive(self, mock_adb_client):
        """Test removing directory recursively from device."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        device.rm("/data/local/tmp/test_dir", recursive=True)

        # Verify
        mock_device.shell.assert_called_once_with("rm -rf /data/local/tmp/test_dir")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_device_info(self, mock_adb_client):
        """Test getting device information."""
        # Setup mock
        mock_device = Mock()
        mock_device.shell.side_effect = [
            "11",  # Android version
            "Pixel 5",  # Model
            "Hardware : Qualcomm Snapdragon 765G",  # CPU
            "MemTotal: 8388608 kB",  # Memory
            "arm64-v8a",  # ABI
        ]
        mock_device.get_properties.return_value = {
            "ro.build.version.sdk": "30",
            "ro.product.manufacturer": "Google",
        }
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        info = device.info()

        # Verify
        assert info["serial"] == "test_serial"
        assert info["os"] == "Android"
        assert info["android_version"] == "11"
        assert info["model"] == "Pixel 5"
        assert info["cpu"] == "Qualcomm Snapdragon 765G"
        assert info["memory_gb"] == 8.0
        assert info["abi"] == "arm64-v8a"
        assert info["sdk_version"] == "30"
        assert info["manufacturer"] == "Google"

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_is_available(self, mock_adb_client):
        """Test checking device availability."""
        # Setup mock
        mock_device = Mock()
        mock_device.get_state.return_value = "device"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        available = device.is_available()

        # Verify
        assert available is True

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_get_temperature(self, mock_adb_client):
        """Test getting device temperature."""
        # Setup mock
        mock_device = Mock()
        mock_device.shell.return_value = "35000"  # 35 degrees Celsius in millidegrees
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        temp = device.get_temperature()

        # Verify
        assert temp == 35.0

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_take_screenshot(self, mock_adb_client):
        """Test taking a screenshot."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        local_path = Path("/tmp/screenshot.png")

        with patch.object(device, "pull") as mock_pull, patch.object(device, "rm") as mock_rm:
            device.take_screenshot(local_path)

            # Verify
            mock_device.shell.assert_called_once_with("screencap -p /sdcard/screenshot.png")
            mock_pull.assert_called_once_with("/sdcard/screenshot.png", local_path)
            mock_rm.assert_called_once_with("/sdcard/screenshot.png")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_install_apk(self, mock_adb_client):
        """Test installing an APK."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        apk_path = Path("/tmp/app.apk")
        device.install_apk(apk_path)

        # Verify
        mock_device.install.assert_called_once_with(str(apk_path))

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_forward_port(self, mock_adb_client):
        """Test port forwarding."""
        # Setup mock
        mock_device = Mock()
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")
        device.forward_port(8080, 8080)

        # Verify
        mock_device.forward.assert_called_once_with("tcp:8080", "tcp:8080")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_error_handling(self, mock_adb_client):
        """Test error handling for device operations."""
        # Setup mock
        from adbutils import AdbError

        mock_device = Mock()
        mock_device.push.side_effect = AdbError("Push failed")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        # Test
        device = AndroidDevice("test_serial")

        with pytest.raises(DeviceError) as exc_info:
            device.push(Path("/tmp/test.txt"), "/data/local/tmp/test.txt")

        assert "Failed to push" in str(exc_info.value)
