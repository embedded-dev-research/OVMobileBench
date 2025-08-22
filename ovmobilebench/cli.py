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
    config_file: Path = typer.Option(
        "experiments/android_example.yaml", "-c", "--config", help="Path to configuration file"
    ),
    api_level: int = typer.Option(None, "--api", help="Android API level (overrides config)"),
    arch: str = typer.Option(
        None, "--arch", help="Architecture (x86_64, arm64-v8a) (overrides config)"
    ),
    create_avd: bool = typer.Option(
        None, "--create-avd", help="Create AVD for emulator (overrides config)"
    ),
    sdk_root: Path = typer.Option(
        None, "--sdk-root", help="Android SDK root path (overrides config)"
    ),
    ndk_version: str = typer.Option(
        None, "--ndk-version", help="NDK version (e.g., r26d, 26.3.11579264). Default: latest"
    ),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
):
    """Setup Android SDK/NDK for OVMobileBench."""
    import yaml

    from ovmobilebench.android.installer.api import ensure_android_tools, verify_installation
    from ovmobilebench.android.installer.types import Arch, NdkSpec
    from ovmobilebench.config.loader import get_project_root

    # For setup-android, we need to load config without full validation
    # since we're installing the SDK/NDK that the config validation checks for
    try:
        with open(config_file) as f:
            config_data = yaml.safe_load(f)

        # Get values from raw config data
        if api_level is None:
            api_level = config_data.get("device", {}).get("api_level", 30)
        if arch is None:
            # Get architecture from openvino.toolchain.abi in config
            arch = config_data.get("openvino", {}).get("toolchain", {}).get("abi", "x86_64")
        if create_avd is None:
            # Default: create AVD only if no physical devices specified in config
            serials = config_data.get("device", {}).get("serials", [])
            create_avd = not serials if serials else True
        if sdk_root is None:
            # Get cache_dir from config
            cache_dir = config_data.get("project", {}).get("cache_dir", "ovmb_cache")
            project_root = get_project_root()
            if not Path(cache_dir).is_absolute():
                cache_dir = project_root / cache_dir
            else:
                cache_dir = Path(cache_dir)
            sdk_root = cache_dir / "android-sdk"
            console.print(f"[blue]Using SDK location from config: {sdk_root}[/blue]")
    except Exception as e:
        # Fallback if config can't be loaded
        console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
        if api_level is None:
            api_level = 30
        if arch is None:
            arch = "x86_64"  # Default for CI
        if create_avd is None:
            create_avd = False
        if sdk_root is None:
            project_root = get_project_root()
            cache_dir = project_root / "ovmb_cache"
            sdk_root = cache_dir / "android-sdk"
            console.print(f"[blue]Using default SDK location: {sdk_root}[/blue]")

    # First, check what's already installed
    console.print("[bold blue]Checking existing Android SDK/NDK installation...[/bold blue]")

    try:
        verification_result = verify_installation(sdk_root, verbose=verbose)

        # Check if essential components are present
        has_platform_tools = verification_result.get("platform_tools", False)
        has_emulator = verification_result.get("emulator", False)
        system_images = verification_result.get("system_images", [])
        ndk_versions = verification_result.get("ndk_versions", [])

        required_system_image = f"system-images;android-{api_level};google_apis;{arch}"
        has_system_image = any(required_system_image in img for img in system_images)

        # Check what needs to be installed
        needs_installation = []
        if not has_platform_tools:
            needs_installation.append("platform-tools")
        if not has_emulator:
            needs_installation.append("emulator")
        if not has_system_image and create_avd:
            needs_installation.append(f"system-image (API {api_level})")
        if not ndk_versions:
            needs_installation.append("NDK")

        if not needs_installation:
            console.print(
                "[bold green]✓ All required Android components are already installed[/bold green]"
            )
            console.print(f"SDK Root: {sdk_root}")
            if ndk_versions:
                console.print(f"NDK Versions: {', '.join(ndk_versions)}")
            return
        else:
            console.print(f"[yellow]Missing components: {', '.join(needs_installation)}[/yellow]")
            console.print("[blue]Installing missing components...[/blue]")

    except Exception as e:
        # If verification fails, assume nothing is installed
        console.print(f"[yellow]Could not verify installation: {e}[/yellow]")
        console.print("[blue]Proceeding with full installation...[/blue]")

    console.print("[bold blue]Setting up Android SDK/NDK...[/bold blue]")
    avd_name = f"ovmobilebench_avd_api{api_level}" if create_avd else None

    # Use specified NDK version or let the installer determine the latest
    if ndk_version:
        ndk_alias = ndk_version
        console.print(f"Using specified NDK version: {ndk_alias}")
    else:
        # Let the installer determine the latest available version
        ndk_alias = "latest"
        console.print("Using latest available NDK version")

    try:
        # Cast arch to proper type
        arch_typed: Arch = arch  # type: ignore
        result = ensure_android_tools(
            sdk_root=sdk_root,
            api=api_level,
            target="google_apis",
            arch=arch_typed,
            ndk=NdkSpec(alias=ndk_alias),
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
