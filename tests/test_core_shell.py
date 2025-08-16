"""Tests for core.shell module."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from ovmobilebench.core.shell import CommandResult, run


class TestCommandResult:
    """Test CommandResult dataclass."""

    def test_success_property_true(self):
        """Test success property returns True for returncode 0."""
        result = CommandResult(
            returncode=0, stdout="output", stderr="", duration_sec=1.0, cmd="echo test"
        )
        assert result.success is True

    def test_success_property_false(self):
        """Test success property returns False for non-zero returncode."""
        result = CommandResult(
            returncode=1, stdout="", stderr="error", duration_sec=1.0, cmd="false"
        )
        assert result.success is False


class TestRun:
    """Test run function."""

    @patch("subprocess.Popen")
    def test_run_simple_command(self, mock_popen):
        """Test running a simple command."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = ("output", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        result = run("echo test")

        assert result.returncode == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.cmd == "echo test"
        assert result.success is True

    @patch("subprocess.Popen")
    def test_run_list_command(self, mock_popen):
        """Test running command as list."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = ("output", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        result = run(["echo", "test"])

        assert result.returncode == 0
        assert result.cmd == "echo test"

    @patch("subprocess.Popen")
    def test_run_with_env(self, mock_popen):
        """Test running with environment variables."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        env = {"TEST_VAR": "value"}
        run("echo test", env=env)

        mock_popen.assert_called_once()
        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs["env"] == env

    @patch("subprocess.Popen")
    def test_run_with_cwd(self, mock_popen):
        """Test running with working directory."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            run("ls", cwd=cwd)

            mock_popen.assert_called_once()
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs["cwd"] == cwd

    @patch("subprocess.Popen")
    def test_run_with_timeout(self, mock_popen):
        """Test running with timeout."""
        mock_proc = Mock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired("cmd", 5)
        mock_proc.kill = Mock()
        mock_proc.communicate.side_effect = [
            subprocess.TimeoutExpired("cmd", 5),
            ("partial", "timeout error"),
        ]
        mock_popen.return_value = mock_proc

        result = run("sleep 10", timeout=5)

        assert result.returncode == 124  # Timeout code
        assert "TIMEOUT" in result.stderr
        mock_proc.kill.assert_called_once()

    @patch("subprocess.Popen")
    def test_run_timeout_with_check(self, mock_popen):
        """Test timeout with check=True raises exception."""
        mock_proc = Mock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired("cmd", 5)
        mock_proc.kill = Mock()
        mock_proc.communicate.side_effect = [subprocess.TimeoutExpired("cmd", 5), ("", "")]
        mock_popen.return_value = mock_proc

        with pytest.raises(TimeoutError) as exc_info:
            run("sleep 10", timeout=5, check=True)

        assert "timed out" in str(exc_info.value)

    @patch("subprocess.Popen")
    def test_run_no_capture(self, mock_popen):
        """Test running without capturing output."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = (None, None)
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        run("echo test", capture=False)

        mock_popen.assert_called_once()
        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs["stdout"] is None
        assert call_kwargs["stderr"] is None

    @patch("subprocess.Popen")
    @patch("builtins.print")
    def test_run_verbose(self, mock_print, mock_popen):
        """Test verbose mode prints command."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        run("echo test", verbose=True)

        mock_print.assert_called_once_with("Executing: echo test")

    @patch("subprocess.Popen")
    def test_run_check_error(self, mock_popen):
        """Test check=True raises on non-zero exit."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = ("", "error")
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            run("false", check=True)

        assert exc_info.value.returncode == 1

    @patch("subprocess.Popen")
    def test_run_exception_handling(self, mock_popen):
        """Test exception handling during execution."""
        mock_popen.side_effect = OSError("Command not found")

        result = run("nonexistent_command")

        assert result.returncode == -1
        assert "Command not found" in result.stderr
        assert result.success is False

    @patch("subprocess.Popen")
    def test_run_exception_with_check(self, mock_popen):
        """Test exception with check=True re-raises."""
        mock_popen.side_effect = OSError("Command not found")

        with pytest.raises(OSError):
            run("nonexistent_command", check=True)

    @patch("subprocess.Popen")
    def test_run_with_special_chars(self, mock_popen):
        """Test command with special characters."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        result = run(["echo", "test with spaces"])

        assert result.cmd == "echo 'test with spaces'"

    @patch("subprocess.Popen")
    def test_run_duration_tracking(self, mock_popen):
        """Test that duration is tracked."""
        mock_proc = Mock()
        mock_proc.communicate.return_value = ("", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with patch("time.time", side_effect=[100.0, 101.5]):
            result = run("echo test")

        assert result.duration_sec == 1.5
