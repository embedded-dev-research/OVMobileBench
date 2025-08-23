"""Comprehensive tests for Android device implementation."""

from unittest.mock import Mock, patch

from ovmobilebench.devices.android import list_android_devices


class TestListAndroidDevices:
    """Test list_android_devices function."""

    def test_list_devices_success(self):
        """Test listing devices successfully."""
        mock_device1 = Mock()
        mock_device1.serial = "device1"
        mock_device1.get_state.return_value = "device"

        mock_device2 = Mock()
        mock_device2.serial = "device2"
        mock_device2.get_state.return_value = "offline"

        with patch("adbutils.AdbClient") as mock_adb_client:
            mock_client = Mock()
            mock_client.device_list.return_value = [mock_device1, mock_device2]
            mock_adb_client.return_value = mock_client

            devices = list_android_devices()

        assert devices == [("device1", "device"), ("device2", "offline")]

    def test_list_devices_empty(self):
        """Test listing devices when none are connected."""
        with patch("adbutils.AdbClient") as mock_adb_client:
            mock_client = Mock()
            mock_client.device_list.return_value = []
            mock_adb_client.return_value = mock_client

            devices = list_android_devices()

        assert devices == []

    def test_list_devices_exception(self):
        """Test handling exception when listing devices."""
        with patch("adbutils.AdbClient", side_effect=Exception("ADB error")):
            devices = list_android_devices()

        assert devices == []
