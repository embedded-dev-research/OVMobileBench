"""Additional tests for shell module coverage gaps."""

from unittest.mock import Mock, patch

from ovmobilebench.core.shell import run


class TestShellAdditional:
    """Test remaining gaps in shell module."""

    def test_run_with_very_long_output(self):
        """Test shell command with very long output."""
        # Create a command that generates lots of output
        with patch("subprocess.run") as mock_run:
            # Generate a very long output
            long_output = "x" * 200000  # 200KB
            mock_run.return_value = Mock(returncode=0, stdout=long_output, stderr="")

            result = run("echo test")

            # Verify output is returned as-is (no truncation in shell module)
            assert len(result.stdout) == len(long_output)
            assert result.stdout == long_output
