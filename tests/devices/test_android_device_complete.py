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
        mock_device.shell.return_value = "output"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        ret, out, err = device.shell("echo test", timeout=30)

        assert ret == 0
        assert out == "output"
        mock_device.shell.assert_called_with("echo test", timeout=30)

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_shell_with_exception(self, mock_adb_client):
        """Test shell with general exception."""
        mock_device = Mock()
        mock_device.shell.side_effect = Exception("Shell error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")

        with pytest.raises(DeviceError) as exc:
            device.shell("command")
        assert "Shell error" in str(exc.value)

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_exists_with_exception(self, mock_adb_client):
        """Test exists with exception."""
        mock_device = Mock()
        mock_device.shell.side_effect = Exception("Error")
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")

        with pytest.raises(DeviceError):
            device.exists("/path")

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

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_get_cpu_info(self, mock_adb_client):
        """Test get_cpu_info method."""
        mock_device = Mock()
        mock_device.shell.return_value = "cpu info output"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        info = device.get_cpu_info()

        assert info == "cpu info output"
        mock_device.shell.assert_called_with("cat /proc/cpuinfo")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_get_memory_info(self, mock_adb_client):
        """Test get_memory_info method."""
        mock_device = Mock()
        mock_device.shell.return_value = "memory info output"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        info = device.get_memory_info()

        assert info == "memory info output"
        mock_device.shell.assert_called_with("cat /proc/meminfo")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_get_gpu_info(self, mock_adb_client):
        """Test get_gpu_info method."""
        mock_device = Mock()
        mock_device.shell.return_value = "gpu info output"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        info = device.get_gpu_info()

        assert info == "gpu info output"
        mock_device.shell.assert_called_with("dumpsys SurfaceFlinger | grep GLES")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_get_battery_info(self, mock_adb_client):
        """Test get_battery_info method."""
        mock_device = Mock()
        mock_device.shell.return_value = "battery info output"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        info = device.get_battery_info()

        assert info == "battery info output"
        mock_device.shell.assert_called_with("dumpsys battery")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_set_performance_mode(self, mock_adb_client):
        """Test set_performance_mode method."""
        mock_device = Mock()
        mock_device.shell.return_value = ""
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        device.set_performance_mode()

        # Should call multiple shell commands for performance settings
        assert mock_device.shell.call_count >= 3

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_start_screen_record(self, mock_adb_client):
        """Test start_screen_record method."""
        mock_device = Mock()
        mock_device.shell.return_value = ""
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        device.start_screen_record("/sdcard/record.mp4")

        mock_device.shell.assert_called()
        call_args = mock_device.shell.call_args[0][0]
        assert "screenrecord" in call_args
        assert "/sdcard/record.mp4" in call_args

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_stop_screen_record(self, mock_adb_client):
        """Test stop_screen_record method."""
        mock_device = Mock()
        mock_device.shell.return_value = ""
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        device.stop_screen_record()

        mock_device.shell.assert_called_with("pkill -SIGINT screenrecord")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_uninstall_apk(self, mock_adb_client):
        """Test uninstall_apk method."""
        mock_device = Mock()
        mock_device.uninstall.return_value = None
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        device.uninstall_apk("com.example.app")

        mock_device.uninstall.assert_called_with("com.example.app")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_forward_reverse_ports(self, mock_adb_client):
        """Test forward_reverse_port method."""
        mock_device = Mock()
        mock_device.reverse.return_value = None
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        device.forward_reverse_port(8080, 8081)

        mock_device.reverse.assert_called_with("tcp:8080", "tcp:8081")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_get_prop(self, mock_adb_client):
        """Test get_prop method."""
        mock_device = Mock()
        mock_device.prop.get.return_value = "property_value"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        value = device.get_prop("ro.build.version.sdk")

        assert value == "property_value"
        mock_device.prop.get.assert_called_with("ro.build.version.sdk")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_set_prop(self, mock_adb_client):
        """Test set_prop method."""
        mock_device = Mock()
        mock_device.shell.return_value = ""
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        device.set_prop("debug.test", "value")

        mock_device.shell.assert_called_with("setprop debug.test value")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_clear_logcat(self, mock_adb_client):
        """Test clear_logcat method."""
        mock_device = Mock()
        mock_device.shell.return_value = ""
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        device.clear_logcat()

        mock_device.shell.assert_called_with("logcat -c")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_get_logcat(self, mock_adb_client):
        """Test get_logcat method."""
        mock_device = Mock()
        mock_device.shell.return_value = "logcat output"
        mock_client = Mock()
        mock_client.device.return_value = mock_device
        mock_adb_client.return_value = mock_client

        device = AndroidDevice("test_serial")
        logs = device.get_logcat()

        assert logs == "logcat output"
        mock_device.shell.assert_called_with("logcat -d")
