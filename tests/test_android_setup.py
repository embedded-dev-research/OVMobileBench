"""Tests for Android SDK/NDK setup script."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Add scripts directory to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.setup_android_tools import AndroidToolsInstaller


class TestAndroidToolsInstaller:
    """Test AndroidToolsInstaller functionality."""

    def test_platform_detection_macos(self):
        """Test platform detection on macOS."""
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.machine", return_value="arm64"):
                installer = AndroidToolsInstaller()

                assert installer.system == "darwin"
                assert installer.arch == "arm64"
                assert "mac" in installer.sdk_tools_file
                assert "darwin" in installer.ndk_file
                assert installer.sdkmanager_cmd == "sdkmanager"
                assert installer.adb_cmd == "adb"

    def test_platform_detection_windows(self):
        """Test platform detection on Windows."""
        with patch("platform.system", return_value="Windows"):
            with patch("platform.machine", return_value="AMD64"):
                installer = AndroidToolsInstaller()

                assert installer.system == "windows"
                assert installer.arch == "amd64"
                assert "win" in installer.sdk_tools_file
                assert "windows" in installer.ndk_file
                assert installer.sdkmanager_cmd == "sdkmanager.bat"
                assert installer.adb_cmd == "adb.exe"

    def test_platform_detection_linux(self):
        """Test platform detection on Linux."""
        with patch("platform.system", return_value="Linux"):
            with patch("platform.machine", return_value="x86_64"):
                installer = AndroidToolsInstaller()

                assert installer.system == "linux"
                assert installer.arch == "x86_64"
                assert "linux" in installer.sdk_tools_file
                assert "linux" in installer.ndk_file
                assert installer.sdkmanager_cmd == "sdkmanager"
                assert installer.adb_cmd == "adb"

    def test_custom_install_directory(self):
        """Test custom installation directory."""
        custom_dir = "/custom/path/android"
        installer = AndroidToolsInstaller(install_dir=custom_dir)

        assert str(installer.install_dir) == custom_dir
        assert str(installer.sdk_dir) == f"{custom_dir}/sdk"
        assert str(installer.ndk_dir) == f"{custom_dir}/ndk/{installer.NDK_VERSION}"

    def test_ndk_only_mode(self):
        """Test NDK-only installation mode."""
        installer = AndroidToolsInstaller(ndk_only=True, fetch_latest=False)

        assert installer.ndk_only is True

        # SDK installation should be skipped
        with patch.object(installer, "download_file", return_value=True):
            result = installer.install_sdk_tools()
            assert result is True  # Should return True but skip actual installation

    def test_url_generation(self):
        """Test download URL generation."""
        installer = AndroidToolsInstaller(fetch_latest=False)

        sdk_url = f"{installer.SDK_BASE_URL}/{installer.sdk_tools_file}"
        ndk_url = f"{installer.NDK_BASE_URL}/{installer.ndk_file}"

        assert sdk_url.startswith("https://dl.google.com/android/repository/")
        assert ndk_url.startswith("https://dl.google.com/android/repository/")
        assert installer.SDK_TOOLS_VERSION in sdk_url
        assert installer.NDK_VERSION in ndk_url

    def test_download_file_success(self):
        """Test successful file download."""
        installer = AndroidToolsInstaller(fetch_latest=False)

        # Mock urlretrieve
        with patch("scripts.setup_android_tools.urlretrieve") as mock_urlretrieve:
            # Mock successful download
            def mock_download(url, dest, reporthook=None):
                # Simulate progress callbacks
                if reporthook:
                    reporthook(0, 1024, 10240)  # 0%
                    reporthook(5, 1024, 10240)  # 50%
                    reporthook(10, 1024, 10240)  # 100%
                return None

            mock_urlretrieve.side_effect = mock_download

            with tempfile.NamedTemporaryFile() as tmp_file:
                result = installer.download_file(
                    "https://example.com/file.zip", tmp_file.name, "Test file"
                )

                assert result is True
                mock_urlretrieve.assert_called_once()

    @patch("urllib.request.urlretrieve")
    def test_download_file_failure(self, mock_urlretrieve):
        """Test failed file download."""
        installer = AndroidToolsInstaller()

        # Mock download failure
        mock_urlretrieve.side_effect = Exception("Network error")

        with tempfile.NamedTemporaryFile() as tmp_file:
            result = installer.download_file(
                "https://example.com/file.zip", tmp_file.name, "Test file"
            )

            assert result is False

    def test_extract_zip_archive(self):
        """Test ZIP archive extraction."""
        import zipfile

        installer = AndroidToolsInstaller()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test ZIP file
            zip_path = temp_path / "test.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("file1.txt", "Content 1")
                zf.writestr("subdir/file2.txt", "Content 2")

            # Extract
            extract_dir = temp_path / "extracted"
            installer.extract_archive(zip_path, extract_dir)

            # Verify extraction
            assert (extract_dir / "file1.txt").exists()
            assert (extract_dir / "subdir" / "file2.txt").exists()
            assert (extract_dir / "file1.txt").read_text() == "Content 1"

    def test_extract_tar_archive(self):
        """Test TAR archive extraction."""
        import tarfile

        installer = AndroidToolsInstaller()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test TAR file
            tar_path = temp_path / "test.tar.gz"
            with tarfile.open(tar_path, "w:gz") as tf:
                # Create temporary files to add
                file1 = temp_path / "file1.txt"
                file1.write_text("Content 1")
                tf.add(file1, arcname="file1.txt")

            # Extract
            extract_dir = temp_path / "extracted"
            installer.extract_archive(tar_path, extract_dir)

            # Verify extraction
            assert (extract_dir / "file1.txt").exists()

    def test_extract_unsupported_format(self):
        """Test extraction of unsupported archive format."""
        installer = AndroidToolsInstaller()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file with unsupported extension
            unsupported_file = temp_path / "test.xyz"
            unsupported_file.write_text("Not an archive")

            # Should raise ValueError
            extract_dir = temp_path / "extracted"
            with pytest.raises(ValueError, match="Unsupported archive format"):
                installer.extract_archive(unsupported_file, extract_dir)

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_extract_dmg_macos(self, mock_run, mock_system):
        """Test DMG extraction on macOS."""
        installer = AndroidToolsInstaller()

        # Mock hdiutil commands
        mock_run.side_effect = [
            # Mount command
            Mock(returncode=0, stdout="/dev/disk2\t/Volumes/AndroidNDK"),
            # Unmount command
            Mock(returncode=0),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create fake DMG file
            dmg_path = temp_path / "test.dmg"
            dmg_path.write_bytes(b"DMG content")

            # Create mock mount point with NDK content
            Path("/Volumes/AndroidNDK")  # Simulated mount point

            with patch("pathlib.Path.exists", return_value=True):
                with patch("shutil.copytree"):
                    extract_dir = temp_path / "extracted"
                    installer.extract_dmg(dmg_path, extract_dir)

                    # Verify mount and unmount were called
                    assert mock_run.call_count == 2
                    mount_call = mock_run.call_args_list[0]
                    assert "hdiutil" in mount_call[0][0][0]
                    assert "attach" in mount_call[0][0][1]

    def test_environment_setup_full(self):
        """Test environment variable setup for full installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir, ndk_only=False)

            # Create mock directories
            (installer.sdk_dir / "platform-tools").mkdir(parents=True)
            (installer.cmdline_tools_dir / "bin").mkdir(parents=True)
            installer.ndk_dir.mkdir(parents=True)

            env_vars = installer.setup_environment()

            # Check all required variables are set
            assert "ANDROID_SDK_ROOT" in env_vars
            assert "ANDROID_HOME" in env_vars
            assert "ANDROID_NDK_ROOT" in env_vars
            assert "ANDROID_NDK_HOME" in env_vars
            assert "NDK_ROOT" in env_vars
            assert "PATH_ADDITIONS" in env_vars

            # Check values
            assert env_vars["ANDROID_SDK_ROOT"] == str(installer.sdk_dir)
            assert env_vars["ANDROID_NDK_ROOT"] == str(installer.ndk_dir)
            assert len(env_vars["PATH_ADDITIONS"]) == 2  # platform-tools and cmdline-tools/bin

    def test_environment_setup_ndk_only(self):
        """Test environment variable setup for NDK-only installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir, ndk_only=True)

            # Create mock directories
            installer.ndk_dir.mkdir(parents=True)

            env_vars = installer.setup_environment()

            # Check only NDK variables are set
            assert "ANDROID_SDK_ROOT" not in env_vars
            assert "ANDROID_HOME" not in env_vars
            assert "PATH_ADDITIONS" not in env_vars

            assert "ANDROID_NDK_ROOT" in env_vars
            assert "ANDROID_NDK_HOME" in env_vars
            assert "NDK_ROOT" in env_vars

            # Check values
            assert env_vars["ANDROID_NDK_ROOT"] == str(installer.ndk_dir)

    def test_environment_script_generation(self):
        """Test generation of environment script file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir, ndk_only=True)

            # Create mock directories (install_dir already exists as temp_dir)
            installer.ndk_dir.mkdir(parents=True, exist_ok=True)

            installer.setup_environment()

            # Check script was created
            env_script = installer.install_dir / "android_env.sh"
            assert env_script.exists()

            # Check script content
            content = env_script.read_text()
            assert "#!/bin/bash" in content
            assert "export ANDROID_NDK_ROOT=" in content
            assert str(installer.ndk_dir) in content

    def test_verify_installation_success(self):
        """Test successful installation verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir, ndk_only=True)

            # Create mock NDK files
            installer.ndk_dir.mkdir(parents=True)
            if installer.system == "windows":
                ndk_build = installer.ndk_dir / "ndk-build.cmd"
            else:
                ndk_build = installer.ndk_dir / "ndk-build"
            ndk_build.touch()

            result = installer.verify_installation()
            assert result is True

    def test_verify_installation_failure(self):
        """Test failed installation verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir, ndk_only=True)

            # Don't create any files
            result = installer.verify_installation()
            assert result is False

    def test_cleanup(self):
        """Test cleanup of downloaded files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir)

            # Create test files to clean up (install_dir already exists as temp_dir)
            test_files = [
                installer.install_dir / "test.zip",
                installer.install_dir / "test.dmg",
                installer.install_dir / "test.tar.gz",
                installer.install_dir / "keep.txt",  # Should not be deleted
            ]

            for file in test_files:
                file.touch()

            # Run cleanup
            installer.cleanup()

            # Check that archive files were deleted
            assert not (installer.install_dir / "test.zip").exists()
            assert not (installer.install_dir / "test.dmg").exists()
            assert not (installer.install_dir / "test.tar.gz").exists()

            # Check that non-archive files were kept
            assert (installer.install_dir / "keep.txt").exists()

    @patch("subprocess.run")
    def test_install_sdk_packages(self, mock_run):
        """Test SDK packages installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir, ndk_only=False)

            # Create mock sdkmanager
            installer.cmdline_tools_dir.mkdir(parents=True)
            sdkmanager = installer.cmdline_tools_dir / "bin" / installer.sdkmanager_cmd
            sdkmanager.parent.mkdir(parents=True)
            sdkmanager.touch()

            # Mock subprocess calls
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            result = installer.install_sdk_packages()

            assert result is True
            # Should call sdkmanager for licenses and each package
            assert mock_run.call_count >= 4  # licenses + 3 packages

    def test_custom_ndk_version(self):
        """Test custom NDK version specification."""
        custom_version = "r25c"
        installer = AndroidToolsInstaller(install_dir="/tmp/test")

        # Override NDK version
        installer.NDK_VERSION = custom_version
        installer.ndk_dir = installer.install_dir / "ndk" / custom_version  # Update ndk_dir
        installer.setup_platform_specific()

        assert custom_version in installer.ndk_file
        assert custom_version in str(installer.ndk_dir)

    @patch.object(AndroidToolsInstaller, "install_sdk_tools", return_value=True)
    @patch.object(AndroidToolsInstaller, "install_sdk_packages", return_value=True)
    @patch.object(AndroidToolsInstaller, "install_ndk", return_value=True)
    @patch.object(AndroidToolsInstaller, "setup_environment", return_value={})
    @patch.object(AndroidToolsInstaller, "verify_installation", return_value=True)
    @patch.object(AndroidToolsInstaller, "cleanup")
    def test_full_installation_flow(
        self, mock_cleanup, mock_verify, mock_env, mock_ndk, mock_packages, mock_tools
    ):
        """Test complete installation flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir)

            # No need to create install directory - it already exists as temp_dir

            result = installer.install()

            assert result is True

            # Verify all steps were called
            mock_tools.assert_called_once()
            mock_packages.assert_called_once()
            mock_ndk.assert_called_once()
            mock_env.assert_called_once()
            mock_verify.assert_called_once()
            mock_cleanup.assert_called_once()

    @patch.object(AndroidToolsInstaller, "install_sdk_tools", return_value=False)
    def test_installation_failure(self, mock_tools):
        """Test handling of installation failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            installer = AndroidToolsInstaller(install_dir=temp_dir)

            result = installer.install()

            assert result is False
            mock_tools.assert_called_once()
