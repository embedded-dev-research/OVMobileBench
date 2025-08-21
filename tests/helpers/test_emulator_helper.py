"""Tests for emulator helper functionality."""

import subprocess

# Import from e2e helper scripts
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent / "tests" / "e2e"))

from test_emulator_helper import (
    create_avd,
    delete_avd,
    start_emulator,
    stop_emulator,
    wait_for_boot,
)


class TestEmulatorHelper:
    """Test emulator management functions."""

    def test_create_avd_with_default_name(self):
        """Test AVD creation with default naming."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            create_avd(api_level=30)

            expected_cmd = [
                "avdmanager",
                "create",
                "avd",
                "-n",
                "test_avd_api30",
                "-k",
                "system-images;android-30;google_apis;arm64-v8a",
                "-d",
                "pixel_5",
                "--force",
            ]
            mock_run.assert_called_once_with(expected_cmd, input="no\n", text=True, check=True)

    def test_create_avd_with_custom_name(self):
        """Test AVD creation with custom name."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            create_avd(api_level=34, avd_name="custom_avd")

            expected_cmd = [
                "avdmanager",
                "create",
                "avd",
                "-n",
                "custom_avd",
                "-k",
                "system-images;android-34;google_apis;arm64-v8a",
                "-d",
                "pixel_5",
                "--force",
            ]
            mock_run.assert_called_once_with(expected_cmd, input="no\n", text=True, check=True)

    def test_create_avd_failure(self):
        """Test AVD creation failure handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "avdmanager")

            with pytest.raises(subprocess.CalledProcessError):
                create_avd(api_level=30)

    @patch("platform.system")
    def test_start_emulator_linux(self, mock_platform):
        """Test emulator start on Linux with KVM acceleration."""
        mock_platform.return_value = "Linux"

        with patch("subprocess.Popen") as mock_popen:
            start_emulator(avd_name="test_avd", api_level=30)

            expected_cmd = [
                "emulator",
                "-avd",
                "test_avd",
                "-no-window",
                "-no-audio",
                "-no-boot-anim",
                "-gpu",
                "swiftshader_indirect",
                "-accel",
                "on",
                "-qemu",
                "-enable-kvm",
            ]
            mock_popen.assert_called_once_with(expected_cmd)

    @patch("platform.system")
    def test_start_emulator_macos(self, mock_platform):
        """Test emulator start on macOS with native acceleration."""
        mock_platform.return_value = "Darwin"

        with patch("subprocess.Popen") as mock_popen:
            start_emulator(avd_name="test_avd", api_level=30)

            expected_cmd = [
                "emulator",
                "-avd",
                "test_avd",
                "-no-window",
                "-no-audio",
                "-no-boot-anim",
                "-gpu",
                "swiftshader_indirect",
                "-accel",
                "on",
            ]
            mock_popen.assert_called_once_with(expected_cmd)

    @patch("platform.system")
    def test_start_emulator_other_platform(self, mock_platform):
        """Test emulator start on other platforms without hardware acceleration."""
        mock_platform.return_value = "Windows"

        with patch("subprocess.Popen") as mock_popen:
            start_emulator()

            expected_cmd = [
                "emulator",
                "-avd",
                "test_avd_api30",
                "-no-window",
                "-no-audio",
                "-no-boot-anim",
                "-gpu",
                "swiftshader_indirect",
            ]
            mock_popen.assert_called_once_with(expected_cmd)

    def test_wait_for_boot_success(self):
        """Test successful boot waiting."""
        with patch("subprocess.run") as mock_run:
            # First call: adb wait-for-device succeeds
            # Second call: getprop returns "1" indicating boot completed
            mock_run.side_effect = [
                Mock(returncode=0),  # adb wait-for-device
                Mock(returncode=0, stdout="1\n"),  # getprop sys.boot_completed
            ]

            with patch("time.time", side_effect=[0, 10]):  # Mock time progression
                result = wait_for_boot()

            assert result is True
            assert mock_run.call_count == 2

    def test_wait_for_boot_timeout(self):
        """Test boot waiting timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0),  # adb wait-for-device
                Mock(returncode=0, stdout="0\n"),  # getprop returns "0"
            ] * 100  # Simulate many failed attempts

            with patch("time.time", side_effect=range(0, 400, 10)):  # Mock timeout
                with patch("time.sleep"):
                    result = wait_for_boot(timeout=300)

            assert result is False

    def test_wait_for_boot_adb_failure(self):
        """Test boot waiting with ADB connection failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)  # adb wait-for-device fails

            with patch("time.time", side_effect=range(0, 400, 10)):
                with patch("time.sleep"):
                    result = wait_for_boot(timeout=300)

            assert result is False

    def test_stop_emulator(self):
        """Test emulator stop functionality."""
        with patch("subprocess.run") as mock_run:
            with patch("time.sleep") as mock_sleep:
                stop_emulator()

                mock_run.assert_called_once_with(["adb", "emu", "kill"], check=False)
                mock_sleep.assert_called_once_with(2)

    def test_delete_avd_with_default_name(self):
        """Test AVD deletion with default naming."""
        with patch("subprocess.run") as mock_run:
            delete_avd(api_level=30)

            mock_run.assert_called_once_with(
                ["avdmanager", "delete", "avd", "-n", "test_avd_api30"], check=False
            )

    def test_delete_avd_with_custom_name(self):
        """Test AVD deletion with custom name."""
        with patch("subprocess.run") as mock_run:
            delete_avd(avd_name="custom_avd", api_level=30)

            mock_run.assert_called_once_with(
                ["avdmanager", "delete", "avd", "-n", "custom_avd"], check=False
            )

    def test_delete_avd_failure_handling(self):
        """Test AVD deletion continues even if command fails."""
        with patch("subprocess.run") as mock_run:
            # Since check=False is used in the actual function, exceptions won't be raised
            mock_run.return_value = Mock(returncode=1)

            # Should not raise exception due to check=False
            delete_avd(api_level=30)

            mock_run.assert_called_once()


class TestEmulatorHelperCLI:
    """Test emulator helper CLI functionality."""

    def test_main_create_avd_command(self):
        """Test CLI create-avd command."""
        with patch("test_emulator_helper.create_avd") as mock_create:
            with patch(
                "sys.argv",
                ["test_emulator_helper.py", "create-avd", "--api", "34", "--name", "test"],
            ):
                from test_emulator_helper import main

                main()

                mock_create.assert_called_once_with(34, "test")

    def test_main_start_emulator_command(self):
        """Test CLI start-emulator command."""
        with patch("test_emulator_helper.start_emulator") as mock_start:
            with patch(
                "sys.argv",
                ["test_emulator_helper.py", "start-emulator", "--name", "test", "--api", "30"],
            ):
                from test_emulator_helper import main

                main()

                mock_start.assert_called_once_with("test", 30)

    def test_main_wait_for_boot_success(self):
        """Test CLI wait-for-boot command success."""
        with patch("test_emulator_helper.wait_for_boot", return_value=True):
            with patch("sys.argv", ["test_emulator_helper.py", "wait-for-boot"]):
                with patch("sys.exit") as mock_exit:
                    from test_emulator_helper import main

                    main()

                    mock_exit.assert_not_called()

    def test_main_wait_for_boot_failure(self):
        """Test CLI wait-for-boot command failure."""
        with patch("test_emulator_helper.wait_for_boot", return_value=False):
            with patch("sys.argv", ["test_emulator_helper.py", "wait-for-boot"]):
                with pytest.raises(SystemExit) as exc_info:
                    from test_emulator_helper import main

                    main()

                assert exc_info.value.code == 1

    def test_main_stop_emulator_command(self):
        """Test CLI stop-emulator command."""
        with patch("test_emulator_helper.stop_emulator") as mock_stop:
            with patch("sys.argv", ["test_emulator_helper.py", "stop-emulator"]):
                from test_emulator_helper import main

                main()

                mock_stop.assert_called_once()

    def test_main_delete_avd_command(self):
        """Test CLI delete-avd command."""
        with patch("test_emulator_helper.delete_avd") as mock_delete:
            with patch(
                "sys.argv",
                ["test_emulator_helper.py", "delete-avd", "--name", "test", "--api", "30"],
            ):
                from test_emulator_helper import main

                main()

                mock_delete.assert_called_once_with("test", 30)

    def test_main_no_command(self):
        """Test CLI with no command shows help."""
        with patch("sys.argv", ["test_emulator_helper.py"]):
            with patch("argparse.ArgumentParser.print_help") as mock_help:
                from test_emulator_helper import main

                main()

                mock_help.assert_called_once()
