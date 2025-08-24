"""Additional tests for SdkManager coverage gaps."""

from unittest.mock import Mock, patch

from ovmobilebench.android.installer.sdkmanager import SdkManager


class TestSdkManagerAdditional:
    """Test remaining gaps in SdkManager."""

    def test_ensure_cmdline_tools_download_and_install(self, tmp_path):
        """Test command line tools download and installation."""
        with patch("ovmobilebench.android.installer.sdkmanager._secure_urlretrieve") as mock_dl:
            with patch("zipfile.ZipFile") as mock_zip:
                mock_zip_inst = Mock()
                mock_zip.return_value.__enter__ = Mock(return_value=mock_zip_inst)
                mock_zip.return_value.__exit__ = Mock(return_value=None)

                manager = SdkManager(tmp_path)

                # Mock that tools don't exist
                with patch.object(manager, "_get_sdkmanager_path", return_value=None):
                    # This should trigger download
                    with patch(
                        "ovmobilebench.android.installer.logging.get_logger"
                    ) as mock_get_logger:
                        mock_logger = Mock()
                        mock_logger.step = Mock(
                            return_value=Mock(__enter__=Mock(), __exit__=Mock())
                        )
                        mock_get_logger.return_value = mock_logger

                        manager = SdkManager(tmp_path, logger=mock_logger)
                        manager.ensure_cmdline_tools()

                        # Verify download was called
                        mock_dl.assert_called()

    def test_run_sdkmanager_with_input(self, tmp_path):
        """Test running sdkmanager with input text."""
        # Create fake sdkmanager
        sdkmanager_dir = tmp_path / "cmdline-tools" / "latest" / "bin"
        sdkmanager_dir.mkdir(parents=True)
        sdkmanager = sdkmanager_dir / "sdkmanager"
        sdkmanager.touch()
        sdkmanager.chmod(0o755)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            manager = SdkManager(tmp_path)
            manager._run_sdkmanager(["--list"], input_text="y\n")

            # Verify input was passed
            mock_run.assert_called()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs.get("input") == "y\n"

    def test_accept_licenses(self, tmp_path):
        """Test accepting SDK licenses."""
        # Create fake sdkmanager
        sdkmanager_dir = tmp_path / "cmdline-tools" / "latest" / "bin"
        sdkmanager_dir.mkdir(parents=True)
        sdkmanager = sdkmanager_dir / "sdkmanager"
        sdkmanager.touch()
        sdkmanager.chmod(0o755)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with patch("ovmobilebench.android.installer.logging.get_logger") as mock_get_logger:
                mock_logger = Mock()
                mock_logger.step = Mock(return_value=Mock(__enter__=Mock(), __exit__=Mock()))
                mock_get_logger.return_value = mock_logger

                manager = SdkManager(tmp_path, logger=mock_logger)
                manager.accept_licenses()

                # Verify licenses command was run
                mock_run.assert_called()
                args = mock_run.call_args[0][0]
                assert "--licenses" in args
