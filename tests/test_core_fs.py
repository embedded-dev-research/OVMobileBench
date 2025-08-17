"""Tests for core filesystem utilities module."""

import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ovmobilebench.core.fs import (
    atomic_write,
    clean_dir,
    copy_tree,
    ensure_dir,
    format_size,
    get_digest,
    get_size,
)


class TestEnsureDir:
    """Test ensure_dir function."""

    def test_ensure_dir_creates_new_directory(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_directory"
            result = ensure_dir(new_dir)

            assert new_dir.exists()
            assert new_dir.is_dir()
            assert result == new_dir

    def test_ensure_dir_existing_directory(self):
        """Test with existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir)
            result = ensure_dir(existing_dir)

            assert existing_dir.exists()
            assert result == existing_dir

    def test_ensure_dir_creates_parent_directories(self):
        """Test creating nested directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "parent" / "child" / "grandchild"
            result = ensure_dir(nested_dir)

            assert nested_dir.exists()
            assert nested_dir.is_dir()
            assert result == nested_dir

    def test_ensure_dir_with_string_path(self):
        """Test ensure_dir with string path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir_str = str(Path(temp_dir) / "string_dir")
            result = ensure_dir(new_dir_str)

            assert Path(new_dir_str).exists()
            assert isinstance(result, Path)

    @patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied"))
    def test_ensure_dir_permission_error(self, mock_mkdir):
        """Test handling permission error."""
        with pytest.raises(PermissionError):
            ensure_dir("/root/restricted")


class TestAtomicWrite:
    """Test atomic_write function."""

    def test_atomic_write_success(self):
        """Test successful atomic write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_file.txt"
            content = "test content"

            atomic_write(file_path, content)

            assert file_path.exists()
            assert file_path.read_text() == content

    def test_atomic_write_creates_parent_directory(self):
        """Test that atomic_write creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nested" / "path" / "test_file.txt"
            content = "test content"

            atomic_write(file_path, content)

            assert file_path.exists()
            assert file_path.read_text() == content
            assert file_path.parent.exists()

    def test_atomic_write_with_string_path(self):
        """Test atomic_write with string path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = str(Path(temp_dir) / "string_file.txt")
            content = "test content"

            atomic_write(file_path, content)

            assert Path(file_path).exists()
            assert Path(file_path).read_text() == content

    def test_atomic_write_custom_mode(self):
        """Test atomic_write with custom mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_file.txt"
            content = "test content"

            atomic_write(file_path, content, mode="w")

            assert file_path.exists()
            assert file_path.read_text() == content

    @patch("tempfile.NamedTemporaryFile")
    @patch("pathlib.Path.replace")
    def test_atomic_write_uses_temporary_file(self, mock_replace, mock_temp_file):
        """Test that atomic_write uses temporary file and rename."""
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/temp_file"
        mock_temp.__enter__.return_value = mock_temp
        mock_temp_file.return_value = mock_temp

        with patch("ovmobilebench.core.fs.ensure_dir"):
            atomic_write("/test/file.txt", "content")

            mock_temp_file.assert_called_once()
            mock_temp.write.assert_called_once_with("content")
            mock_temp.flush.assert_called_once()
            mock_replace.assert_called_once()

    @patch("tempfile.NamedTemporaryFile", side_effect=IOError("Cannot create temp file"))
    def test_atomic_write_temp_file_error(self, mock_temp_file):
        """Test handling temporary file creation error."""
        with pytest.raises(IOError):
            atomic_write("/test/file.txt", "content")


class TestGetDigest:
    """Test get_digest function."""

    def test_get_digest_default_algorithm(self):
        """Test digest calculation with default SHA256."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            temp_file.flush()
            temp_path = temp_file.name

        try:
            digest = get_digest(temp_path)

            # Calculate expected digest
            expected = hashlib.sha256("test content".encode()).hexdigest()
            assert digest == expected
            assert len(digest) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_get_digest_custom_algorithm(self):
        """Test digest calculation with custom algorithm."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            temp_file.flush()
            temp_path = temp_file.name

        try:
            digest = get_digest(temp_path, algorithm="md5")

            expected = hashlib.md5("test content".encode()).hexdigest()
            assert digest == expected
            assert len(digest) == 32  # MD5 hex length
        finally:
            os.unlink(temp_path)

    def test_get_digest_large_file(self):
        """Test digest calculation for large file (chunked reading)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            # Write content larger than chunk size (65536 bytes)
            large_content = "a" * 100000
            temp_file.write(large_content)
            temp_file.flush()
            temp_path = temp_file.name

        try:
            digest = get_digest(temp_path)

            expected = hashlib.sha256(large_content.encode()).hexdigest()
            assert digest == expected
        finally:
            os.unlink(temp_path)

    def test_get_digest_with_path_object(self):
        """Test digest calculation with Path object."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            temp_file.flush()
            temp_path = temp_file.name

        try:
            digest = get_digest(Path(temp_path))

            expected = hashlib.sha256("test content".encode()).hexdigest()
            assert digest == expected
        finally:
            os.unlink(temp_path)

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_get_digest_file_not_found(self, mock_open):
        """Test handling file not found error."""
        with pytest.raises(FileNotFoundError):
            get_digest("/nonexistent/file.txt")

    @patch("hashlib.new", side_effect=ValueError("Invalid algorithm"))
    def test_get_digest_invalid_algorithm(self, mock_hashlib):
        """Test handling invalid hash algorithm."""
        with pytest.raises(ValueError):
            get_digest("/test/file.txt", algorithm="invalid")


class TestCopyTree:
    """Test copy_tree function."""

    def test_copy_tree_file(self):
        """Test copying a single file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = Path(temp_dir) / "source.txt"
            dst_file = Path(temp_dir) / "destination.txt"
            src_file.write_text("test content")

            copy_tree(src_file, dst_file)

            assert dst_file.exists()
            assert dst_file.read_text() == "test content"

    def test_copy_tree_directory(self):
        """Test copying a directory tree."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "source"
            dst_dir = Path(temp_dir) / "destination"

            # Create source structure
            src_dir.mkdir()
            (src_dir / "file1.txt").write_text("content1")
            (src_dir / "subdir").mkdir()
            (src_dir / "subdir" / "file2.txt").write_text("content2")

            copy_tree(src_dir, dst_dir)

            assert dst_dir.exists()
            assert (dst_dir / "file1.txt").exists()
            assert (dst_dir / "subdir" / "file2.txt").exists()
            assert (dst_dir / "file1.txt").read_text() == "content1"
            assert (dst_dir / "subdir" / "file2.txt").read_text() == "content2"

    def test_copy_tree_with_symlinks(self):
        """Test copying directory with symlinks."""
        import platform

        import pytest

        # Skip on Windows if not running as admin
        if platform.system() == "Windows":
            import ctypes

            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if not is_admin:
                pytest.skip("Symlink test requires admin privileges on Windows")

        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "source"
            dst_dir = Path(temp_dir) / "destination"

            src_dir.mkdir()
            (src_dir / "file.txt").write_text("content")

            try:
                (src_dir / "link.txt").symlink_to("file.txt")
            except OSError as e:
                if platform.system() == "Windows":
                    pytest.skip(f"Cannot create symlink on Windows: {e}")
                raise

            copy_tree(src_dir, dst_dir, symlinks=True)

            assert dst_dir.exists()
            assert (dst_dir / "file.txt").exists()
            assert (dst_dir / "link.txt").exists()
            assert (dst_dir / "link.txt").is_symlink()

    def test_copy_tree_source_not_found(self):
        """Test copying non-existent source."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = Path(temp_dir) / "nonexistent"
            dst_path = Path(temp_dir) / "destination"

            with pytest.raises(FileNotFoundError) as exc_info:
                copy_tree(src_path, dst_path)

            assert "Source not found" in str(exc_info.value)

    def test_copy_tree_file_creates_parent_dir(self):
        """Test that copying file creates parent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = Path(temp_dir) / "source.txt"
            dst_file = Path(temp_dir) / "nested" / "path" / "destination.txt"
            src_file.write_text("test content")

            copy_tree(src_file, dst_file)

            assert dst_file.exists()
            assert dst_file.parent.exists()

    @patch("shutil.copy2", side_effect=PermissionError("Permission denied"))
    def test_copy_tree_file_permission_error(self, mock_copy2):
        """Test handling permission error when copying file."""
        with pytest.raises(PermissionError):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    copy_tree("/test/source.txt", "/test/dest.txt")

    @patch("shutil.copytree", side_effect=PermissionError("Permission denied"))
    def test_copy_tree_dir_permission_error(self, mock_copytree):
        """Test handling permission error when copying directory."""
        with pytest.raises(PermissionError):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=False):
                    copy_tree("/test/source", "/test/dest")


class TestCleanDir:
    """Test clean_dir function."""

    def test_clean_dir_keep_root(self):
        """Test cleaning directory contents while keeping root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()

            # Create some content
            (test_dir / "file1.txt").write_text("content")
            (test_dir / "subdir").mkdir()
            (test_dir / "subdir" / "file2.txt").write_text("content")

            clean_dir(test_dir, keep_root=True)

            assert test_dir.exists()  # Root should still exist
            assert len(list(test_dir.iterdir())) == 0  # But be empty

    def test_clean_dir_remove_root(self):
        """Test cleaning directory and removing root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()

            # Create some content
            (test_dir / "file1.txt").write_text("content")
            (test_dir / "subdir").mkdir()

            clean_dir(test_dir, keep_root=False)

            assert not test_dir.exists()  # Root should be removed

    def test_clean_dir_nonexistent_directory(self):
        """Test cleaning non-existent directory (should not raise error)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_dir = Path(temp_dir) / "nonexistent"

            # Should not raise any exception
            clean_dir(nonexistent_dir)
            clean_dir(nonexistent_dir, keep_root=False)

    def test_clean_dir_with_string_path(self):
        """Test clean_dir with string path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()
            (test_dir / "file.txt").write_text("content")

            clean_dir(str(test_dir))

            assert test_dir.exists()
            assert len(list(test_dir.iterdir())) == 0

    @patch("shutil.rmtree", side_effect=PermissionError("Permission denied"))
    def test_clean_dir_permission_error_remove_root(self, mock_rmtree):
        """Test handling permission error when removing root."""
        with pytest.raises(PermissionError):
            with patch("pathlib.Path.exists", return_value=True):
                clean_dir("/test/dir", keep_root=False)


class TestGetSize:
    """Test get_size function."""

    def test_get_size_file(self):
        """Test getting size of a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            content = "test content"
            temp_file.write(content)
            temp_file.flush()
            temp_path = temp_file.name

        try:
            size = get_size(temp_path)
            assert size == len(content.encode())
        finally:
            os.unlink(temp_path)

    def test_get_size_directory(self):
        """Test getting size of a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()

            # Create files with known sizes
            (test_dir / "file1.txt").write_text("12345")  # 5 bytes
            (test_dir / "subdir").mkdir()
            (test_dir / "subdir" / "file2.txt").write_text("1234567890")  # 10 bytes

            size = get_size(test_dir)
            assert size == 15  # 5 + 10 bytes

    def test_get_size_empty_directory(self):
        """Test getting size of empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "empty_dir"
            test_dir.mkdir()

            size = get_size(test_dir)
            assert size == 0

    def test_get_size_with_path_object(self):
        """Test get_size with Path object."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test")
            temp_file.flush()
            temp_path = temp_file.name

        try:
            size = get_size(Path(temp_path))
            assert size == 4
        finally:
            os.unlink(temp_path)

    @patch("pathlib.Path.stat", side_effect=FileNotFoundError("File not found"))
    def test_get_size_file_not_found(self, mock_stat):
        """Test handling file not found error."""
        with pytest.raises(FileNotFoundError):
            with patch("pathlib.Path.is_file", return_value=True):
                get_size("/nonexistent/file.txt")


class TestFormatSize:
    """Test format_size function."""

    def test_format_size_bytes(self):
        """Test formatting size in bytes."""
        assert format_size(100) == "100.00 B"
        assert format_size(1023) == "1023.00 B"

    def test_format_size_kilobytes(self):
        """Test formatting size in kilobytes."""
        assert format_size(1024) == "1.00 KB"
        assert format_size(1536) == "1.50 KB"  # 1.5 KB
        assert format_size(1048575) == "1023.00 KB"  # Just under 1 MB

    def test_format_size_megabytes(self):
        """Test formatting size in megabytes."""
        assert format_size(1048576) == "1.00 MB"  # 1 MB
        assert format_size(1572864) == "1.50 MB"  # 1.5 MB
        assert format_size(1073741823) == "1023.00 MB"  # Just under 1 GB

    def test_format_size_gigabytes(self):
        """Test formatting size in gigabytes."""
        assert format_size(1073741824) == "1.00 GB"  # 1 GB
        assert format_size(1610612736) == "1.50 GB"  # 1.5 GB
        assert format_size(1099511627775) == "1023.00 GB"  # Just under 1 TB

    def test_format_size_terabytes(self):
        """Test formatting size in terabytes."""
        assert format_size(1099511627776) == "1.00 TB"  # 1 TB
        assert format_size(1649267441664) == "1.50 TB"  # 1.5 TB

    def test_format_size_zero(self):
        """Test formatting zero size."""
        assert format_size(0) == "0.00 B"

    def test_format_size_large_number(self):
        """Test formatting very large number."""
        very_large = 1024**5  # 1 PB in bytes, but formatted as TB
        result = format_size(very_large)
        assert result.endswith(" TB")
        assert "1024.00" in result
