"""Tests for typer_patch module."""

from unittest.mock import Mock, patch
import typer.core
import click.core

from ovmobilebench.typer_patch import (
    patched_format_help,
    patched_get_help_record_option,
    patched_get_help_record_argument,
)


class TestPatchedFormatHelp:
    """Test patched_format_help function."""

    def test_patched_format_help(self):
        """Test that patched format_help calls parent class method."""
        # Create mock objects
        mock_self = Mock(spec=typer.core.TyperCommand)
        mock_ctx = Mock()
        mock_formatter = Mock()

        # Patch the parent class method
        with patch.object(click.core.Command, "format_help") as mock_parent_format_help:
            patched_format_help(mock_self, mock_ctx, mock_formatter)

            # Verify parent method was called
            mock_parent_format_help.assert_called_once_with(mock_self, mock_ctx, mock_formatter)


class TestPatchedGetHelpRecordOption:
    """Test patched_get_help_record_option function."""

    def test_with_metavar(self):
        """Test with explicit metavar."""
        mock_self = Mock(spec=typer.core.TyperOption)
        mock_self.opts = ["--option", "-o"]
        mock_self.secondary_opts = None
        mock_self.metavar = "VALUE"
        mock_self.is_flag = False
        mock_self.help = "Test help"
        mock_self.default = None

        mock_ctx = Mock()

        result = patched_get_help_record_option(mock_self, mock_ctx)

        assert result[0] == "--option, -o VALUE"
        assert result[1] == "Test help"

    def test_without_metavar(self):
        """Test without metavar, should call make_metavar."""
        mock_self = Mock(spec=typer.core.TyperOption)
        mock_self.opts = ["--option"]
        mock_self.secondary_opts = None
        mock_self.metavar = None
        mock_self.is_flag = False
        mock_self.make_metavar.return_value = "TEXT"
        mock_self.help = "Test help"
        mock_self.default = None

        mock_ctx = Mock()

        result = patched_get_help_record_option(mock_self, mock_ctx)

        mock_self.make_metavar.assert_called_once_with(mock_ctx)
        assert result[0] == "--option TEXT"
        assert result[1] == "Test help"

    def test_with_secondary_opts(self):
        """Test with secondary options."""
        mock_self = Mock(spec=typer.core.TyperOption)
        mock_self.opts = ["--option"]
        mock_self.secondary_opts = ["--opt", "-o"]
        mock_self.metavar = "VALUE"
        mock_self.is_flag = False
        mock_self.help = "Test help"
        mock_self.default = None

        mock_ctx = Mock()

        result = patched_get_help_record_option(mock_self, mock_ctx)

        assert result[0] == "--opt, -o, --option VALUE"
        assert result[1] == "Test help"

    def test_with_default_value(self):
        """Test with default value."""
        mock_self = Mock(spec=typer.core.TyperOption)
        mock_self.opts = ["--option"]
        mock_self.secondary_opts = None
        mock_self.metavar = "VALUE"
        mock_self.is_flag = False
        mock_self.help = "Test help"
        mock_self.default = "default_val"

        mock_ctx = Mock()

        result = patched_get_help_record_option(mock_self, mock_ctx)

        assert result[0] == "--option VALUE"
        assert result[1] == "Test help  [default: default_val]"

    def test_with_default_no_help(self):
        """Test with default but no help text."""
        mock_self = Mock(spec=typer.core.TyperOption)
        mock_self.opts = ["--option"]
        mock_self.secondary_opts = None
        mock_self.metavar = "VALUE"
        mock_self.is_flag = False
        mock_self.help = None
        mock_self.default = "default_val"

        mock_ctx = Mock()

        result = patched_get_help_record_option(mock_self, mock_ctx)

        assert result[0] == "--option VALUE"
        assert result[1] == "[default: default_val]"

    def test_flag_option(self):
        """Test flag option (no metavar needed)."""
        mock_self = Mock(spec=typer.core.TyperOption)
        mock_self.opts = ["--flag"]
        mock_self.secondary_opts = None
        mock_self.metavar = None
        mock_self.is_flag = True
        mock_self.help = "Enable flag"
        mock_self.default = False

        mock_ctx = Mock()

        result = patched_get_help_record_option(mock_self, mock_ctx)

        assert result[0] == "--flag"
        assert result[1] == "Enable flag"

    def test_empty_metavar(self):
        """Test when make_metavar returns empty string."""
        mock_self = Mock(spec=typer.core.TyperOption)
        mock_self.opts = ["--option"]
        mock_self.secondary_opts = None
        mock_self.metavar = None
        mock_self.is_flag = False
        mock_self.make_metavar.return_value = ""
        mock_self.help = "Test help"
        mock_self.default = None

        mock_ctx = Mock()

        result = patched_get_help_record_option(mock_self, mock_ctx)

        assert result[0] == "--option"
        assert result[1] == "Test help"


class TestPatchedGetHelpRecordArgument:
    """Test patched_get_help_record_argument function."""

    def test_with_help(self):
        """Test argument with help text."""
        mock_self = Mock(spec=typer.core.TyperArgument)
        mock_self.help = "Argument help"
        mock_self.make_metavar.return_value = "ARG"

        mock_ctx = Mock()

        result = patched_get_help_record_argument(mock_self, mock_ctx)

        mock_self.make_metavar.assert_called_once_with(mock_ctx)
        assert result[0] == "ARG"
        assert result[1] == "Argument help"

    def test_without_help(self):
        """Test argument without help text."""
        mock_self = Mock(spec=typer.core.TyperArgument)
        mock_self.help = None

        mock_ctx = Mock()

        result = patched_get_help_record_argument(mock_self, mock_ctx)

        assert result is None


class TestPatchApplication:
    """Test that patches are applied correctly."""

    def test_patches_applied(self):
        """Test that all patches are applied to typer.core classes."""
        # Import after patching
        import ovmobilebench.typer_patch  # noqa: F401

        # Check that patches are applied
        assert typer.core.TyperCommand.format_help == patched_format_help
        assert typer.core.TyperGroup.format_help == patched_format_help
        assert typer.core.TyperOption.get_help_record == patched_get_help_record_option
        assert typer.core.TyperArgument.get_help_record == patched_get_help_record_argument
