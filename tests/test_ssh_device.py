"""Tests for LinuxSSHDevice."""

from pathlib import Path
from unittest.mock import Mock, patch
from ovmobilebench.devices.linux_ssh import LinuxSSHDevice, list_ssh_devices


class TestLinuxSSHDevice:
    """Test LinuxSSHDevice functionality."""

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_device_connection(self, mock_ssh_client):
        """Test SSH device connection."""
        # Setup mock
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.connect.return_value = None
        mock_client.open_sftp.return_value = Mock()

        # Create device
        device = LinuxSSHDevice(
            host="localhost", username="test", password="test123", push_dir="/tmp/test"
        )

        # Verify connection was attempted
        mock_client.connect.assert_called_once()
        assert device.serial == "test@localhost:22"
        assert device.push_dir == "/tmp/test"

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_push_file(self, mock_ssh_client):
        """Test pushing file via SFTP."""
        # Setup mock
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp

        # Mock exec_command for chmod
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Create device and push file
        device = LinuxSSHDevice(host="localhost", username="test")
        device.push(Path("/tmp/test.txt"), "/remote/test.txt")

        # Verify SFTP put was called
        mock_sftp.put.assert_called_once_with("/tmp/test.txt", "/remote/test.txt")

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_shell_command(self, mock_ssh_client):
        """Test executing shell command."""
        # Setup mock
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        # Mock exec_command
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b"command output"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Create device and run command
        device = LinuxSSHDevice(host="localhost", username="test")
        ret, out, err = device.shell("echo test")

        # Verify command execution
        mock_client.exec_command.assert_called_with("echo test", timeout=120)
        assert ret == 0
        assert out == "command output"
        assert err == ""

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_device_info(self, mock_ssh_client):
        """Test getting device info."""
        # Setup mock
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        # Mock multiple exec_command calls
        responses = [
            (0, "Linux localhost 5.15.0", ""),  # uname -a
            (0, "8", ""),  # nproc
            (0, "16G", ""),  # free -h
            (0, "x86_64", ""),  # uname -m
            (0, "test-host", ""),  # hostname
        ]

        response_iter = iter(responses)

        def exec_side_effect(cmd, timeout=120):
            ret, out, err = next(response_iter, (1, "", "error"))
            mock_stdin = Mock()
            mock_stdout = Mock()
            mock_stderr = Mock()
            mock_stdout.read.return_value = out.encode()
            mock_stderr.read.return_value = err.encode()
            mock_stdout.channel.recv_exit_status.return_value = ret
            return mock_stdin, mock_stdout, mock_stderr

        mock_client.exec_command.side_effect = exec_side_effect

        # Create device and get info
        device = LinuxSSHDevice(host="localhost", username="test")
        info = device.info()

        # Verify info
        assert info["type"] == "linux_ssh"
        assert info["host"] == "localhost"
        assert info["username"] == "test"
        assert "kernel" in info
        assert "cpu_cores" in info

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_is_available(self, mock_ssh_client):
        """Test checking device availability."""
        # Setup mock
        mock_client = Mock()
        mock_transport = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()
        mock_client.get_transport.return_value = mock_transport
        mock_transport.is_active.return_value = True

        # Create device and check availability
        device = LinuxSSHDevice(host="localhost", username="test")
        assert device.is_available() is True

        # Test when not available
        mock_transport.is_active.return_value = False
        assert device.is_available() is False

    def test_list_ssh_devices(self):
        """Test listing SSH devices."""
        devices = list_ssh_devices()

        # Should detect localhost
        assert len(devices) > 0

        # Check first device
        first = devices[0]
        assert "localhost" in first["serial"]
        assert first["type"] == "linux_ssh"
        assert first["status"] == "available"
