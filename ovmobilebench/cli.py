"""Command-line interface for OVMobileBench."""

# Apply typer compatibility patch
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ovmobilebench import typer_patch  # noqa: F401
from ovmobilebench.config.loader import load_experiment
from ovmobilebench.pipeline import Pipeline

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Also set console code page to UTF-8 if possible
    try:
        import subprocess

        subprocess.run("chcp 65001", shell=True, capture_output=True)
    except Exception:
        pass

app = typer.Typer(
    name="ovmobilebench",
    help="End-to-end benchmarking pipeline for OpenVINO on mobile devices",
    add_completion=False,
    pretty_exceptions_enable=False,  # Disable pretty exceptions
    rich_markup_mode=None,  # Disable Rich formatting
)

# Configure console with safe encoding for Windows
console = Console(legacy_windows=True if sys.platform == "win32" else None)


@app.command()
def build(
    config: Path = typer.Option(..., "-c", "--config", help="Experiment config YAML file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run without actual execution"),
):
    """Build OpenVINO runtime and benchmark_app for target platform."""
    console.print("[bold blue]Building OpenVINO runtime...[/bold blue]")
    cfg = load_experiment(config)
    pipeline = Pipeline(cfg, verbose=verbose, dry_run=dry_run)
    pipeline.build()
    console.print("[bold green][OK] Build completed[/bold green]")


@app.command()
def package(
    config: Path = typer.Option(..., "-c", "--config", help="Experiment config YAML file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run without actual execution"),
):
    """Package runtime, libraries and models into deployable bundle."""
    console.print("[bold blue]Packaging bundle...[/bold blue]")
    cfg = load_experiment(config)
    pipeline = Pipeline(cfg, verbose=verbose, dry_run=dry_run)
    pipeline.package()
    console.print("[bold green][OK] Package created[/bold green]")


@app.command()
def deploy(
    config: Path = typer.Option(..., "-c", "--config", help="Experiment config YAML file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run without actual execution"),
):
    """Deploy bundle to target device(s)."""
    console.print("[bold blue]Deploying to device(s)...[/bold blue]")
    cfg = load_experiment(config)
    pipeline = Pipeline(cfg, verbose=verbose, dry_run=dry_run)
    pipeline.deploy()
    console.print("[bold green][OK] Deployment completed[/bold green]")


@app.command()
def run(
    config: Path = typer.Option(..., "-c", "--config", help="Experiment config YAML file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run without actual execution"),
    timeout: int | None = typer.Option(None, "--timeout", help="Timeout in seconds"),
    cooldown: int | None = typer.Option(None, "--cooldown", help="Cooldown between runs"),
):
    """Execute benchmark matrix on device(s)."""
    console.print("[bold blue]Running benchmarks...[/bold blue]")
    cfg = load_experiment(config)
    pipeline = Pipeline(cfg, verbose=verbose, dry_run=dry_run)
    pipeline.run(timeout=timeout, cooldown=cooldown)
    console.print("[bold green][OK] Benchmarks completed[/bold green]")


