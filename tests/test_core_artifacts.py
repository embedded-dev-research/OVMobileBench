"""Tests for core artifacts module."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, call
from datetime import datetime, timedelta, timezone

from ovmobilebench.core.artifacts import ArtifactManager


class TestArtifactManager:
    """Test ArtifactManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def artifact_manager(self, temp_dir):
        """Create artifact manager instance."""
        return ArtifactManager(temp_dir)

    @patch("ovmobilebench.core.artifacts.ensure_dir")
    def test_init(self, mock_ensure_dir, temp_dir):
        """Test ArtifactManager initialization."""
        mock_ensure_dir.side_effect = lambda x: x

        manager = ArtifactManager(temp_dir)

        assert manager.base_dir == temp_dir
        assert manager.build_dir == temp_dir / "build"
        assert manager.packages_dir == temp_dir / "packages"
        assert manager.results_dir == temp_dir / "results"
        assert manager.logs_dir == temp_dir / "logs"
        assert manager.metadata_file == temp_dir / "metadata.json"

        # Verify ensure_dir calls
        expected_calls = [
            call(temp_dir / "build"),
            call(temp_dir / "packages"),
            call(temp_dir / "results"),
            call(temp_dir / "logs"),
        ]
        mock_ensure_dir.assert_has_calls(expected_calls)

    @patch("ovmobilebench.core.artifacts.ensure_dir")
    def test_get_build_path(self, mock_ensure_dir, artifact_manager):
        """Test getting build path."""
        mock_ensure_dir.return_value = Path("/build/android_abc12345")

        result = artifact_manager.get_build_path("android", "abc12345defg")

        expected_path = artifact_manager.build_dir / "android_abc12345"
        mock_ensure_dir.assert_called_with(expected_path)
        assert result == Path("/build/android_abc12345")

    def test_get_package_path(self, artifact_manager):
        """Test getting package path."""
        result = artifact_manager.get_package_path("openvino", "2023.1")

        expected = artifact_manager.packages_dir / "openvino_2023.1.tar.gz"
        assert result == expected

    @patch("ovmobilebench.core.artifacts.ensure_dir")
    def test_get_results_path(self, mock_ensure_dir, artifact_manager):
        """Test getting results path."""
        mock_ensure_dir.return_value = Path("/results/test_run_001")

        result = artifact_manager.get_results_path("test_run_001")

        expected_path = artifact_manager.results_dir / "test_run_001"
        mock_ensure_dir.assert_called_with(expected_path)
        assert result == Path("/results/test_run_001")

    @patch("ovmobilebench.core.artifacts.ensure_dir")
    def test_get_log_path(self, mock_ensure_dir, artifact_manager):
        """Test getting log path."""
        mock_ensure_dir.return_value = Path("/logs/test_run_001")

        result = artifact_manager.get_log_path("test_run_001", "build")

        expected_dir = artifact_manager.logs_dir / "test_run_001"
        mock_ensure_dir.assert_called_with(expected_dir)
        assert result == Path("/logs/test_run_001/build.log")

    @patch("ovmobilebench.core.artifacts.atomic_write")
    def test_save_metadata_new(self, mock_atomic_write, artifact_manager):
        """Test saving metadata to new file."""
        metadata = {"test": "data", "number": 123}

        with patch.object(artifact_manager, "load_metadata", return_value={}):
            with patch("ovmobilebench.core.artifacts.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T00:00:00"

                artifact_manager.save_metadata(metadata)

                expected_content = json.dumps(
                    {"test": "data", "number": 123, "updated_at": "2023-01-01T00:00:00"},
                    indent=2,
                    default=str,
                )

                mock_atomic_write.assert_called_once_with(
                    artifact_manager.metadata_file, expected_content
                )

    @patch("ovmobilebench.core.artifacts.atomic_write")
    def test_save_metadata_update_existing(self, mock_atomic_write, artifact_manager):
        """Test updating existing metadata."""
        existing_metadata = {"existing": "value", "keep": "this"}
        new_metadata = {"test": "data", "existing": "updated"}

        with patch.object(artifact_manager, "load_metadata", return_value=existing_metadata):
            with patch("ovmobilebench.core.artifacts.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T00:00:00"

                artifact_manager.save_metadata(new_metadata)

                mock_atomic_write.assert_called_once()
                # Check content was correct
                call_args = mock_atomic_write.call_args[0]
                content = json.loads(call_args[1])
                assert content["existing"] == "updated"
                assert content["keep"] == "this"
                assert content["test"] == "data"

    def test_load_metadata_file_exists(self, artifact_manager):
        """Test loading metadata when file exists."""
        metadata = {"test": "value", "number": 42}

        with patch("builtins.open", mock_open(read_data=json.dumps(metadata))):
            with patch("pathlib.Path.exists", return_value=True):
                result = artifact_manager.load_metadata()

                assert result == metadata

    def test_load_metadata_file_not_exists(self, artifact_manager):
        """Test loading metadata when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = artifact_manager.load_metadata()

            assert result == {}

    def test_load_metadata_json_error(self, artifact_manager):
        """Test loading metadata with JSON decode error."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(json.JSONDecodeError):
                    artifact_manager.load_metadata()

    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.is_file")
    def test_register_artifact_file(self, mock_is_file, mock_stat, artifact_manager):
        """Test registering a file artifact."""
        mock_is_file.return_value = True
        mock_stat.return_value.st_size = 1024

        artifact_path = Path("/test/artifact.bin")
        metadata = {"custom": "data"}

        with patch.object(artifact_manager, "_calculate_checksum", return_value="abc123def456"):
            with patch.object(artifact_manager, "load_metadata", return_value={}):
                with patch.object(artifact_manager, "save_metadata") as mock_save:
                    with patch("ovmobilebench.core.artifacts.datetime") as mock_datetime:
                        mock_datetime.utcnow.return_value.isoformat.return_value = (
                            "2023-01-01T00:00:00"
                        )

                        result = artifact_manager.register_artifact(
                            "build", artifact_path, metadata
                        )

                        assert result == "abc123def456"

                        # Check save_metadata was called with correct data
                        save_call = mock_save.call_args[0][0]
                        artifact_record = save_call["artifacts"]["abc123def456"]

                        assert artifact_record["type"] == "build"
                        assert artifact_record["size"] == 1024
                        assert artifact_record["metadata"] == metadata
                        assert artifact_record["checksum"] == "abc123def456"

    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.is_file")
    def test_register_artifact_directory(self, mock_is_file, mock_stat, artifact_manager):
        """Test registering a directory artifact."""
        mock_is_file.return_value = False  # It's a directory

        artifact_path = Path("/test/artifact_dir")

        with patch.object(artifact_manager, "_calculate_checksum", return_value="dir123abc456"):
            with patch.object(artifact_manager, "load_metadata", return_value={}):
                with patch.object(artifact_manager, "save_metadata") as mock_save:
                    with patch("ovmobilebench.core.artifacts.datetime") as mock_datetime:
                        mock_datetime.utcnow.return_value.isoformat.return_value = (
                            "2023-01-01T00:00:00"
                        )

                        result = artifact_manager.register_artifact("package", artifact_path)

                        assert result == "dir123abc456"

                        # Check save_metadata was called with correct data
                        save_call = mock_save.call_args[0][0]
                        artifact_record = save_call["artifacts"]["dir123abc456"]

                        assert artifact_record["type"] == "package"
                        assert artifact_record["size"] is None  # Directory has no size
                        assert "metadata" not in artifact_record  # No metadata provided

    def test_get_artifact_exists(self, artifact_manager):
        """Test getting existing artifact."""
        artifacts = {
            "abc123": {
                "type": "build",
                "path": "build/test",
                "size": 1024,
                "created_at": "2023-01-01T00:00:00",
            }
        }

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            result = artifact_manager.get_artifact("abc123")

            assert result == artifacts["abc123"]

    def test_get_artifact_not_exists(self, artifact_manager):
        """Test getting non-existent artifact."""
        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": {}}):
            result = artifact_manager.get_artifact("nonexistent")

            assert result is None

    def test_list_artifacts_no_filters(self, artifact_manager):
        """Test listing all artifacts."""
        artifacts = {
            "abc123": {"type": "build", "created_at": "2023-01-01T00:00:00"},
            "def456": {"type": "package", "created_at": "2023-01-02T00:00:00"},
        }

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            result = artifact_manager.list_artifacts()

            assert len(result) == 2
            # Should be sorted by creation time (newest first)
            assert result[0]["id"] == "def456"
            assert result[1]["id"] == "abc123"

    def test_list_artifacts_type_filter(self, artifact_manager):
        """Test listing artifacts with type filter."""
        artifacts = {
            "abc123": {"type": "build", "created_at": "2023-01-01T00:00:00"},
            "def456": {"type": "package", "created_at": "2023-01-02T00:00:00"},
        }

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            result = artifact_manager.list_artifacts(artifact_type="build")

            assert len(result) == 1
            assert result[0]["id"] == "abc123"
            assert result[0]["type"] == "build"

    def test_list_artifacts_since_filter(self, artifact_manager):
        """Test listing artifacts with since filter."""
        artifacts = {
            "abc123": {"type": "build", "created_at": "2023-01-01T00:00:00"},
            "def456": {"type": "package", "created_at": "2023-01-03T00:00:00"},
        }

        since_date = datetime(2023, 1, 2, 0, 0, 0)

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            result = artifact_manager.list_artifacts(since=since_date)

            assert len(result) == 1
            assert result[0]["id"] == "def456"

    def test_list_artifacts_combined_filters(self, artifact_manager):
        """Test listing artifacts with combined filters."""
        artifacts = {
            "abc123": {"type": "build", "created_at": "2023-01-01T00:00:00"},
            "def456": {"type": "build", "created_at": "2023-01-03T00:00:00"},
            "ghi789": {"type": "package", "created_at": "2023-01-03T00:00:00"},
        }

        since_date = datetime(2023, 1, 2, 0, 0, 0)

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            result = artifact_manager.list_artifacts(artifact_type="build", since=since_date)

            assert len(result) == 1
            assert result[0]["id"] == "def456"
            assert result[0]["type"] == "build"

    def test_list_artifacts_empty(self, artifact_manager):
        """Test listing artifacts when none exist."""
        with patch.object(artifact_manager, "load_metadata", return_value={}):
            result = artifact_manager.list_artifacts()

            assert result == []

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.unlink")
    @patch("shutil.rmtree")
    def test_cleanup_old_artifacts(
        self, mock_rmtree, mock_unlink, mock_is_dir, mock_exists, artifact_manager
    ):
        """Test cleaning up old artifacts."""
        # Create test artifacts - some old, some new
        now = datetime.now(timezone.utc)
        old_date = (now - timedelta(days=40)).isoformat()
        new_date = (now - timedelta(days=10)).isoformat()

        artifacts = {
            "old_file": {"type": "build", "path": "build/old_file.bin", "created_at": old_date},
            "old_dir": {"type": "build", "path": "build/old_dir", "created_at": old_date},
            "new_file": {"type": "build", "path": "build/new_file.bin", "created_at": new_date},
        }

        # Mock file system operations
        mock_exists.return_value = True

        def is_dir_side_effect(self):
            return "old_dir" in str(self)

        mock_is_dir.side_effect = is_dir_side_effect

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            with patch.object(artifact_manager, "save_metadata") as mock_save:
                result = artifact_manager.cleanup_old_artifacts(days=30)

                assert result == 2  # Two artifacts removed

                # Check that files were removed
                mock_rmtree.assert_called_once()  # For directory
                mock_unlink.assert_called_once()  # For file

                # Check metadata was updated
                save_call = mock_save.call_args[0][0]
                remaining_artifacts = save_call["artifacts"]
                assert "new_file" in remaining_artifacts
                assert "old_file" not in remaining_artifacts
                assert "old_dir" not in remaining_artifacts

    @patch("pathlib.Path.exists")
    def test_cleanup_old_artifacts_missing_files(self, mock_exists, artifact_manager):
        """Test cleanup when artifact files don't exist."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()

        artifacts = {
            "missing_file": {"type": "build", "path": "build/missing.bin", "created_at": old_date}
        }

        mock_exists.return_value = False  # File doesn't exist

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            with patch.object(artifact_manager, "save_metadata") as mock_save:
                result = artifact_manager.cleanup_old_artifacts(days=30)

                assert result == 1  # Still counted as removed from metadata

                # Check metadata was updated
                save_call = mock_save.call_args[0][0]
                remaining_artifacts = save_call["artifacts"]
                assert "missing_file" not in remaining_artifacts

    def test_cleanup_old_artifacts_no_old_artifacts(self, artifact_manager):
        """Test cleanup when no artifacts are old enough."""
        new_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

        artifacts = {
            "new_file": {"type": "build", "path": "build/new_file.bin", "created_at": new_date}
        }

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            with patch.object(artifact_manager, "save_metadata") as mock_save:
                result = artifact_manager.cleanup_old_artifacts(days=30)

                assert result == 0  # No artifacts removed

                # Metadata should still be saved (but unchanged)
                save_call = mock_save.call_args[0][0]
                remaining_artifacts = save_call["artifacts"]
                assert "new_file" in remaining_artifacts

    @patch("builtins.open", new_callable=mock_open, read_data=b"test file content")
    @patch("pathlib.Path.is_file")
    def test_calculate_checksum_file(self, mock_is_file, mock_file, artifact_manager):
        """Test checksum calculation for file."""
        mock_is_file.return_value = True

        path = Path("/test/file.bin")
        result = artifact_manager._calculate_checksum(path)

        # Should be a 16-character hex string
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.stat")
    def test_calculate_checksum_directory(self, mock_stat, mock_is_file, artifact_manager):
        """Test checksum calculation for directory."""
        mock_is_file.return_value = False  # It's a directory
        mock_stat.return_value.st_mtime = 1672531200.0  # Fixed timestamp

        path = Path("/test/directory")
        result = artifact_manager._calculate_checksum(path)

        # Should be a 16-character hex string
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    @patch("pathlib.Path.is_file")
    def test_calculate_checksum_custom_algorithm(self, mock_is_file, artifact_manager):
        """Test checksum calculation with custom algorithm."""
        mock_is_file.return_value = False

        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_mtime = 1672531200.0

            path = Path("/test/directory")
            result = artifact_manager._calculate_checksum(path, algorithm="md5")

            # Should still be 16 characters (truncated)
            assert len(result) == 16

    @patch("hashlib.new", side_effect=ValueError("Unknown algorithm"))
    def test_calculate_checksum_invalid_algorithm(self, mock_hashlib, artifact_manager):
        """Test checksum calculation with invalid algorithm."""
        path = Path("/test/file")

        with pytest.raises(ValueError):
            artifact_manager._calculate_checksum(path, algorithm="invalid")

    @patch("builtins.open", side_effect=IOError("Cannot read file"))
    @patch("pathlib.Path.is_file")
    def test_calculate_checksum_read_error(self, mock_is_file, mock_file, artifact_manager):
        """Test checksum calculation with file read error."""
        mock_is_file.return_value = True

        path = Path("/test/unreadable.bin")

        with pytest.raises(IOError):
            artifact_manager._calculate_checksum(path)

    def test_register_artifact_relative_path_calculation(self, artifact_manager):
        """Test that artifact paths are stored relative to base_dir."""
        artifact_path = artifact_manager.base_dir / "build" / "test_artifact.bin"

        with patch("pathlib.Path.is_file", return_value=True):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1024

                with patch.object(artifact_manager, "_calculate_checksum", return_value="test123"):
                    with patch.object(artifact_manager, "load_metadata", return_value={}):
                        with patch.object(artifact_manager, "save_metadata") as mock_save:
                            artifact_manager.register_artifact("build", artifact_path)

                            save_call = mock_save.call_args[0][0]
                            artifact_record = save_call["artifacts"]["test123"]

                            # Path should be relative to base_dir - use as_posix() for consistent path format
                            expected_path = Path("build/test_artifact.bin").as_posix()
                            assert artifact_record["path"] == expected_path

    def test_load_metadata_file_read_error(self, artifact_manager):
        """Test load_metadata with file read error."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("Cannot read file")):
                with pytest.raises(IOError):
                    artifact_manager.load_metadata()

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("shutil.rmtree", side_effect=OSError("Cannot remove directory"))
    def test_cleanup_old_artifacts_remove_error(
        self, mock_rmtree, mock_is_dir, mock_exists, artifact_manager
    ):
        """Test cleanup with file removal error."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()

        artifacts = {"old_dir": {"type": "build", "path": "build/old_dir", "created_at": old_date}}

        mock_exists.return_value = True
        mock_is_dir.return_value = True

        with patch.object(artifact_manager, "load_metadata", return_value={"artifacts": artifacts}):
            with patch.object(artifact_manager, "save_metadata"):
                # Should raise the removal error
                with pytest.raises(OSError):
                    artifact_manager.cleanup_old_artifacts(days=30)
