"""Complete tests for Android device module to achieve 100% coverage."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ovmobilebench.core.errors import DeviceError
from ovmobilebench.devices.android import AndroidDevice


class TestAndroidDeviceComplete:
    """Complete tests for AndroidDevice class."""

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_push_with_exception(self, mock_adb_client):
        """Test push with general exception."""
        mock_device = Mock()
        mock_device.push.side_effect = Exception("Unknown error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")

        with pytest.raises(DeviceError) as exc:
            device.push(Path("/local"), "/remote")
        assert "Unknown error" in str(exc.value)

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_pull_with_adb_error(self, mock_adb_client):
        """Test pull with ADB error."""
        from adbutils import AdbError

        mock_device = Mock()
        mock_device.pull.side_effect = AdbError("ADB error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")

        with pytest.raises(DeviceError) as exc:
            device.pull("/remote", Path("/local"))
        assert "ADB error" in str(exc.value)

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_pull_with_exception(self, mock_adb_client):
        """Test pull with general exception."""
        mock_device = Mock()
        mock_device.pull.side_effect = Exception("Unknown error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        local_path = Path("/local")

        with pytest.raises(DeviceError) as exc:
            device.pull("/remote", local_path)
        assert "Unknown error" in str(exc.value)

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_shell_with_timeout(self, mock_adb_client):
        """Test shell command with timeout."""
        mock_device = Mock()
        mock_device.shell.return_value = "output\n__EXIT_CODE__0"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        ret, out, err = device.shell("echo test", timeout=30)

        assert ret == 0
        assert out == "output\n"
        mock_device.shell.assert_called_with("echo test; echo __EXIT_CODE__$?", timeout=30)

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_shell_with_exception(self, mock_adb_client):
        """Test shell with general exception."""
        mock_device = Mock()
        mock_device.shell.side_effect = Exception("Shell error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")

        # Shell method catches exceptions and returns them as errors
        ret, out, err = device.shell("command")
        assert ret == 1
        assert err == "Shell error"
        assert out == ""

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_exists_with_exception(self, mock_adb_client):
        """Test exists with exception."""
        mock_device = Mock()
        mock_device.shell.side_effect = Exception("Error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")

        # exists method catches exceptions and returns False
        result = device.exists("/path")
        assert result is False

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_mkdir_with_exception(self, mock_adb_client):
        """Test mkdir with exception."""
        mock_device = Mock()
        mock_device.shell.side_effect = Exception("Error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")

        with pytest.raises(DeviceError):
            device.mkdir("/path")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_rm_recursive_with_exception(self, mock_adb_client):
        """Test rm recursive with exception."""
        mock_device = Mock()
        mock_device.shell.side_effect = Exception("Error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")

        with pytest.raises(DeviceError):
            device.rm("/path", recursive=True)

    # Removed test_get_cpu_info - method doesn't exist in AndroidDevice

    # Removed test_get_memory_info - method doesn't exist in AndroidDevice

    # Removed test_get_gpu_info - method doesn't exist in AndroidDevice

    # Removed test_get_battery_info - method doesn't exist in AndroidDevice

    # Removed test_set_performance_mode - method doesn't exist in AndroidDevice

    # Removed test_start_screen_record - method doesn't exist in AndroidDevice

    # Removed test_stop_screen_record - method doesn't exist in AndroidDevice

    # Removed test_uninstall_apk - method doesn't exist in AndroidDevice

    # Removed test_forward_reverse_ports - method doesn't exist in AndroidDevice

    # Removed test_get_prop - method doesn't exist in AndroidDevice

    # Removed test_set_prop - method doesn't exist in AndroidDevice

    # Removed test_clear_logcat - method doesn't exist in AndroidDevice

    # Removed test_get_logcat - method doesn't exist in AndroidDevice
