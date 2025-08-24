"""Additional tests for installer core coverage gaps."""

from unittest.mock import Mock, patch

import pytest

from ovmobilebench.android.installer.core import AndroidInstaller


class TestInstallerCoreAdditional:
    """Test remaining gaps in installer core."""

    def test_check_permissions_failure_with_details(self, tmp_path):
        """Test permission check failure with specific error."""
        import platform

        # Skip on Windows as chmod doesn't work the same way
        if platform.system() == "Windows":
            pytest.skip("Permission test not applicable on Windows")

        sdk_root = tmp_path / "android-sdk"
        sdk_root.mkdir()

        # Make directory non-writable
        sdk_root.chmod(0o444)

        try:
            with patch("ovmobilebench.android.installer.logging.get_logger") as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                installer = AndroidInstaller(sdk_root=sdk_root)

                with pytest.raises(PermissionError):
                    installer._check_permissions()
        finally:
            # Restore permissions for cleanup
            sdk_root.chmod(0o755)

    def test_cleanup_with_error_handling(self, tmp_path):
        """Test cleanup with error during removal."""
        sdk_root = tmp_path / "android-sdk"
        sdk_root.mkdir()

        # Create temp directory to trigger rmtree
        temp_dir = sdk_root / "temp"
        temp_dir.mkdir()

        with patch("ovmobilebench.android.installer.logging.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            installer = AndroidInstaller(sdk_root=sdk_root)

            # Mock shutil.rmtree to raise error - this will crash if not handled
            with patch("shutil.rmtree", side_effect=OSError("Permission denied")):
                # Should raise the OSError since there's no error handling in cleanup
                with pytest.raises(OSError):
                    installer.cleanup(remove_downloads=False, remove_temp=True)

    def test_ensure_with_logging(self, tmp_path):
        """Test ensure method with detailed logging."""
        sdk_root = tmp_path / "android-sdk"
        sdk_root.mkdir()

        mock_logger = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_logger.step = Mock(return_value=mock_context)

        with patch("ovmobilebench.android.installer.core.Planner") as mock_planner:
            mock_plan = Mock()
            mock_plan.has_work = Mock(return_value=False)
            mock_planner.return_value.build_plan.return_value = mock_plan

            installer = AndroidInstaller(sdk_root=sdk_root, logger=mock_logger)
            from ovmobilebench.android.installer.types import NdkSpec

            installer.ensure(
                api=30,
                target="google_atd",
                arch="arm64-v8a",
                ndk=NdkSpec(alias="r26d"),
                dry_run=True,
            )

            # Verify logging occurred - check if step was called or info was called
            assert mock_logger.step.called or mock_logger.info.called
