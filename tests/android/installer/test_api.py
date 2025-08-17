"""Tests for public API functions."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ovmobilebench.android.installer.api import (
    ensure_android_tools,
    export_android_env,
    verify_installation,
)
from ovmobilebench.android.installer.types import NdkSpec, InstallerResult


class TestEnsureAndroidTools:
    """Test ensure_android_tools function."""

    @patch("ovmobilebench.android.installer.api.AndroidInstaller")
    @patch("ovmobilebench.android.installer.api.get_logger")
    def test_ensure_android_tools_basic(self, mock_get_logger, mock_installer_class):
        """Test basic ensure_android_tools call."""
        # Setup mocks
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer

        expected_result = InstallerResult(
            sdk_root=Path("/opt/sdk"),
            ndk_path=Path("/opt/sdk/ndk/r26d"),
            avd_created=False,
            performed={"test": True},
        )
        mock_installer.ensure.return_value = expected_result

        # Call function
        result = ensure_android_tools(
            sdk_root=Path("/opt/sdk"),
            api=30,
            target="google_atd",
            arch="arm64-v8a",
            ndk=NdkSpec(alias="r26d"),
        )

        # Verify
        assert result == expected_result
        mock_get_logger.assert_called_once_with(verbose=False, jsonl_path=None)
        mock_installer_class.assert_called_once_with(
            Path("/opt/sdk"),
            logger=mock_logger,
            verbose=False,
        )
        mock_installer.ensure.assert_called_once()
        mock_logger.close.assert_called_once()

    @patch("ovmobilebench.android.installer.api.AndroidInstaller")
    @patch("ovmobilebench.android.installer.api.get_logger")
    def test_ensure_android_tools_with_options(self, mock_get_logger, mock_installer_class):
        """Test ensure_android_tools with all options."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer

        expected_result = InstallerResult(
            sdk_root=Path("/opt/sdk"),
            ndk_path=Path("/opt/sdk/ndk/r26d"),
            avd_created=True,
            performed={"all": True},
        )
        mock_installer.ensure.return_value = expected_result

        # Call with all options
        result = ensure_android_tools(
            sdk_root=Path("/opt/sdk"),
            api=33,
            target="google_apis",
            arch="x86_64",
            ndk=NdkSpec(alias="r25c"),
            install_platform_tools=False,
            install_emulator=False,
            install_build_tools="34.0.0",
            create_avd_name="test_avd",
            accept_licenses=False,
            dry_run=True,
            verbose=True,
            jsonl_log=Path("/tmp/log.jsonl"),
        )

        # Verify options passed correctly
        assert result == expected_result
        mock_get_logger.assert_called_once_with(
            verbose=True,
            jsonl_path=Path("/tmp/log.jsonl"),
        )
        mock_installer.ensure.assert_called_once_with(
            api=33,
            target="google_apis",
            arch="x86_64",
            ndk=NdkSpec(alias="r25c"),
            install_platform_tools=False,
            install_emulator=False,
            install_build_tools="34.0.0",
            create_avd_name="test_avd",
            accept_licenses=False,
            dry_run=True,
        )

    @patch("ovmobilebench.android.installer.api.AndroidInstaller")
    @patch("ovmobilebench.android.installer.api.get_logger")
    def test_ensure_android_tools_exception_handling(self, mock_get_logger, mock_installer_class):
        """Test that logger is closed even on exception."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer
        mock_installer.ensure.side_effect = Exception("Test error")

        # Call should raise exception
        with pytest.raises(Exception, match="Test error"):
            ensure_android_tools(
                sdk_root=Path("/opt/sdk"),
                api=30,
                target="google_atd",
                arch="arm64-v8a",
                ndk=NdkSpec(alias="r26d"),
            )

        # Logger should still be closed
        mock_logger.close.assert_called_once()


class TestExportAndroidEnv:
    """Test export_android_env function."""

    @patch("ovmobilebench.android.installer.api._export_android_env")
    def test_export_android_env(self, mock_export):
        """Test export_android_env function."""
        expected_vars = {
            "ANDROID_SDK_ROOT": "/opt/sdk",
            "ANDROID_NDK": "/opt/sdk/ndk/r26d",
        }
        mock_export.return_value = expected_vars

        result = export_android_env(
            github_env=Path("/tmp/github_env"),
            print_stdout=True,
            sdk_root=Path("/opt/sdk"),
            ndk_path=Path("/opt/sdk/ndk/r26d"),
        )

        assert result == expected_vars
        mock_export.assert_called_once_with(
            github_env=Path("/tmp/github_env"),
            print_stdout=True,
            sdk_root=Path("/opt/sdk"),
            ndk_path=Path("/opt/sdk/ndk/r26d"),
        )


class TestVerifyInstallation:
    """Test verify_installation function."""

    @patch("ovmobilebench.android.installer.api.AndroidInstaller")
    @patch("ovmobilebench.android.installer.api.get_logger")
    def test_verify_installation_verbose(self, mock_get_logger, mock_installer_class):
        """Test verify_installation with verbose mode."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer

        expected_status = {
            "sdk_root_exists": True,
            "cmdline_tools": True,
            "platform_tools": True,
            "emulator": False,
            "ndk": True,
            "ndk_versions": ["r26d"],
            "avds": ["test_avd"],
        }
        mock_installer.verify.return_value = expected_status

        result = verify_installation(Path("/opt/sdk"), verbose=True)

        assert result == expected_status
        mock_get_logger.assert_called_once_with(verbose=True)
        mock_installer_class.assert_called_once_with(
            Path("/opt/sdk"),
            logger=mock_logger,
            verbose=True,
        )
        mock_installer.verify.assert_called_once()

    @patch("ovmobilebench.android.installer.api.AndroidInstaller")
    def test_verify_installation_quiet(self, mock_installer_class):
        """Test verify_installation without verbose mode."""
        mock_installer = Mock()
        mock_installer_class.return_value = mock_installer

        expected_status = {
            "sdk_root_exists": False,
            "cmdline_tools": False,
            "platform_tools": False,
            "emulator": False,
            "ndk": False,
            "avds": [],
        }
        mock_installer.verify.return_value = expected_status

        result = verify_installation(Path("/opt/sdk"), verbose=False)

        assert result == expected_status
        mock_installer_class.assert_called_once_with(
            Path("/opt/sdk"),
            logger=None,
            verbose=False,
        )
        mock_installer.verify.assert_called_once()
