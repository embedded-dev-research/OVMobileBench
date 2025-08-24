"""Additional tests for EnvExporter coverage gaps."""

import os
from unittest.mock import patch

from ovmobilebench.android.installer.env import EnvExporter


class TestEnvExporterAdditional:
    """Test remaining gaps in EnvExporter."""

    def test_export_to_github_env_with_file(self, tmp_path):
        """Test exporting to GitHub Actions environment file."""
        env_file = tmp_path / "github_env"
        sdk_root = tmp_path / "sdk"
        ndk_path = tmp_path / "ndk"

        # Create the directories so they exist
        sdk_root.mkdir()
        ndk_path.mkdir()

        exporter = EnvExporter()
        exporter.export(
            github_env=env_file,
            sdk_root=sdk_root,
            ndk_path=ndk_path,
        )

        # Check file was written
        with open(env_file) as f:
            content = f.read()
            assert str(sdk_root) in content
            assert "ANDROID_HOME=" in content
            assert "ANDROID_SDK_ROOT=" in content

    def test_export_to_stdout_formats(self, tmp_path):
        """Test export to stdout with different shell formats."""
        import platform

        exporter = EnvExporter()

        # Create test directories
        sdk_root = tmp_path / "sdk"
        sdk_root.mkdir()

        # Test bash format (default)
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            with patch("builtins.print") as mock_print:
                exporter.export(
                    print_stdout=True,
                    sdk_root=sdk_root,
                )
                calls = [str(call) for call in mock_print.call_args_list]
                # On Windows, check for SET instead of export
                if platform.system() == "Windows":
                    assert any("ANDROID_HOME" in call for call in calls)
                else:
                    assert any("export ANDROID_HOME" in call for call in calls)

        # Test fish format
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            with patch("builtins.print") as mock_print:
                exporter.export(
                    print_stdout=True,
                    sdk_root=sdk_root,
                )
                calls = [str(call) for call in mock_print.call_args_list]
                assert any("set -x ANDROID_HOME" in call for call in calls)

        # Test Windows format
        with patch("sys.platform", "win32"):
            with patch("builtins.print") as mock_print:
                exporter.export(
                    print_stdout=True,
                    sdk_root=sdk_root,
                )
                calls = [str(call) for call in mock_print.call_args_list]
                assert any("set ANDROID_HOME" in call for call in calls)

    def test_save_and_load(self, tmp_path):
        """Test saving environment configuration to file."""
        config_file = tmp_path / "android_env.sh"

        # Create test directories
        sdk_root = tmp_path / "sdk"
        ndk_path = tmp_path / "ndk"
        sdk_root.mkdir()
        ndk_path.mkdir()

        # Save
        exporter = EnvExporter()
        env_vars = exporter.export(
            sdk_root=sdk_root,
            ndk_path=ndk_path,
        )

        # Write to file manually (simulating save_to_file)
        exporter.save_to_file(config_file, env_vars)

        assert config_file.exists()
        content = config_file.read_text()
        assert str(sdk_root) in content
        assert str(ndk_path) in content
