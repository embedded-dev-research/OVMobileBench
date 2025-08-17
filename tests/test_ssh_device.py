"""Tests for LinuxSSHDevice."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from ovmobilebench.devices.linux_ssh import LinuxSSHDevice, list_ssh_devices
from ovmobilebench.core.errors import DeviceError


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
        local_path = Path("/tmp/test.txt")
        device.push(local_path, "/remote/test.txt")

        # Verify SFTP put was called
        mock_sftp.put.assert_called_once_with(str(local_path), "/remote/test.txt")

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

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_init_with_key_file(self, mock_ssh_client):
        """Test SSH device initialization with key file."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        with patch("os.path.exists", return_value=True):
            with patch("os.path.expanduser", return_value="/home/user/.ssh/id_rsa"):
                device = LinuxSSHDevice(
                    host="test.example.com",
                    username="testuser",
                    key_filename="~/.ssh/id_rsa",
                    port=2222,
                    push_dir="/tmp/custom",
                )

                assert device.host == "test.example.com"
                assert device.username == "testuser"
                assert device.key_filename == "~/.ssh/id_rsa"
                assert device.port == 2222
                assert device.push_dir == "/tmp/custom"
                assert device.serial == "testuser@test.example.com:2222"

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_init_with_missing_key_file(self, mock_ssh_client):
        """Test SSH device initialization with missing key file."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        with patch("os.path.exists", return_value=False):
            with patch("os.path.expanduser", return_value="/home/user/.ssh/missing"):
                LinuxSSHDevice(
                    host="test.example.com",
                    username="testuser",
                    key_filename="~/.ssh/missing",
                    password="fallback_pass",
                )

                # Should fall back to password auth
                mock_client.connect.assert_called_once()
                connect_kwargs = mock_client.connect.call_args[1]
                assert "password" in connect_kwargs

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_init_with_ssh_agent(self, mock_ssh_client):
        """Test SSH device initialization using SSH agent."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        LinuxSSHDevice(host="test.example.com", username="testuser")

        # Should use agent/default keys
        mock_client.connect.assert_called_once()
        connect_kwargs = mock_client.connect.call_args[1]
        assert connect_kwargs.get("look_for_keys") is True
        assert connect_kwargs.get("allow_agent") is True

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_connection_failure(self, mock_ssh_client):
        """Test SSH connection failure."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.connect.side_effect = Exception("Connection failed")

        with pytest.raises(DeviceError) as exc_info:
            LinuxSSHDevice(host="badhost", username="test")

        assert "Failed to connect to test@badhost:22" in str(exc_info.value)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_pull_file(self, mock_ssh_client):
        """Test pulling file via SFTP."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp

        device = LinuxSSHDevice(host="localhost", username="test")
        local_path = Path("/tmp/local.txt")

        with patch("pathlib.Path.mkdir"):
            device.pull("/remote/test.txt", local_path)

        mock_sftp.get.assert_called_once_with("/remote/test.txt", str(local_path))

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_pull_file_error(self, mock_ssh_client):
        """Test pull file error handling."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.get.side_effect = Exception("Transfer failed")

        device = LinuxSSHDevice(host="localhost", username="test")

        with pytest.raises(DeviceError) as exc_info:
            device.pull("/remote/test.txt", Path("/tmp/local.txt"))

        assert "Failed to pull /remote/test.txt" in str(exc_info.value)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_push_file_no_sftp(self, mock_ssh_client):
        """Test push file when SFTP is not established."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = None

        device = LinuxSSHDevice(host="localhost", username="test")
        device.sftp = None  # Simulate no SFTP connection

        with pytest.raises(DeviceError) as exc_info:
            device.push(Path("/tmp/test.txt"), "/remote/test.txt")

        assert "SFTP connection not established" in str(exc_info.value)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_push_file_error(self, mock_ssh_client):
        """Test push file error handling."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.put.side_effect = Exception("Transfer failed")

        device = LinuxSSHDevice(host="localhost", username="test")

        with pytest.raises(DeviceError) as exc_info:
            device.push(Path("/tmp/test.txt"), "/remote/test.txt")

        # Check error message contains file path (format varies by OS)
        assert "Failed to push" in str(exc_info.value) and "test.txt" in str(exc_info.value)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_shell_no_client(self, mock_ssh_client):
        """Test shell command when SSH client is not established."""
        mock_ssh_client.return_value = Mock()

        device = LinuxSSHDevice(host="localhost", username="test")
        device.client = None  # Simulate no SSH connection

        with pytest.raises(DeviceError) as exc_info:
            device.shell("echo test")

        assert "SSH connection not established" in str(exc_info.value)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_shell_command_error(self, mock_ssh_client):
        """Test shell command execution error."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()
        mock_client.exec_command.side_effect = Exception("Command failed")

        device = LinuxSSHDevice(host="localhost", username="test")

        with pytest.raises(DeviceError) as exc_info:
            device.shell("echo test")

        assert "Failed to execute command" in str(exc_info.value)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_shell_with_custom_timeout(self, mock_ssh_client):
        """Test shell command with custom timeout."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        # Mock exec_command
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b"output"
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        device = LinuxSSHDevice(host="localhost", username="test")
        device.shell("echo test", timeout=300)

        mock_client.exec_command.assert_called_with("echo test", timeout=300)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_exists_file_found(self, mock_ssh_client):
        """Test exists method when file exists."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.stat.return_value = Mock()  # File exists

        device = LinuxSSHDevice(host="localhost", username="test")
        assert device.exists("/remote/test.txt") is True

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_exists_file_not_found(self, mock_ssh_client):
        """Test exists method when file doesn't exist."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.stat.side_effect = FileNotFoundError()

        device = LinuxSSHDevice(host="localhost", username="test")
        assert device.exists("/remote/nonexistent.txt") is False

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_exists_other_error(self, mock_ssh_client):
        """Test exists method with other SFTP error."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.stat.side_effect = Exception("SFTP error")

        device = LinuxSSHDevice(host="localhost", username="test")
        assert device.exists("/remote/test.txt") is False

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_exists_no_sftp(self, mock_ssh_client):
        """Test exists method when SFTP is not available."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        device = LinuxSSHDevice(host="localhost", username="test")
        device.sftp = None

        assert device.exists("/remote/test.txt") is False

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_mkdir(self, mock_ssh_client):
        """Test mkdir functionality."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.stat.side_effect = FileNotFoundError()  # Directory doesn't exist

        device = LinuxSSHDevice(host="localhost", username="test")
        device.mkdir("/remote/new/dir")

        # Should attempt to create directory
        assert mock_sftp.mkdir.called

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_mkdir_already_exists(self, mock_ssh_client):
        """Test mkdir when directory already exists."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.stat.return_value = Mock()  # Directory exists

        device = LinuxSSHDevice(host="localhost", username="test")
        device.mkdir("/remote/existing/dir")

        # Should not attempt to create directory
        mock_sftp.mkdir.assert_not_called()

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_mkdir_no_sftp(self, mock_ssh_client):
        """Test mkdir when SFTP is not established."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        device = LinuxSSHDevice(host="localhost", username="test")
        device.sftp = None

        with pytest.raises(DeviceError) as exc_info:
            device.mkdir("/remote/dir")

        assert "SFTP connection not established" in str(exc_info.value)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_rm_file(self, mock_ssh_client):
        """Test removing file."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        # Mock shell command
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        device = LinuxSSHDevice(host="localhost", username="test")
        device.rm("/remote/test.txt")

        mock_client.exec_command.assert_called_with("rm -f /remote/test.txt", timeout=120)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_rm_recursive(self, mock_ssh_client):
        """Test removing directory recursively."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        # Mock shell command
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        device = LinuxSSHDevice(host="localhost", username="test")
        device.rm("/remote/dir", recursive=True)

        mock_client.exec_command.assert_called_with("rm -rf /remote/dir", timeout=120)

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_rm_failure(self, mock_ssh_client):
        """Test rm command failure handling."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        # Mock failed shell command
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"Permission denied"
        mock_stdout.channel.recv_exit_status.return_value = 1
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        device = LinuxSSHDevice(host="localhost", username="test")

        # Should not raise exception, just log warning
        device.rm("/remote/protected.txt")

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_info_command_failures(self, mock_ssh_client):
        """Test device info with command failures."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        # Mock all commands to fail
        def exec_side_effect(cmd, timeout=120):
            mock_stdin = Mock()
            mock_stdout = Mock()
            mock_stderr = Mock()
            mock_stdout.read.return_value = b""
            mock_stderr.read.return_value = b"Command not found"
            mock_stdout.channel.recv_exit_status.return_value = 1
            return mock_stdin, mock_stdout, mock_stderr

        mock_client.exec_command.side_effect = exec_side_effect

        device = LinuxSSHDevice(host="localhost", username="test")
        info = device.info()

        # Should still return basic info
        assert info["type"] == "linux_ssh"
        assert info["host"] == "localhost"
        assert info["username"] == "test"
        # Should not have system info due to command failures
        assert "kernel" not in info

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_info_exception_handling(self, mock_ssh_client):
        """Test device info with exception during system info gathering."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()
        mock_client.exec_command.side_effect = Exception("System error")

        device = LinuxSSHDevice(host="localhost", username="test")
        info = device.info()

        # Should still return basic info despite exception
        assert info["type"] == "linux_ssh"
        assert info["host"] == "localhost"
        assert info["username"] == "test"

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_is_available_no_client(self, mock_ssh_client):
        """Test is_available when client is None."""
        mock_ssh_client.return_value = Mock()

        device = LinuxSSHDevice(host="localhost", username="test")
        device.client = None

        assert device.is_available() is False

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_is_available_no_transport(self, mock_ssh_client):
        """Test is_available when transport is None."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()
        mock_client.get_transport.return_value = None

        device = LinuxSSHDevice(host="localhost", username="test")
        assert device.is_available() is False

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_is_available_exception(self, mock_ssh_client):
        """Test is_available with exception."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()
        mock_client.get_transport.side_effect = Exception("Transport error")

        device = LinuxSSHDevice(host="localhost", username="test")
        assert device.is_available() is False

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_get_env(self, mock_ssh_client):
        """Test get_env method."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = Mock()

        device = LinuxSSHDevice(host="localhost", username="test", push_dir="/custom/path")
        env = device.get_env()

        assert "LD_LIBRARY_PATH" in env
        assert "/custom/path/lib:$LD_LIBRARY_PATH" in env["LD_LIBRARY_PATH"]

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_destructor(self, mock_ssh_client):
        """Test device destructor cleanup."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp

        device = LinuxSSHDevice(host="localhost", username="test")

        # Manually call destructor
        device.__del__()

        mock_sftp.close.assert_called_once()
        mock_client.close.assert_called_once()

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_destructor_exception(self, mock_ssh_client):
        """Test device destructor with exception during cleanup."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp
        mock_sftp.close.side_effect = Exception("Close failed")

        device = LinuxSSHDevice(host="localhost", username="test")

        # Should not raise exception
        device.__del__()

    @patch("socket.gethostname")
    @patch("os.environ.get")
    def test_list_ssh_devices_with_hostname(self, mock_environ_get, mock_gethostname):
        """Test list_ssh_devices with different hostname."""
        mock_environ_get.return_value = "testuser"
        mock_gethostname.return_value = "testhost"

        devices = list_ssh_devices()

        assert len(devices) == 2  # localhost + actual hostname
        assert any(d["host"] == "localhost" for d in devices)
        assert any(d["host"] == "testhost" for d in devices)

    @patch("socket.gethostname")
    def test_list_ssh_devices_exception(self, mock_gethostname):
        """Test list_ssh_devices with exception."""
        mock_gethostname.side_effect = Exception("Network error")

        devices = list_ssh_devices()

        # Should return empty list on exception
        assert devices == []

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_push_executable_file(self, mock_ssh_client):
        """Test pushing executable file (should chmod +x)."""
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

        device = LinuxSSHDevice(host="localhost", username="test")

        # Test with executable file (no extension)
        local_path = Path("/tmp/binary_file")
        device.push(local_path, "/remote/binary_file")

        # Should call chmod +x
        mock_client.exec_command.assert_called()
        cmd_args = mock_client.exec_command.call_args[0][0]
        assert "chmod +x" in cmd_args

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_push_shell_script(self, mock_ssh_client):
        """Test pushing shell script (should chmod +x)."""
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

        device = LinuxSSHDevice(host="localhost", username="test")

        # Test with shell script
        local_path = Path("/tmp/script.sh")
        device.push(local_path, "/remote/script.sh")

        # Should call chmod +x
        mock_client.exec_command.assert_called()
        cmd_args = mock_client.exec_command.call_args[0][0]
        assert "chmod +x" in cmd_args

    @patch("ovmobilebench.devices.linux_ssh.paramiko.SSHClient")
    def test_push_non_executable_file(self, mock_ssh_client):
        """Test pushing non-executable file (should not chmod)."""
        mock_client = Mock()
        mock_sftp = Mock()
        mock_ssh_client.return_value = mock_client
        mock_client.open_sftp.return_value = mock_sftp

        device = LinuxSSHDevice(host="localhost", username="test")

        # Test with text file
        local_path = Path("/tmp/data.txt")
        device.push(local_path, "/remote/data.txt")

        # Should not call chmod +x for text files
        mock_client.exec_command.assert_not_called()

    def test_list_ssh_devices_with_config_file(self):
        """Test list_ssh_devices with config file parameter."""
        # This function currently ignores the config_file parameter
        # but we test that it doesn't break
        devices = list_ssh_devices(config_file="/some/config")

        # Should still work the same way
        assert isinstance(devices, list)
