"""Tests for device listing functionality."""

from unittest.mock import patch, Mock

from ovmobilebench.devices.android import list_android_devices


class TestListAndroidDevices:
    """Test listing Android devices."""

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_list_devices_success(self, mock_adb_client):
        """Test successful device listing."""
        # Setup mock devices
        mock_device1 = Mock()
        mock_device1.serial = "12345678"
        mock_device1.get_state.return_value = "device"

        mock_device2 = Mock()
        mock_device2.serial = "abcd1234"
        mock_device2.get_state.return_value = "offline"

        mock_client = Mock()
        mock_client.device_list.return_value = [mock_device1, mock_device2]
        mock_adb_client.return_value = mock_client

        devices = list_android_devices()

        assert len(devices) == 2
        assert devices[0] == ("12345678", "device")
        assert devices[1] == ("abcd1234", "offline")

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_list_devices_empty(self, mock_adb_client):
        """Test listing when no devices connected."""
        mock_client = Mock()
        mock_client.device_list.return_value = []
        mock_adb_client.return_value = mock_client

        devices = list_android_devices()
        assert devices == []

    @patch("ovmobilebench.devices.android.adbutils.AdbClient")
    def test_list_devices_error(self, mock_adb_client):
        """Test handling ADB error."""
        mock_adb_client.side_effect = Exception("ADB connection failed")

        devices = list_android_devices()
        assert devices == []
