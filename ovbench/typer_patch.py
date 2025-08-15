"""Patch for Typer compatibility issues."""

import typer.core
import typer.rich_utils
import click.core


# Override format_help to bypass Rich formatting
def patched_format_help(self, ctx, formatter):
    """Use standard Click help formatting instead of Rich."""
    # Call parent class's format_help to bypass Rich
    click.core.Command.format_help(self, ctx, formatter)


# Fix get_help_record for TyperOption to pass ctx to make_metavar
def patched_get_help_record_option(self, ctx):
    """Fixed get_help_record that properly passes ctx to make_metavar."""

    def _write_opts(opts):
        rv = ", ".join(opts)
        if self.secondary_opts:
            rv = ", ".join(self.secondary_opts) + ", " + rv
        return rv

    opts_str = _write_opts(self.opts)
    if self.metavar:
        opts_str += f" {self.metavar}"
    elif not self.is_flag:
        # Pass ctx to make_metavar - this is the fix
        metavar = self.make_metavar(ctx)
        if metavar:
            opts_str += f" {metavar}"

    help_text = self.help or ""
    if self.default is not None and not self.is_flag:
        if help_text:
            help_text = f"{help_text}  [default: {self.default}]"
        else:
            help_text = f"[default: {self.default}]"

    return (opts_str, help_text)


# Fix get_help_record for TyperArgument to pass ctx to make_metavar
def patched_get_help_record_argument(self, ctx):
    """Fixed get_help_record for TyperArgument."""
    if self.help:
        return (self.make_metavar(ctx), self.help)
    return None


# Apply patches
typer.core.TyperCommand.format_help = patched_format_help  # type: ignore[method-assign]
typer.core.TyperGroup.format_help = patched_format_help  # type: ignore[method-assign]
typer.core.TyperOption.get_help_record = patched_get_help_record_option  # type: ignore[method-assign]
typer.core.TyperArgument.get_help_record = patched_get_help_record_argument  # type: ignore[method-assign]
