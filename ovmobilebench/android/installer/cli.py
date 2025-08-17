"""CLI interface for Android installer."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional, cast

import typer
from rich.console import Console
from rich.table import Table

from .api import ensure_android_tools, export_android_env, verify_installation
from .detect import get_recommended_settings
from .errors import InstallerError
from .types import NdkSpec

app = typer.Typer(
    name="android",
    help="Android SDK/NDK installation and management tools",
    no_args_is_help=True,
)

console = Console()


@app.command("setup")
def setup(
    sdk_root: Path = typer.Option(
        Path.home() / "Android" / "Sdk",
        "--sdk-root",
        "-s",
        help="SDK root directory",
    ),
    api: int = typer.Option(
        30,
        "--api",
        "-a",
        help="Android API level (e.g., 30 for Android 11)",
    ),
    target: str = typer.Option(
        "google_atd",
        "--target",
        "-t",
        help="System image target: google_atd, google_apis, default",
    ),
    arch: str = typer.Option(
        None,
        "--arch",
        help="Architecture: arm64-v8a, x86_64, x86, armeabi-v7a (auto-detect if not specified)",
    ),
    ndk: str = typer.Option(
        "r26d",
        "--ndk",
        "-n",
        help="NDK version (e.g., r26d) or absolute path",
    ),
    with_platform_tools: bool = typer.Option(
        True,
        "--with-platform-tools/--no-platform-tools",
        help="Install platform-tools (adb, fastboot)",
    ),
    with_emulator: bool = typer.Option(
        True,
        "--with-emulator/--no-emulator",
        help="Install emulator and system image",
    ),
    with_build_tools: Optional[str] = typer.Option(
        None,
        "--with-build-tools",
        help="Install specific build-tools version",
    ),
    create_avd: Optional[str] = typer.Option(
        None,
        "--create-avd",
        help="Create AVD with specified name",
    ),
    accept_licenses: bool = typer.Option(
        True,
        "--accept-licenses/--prompt-licenses",
        help="Automatically accept SDK licenses",
    ),
    export_env: Optional[Path] = typer.Option(
        None,
        "--export-env",
        help="Export environment variables to file (e.g., $GITHUB_ENV)",
    ),
    print_env: bool = typer.Option(
        False,
        "--print-env",
        help="Print environment variables to stdout",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be installed without making changes",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
    jsonl_log: Optional[Path] = typer.Option(
        None,
        "--jsonl-log",
        help="Write structured logs to JSON lines file",
    ),
) -> None:
    """Install Android SDK, NDK, and related tools.

    This command installs and configures the Android development environment
    including SDK tools, NDK, platform tools, emulator, and optionally creates
    an AVD for testing.

    Examples:
        # Basic installation with defaults
        ovmobilebench android setup

        # Install for CI with specific versions
        ovmobilebench android setup --api 30 --ndk r26d --create-avd test_avd

        # Export environment for GitHub Actions
        ovmobilebench android setup --export-env $GITHUB_ENV --print-env

        # Dry run to see what would be installed
        ovmobilebench android setup --dry-run --verbose
    """
    try:
        # Auto-detect architecture if not specified
        if not arch:
            settings = get_recommended_settings()
            arch = settings["arch"]
            if verbose:
                console.print(f"[cyan]Auto-detected architecture: {arch}[/cyan]")

        # Parse NDK specification
        ndk_path = Path(ndk) if Path(ndk).exists() else None
        ndk_spec = NdkSpec(path=ndk_path) if ndk_path else NdkSpec(alias=ndk)

        # Show configuration
        if verbose or dry_run:
            console.print("\n[bold]Configuration:[/bold]")
            config_table = Table(show_header=False)
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value")
            
            config_table.add_row("SDK Root", str(sdk_root))
            config_table.add_row("API Level", str(api))
            config_table.add_row("Target", target)
            config_table.add_row("Architecture", arch)
            config_table.add_row("NDK", ndk)
            config_table.add_row("Platform Tools", "Yes" if with_platform_tools else "No")
            config_table.add_row("Emulator", "Yes" if with_emulator else "No")
            if with_build_tools:
                config_table.add_row("Build Tools", with_build_tools)
            if create_avd:
                config_table.add_row("AVD", create_avd)
            config_table.add_row("Dry Run", "Yes" if dry_run else "No")
            
            console.print(config_table)
            console.print()

        # Run installation
        with console.status("[bold green]Installing Android tools...") if not verbose else nullcontext():
            result = ensure_android_tools(
                sdk_root=sdk_root,
                api=api,
                target=cast(Any, target),  # Cast to satisfy type checker
                arch=cast(Any, arch),  # Cast to satisfy type checker
                ndk=ndk_spec,
                install_platform_tools=with_platform_tools,
                install_emulator=with_emulator,
                install_build_tools=with_build_tools,
                create_avd_name=create_avd,
                accept_licenses=accept_licenses,
                dry_run=dry_run,
                verbose=verbose,
                jsonl_log=jsonl_log,
            )

        # Export environment if requested
        if (export_env or print_env) and not dry_run:
            export_android_env(
                github_env=export_env,
                print_stdout=print_env,
                sdk_root=result["sdk_root"],
                ndk_path=result["ndk_path"],
            )
            
            if export_env and verbose:
                console.print(f"[green]✓[/green] Environment exported to: {export_env}")

        # Show summary
        if not dry_run:
            console.print("\n[bold green]✓ Installation complete![/bold green]")
            console.print(f"  SDK Root: {result['sdk_root']}")
            console.print(f"  NDK Path: {result['ndk_path']}")
            if result.get("avd_created"):
                console.print(f"  AVD Created: {create_avd}")
        elif verbose:
            console.print("\n[yellow]Dry run complete (no changes made)[/yellow]")

    except InstallerError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose and hasattr(e, "details"):
            console.print(f"[dim]Details: {e.details}[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@app.command("verify")
def verify(
    sdk_root: Path = typer.Option(
        Path.home() / "Android" / "Sdk",
        "--sdk-root",
        "-s",
        help="SDK root directory",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information",
    ),
) -> None:
    """Verify Android tools installation.

    Check the status of Android SDK, NDK, and related tools installation.

    Example:
        ovmobilebench android verify --sdk-root /opt/android-sdk
    """
    try:
        console.print(f"[cyan]Verifying installation at: {sdk_root}[/cyan]\n")
        
        status = verify_installation(sdk_root, verbose=verbose)
        
        # Create status table
        table = Table(title="Installation Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        # SDK root
        table.add_row(
            "SDK Root",
            "✓" if status["sdk_root_exists"] else "✗",
            str(sdk_root) if status["sdk_root_exists"] else "Not found",
        )
        
        # Command-line tools
        table.add_row(
            "Command-line Tools",
            "✓" if status["cmdline_tools"] else "✗",
            "Installed" if status["cmdline_tools"] else "Not installed",
        )
        
        # Platform tools
        table.add_row(
            "Platform Tools",
            "✓" if status["platform_tools"] else "✗",
            "Installed" if status["platform_tools"] else "Not installed",
        )
        
        # Emulator
        table.add_row(
            "Emulator",
            "✓" if status["emulator"] else "✗",
            "Installed" if status["emulator"] else "Not installed",
        )
        
        # NDK
        ndk_details = "Not installed"
        if status["ndk"] and status.get("ndk_versions"):
            ndk_details = ", ".join(status["ndk_versions"])
        table.add_row(
            "NDK",
            "✓" if status["ndk"] else "✗",
            ndk_details,
        )
        
        # AVDs
        avd_details = "None"
        if status.get("avds"):
            avd_details = ", ".join(status["avds"])
        table.add_row(
            "AVDs",
            "✓" if status.get("avds") else "-",
            avd_details,
        )
        
        console.print(table)
        
        # Show installed components if verbose
        if verbose and status.get("components"):
            console.print("\n[bold]Installed Components:[/bold]")
            for component in status["components"]:
                console.print(f"  • {component}")
        
        # Exit code based on status
        if not status["sdk_root_exists"]:
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@app.command("list-targets")
def list_targets() -> None:
    """List valid API/target/architecture combinations.

    Shows all supported combinations for system images.
    """
    from .plan import Planner
    
    console.print("[bold]Supported System Image Combinations:[/bold]\n")
    
    # Group by API level
    combinations: Dict[int, Dict[str, list]] = {}
    for api, target, arch in Planner.VALID_COMBINATIONS:
        if api not in combinations:
            combinations[api] = {}
        if target not in combinations[api]:
            combinations[api][target] = []
        combinations[api][target].append(arch)
    
    # Display as table
    for api in sorted(combinations.keys(), reverse=True):
        table = Table(title=f"API Level {api}")
        table.add_column("Target", style="cyan")
        table.add_column("Architectures")
        
        for target in sorted(combinations[api].keys()):
            archs = ", ".join(sorted(combinations[api][target]))
            table.add_row(target, archs)
        
        console.print(table)
        console.print()


# Context manager for when console status is not needed
class nullcontext:
    """Null context manager."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


if __name__ == "__main__":
    app()