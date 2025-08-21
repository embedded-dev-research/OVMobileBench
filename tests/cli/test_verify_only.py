"""Tests for --verify-only CLI functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from ovmobilebench.cli import setup_android


class TestVerifyOnlyFunctionality:
    """Test --verify-only CLI option."""

    def test_verify_only_success(self):
        """Test successful verification of existing installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Mock verification result showing all components present
            mock_verification_result = {
                "platform_tools": True,
                "emulator": True,
                "system_images": ["system-images;android-34;google_apis;arm64-v8a"],
                "ndk_versions": ["26.3.11579264"],
            }

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch("ovmobilebench.cli.console") as mock_console:
                    # Should complete successfully without raising SystemExit
                    setup_android(
                        api_level=34,
                        create_avd=False,
                        sdk_root=sdk_root,
                        verify_only=True,
                        verbose=False,
                    )

                    # Verify success messages were printed
                    success_calls = [
                        call
                        for call in mock_console.print.call_args_list
                        if "All required Android components are installed" in str(call)
                    ]
                    assert len(success_calls) > 0

                    # Verify SDK root was displayed
                    sdk_calls = [
                        call
                        for call in mock_console.print.call_args_list
                        if str(sdk_root) in str(call)
                    ]
                    assert len(sdk_calls) > 0

    def test_verify_only_missing_platform_tools(self):
        """Test verification failure when platform-tools are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Mock verification result missing platform_tools
            mock_verification_result = {
                "platform_tools": False,
                "emulator": True,
                "system_images": ["system-images;android-34;google_apis;arm64-v8a"],
                "ndk_versions": ["26.3.11579264"],
            }

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch("ovmobilebench.cli.console") as mock_console:
                    with pytest.raises(typer.Exit) as exc_info:
                        setup_android(
                            api_level=34,
                            create_avd=False,
                            sdk_root=sdk_root,
                            verify_only=True,
                            verbose=False,
                        )

                    # Should exit with code 1
                    assert exc_info.value.exit_code == 1

                    # Verify failure message was printed
                    failure_calls = [
                        call
                        for call in mock_console.print.call_args_list
                        if "platform_tools" in str(call) and "Missing components" in str(call)
                    ]
                    assert len(failure_calls) > 0

    def test_verify_only_missing_emulator(self):
        """Test verification failure when emulator is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Mock verification result missing emulator
            mock_verification_result = {
                "platform_tools": True,
                "emulator": False,
                "system_images": ["system-images;android-34;google_apis;arm64-v8a"],
                "ndk_versions": ["26.3.11579264"],
            }

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch("ovmobilebench.cli.console") as mock_console:
                    with pytest.raises(typer.Exit) as exc_info:
                        setup_android(
                            api_level=34,
                            create_avd=False,
                            sdk_root=sdk_root,
                            verify_only=True,
                            verbose=False,
                        )

                    # Should exit with code 1
                    assert exc_info.value.exit_code == 1

                    # Verify failure message contains emulator
                    failure_calls = [
                        call
                        for call in mock_console.print.call_args_list
                        if "emulator" in str(call) and "Missing components" in str(call)
                    ]
                    assert len(failure_calls) > 0

    def test_verify_only_missing_system_image(self):
        """Test verification failure when system image is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Mock verification result missing system image for API 34
            mock_verification_result = {
                "platform_tools": True,
                "emulator": True,
                "system_images": [
                    "system-images;android-30;google_apis;arm64-v8a"
                ],  # Wrong API level
                "ndk_versions": ["26.3.11579264"],
            }

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch("ovmobilebench.cli.console") as mock_console:
                    with pytest.raises(typer.Exit) as exc_info:
                        setup_android(
                            api_level=34,
                            create_avd=False,
                            sdk_root=sdk_root,
                            verify_only=True,
                            verbose=False,
                        )

                    # Should exit with code 1
                    assert exc_info.value.exit_code == 1

                    # Verify failure message contains system image reference
                    failure_calls = [
                        call
                        for call in mock_console.print.call_args_list
                        if "system-image-api34" in str(call)
                    ]
                    assert len(failure_calls) > 0

    def test_verify_only_missing_ndk(self):
        """Test verification failure when NDK is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Mock verification result missing NDK
            mock_verification_result = {
                "platform_tools": True,
                "emulator": True,
                "system_images": ["system-images;android-34;google_apis;arm64-v8a"],
                "ndk_versions": [],  # No NDK installed
            }

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch("ovmobilebench.cli.console") as mock_console:
                    with pytest.raises(typer.Exit) as exc_info:
                        setup_android(
                            api_level=34,
                            create_avd=False,
                            sdk_root=sdk_root,
                            verify_only=True,
                            verbose=False,
                        )

                    # Should exit with code 1
                    assert exc_info.value.exit_code == 1

                    # Verify failure message contains NDK
                    failure_calls = [
                        call
                        for call in mock_console.print.call_args_list
                        if "ndk" in str(call) and "Missing components" in str(call)
                    ]
                    assert len(failure_calls) > 0

    def test_verify_only_multiple_missing_components(self):
        """Test verification failure with multiple missing components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Mock verification result missing multiple components
            mock_verification_result = {
                "platform_tools": False,
                "emulator": False,
                "system_images": [],
                "ndk_versions": [],
            }

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch("ovmobilebench.cli.console") as mock_console:
                    with pytest.raises(typer.Exit) as exc_info:
                        setup_android(
                            api_level=34,
                            create_avd=False,
                            sdk_root=sdk_root,
                            verify_only=True,
                            verbose=False,
                        )

                    # Should exit with code 1
                    assert exc_info.value.exit_code == 1

                    # Verify failure message contains all missing components
                    failure_calls = mock_console.print.call_args_list
                    failure_text = " ".join(str(call) for call in failure_calls)

                    assert "platform_tools" in failure_text
                    assert "emulator" in failure_text
                    assert "system-image-api34" in failure_text
                    assert "ndk" in failure_text

    def test_verify_only_with_verbose_flag(self):
        """Test verification with verbose logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            mock_verification_result = {
                "platform_tools": True,
                "emulator": True,
                "system_images": ["system-images;android-34;google_apis;arm64-v8a"],
                "ndk_versions": ["26.3.11579264"],
            }

            with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
                mock_verify.return_value = mock_verification_result
                with patch("ovmobilebench.cli.console"):
                    setup_android(
                        api_level=34,
                        create_avd=False,
                        sdk_root=sdk_root,
                        verify_only=True,
                        verbose=True,
                    )

                    # Verify verify_installation was called with verbose=True
                    mock_verify.assert_called_once_with(sdk_root, verbose=True)

    def test_verify_only_different_api_levels(self):
        """Test verification with different API levels."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Test API 30
            mock_verification_result = {
                "platform_tools": True,
                "emulator": True,
                "system_images": ["system-images;android-30;google_apis;arm64-v8a"],
                "ndk_versions": ["26.3.11579264"],
            }

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch("ovmobilebench.cli.console"):
                    setup_android(
                        api_level=30,
                        create_avd=False,
                        sdk_root=sdk_root,
                        verify_only=True,
                        verbose=False,
                    )
                    # Should succeed for API 30

            # Test API 31 (should fail with same system images)
            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch("ovmobilebench.cli.console"):
                    with pytest.raises(typer.Exit):
                        setup_android(
                            api_level=31,
                            create_avd=False,
                            sdk_root=sdk_root,
                            verify_only=True,
                            verbose=False,
                        )

    def test_verify_only_verification_exception(self):
        """Test handling of verification exceptions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                side_effect=Exception("Verification error"),
            ):
                with patch("ovmobilebench.cli.console") as mock_console:
                    with pytest.raises(typer.Exit) as exc_info:
                        setup_android(
                            api_level=34,
                            create_avd=False,
                            sdk_root=sdk_root,
                            verify_only=True,
                            verbose=False,
                        )

                    # Should exit with code 1
                    assert exc_info.value.exit_code == 1

                    # Verify error message was printed
                    error_calls = [
                        call
                        for call in mock_console.print.call_args_list
                        if "Verification failed" in str(call) and "Verification error" in str(call)
                    ]
                    assert len(error_calls) > 0

    def test_verify_only_does_not_trigger_installation(self):
        """Test that verify-only mode never triggers installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Mock verification result showing missing components
            mock_verification_result = {
                "platform_tools": False,
                "emulator": False,
                "system_images": [],
                "ndk_versions": [],
            }

            with patch(
                "ovmobilebench.android.installer.api.verify_installation",
                return_value=mock_verification_result,
            ):
                with patch(
                    "ovmobilebench.android.installer.api.ensure_android_tools"
                ) as mock_ensure:
                    with patch("ovmobilebench.cli.console"):
                        with pytest.raises(typer.Exit):
                            setup_android(
                                api_level=34,
                                create_avd=True,
                                sdk_root=sdk_root,
                                verify_only=True,
                                verbose=False,
                            )

                        # Verify installation was never called
                        mock_ensure.assert_not_called()

    def test_verify_only_sdk_root_default(self):
        """Test verify-only with default SDK root path."""
        # Mock verification result
        mock_verification_result = {
            "platform_tools": True,
            "emulator": True,
            "system_images": ["system-images;android-34;google_apis;arm64-v8a"],
            "ndk_versions": ["26.3.11579264"],
        }

        with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
            mock_verify.return_value = mock_verification_result
            with patch("ovmobilebench.cli.console"):
                with patch.dict("os.environ", {}, clear=True):  # Clear ANDROID_HOME
                    setup_android(
                        api_level=34,
                        create_avd=False,
                        sdk_root=None,  # Use default
                        verify_only=True,
                        verbose=False,
                    )

                    # Verify verify_installation was called with default path
                    expected_path = Path("/opt/android-sdk")
                    mock_verify.assert_called_once_with(expected_path, verbose=False)

    def test_verify_only_with_android_home_env(self):
        """Test verify-only with ANDROID_HOME environment variable."""
        mock_verification_result = {
            "platform_tools": True,
            "emulator": True,
            "system_images": ["system-images;android-34;google_apis;arm64-v8a"],
            "ndk_versions": ["26.3.11579264"],
        }

        custom_android_home = "/custom/android/sdk"

        with patch("ovmobilebench.android.installer.api.verify_installation") as mock_verify:
            mock_verify.return_value = mock_verification_result
            with patch("ovmobilebench.cli.console"):
                with patch.dict("os.environ", {"ANDROID_HOME": custom_android_home}):
                    setup_android(
                        api_level=34,
                        create_avd=False,
                        sdk_root=None,  # Use default (should read from env)
                        verify_only=True,
                        verbose=False,
                    )

                    # Verify verify_installation was called with env path
                    expected_path = Path(custom_android_home)
                    mock_verify.assert_called_once_with(expected_path, verbose=False)
