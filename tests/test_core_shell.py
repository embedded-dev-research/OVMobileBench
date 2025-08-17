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

    @patch("subprocess.run")
    def test_run_simple_command(self, mock_run):
        """Test running a simple command."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="output",
            stderr=""
        )

        result = run("echo test")

        assert result.returncode == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.cmd == "echo test"
        assert result.success is True

    @patch("subprocess.run")
    def test_run_list_command(self, mock_run):
        """Test running command as list."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="output",
            stderr=""
        )

        result = run(["echo", "test"])

        assert result.returncode == 0
        assert result.cmd == "echo test"

    @patch("subprocess.run")
    def test_run_with_env(self, mock_run):
        """Test running with environment variables."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        env = {"TEST_VAR": "value"}
        run("echo test", env=env)

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"] == env

    @patch("subprocess.run")
    def test_run_with_cwd(self, mock_run):
        """Test running with working directory."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            run("echo test", cwd=cwd)

            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cwd"] == cwd

    @patch("subprocess.run")
    def test_run_with_timeout(self, mock_run):
        """Test running with timeout."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        run("echo test", timeout=30)

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 30

    @patch("subprocess.run")
    def test_run_timeout_with_check(self, mock_run):
        """Test timeout with check=True raises TimeoutError."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)

        with pytest.raises(TimeoutError) as exc_info:
            run("sleep 10", timeout=5, check=True)

        assert "timed out after 5s" in str(exc_info.value)

    @patch("subprocess.run")
    def test_run_no_capture(self, mock_run):
        """Test running without capturing output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=None,
            stderr=None
        )

        result = run("echo test", capture=False)

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["stdout"] is None
        assert call_kwargs["stderr"] is None
        assert result.stdout == ""
        assert result.stderr == ""

    @patch("subprocess.run")
    def test_run_verbose(self, mock_run):
        """Test verbose mode prints command."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        with patch("builtins.print") as mock_print:
            run("echo test", verbose=True)
            mock_print.assert_called_once_with("Executing: echo test")

    @patch("subprocess.run")
    def test_run_check_error(self, mock_run):
        """Test check=True raises CalledProcessError on failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="output",
            stderr="error"
        )

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            run("false", check=True)

        assert exc_info.value.returncode == 1

    @patch("subprocess.run")
    def test_run_exception_handling(self, mock_run):
        """Test exception handling without check."""
        mock_run.side_effect = OSError("Command not found")

        result = run("nonexistent_command")

        assert result.returncode == -1
        assert "Command not found" in result.stderr
        assert result.success is False

    @patch("subprocess.run")
    def test_run_exception_with_check(self, mock_run):
        """Test exception with check=True re-raises."""
        mock_run.side_effect = OSError("Command not found")

        with pytest.raises(OSError):
            run("nonexistent_command", check=True)

    @patch("subprocess.run")
    def test_run_with_special_chars(self, mock_run):
        """Test command with special characters."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        result = run(["echo", "test with spaces"])

        # Command string is now consistent across platforms
        assert result.cmd == "echo test with spaces"

    @patch("subprocess.run")
    def test_run_duration_tracking(self, mock_run):
        """Test that duration is tracked."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        result = run("echo test")

        assert result.duration_sec >= 0
        assert isinstance(result.duration_sec, float)