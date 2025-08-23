"""Tests for emulator helper functionality."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add helpers directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "heplers"))

# Import and configure emulator_helper module
import emulator_helper

# Set ANDROID_HOME, AVD_HOME and ARCHITECTURE for all tests
emulator_helper.ANDROID_HOME = "/mock/android-sdk"
emulator_helper.AVD_HOME = "/mock/android-sdk/.android/avd"
emulator_helper.ARCHITECTURE = "arm64-v8a"  # Default for tests


class TestEmulatorHelper:
    """Test emulator management functions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Ensure ANDROID_HOME, AVD_HOME and ARCHITECTURE are set for all tests
        emulator_helper.ANDROID_HOME = "/mock/android-sdk"
        emulator_helper.AVD_HOME = "/mock/android-sdk/.android/avd"
        emulator_helper.ARCHITECTURE = "arm64-v8a"  # Default for tests

    def test_create_avd_with_default_name(self):
        """Test AVD creation with default naming."""
        from emulator_helper import create_avd

        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.mkdir"):  # Mock mkdir to avoid filesystem operations
                mock_run.return_value = Mock(returncode=0)

                create_avd(api_level=30)

                # Check that subprocess.run was called with correct parameters
                actual_call = mock_run.call_args
                expected_path = str(
                    Path("/mock/android-sdk") / "cmdline-tools" / "latest" / "bin" / "avdmanager"
                )
                assert actual_call[0][0][0] == expected_path
                assert "create" in actual_call[0][0]
                assert "avd" in actual_call[0][0]
                assert "ovmobilebench_avd_api30" in actual_call[0][0]
                assert "system-images;android-30;google_apis;arm64-v8a" in actual_call[0][0]
                assert actual_call[1]["input"] == "no\n"
                assert actual_call[1]["check"] is True

    def test_create_avd_with_custom_name(self):
        """Test AVD creation with custom name."""
        from emulator_helper import create_avd

        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.mkdir"):  # Mock mkdir to avoid filesystem operations
                mock_run.return_value = Mock(returncode=0)

                create_avd(api_level=34, avd_name="custom_avd")

                # Check that subprocess.run was called with correct parameters
                actual_call = mock_run.call_args
                expected_path = str(
                    Path("/mock/android-sdk") / "cmdline-tools" / "latest" / "bin" / "avdmanager"
                )
                assert actual_call[0][0][0] == expected_path
                assert "create" in actual_call[0][0]
                assert "avd" in actual_call[0][0]
                assert "custom_avd" in actual_call[0][0]
                assert "system-images;android-34;google_apis;arm64-v8a" in actual_call[0][0]
                assert actual_call[1]["input"] == "no\n"
                assert actual_call[1]["check"] is True

    def test_create_avd_failure(self):
        """Test AVD creation failure handling."""
        from emulator_helper import create_avd

        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.mkdir"):  # Mock mkdir to avoid filesystem operations
                mock_run.side_effect = subprocess.CalledProcessError(1, "avdmanager")

                with pytest.raises(subprocess.CalledProcessError):
                    create_avd(api_level=30)

    @patch("platform.system")
    def test_start_emulator_linux(self, mock_platform):
        """Test emulator start on Linux with KVM acceleration."""
        from emulator_helper import start_emulator

        mock_platform.return_value = "Linux"

        # Mock Path.exists to return True for emulator executable
        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                start_emulator(avd_name="test_avd", api_level=30)

                # Get the actual call
                actual_call = mock_popen.call_args[0][0]

                # Check key components
                expected_emulator = str(Path("/mock/android-sdk") / "emulator" / "emulator")
                assert expected_emulator in actual_call[0]
                assert "-avd" in actual_call
                assert "test_avd" in actual_call
                assert "-no-window" in actual_call

    @patch("platform.system")
    def test_start_emulator_macos(self, mock_platform):
        """Test emulator start on macOS with native acceleration."""
        from emulator_helper import start_emulator

        mock_platform.return_value = "Darwin"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                start_emulator(avd_name="test_avd", api_level=30)

                # Get the actual call
                actual_call = mock_popen.call_args[0][0]

                # Check key components
                expected_emulator = str(Path("/mock/android-sdk") / "emulator" / "emulator")
                assert expected_emulator in actual_call[0]
                assert "-avd" in actual_call
                assert "test_avd" in actual_call

    @patch("platform.system")
    def test_start_emulator_other_platform(self, mock_platform):
        """Test emulator start on other platforms (Windows)."""
        from emulator_helper import start_emulator

        mock_platform.return_value = "Windows"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                start_emulator(avd_name="test_avd", api_level=30)

                # Get the actual call
                actual_call = mock_popen.call_args[0][0]

                # Check key components
                expected_emulator = str(Path("/mock/android-sdk") / "emulator" / "emulator")
                assert expected_emulator in actual_call[0]
                assert "-avd" in actual_call
                assert "test_avd" in actual_call

    def test_wait_for_boot_success(self):
        """Test successful emulator boot wait."""
        from emulator_helper import wait_for_boot

        # Mock Path.exists for adb
        with patch("pathlib.Path.exists", return_value=True):
            # Mock subprocess.run to simulate successful boot
            with patch("subprocess.run") as mock_run:
                # Our new implementation makes these calls:
                # 1. adb devices (initial check)
                # 2. adb wait-for-device
                # 3. adb shell getprop sys.boot_completed
                mock_run.side_effect = [
                    Mock(
                        returncode=0, stdout="List of devices attached\nemulator-5554\tdevice\n"
                    ),  # adb devices
                    Mock(returncode=0),  # wait-for-device
                    Mock(returncode=0, stdout="1\n"),  # getprop sys.boot_completed
                ]

                with patch("time.sleep"):  # Speed up test
                    result = wait_for_boot(timeout=10)

                assert result is True
                # Should have called adb at least 3 times
                assert mock_run.call_count >= 3

    def test_wait_for_boot_timeout(self):
        """Test emulator boot timeout."""
        from emulator_helper import wait_for_boot

        with patch("subprocess.run") as mock_run:
            # Always return "1" (still booting)
            mock_run.return_value = Mock(returncode=0, stdout="1\n")

            with patch("time.sleep"):  # Speed up test
                with patch("builtins.print"):  # Suppress output
                    with patch("sys.exit") as mock_exit:
                        wait_for_boot(timeout=1)
                        mock_exit.assert_called_once_with(1)

    def test_wait_for_boot_adb_failure(self):
        """Test wait for boot with adb failure."""
        from emulator_helper import wait_for_boot

        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.run") as mock_run:
                # Simulate adb failure - keep returning error
                mock_run.return_value = Mock(returncode=1, stdout="")

                with patch("time.sleep"):  # Speed up test
                    # Provide enough time values for all calls, then jump to timeout
                    time_values = list(range(0, 20)) + [400] * 10  # Provide plenty of values
                    with patch("time.time", side_effect=time_values):  # Simulate timeout
                        result = wait_for_boot(timeout=10)

                assert result is False  # Should return False on timeout

    def test_stop_emulator(self):
        """Test emulator stop."""
        from emulator_helper import stop_emulator

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            stop_emulator()

            # Should call adb emu kill
            actual_call = mock_run.call_args[0][0]
            assert "adb" in actual_call[0]
            assert "emu" in actual_call
            assert "kill" in actual_call

    def test_delete_avd_with_default_name(self):
        """Test AVD deletion with default name."""
        from emulator_helper import delete_avd

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            delete_avd(api_level=30)

            actual_call = mock_run.call_args[0][0]
            expected_path = str(
                Path("/mock/android-sdk") / "cmdline-tools" / "latest" / "bin" / "avdmanager"
            )
            assert expected_path in actual_call[0]
            assert "delete" in actual_call
            assert "avd" in actual_call
            assert "-n" in actual_call
            assert "ovmobilebench_avd_api30" in actual_call

    def test_delete_avd_with_custom_name(self):
        """Test AVD deletion with custom name."""
        from emulator_helper import delete_avd

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            delete_avd(avd_name="custom_avd")

            actual_call = mock_run.call_args[0][0]
            expected_path = str(
                Path("/mock/android-sdk") / "cmdline-tools" / "latest" / "bin" / "avdmanager"
            )
            assert expected_path in actual_call[0]
            assert "delete" in actual_call
            assert "avd" in actual_call
            assert "-n" in actual_call
            assert "custom_avd" in actual_call

    def test_delete_avd_failure_handling(self):
        """Test AVD deletion failure handling."""
        from emulator_helper import delete_avd

        with patch("subprocess.run") as mock_run:
            # Since check=False, CalledProcessError won't be raised
            # Instead, return a failed result
            mock_run.return_value = Mock(returncode=1)

            # Should not raise exception
            delete_avd(api_level=30)

            # Should have attempted deletion
            assert mock_run.called
            # Check that check=False was passed
            assert mock_run.call_args[1].get("check") is False
