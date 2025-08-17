"""Environment variable export utilities."""

import os
import sys
from pathlib import Path

from .logging import StructuredLogger


class EnvExporter:
    """Export Android SDK/NDK environment variables."""

    def __init__(self, logger: StructuredLogger | None = None):
        """Initialize environment exporter.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger

    def export(
        self,
        github_env: Path | None = None,
        print_stdout: bool = False,
        sdk_root: Path | None = None,
        ndk_path: Path | None = None,
    ) -> dict[str, str]:
        """Export environment variables.

        Args:
            github_env: Path to GitHub environment file
            print_stdout: Print variables to stdout
            sdk_root: Android SDK root path
            ndk_path: Android NDK path

        Returns:
            Dictionary of exported variables
        """
        env_vars: dict[str, str] = {}

        # Build environment variables
        if sdk_root and sdk_root.exists():
            sdk_root_str = str(sdk_root.absolute())
            env_vars["ANDROID_SDK_ROOT"] = sdk_root_str
            env_vars["ANDROID_HOME"] = sdk_root_str  # Legacy compatibility

            # Add platform-tools to PATH if it exists
            platform_tools = sdk_root / "platform-tools"
            if platform_tools.exists():
                env_vars["ANDROID_PLATFORM_TOOLS"] = str(platform_tools.absolute())

        if ndk_path and ndk_path.exists():
            ndk_path_str = str(ndk_path.absolute())
            env_vars["ANDROID_NDK"] = ndk_path_str
            env_vars["ANDROID_NDK_ROOT"] = ndk_path_str  # Legacy compatibility
            env_vars["ANDROID_NDK_HOME"] = ndk_path_str  # Legacy compatibility
            env_vars["NDK_ROOT"] = ndk_path_str  # Some tools expect this

        # Export to GitHub environment file
        if github_env:
            self._export_to_github_env(github_env, env_vars)

        # Print to stdout if requested
        if print_stdout:
            self._print_to_stdout(env_vars)

        # Also set in current process
        self._set_in_process(env_vars)

        if self.logger:
            self.logger.info(
                f"Exported {len(env_vars)} environment variables",
                variables=list(env_vars.keys()),
            )

        return env_vars

    def _export_to_github_env(self, github_env: Path, env_vars: dict[str, str]) -> None:
        """Export variables to GitHub environment file.

        Args:
            github_env: Path to GitHub environment file
            env_vars: Variables to export
        """
        try:
            with open(github_env, "a", encoding="utf-8") as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")

            if self.logger:
                self.logger.debug(
                    f"Exported to GitHub environment: {github_env}",
                    path=str(github_env),
                    count=len(env_vars),
                )
        except OSError as e:
            if self.logger:
                self.logger.error(
                    f"Failed to write to GitHub environment file: {e}",
                    path=str(github_env),
                    error=str(e),
                )
            raise

    def _print_to_stdout(self, env_vars: dict[str, str]) -> None:
        """Print variables to stdout for shell evaluation.

        Args:
            env_vars: Variables to print
        """
        # Detect shell type
        shell = os.environ.get("SHELL", "").lower()
        is_windows = sys.platform.startswith("win")

        if is_windows:
            # Windows Command Prompt format
            for key, value in env_vars.items():
                print(f"set {key}={value}")
        elif "fish" in shell:
            # Fish shell format
            for key, value in env_vars.items():
                print(f"set -x {key} {value}")
        else:
            # Bash/Zsh format (default)
            for key, value in env_vars.items():
                print(f'export {key}="{value}"')

        # Special handling for PATH additions
        if "ANDROID_PLATFORM_TOOLS" in env_vars:
            platform_tools = env_vars["ANDROID_PLATFORM_TOOLS"]
            if is_windows:
                print(f"set PATH=%PATH%;{platform_tools}")
            elif "fish" in shell:
                print(f"set -x PATH {platform_tools} $PATH")
            else:
                print(f'export PATH="{platform_tools}:$PATH"')

    def _set_in_process(self, env_vars: dict[str, str]) -> None:
        """Set variables in current process environment.

        Args:
            env_vars: Variables to set
        """
        for key, value in env_vars.items():
            if key != "ANDROID_PLATFORM_TOOLS":  # Don't modify PATH in process
                os.environ[key] = value

    def save_to_file(self, path: Path, env_vars: dict[str, str]) -> None:
        """Save environment variables to a file.

        Args:
            path: File path to save to
            env_vars: Variables to save
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            # Write as shell script
            f.write("#!/bin/bash\n")
            f.write("# Android SDK/NDK environment variables\n")
            f.write("# Generated by ovmobilebench.android.installer\n\n")

            for key, value in env_vars.items():
                if key == "ANDROID_PLATFORM_TOOLS":
                    f.write(f'export PATH="{value}:$PATH"\n')
                else:
                    f.write(f'export {key}="{value}"\n')

        # Make executable on Unix-like systems
        if not sys.platform.startswith("win"):
            path.chmod(0o755)

        if self.logger:
            self.logger.info(f"Saved environment script to: {path}", path=str(path))

    def load_from_file(self, path: Path) -> dict[str, str]:
        """Load environment variables from a file.

        Args:
            path: File path to load from

        Returns:
            Dictionary of loaded variables
        """
        env_vars: dict[str, str] = {}

        if not path.exists():
            if self.logger:
                self.logger.warning(f"Environment file not found: {path}")
            return env_vars

        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse export statements
                if line.startswith("export "):
                    line = line[7:]  # Remove "export "

                # Parse KEY=VALUE or KEY="VALUE"
                if "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    # Skip PATH modifications
                    if not key.startswith("PATH"):
                        env_vars[key] = value

        if self.logger:
            self.logger.debug(
                f"Loaded {len(env_vars)} variables from: {path}",
                path=str(path),
                variables=list(env_vars.keys()),
            )

        return env_vars


def export_android_env(
    github_env: Path | None = None,
    print_stdout: bool = False,
    sdk_root: Path | None = None,
    ndk_path: Path | None = None,
    logger: StructuredLogger | None = None,
) -> dict[str, str]:
    """Convenience function to export Android environment variables.

    Args:
        github_env: Path to GitHub environment file
        print_stdout: Print variables to stdout
        sdk_root: Android SDK root path
        ndk_path: Android NDK path
        logger: Optional logger instance

    Returns:
        Dictionary of exported variables
    """
    exporter = EnvExporter(logger=logger)
    return exporter.export(
        github_env=github_env,
        print_stdout=print_stdout,
        sdk_root=sdk_root,
        ndk_path=ndk_path,
    )
