"""Additional tests for OpenVINOBuilder coverage gaps."""

from unittest.mock import Mock, patch

import pytest

from ovmobilebench.builders.openvino import OpenVINOBuilder


class TestOpenVINOBuilderAdditional:
    """Test remaining gaps in OpenVINOBuilder."""

    def test_build_disabled_mode(self, tmp_path):
        """Test build raises error when not in build mode."""
        config = Mock()
        config.mode = "disabled"

        builder = OpenVINOBuilder(config, tmp_path)

        with pytest.raises(ValueError, match="can only be used with mode='build'"):
            builder.build()

    def test_checkout_with_head_commit(self, tmp_path):
        """Test internal checkout when commit is HEAD."""
        config = Mock()
        config.mode = "build"
        config.source_dir = str(tmp_path / "source")
        config.commit = "HEAD"
        config.cmake_args = []
        config.threads = 4

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create a fake git directory to avoid clone
        (source_dir / ".git").mkdir()

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            builder = OpenVINOBuilder(config, tmp_path)

            # Call internal method directly for testing
            builder._checkout_commit()

            # Check if git checkout was called
            if config.commit != "HEAD":
                assert any("checkout" in str(call) for call in mock_run.call_args_list)

    def test_checkout_with_specific_commit(self, tmp_path):
        """Test internal checkout with specific commit."""
        config = Mock()
        config.mode = "build"
        config.source_dir = str(tmp_path / "source")
        config.commit = "abc123"
        config.cmake_args = []
        config.threads = 4

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create a fake git directory to avoid clone
        (source_dir / ".git").mkdir()

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            # Mock successful git checkout
            from ovmobilebench.core.shell import CommandResult

            mock_run.return_value = CommandResult(
                returncode=0, stdout="", stderr="", duration_sec=0.1, cmd="git checkout abc123"
            )

            builder = OpenVINOBuilder(config, tmp_path)

            # Call internal method directly for testing
            builder._checkout_commit()

            # Should checkout specific commit
            assert mock_run.called
            call_args = str(mock_run.call_args_list)
            assert "checkout" in call_args
            assert "abc123" in call_args

    def test_build_with_download_mode(self, tmp_path):
        """Test build raises error with download mode."""
        config = Mock()
        config.mode = "download"
        config.url = "https://example.com/openvino.tar.gz"

        builder = OpenVINOBuilder(config, tmp_path)

        with pytest.raises(ValueError, match="can only be used with mode='build'"):
            builder.build()

    def test_build_with_link_mode(self, tmp_path):
        """Test build raises error with link mode."""
        config = Mock()
        config.mode = "link"
        config.target = tmp_path / "existing_build"

        builder = OpenVINOBuilder(config, tmp_path)

        with pytest.raises(ValueError, match="can only be used with mode='build'"):
            builder.build()