@app.command()
def report(
    config: Path = typer.Option(..., "-c", "--config", help="Experiment config YAML file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
):
    """Parse results and generate reports."""
    console.print("[bold blue]Generating reports...[/bold blue]")
    cfg = load_experiment(config)
    pipeline = Pipeline(cfg, verbose=verbose)
    pipeline.report()
    console.print("[bold green][OK] Reports generated[/bold green]")


@app.command()
def all(
    config: Path = typer.Option(..., "-c", "--config", help="Experiment config YAML file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run without actual execution"),
    timeout: int | None = typer.Option(None, "--timeout", help="Timeout in seconds"),
    cooldown: int | None = typer.Option(None, "--cooldown", help="Cooldown between runs"),
):
    """Execute complete pipeline: build, package, deploy, run, and report."""
    # Check if we're in CI environment
    is_ci = os.environ.get("CI", "").lower() == "true"

    try:
        cfg = load_experiment(config)
        pipeline = Pipeline(cfg, verbose=verbose, dry_run=dry_run)

        stages = [
            ("Building OpenVINO runtime...", pipeline.build),
            ("Packaging bundle...", pipeline.package),
            ("Deploying to device(s)...", pipeline.deploy),
            ("Running benchmarks...", lambda: pipeline.run(timeout, cooldown)),
            ("Generating reports...", pipeline.report),
        ]

        if is_ci or verbose:
            # Simple output for CI or verbose mode
            for description, stage_func in stages:
                print(f"[*] {description}")
                try:
                    stage_func()
                    print(f"[OK] {description} completed")
                except Exception as e:
                    print(f"[FAIL] {description} failed: {e}")
                    raise
            print("[OK] Pipeline completed successfully")
        else:
            # Rich progress bar for interactive use
            spinner = SpinnerColumn(spinner_name="dots" if sys.platform == "win32" else "aesthetic")

            with Progress(
                spinner,
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,  # Clear progress when done
            ) as progress:
                for description, stage_func in stages:
                    task = progress.add_task(description, total=None)
                    try:
                        stage_func()
                        progress.update(task, completed=True)
                    except Exception as e:
                        console.print(f"[bold red][FAIL] {description} failed: {e}[/bold red]")
                        raise

            console.print("[bold green][OK] Pipeline completed successfully[/bold green]")
    except UnicodeEncodeError as e:
        # Fallback for encoding errors
        print(f"Encoding error: {e}")
        print("Pipeline failed due to encoding issues. Try setting PYTHONIOENCODING=utf-8")
        sys.exit(1)


@app.command()
def list_devices():
    """List available Android devices."""
    from ovmobilebench.devices.android import list_android_devices

    console.print("[bold blue]Searching for Android devices...[/bold blue]")

    devices = list_android_devices()
    if not devices:
        console.print("[yellow]No Android devices found[/yellow]")
        console.print("\nMake sure:")
        console.print("  • USB debugging is enabled on your device")
        console.print("  • Device is connected via USB")
        console.print("  • You have authorized this computer on the device")
        return

    console.print("[bold green]Available Android devices:[/bold green]")
    for serial, status in devices:
        status_color = "green" if status == "device" else "yellow"
        console.print(f"  • {serial} [[{status_color}]{status}[/{status_color}]]")


@app.command("list-ssh-devices")
def list_ssh_devices():
    """List available SSH devices."""
    from rich.console import Console

    from .devices.linux_ssh import list_ssh_devices as list_ssh

    console = Console()
    devices = list_ssh()

    if not devices:
        console.print("[yellow]No SSH devices configured[/yellow]")
        console.print("\nTo configure SSH devices, add them to your experiment YAML")
        return

    console.print("[bold green]Available SSH devices:[/bold green]")
    for device in devices:
        status_color = "green" if device.get("status") == "available" else "yellow"
        serial = device.get("serial", "unknown")
        status = device.get("status", "unknown")
        console.print(f"  • {serial} [[{status_color}]{status}[/{status_color}]]")


@app.command("setup-android")
def setup_android(
    api_level: int = typer.Option(30, "--api", help="Android API level"),
    create_avd: bool = typer.Option(False, "--create-avd", help="Create AVD for emulator"),
    sdk_root: Path = typer.Option(None, "--sdk-root", help="Android SDK root path"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
):
    """Setup Android SDK/NDK for OVMobileBench."""
    from ovmobilebench.android.installer.api import ensure_android_tools
    from ovmobilebench.android.installer.types import NdkSpec

    console.print("[bold blue]Setting up Android SDK/NDK...[/bold blue]")

    if sdk_root is None:
        sdk_root = Path(os.environ.get("ANDROID_HOME", "/opt/android-sdk"))

    avd_name = f"ovmobilebench_avd_api{api_level}" if create_avd else None

    try:
        result = ensure_android_tools(
            sdk_root=sdk_root,
            api=api_level,
            target="google_apis",
            arch="arm64-v8a",
            ndk=NdkSpec(alias="r26d"),
            install_platform_tools=True,
            install_emulator=True,
            install_build_tools="34.0.0",
            create_avd_name=avd_name,
            accept_licenses=True,
            verbose=verbose,
        )

        console.print("[bold green][OK] Android SDK/NDK setup completed[/bold green]")
        console.print(f"SDK Root: {result['sdk_root']}")
        console.print(f"NDK Path: {result['ndk_path']}")

        if avd_name:
            console.print(f"AVD Created: {avd_name}")

        # Print export commands for user
        console.print("\n[yellow]Export these environment variables:[/yellow]")
        console.print(f"export ANDROID_HOME={result['sdk_root']}")
        console.print(f"export ANDROID_SDK_ROOT={result['sdk_root']}")
        console.print(f"export ANDROID_NDK_HOME={result['ndk_path']}")

    except Exception as e:
        console.print(f"[bold red][ERROR] Setup failed: {e}[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
