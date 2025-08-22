"""Tests for packaging packager module."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from ovmobilebench.config.schema import ModelItem, PackageConfig
from ovmobilebench.core.errors import OVMobileBenchError
from ovmobilebench.packaging.packager import Packager


class TestPackager:
    """Test Packager class."""

    @pytest.fixture
    def package_config(self):
        """Create a test package configuration."""
        return PackageConfig(
            include_symbols=False,
            extra_files=["/path/to/extra1.txt", "/path/to/extra2.so"],
        )

    @pytest.fixture
    def package_config_with_symbols(self):
        """Create a test package configuration with symbols."""
        return PackageConfig(
            include_symbols=True,
            extra_files=[],
        )

    @pytest.fixture
    def models(self):
        """Create test model items."""
        return [
            ModelItem(name="resnet50", path="/models/resnet50.xml", precision="FP16"),
            ModelItem(name="mobilenet", path="/models/mobilenet.xml", precision="FP32"),
        ]

    @pytest.fixture
    def single_model(self):
        """Create single test model."""
        return [ModelItem(name="test_model", path="/models/test_model.xml")]

    @pytest.fixture
    def artifacts(self):
        """Create test artifacts dictionary."""
        return {
            "benchmark_app": Path("/build/bin/benchmark_app"),
            "libs": Path("/build/lib"),
        }

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_init(self, mock_ensure_dir, package_config, models):
        """Test Packager initialization."""
        mock_ensure_dir.return_value = Path("/output")

        packager = Packager(package_config, models, Path("/output"))

        assert packager.config == package_config
        assert packager.models == models
        assert packager.output_dir == Path("/output")
        mock_ensure_dir.assert_called_once_with(Path("/output"))

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("ovmobilebench.packaging.packager.shutil.copy2")
    @patch("pathlib.Path.chmod")
    def test_create_bundle_basic(
        self, mock_chmod, mock_copy2, mock_ensure_dir, package_config, single_model, artifacts
    ):
        """Test basic bundle creation."""
        mock_ensure_dir.side_effect = lambda x: x  # Return the path as-is

        packager = Packager(package_config, single_model, Path("/output"))

        with patch.object(packager, "_copy_libs") as mock_copy_libs:
            with patch.object(packager, "_copy_models") as mock_copy_models:
                with patch.object(packager, "_create_readme") as mock_create_readme:
                    with patch.object(packager, "_create_archive") as mock_create_archive:
                        mock_create_archive.return_value = Path("/output/ovbundle.tar.gz")

                        result = packager.create_bundle(artifacts)

                        assert result == Path("/output/ovbundle.tar.gz")

                        # Verify binary was copied and made executable
                        mock_copy2.assert_called_with(
                            artifacts["benchmark_app"], Path("/output/ovbundle/bin/benchmark_app")
                        )
                        mock_chmod.assert_called_once_with(0o755)

                        # Verify other methods were called
                        mock_copy_libs.assert_called_once()
                        mock_copy_models.assert_called_once()
                        mock_create_readme.assert_called_once()
                        mock_create_archive.assert_called_once()

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("shutil.copy2")
    @patch("pathlib.Path.chmod")
    def test_create_bundle_custom_name(
        self, mock_chmod, mock_copy2, mock_ensure_dir, package_config, single_model, artifacts
    ):
        """Test bundle creation with custom name."""
        mock_ensure_dir.side_effect = lambda x: x

        packager = Packager(package_config, single_model, Path("/output"))

        with patch.object(packager, "_copy_libs"):
            with patch.object(packager, "_copy_models"):
                with patch.object(packager, "_create_readme"):
                    with patch.object(packager, "_create_archive") as mock_create_archive:
                        mock_create_archive.return_value = Path("/output/custom_bundle.tar.gz")

                        packager.create_bundle(artifacts, bundle_name="custom_bundle")

                        mock_create_archive.assert_called_with(
                            Path("/output/custom_bundle"), "custom_bundle"
                        )

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_create_bundle_missing_benchmark_app(
        self, mock_ensure_dir, package_config, single_model
    ):
        """Test bundle creation without benchmark_app in artifacts."""
        mock_ensure_dir.side_effect = lambda x: x
        artifacts = {"libs": Path("/build/lib")}  # Missing benchmark_app

        packager = Packager(package_config, single_model, Path("/output"))

        with patch.object(packager, "_copy_libs"):
            with patch.object(packager, "_copy_models"):
                with patch.object(packager, "_create_readme"):
                    with patch.object(packager, "_create_archive") as mock_create_archive:
                        mock_create_archive.return_value = Path("/output/ovbundle.tar.gz")

                        # Should work without benchmark_app
                        result = packager.create_bundle(artifacts)
                        assert result == Path("/output/ovbundle.tar.gz")

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("shutil.copy2")
    @patch("pathlib.Path.chmod")
    def test_create_bundle_missing_libs(
        self, mock_chmod, mock_copy2, mock_ensure_dir, package_config, single_model
    ):
        """Test bundle creation without libs in artifacts."""
        mock_ensure_dir.side_effect = lambda x: x
        artifacts = {"benchmark_app": Path("/build/bin/benchmark_app")}  # Missing libs

        packager = Packager(package_config, single_model, Path("/output"))

        with patch.object(packager, "_copy_libs") as mock_copy_libs:
            with patch.object(packager, "_copy_models"):
                with patch.object(packager, "_create_readme"):
                    with patch.object(packager, "_create_archive") as mock_create_archive:
                        mock_create_archive.return_value = Path("/output/ovbundle.tar.gz")

                        packager.create_bundle(artifacts)

                        # _copy_libs should NOT be called since libs is missing from artifacts
                        mock_copy_libs.assert_not_called()

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("ovmobilebench.packaging.packager.shutil.copy2")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.chmod")
    def test_create_bundle_with_extra_files(
        self, mock_chmod, mock_exists, mock_copy2, mock_ensure_dir, models
    ):
        """Test bundle creation with extra files."""
        mock_ensure_dir.side_effect = lambda x: x
        mock_exists.return_value = True

        config = PackageConfig(extra_files=["/path/to/extra1.txt", "/path/to/extra2.so"])
        packager = Packager(config, models, Path("/output"))
        artifacts = {"benchmark_app": Path("/build/bin/benchmark_app")}

        with patch.object(packager, "_copy_libs"):
            with patch.object(packager, "_copy_models"):
                with patch.object(packager, "_create_readme"):
                    with patch.object(packager, "_create_archive") as mock_create_archive:
                        mock_create_archive.return_value = Path("/output/ovbundle.tar.gz")

                        packager.create_bundle(artifacts)

                        # Verify extra files were copied
                        expected_calls = [
                            call(
                                Path("/build/bin/benchmark_app"),
                                Path("/output/ovbundle/bin/benchmark_app"),
                            ),
                            call(Path("/path/to/extra1.txt"), Path("/output/ovbundle/extra1.txt")),
                            call(Path("/path/to/extra2.so"), Path("/output/ovbundle/extra2.so")),
                        ]
                        mock_copy2.assert_has_calls(expected_calls, any_order=True)

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("pathlib.Path.exists")
    def test_create_bundle_extra_files_not_exist(self, mock_exists, mock_ensure_dir, models):
        """Test bundle creation with non-existent extra files."""
        mock_ensure_dir.side_effect = lambda x: x
        mock_exists.return_value = False

        config = PackageConfig(extra_files=["/path/to/nonexistent.txt"])
        packager = Packager(config, models, Path("/output"))
        artifacts = {}

        with patch.object(packager, "_copy_libs"):
            with patch.object(packager, "_copy_models"):
                with patch.object(packager, "_create_readme"):
                    with patch.object(packager, "_create_archive") as mock_create_archive:
                        mock_create_archive.return_value = Path("/output/ovbundle.tar.gz")

                        # Should work without error, just skip non-existent files
                        result = packager.create_bundle(artifacts)
                        assert result == Path("/output/ovbundle.tar.gz")

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_copy_libs(self, mock_ensure_dir, package_config, single_model):
        """Test copying library files."""
        mock_ensure_dir.side_effect = lambda x: x
        packager = Packager(package_config, single_model, Path("/output"))

        # Mock library directory with some files
        libs_dir = MagicMock()
        libs_dir.exists.return_value = True

        # Create mock files
        mock_lib1 = MagicMock()
        mock_lib1.is_file.return_value = True
        mock_lib1.relative_to.return_value = Path("libopenvino.so")
        mock_lib1.name = "libopenvino.so"

        mock_lib2 = MagicMock()
        mock_lib2.is_file.return_value = True
        mock_lib2.relative_to.return_value = Path("libtest.so.1")
        mock_lib2.name = "libtest.so.1"

        libs_dir.rglob.return_value = [mock_lib1, mock_lib2]

        dest_dir = Path("/bundle/lib")

        with patch("ovmobilebench.packaging.packager.shutil.copy2") as mock_copy2:
            with patch.object(packager, "_copy_ndk_stl_lib"):
                with patch("pathlib.Path.mkdir"):
                    packager._copy_libs(libs_dir, dest_dir)

                    # Should copy all library files
                    assert mock_copy2.call_count == 2
                    # Check that both libraries were copied
                    mock_copy2.assert_any_call(mock_lib1, dest_dir / "libopenvino.so")
                    mock_copy2.assert_any_call(mock_lib2, dest_dir / "libtest.so.1")

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_copy_libs_no_files(self, mock_ensure_dir, package_config, single_model):
        """Test copying libraries when no files match patterns."""
        mock_ensure_dir.side_effect = lambda x: x
        packager = Packager(package_config, single_model, Path("/output"))

        libs_dir = MagicMock()
        libs_dir.exists.return_value = True
        libs_dir.rglob.return_value = []  # No files found

        dest_dir = Path("/bundle/lib")

        with patch("ovmobilebench.packaging.packager.shutil.copy2") as mock_copy2:
            with patch.object(packager, "_copy_ndk_stl_lib"):
                packager._copy_libs(libs_dir, dest_dir)

                # Should not copy anything
                mock_copy2.assert_not_called()

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_copy_libs_directories_ignored(self, mock_ensure_dir, package_config, single_model):
        """Test that directories are ignored when copying libs."""
        mock_ensure_dir.side_effect = lambda x: x
        packager = Packager(package_config, single_model, Path("/output"))

        # Mock a directory that matches the pattern
        mock_dir = MagicMock()
        mock_dir.is_file.return_value = False  # It's a directory

        libs_dir = MagicMock()
        libs_dir.exists.return_value = True
        libs_dir.rglob.return_value = [mock_dir]

        dest_dir = Path("/bundle/lib")

        with patch("ovmobilebench.packaging.packager.shutil.copy2") as mock_copy2:
            with patch.object(packager, "_copy_ndk_stl_lib"):
                packager._copy_libs(libs_dir, dest_dir)

                # Should not copy directories
                mock_copy2.assert_not_called()

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("ovmobilebench.packaging.packager.shutil.copy2")
    @patch("pathlib.Path.exists")
    def test_copy_models_success(
        self, mock_exists, mock_copy2, mock_ensure_dir, package_config, models
    ):
        """Test successful model copying."""
        mock_exists.return_value = True  # All model files exist
        mock_ensure_dir.side_effect = lambda x: x

        packager = Packager(package_config, models, Path("/output"))
        models_dir = Path("/bundle/models")

        packager._copy_models(models_dir)

        # Should copy both XML and BIN files for each model
        expected_calls = [
            call(Path("/models/resnet50.xml"), models_dir / "resnet50.xml"),
            call(Path("/models/resnet50.bin"), models_dir / "resnet50.bin"),
            call(Path("/models/mobilenet.xml"), models_dir / "mobilenet.xml"),
            call(Path("/models/mobilenet.bin"), models_dir / "mobilenet.bin"),
        ]
        mock_copy2.assert_has_calls(expected_calls, any_order=True)

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_copy_models_missing_xml(self, mock_ensure_dir, package_config, single_model):
        """Test model copying with missing XML file."""
        mock_ensure_dir.side_effect = lambda x: x  # Return path as-is

        packager = Packager(package_config, single_model, Path("/output"))
        models_dir = Path("/bundle/models")

        # Create mock for Path.exists that returns False for XML files
        def mock_exists(self):
            return "xml" not in str(self)

        with patch.object(Path, "exists", mock_exists):
            with pytest.raises(OVMobileBenchError) as exc_info:
                packager._copy_models(models_dir)

            assert "Model XML not found" in str(exc_info.value)

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_copy_models_missing_bin(self, mock_ensure_dir, package_config, single_model):
        """Test model copying with missing BIN file."""
        mock_ensure_dir.side_effect = lambda x: x  # Return path as-is

        packager = Packager(package_config, single_model, Path("/output"))
        models_dir = Path("/bundle/models")

        # Create mock for Path.exists that returns False for BIN files
        def mock_exists(self):
            return "bin" not in str(self)

        with patch.object(Path, "exists", mock_exists):

            with pytest.raises(OVMobileBenchError) as exc_info:
                packager._copy_models(models_dir)

            assert "Model BIN not found" in str(exc_info.value)

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_create_readme(self, mock_ensure_dir, package_config, single_model):
        """Test README creation."""
        mock_ensure_dir.side_effect = lambda x: x  # Return path as-is
        packager = Packager(package_config, single_model, Path("/output"))
        bundle_dir = Path("/bundle")

        with patch("pathlib.Path.write_text") as mock_write_text:
            packager._create_readme(bundle_dir)

            # Should write README.txt
            mock_write_text.assert_called_once()
            call_args = mock_write_text.call_args

            # Check that README content is reasonable
            content = call_args[0][0]
            assert "OVMobileBench Bundle" in content
            assert "Usage" in content
            assert "benchmark_app" in content
            assert "LD_LIBRARY_PATH" in content

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("ovmobilebench.packaging.packager.get_digest")
    @patch("pathlib.Path.write_text")
    @patch("tarfile.open")
    def test_create_archive(
        self,
        mock_tarfile_open,
        mock_write_text,
        mock_get_digest,
        mock_ensure_dir,
        package_config,
        single_model,
    ):
        """Test archive creation."""
        mock_ensure_dir.side_effect = lambda x: x  # Return path as-is
        mock_get_digest.return_value = "abc123def456"
        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        packager = Packager(package_config, single_model, Path("/output"))
        bundle_dir = Path("/output/bundle")
        name = "testbundle"

        result = packager._create_archive(bundle_dir, name)

        # Check archive path
        assert result == Path("/output/testbundle.tar.gz")

        # Check tarfile operations
        mock_tarfile_open.assert_called_once_with(Path("/output/testbundle.tar.gz"), "w:gz")
        mock_tar.add.assert_called_once_with(bundle_dir, arcname=name)

        # Check checksum file creation
        mock_get_digest.assert_called_once_with(Path("/output/testbundle.tar.gz"))
        mock_write_text.assert_called_once_with("abc123def456  testbundle.tar.gz\n")

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("ovmobilebench.packaging.packager.get_digest", side_effect=Exception("Digest failed"))
    @patch("tarfile.open")
    def test_create_archive_digest_error(
        self, mock_tarfile_open, mock_get_digest, mock_ensure_dir, package_config, single_model
    ):
        """Test archive creation with digest calculation error."""
        mock_ensure_dir.side_effect = lambda x: x  # Return path as-is
        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        packager = Packager(package_config, single_model, Path("/output"))
        bundle_dir = Path("/output/bundle")
        name = "testbundle"

        # Should raise the digest exception
        with pytest.raises(Exception, match="Digest failed"):
            packager._create_archive(bundle_dir, name)

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("tarfile.open", side_effect=Exception("Tar creation failed"))
    def test_create_archive_tar_error(
        self, mock_tarfile_open, mock_ensure_dir, package_config, single_model
    ):
        """Test archive creation with tar creation error."""
        mock_ensure_dir.side_effect = lambda x: x  # Return path as-is
        packager = Packager(package_config, single_model, Path("/output"))
        bundle_dir = Path("/output/bundle")
        name = "testbundle"

        # Should raise the tar exception
        with pytest.raises(Exception, match="Tar creation failed"):
            packager._create_archive(bundle_dir, name)

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    @patch("shutil.copy2")
    @patch("pathlib.Path.chmod")
    def test_create_bundle_logs_completion(
        self, mock_chmod, mock_copy2, mock_ensure_dir, package_config, single_model, artifacts
    ):
        """Test that bundle creation logs completion."""
        mock_ensure_dir.side_effect = lambda x: x

        packager = Packager(package_config, single_model, Path("/output"))

        with patch.object(packager, "_copy_libs"):
            with patch.object(packager, "_copy_models"):
                with patch.object(packager, "_create_readme"):
                    with patch.object(packager, "_create_archive") as mock_create_archive:
                        mock_create_archive.return_value = Path("/output/ovbundle.tar.gz")

                        with patch("ovmobilebench.packaging.packager.logger") as mock_logger:
                            packager.create_bundle(artifacts)

                            # Check that logger was called with the bundle path
                            # Use str() to handle platform-specific path separators
                            expected_path = Path("/output/ovbundle.tar.gz")
                            mock_logger.info.assert_called_with(f"Bundle created: {expected_path}")

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_copy_models_logs_progress(self, mock_ensure_dir, package_config, models):
        """Test that model copying logs progress."""
        mock_ensure_dir.side_effect = lambda x: x  # Return path as-is
        packager = Packager(package_config, models, Path("/output"))

        with patch("ovmobilebench.packaging.packager.shutil.copy2"):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("ovmobilebench.packaging.packager.logger") as mock_logger:
                    packager._copy_models(Path("/bundle/models"))

                    # Should log each model
                    expected_calls = [
                        call("Copied model: resnet50"),
                        call("Copied model: mobilenet"),
                    ]
                    mock_logger.info.assert_has_calls(expected_calls, any_order=True)

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_copy_libs_logs_debug(self, mock_ensure_dir, package_config, single_model):
        """Test that library copying logs debug messages."""
        mock_ensure_dir.side_effect = lambda x: x  # Return path as-is
        packager = Packager(package_config, single_model, Path("/output"))

        # Mock library files
        mock_lib = MagicMock()
        mock_lib.is_file.return_value = True
        mock_lib.relative_to.return_value = Path("libtest.so")

        libs_dir = MagicMock()
        libs_dir.exists.return_value = True
        libs_dir.rglob.return_value = [mock_lib]  # Return mock library from rglob

        dest_dir = MagicMock()
        dest_dir.rglob.return_value = [mock_lib]  # For counting total libs

        with patch("ovmobilebench.packaging.packager.shutil.copy2"):
            with patch.object(packager, "_copy_ndk_stl_lib"):  # Mock NDK lib copy
                with patch("ovmobilebench.packaging.packager.logger") as mock_logger:
                    packager._copy_libs(libs_dir, dest_dir)

                    mock_logger.debug.assert_called_with("Copied library: libtest.so")
                    mock_logger.info.assert_called_with(f"Copied 1 libraries from {libs_dir}")

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_empty_models_list(self, mock_ensure_dir):
        """Test packager with empty models list."""
        mock_ensure_dir.side_effect = lambda x: x

        config = PackageConfig()
        packager = Packager(config, [], Path("/output"))

        with patch("ovmobilebench.packaging.packager.shutil.copy2"):
            # Should not raise any errors
            packager._copy_models(Path("/bundle/models"))

    @patch("ovmobilebench.packaging.packager.ensure_dir")
    def test_empty_extra_files(self, mock_ensure_dir):
        """Test packager with empty extra files list."""
        mock_ensure_dir.side_effect = lambda x: x

        config = PackageConfig(extra_files=[])
        packager = Packager(config, [], Path("/output"))
        artifacts = {}

        with patch.object(packager, "_copy_libs"):
            with patch.object(packager, "_copy_models"):
                with patch.object(packager, "_create_readme"):
                    with patch.object(packager, "_create_archive") as mock_create_archive:
                        mock_create_archive.return_value = Path("/output/ovbundle.tar.gz")

                        # Should work without errors
                        result = packager.create_bundle(artifacts)
                        assert result == Path("/output/ovbundle.tar.gz")
