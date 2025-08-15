"""Tests for device abstractions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from ovbench.devices.android import AndroidDevice, list_android_devices


class TestListAndroidDevices:
    """Test listing Android devices."""
    
    @patch('subprocess.run')
    def test_list_devices_success(self, mock_run):
        """Test successful device listing."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\n12345678\tdevice\nabcd1234\toffline\n",
            stderr=""
        )
        
        devices = list_android_devices()
        
        assert len(devices) == 2
        assert devices[0] == ("12345678", "device")
        assert devices[1] == ("abcd1234", "offline")
    
    @patch('subprocess.run')
    def test_list_devices_empty(self, mock_run):
        """Test listing when no devices connected."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\n",
            stderr=""
        )
        
        devices = list_android_devices()
        assert devices == []
    
    @patch('subprocess.run')
    def test_list_devices_error(self, mock_run):
        """Test handling ADB error."""
        mock_run.side_effect = FileNotFoundError("adb not found")
        
        devices = list_android_devices()
        assert devices == []


class TestAndroidDevice:
    """Test AndroidDevice class."""
    
    @pytest.fixture
    def device(self):
        """Create AndroidDevice instance."""
        return AndroidDevice("test_serial", "/data/local/tmp/test")
    
    @patch('subprocess.run')
    def test_push_success(self, mock_run, device):
        """Test successful file push."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        device.push(Path("/local/file.txt"), "/remote/file.txt")
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "adb" in args
        assert "-s" in args
        assert "test_serial" in args
        assert "push" in args
    
    @patch('subprocess.run')
    def test_push_failure(self, mock_run, device):
        """Test failed file push."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="adb: error: failed to copy"
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            device.push(Path("/local/file.txt"), "/remote/file.txt")
        
        assert "Failed to push" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_shell_command(self, mock_run, device):
        """Test executing shell command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Hello World",
            stderr=""
        )
        
        rc, stdout, stderr = device.shell("echo Hello World")
        
        assert rc == 0
        assert stdout == "Hello World"
        assert stderr == ""
    
    @patch('subprocess.run')
    def test_exists_true(self, mock_run, device):
        """Test checking if file exists (exists)."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="1",
            stderr=""
        )
        
        exists = device.exists("/data/local/tmp/file.txt")
        assert exists is True
    
    @patch('subprocess.run')
    def test_exists_false(self, mock_run, device):
        """Test checking if file exists (doesn't exist)."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="0",
            stderr=""
        )
        
        exists = device.exists("/data/local/tmp/file.txt")
        assert exists is False
    
    @patch('subprocess.run')
    def test_mkdir(self, mock_run, device):
        """Test creating directory."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        device.mkdir("/data/local/tmp/newdir")
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "shell" in args
        assert "mkdir -p" in ' '.join(args)
    
    @patch('subprocess.run')
    def test_get_info(self, mock_run, device):
        """Test getting device information."""
        # Mock multiple shell commands
        responses = [
            MagicMock(returncode=0, stdout="12", stderr=""),  # Android version
            MagicMock(returncode=0, stdout="Pixel 5", stderr=""),  # Model
            MagicMock(returncode=0, stdout="Hardware : Qualcomm", stderr=""),  # CPU
            MagicMock(returncode=0, stdout="MemTotal:      8000000 kB", stderr=""),  # Memory
            MagicMock(returncode=0, stdout="arm64-v8a", stderr=""),  # ABI
        ]
        mock_run.side_effect = responses
        
        info = device.info()
        
        assert info["serial"] == "test_serial"
        assert info["os"] == "Android"
        assert info["android_version"] == "12"
        assert info["model"] == "Pixel 5"
        assert "Qualcomm" in info["cpu"]
        assert info["memory_gb"] == pytest.approx(7.63, rel=0.1)
        assert info["abi"] == "arm64-v8a"
    
    @patch('ovbench.devices.android.list_android_devices')
    def test_is_available_true(self, mock_list, device):
        """Test device availability check (available)."""
        mock_list.return_value = [("test_serial", "device"), ("other", "device")]
        
        available = device.is_available()
        assert available is True
    
    @patch('ovbench.devices.android.list_android_devices')
    def test_is_available_false(self, mock_list, device):
        """Test device availability check (not available)."""
        mock_list.return_value = [("other", "device")]
        
        available = device.is_available()
        assert available is False
    
    @patch('subprocess.run')
    def test_get_temperature(self, mock_run, device):
        """Test getting device temperature."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="45000",  # 45 degrees in millidegrees
            stderr=""
        )
        
        temp = device.get_temperature()
        assert temp == pytest.approx(45.0)
    
    @patch('subprocess.run')
    def test_screen_off(self, mock_run, device):
        """Test turning screen off."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        device.screen_off()
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "input keyevent 26" in ' '.join(args)