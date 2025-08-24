"""Additional tests for detect module coverage gaps."""

import os
from unittest.mock import patch

from ovmobilebench.android.installer import detect


class TestDetectAdditional:
    """Test remaining gaps in detect module."""

    def test_detect_host_windows_32bit(self):
        """Test host detection on 32-bit Windows."""
        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="i386"):
                with patch(
                    "ovmobilebench.android.installer.detect.detect_java_version"
                ) as mock_java:
                    mock_java.return_value = "11.0.1"

                    host_info = detect.detect_host()

                    assert host_info.os == "windows"
                    assert host_info.arch == "x86"
                    assert host_info.has_kvm is False

    def test_detect_host_unsupported_arch(self):
        """Test host detection with unsupported architecture."""
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="riscv64"):
                with patch(
                    "ovmobilebench.android.installer.detect.detect_java_version"
                ) as mock_java:
                    mock_java.return_value = "17.0.1"

                    host_info = detect.detect_host()

                    # riscv64 is not normalized, so it remains as-is
                    assert host_info.arch == "riscv64"

    def test_is_ci_environment_edge_cases(self):
        """Test CI environment detection edge cases."""
        # Test with CI=true
        with patch.dict(os.environ, {"CI": "true"}):
            assert detect.is_ci_environment() is True

        # Test with CI=1
        with patch.dict(os.environ, {"CI": "1"}):
            assert detect.is_ci_environment() is True

        # Test with CONTINUOUS_INTEGRATION
        with patch.dict(os.environ, {"CONTINUOUS_INTEGRATION": "true"}):
            assert detect.is_ci_environment() is True
