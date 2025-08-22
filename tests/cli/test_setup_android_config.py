"""Test setup-android command with config support."""

from unittest.mock import MagicMock, patch

import yaml
from typer.testing import CliRunner

from ovmobilebench.cli import app

runner = CliRunner()


class TestSetupAndroidWithConfig:
    """Test setup-android command with configuration file."""

    def test_setup_android_reads_config(self, tmp_path):
        """Test that setup-android reads SDK location from config."""
        # Create a test config with x86_64 architecture
        config_data = {
            "project": {
                "name": "test",
                "run_id": "test_001",
                "cache_dir": str(tmp_path / "test_cache"),
            },
            "openvino": {
                "mode": "build",
                "toolchain": {
                    "abi": "x86_64",  # Specify architecture to match what we check
                    "api_level": 30,
                },
            },
            "device": {"kind": "android", "serials": []},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
            with patch("ovmobilebench.android.installer.api.ensure_android_tools") as mock_ensure:
                # Mock verification to say everything is installed (with x86_64)
                mock_verify.return_value = {
                    "platform_tools": True,
                    "emulator": True,
                    "system_images": ["system-images;android-30;google_apis;x86_64"],
                    "ndk_versions": ["27.2.12479018"],
                }

                result = runner.invoke(
                    app,
                    ["setup-android", "-c", str(config_file), "--api", "30"],
                )

                assert result.exit_code == 0
                # Remove newlines from output for path checking (Rich formatting can split paths)
                stdout_oneline = result.stdout.replace("\n", " ")
                assert "test_cache/android-sdk" in stdout_oneline
                assert "All required Android components are already installed" in result.stdout

                # Should not call ensure_android_tools since everything is installed
                mock_ensure.assert_not_called()

    def test_setup_android_installs_missing_components(self, tmp_path):
        """Test that setup-android installs only missing components."""
        # Create a test config with x86_64 architecture
        config_data = {
            "project": {
                "name": "test",
                "run_id": "test_001",
                "cache_dir": str(tmp_path / "test_cache"),
            },
            "openvino": {
                "mode": "build",
                "toolchain": {
                    "abi": "x86_64",
                    "api_level": 30,
                },
            },
            "device": {"kind": "android", "serials": []},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
            with patch("ovmobilebench.android.installer.api.ensure_android_tools") as mock_ensure:
                # Mock verification to say NDK is missing
                mock_verify.return_value = {
                    "platform_tools": True,
                    "emulator": True,
                    "system_images": ["system-images;android-30;google_apis;x86_64"],
                    "ndk_versions": [],  # NDK missing
                }

                mock_ensure.return_value = {
                    "sdk_root": str(tmp_path / "test_cache" / "android-sdk"),
                    "ndk_path": str(
                        tmp_path / "test_cache" / "android-sdk" / "ndk" / "27.2.12479018"
                    ),
                }

                result = runner.invoke(
                    app,
                    ["setup-android", "-c", str(config_file), "--api", "30"],
                )

                assert result.exit_code == 0
                assert "Missing components: NDK" in result.stdout
                assert "Installing missing components" in result.stdout

                # Should call ensure_android_tools to install missing NDK
                mock_ensure.assert_called_once()

    def test_setup_android_with_override_params(self, tmp_path):
        """Test that command line params override config values."""
        # Create a test config
        config_data = {
            "project": {
                "name": "test",
                "run_id": "test_001",
                "cache_dir": str(tmp_path / "config_cache"),
            },
            "openvino": {"mode": "build"},
            "device": {"kind": "android", "serials": []},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        override_sdk = tmp_path / "override_sdk"

        with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
            with patch("ovmobilebench.android.installer.api.ensure_android_tools") as mock_ensure:
                mock_verify.return_value = {
                    "platform_tools": True,
                    "emulator": True,
                    "system_images": [],
                    "ndk_versions": ["27.2.12479018"],
                }

                mock_ensure.return_value = {
                    "sdk_root": str(override_sdk),
                    "ndk_path": str(override_sdk / "ndk" / "27.2.12479018"),
                }

                result = runner.invoke(
                    app,
                    [
                        "setup-android",
                        "-c",
                        str(config_file),
                        "--sdk-root",
                        str(override_sdk),
                        "--api",
                        "30",
                    ],
                )

                assert result.exit_code == 0
                # Check that override SDK path was used
                mock_ensure.assert_called_once()
                call_args = mock_ensure.call_args
                assert call_args[1]["sdk_root"] == override_sdk

    def test_setup_android_without_config_fallback(self, tmp_path):
        """Test that setup-android works without config file."""
        nonexistent_config = tmp_path / "nonexistent.yaml"

        with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
            with patch("ovmobilebench.android.installer.api.ensure_android_tools") as mock_ensure:
                with patch("ovmobilebench.config.loader.get_project_root") as mock_root:
                    mock_root.return_value = tmp_path
                    mock_verify.return_value = {
                        "platform_tools": False,
                        "emulator": False,
                        "system_images": [],
                        "ndk_versions": [],
                    }
                    mock_ensure.return_value = MagicMock(returncode=0)

                    result = runner.invoke(
                        app,
                        ["setup-android", "-c", str(nonexistent_config), "--api", "30"],
                    )

                    assert result.exit_code == 0
                    assert "Could not load config" in result.stdout
                    assert "Using default SDK location" in result.stdout

                    # Should still proceed with installation
                    mock_ensure.assert_called_once()

    def test_setup_android_checks_all_components(self, tmp_path):
        """Test that setup-android checks all required components."""
        config_data = {
            "project": {
                "name": "test",
                "run_id": "test_001",
                "cache_dir": str(tmp_path / "test_cache"),
            },
            "openvino": {"mode": "build"},
            "device": {"kind": "android", "serials": []},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
            with patch("ovmobilebench.android.installer.api.ensure_android_tools") as mock_ensure:
                # Mock verification to say multiple components are missing
                mock_verify.return_value = {
                    "platform_tools": False,  # Missing
                    "emulator": False,  # Missing
                    "system_images": [],  # Missing
                    "ndk_versions": [],  # Missing
                }

                mock_ensure.return_value = MagicMock(returncode=0)

                result = runner.invoke(
                    app,
                    ["setup-android", "-c", str(config_file), "--api", "30", "--create-avd"],
                )

                assert result.exit_code == 0
                assert "Missing components:" in result.stdout
                assert "platform-tools" in result.stdout
                assert "emulator" in result.stdout
                assert "system-image (API 30)" in result.stdout
                assert "NDK" in result.stdout

                # Should install everything
                mock_ensure.assert_called_once()

    def test_setup_android_skip_avd_when_not_needed(self, tmp_path):
        """Test that setup-android doesn't require system image when AVD not needed."""
        config_data = {
            "project": {
                "name": "test",
                "run_id": "test_001",
                "cache_dir": str(tmp_path / "test_cache"),
            },
            "openvino": {"mode": "build"},
            "device": {"kind": "android", "serials": ["device-123"]},  # Physical device
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
            with patch("ovmobilebench.android.installer.api.ensure_android_tools") as mock_ensure:
                # No system images but other components present
                mock_verify.return_value = {
                    "platform_tools": True,
                    "emulator": True,
                    "system_images": [],  # No system images
                    "ndk_versions": ["27.2.12479018"],
                }

                result = runner.invoke(
                    app,
                    ["setup-android", "-c", str(config_file), "--api", "30"],
                    # Note: no --create-avd flag, so system images not required
                )

                assert result.exit_code == 0
                # Should recognize that all required components are installed
                # (system images not required when no AVD creation requested)
                assert "All required Android components are already installed" in result.stdout

                # Should not call ensure_android_tools since all required components present
                mock_ensure.assert_not_called()
