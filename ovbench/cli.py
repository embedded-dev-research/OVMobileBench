"""Command-line interface for OVBench."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ovbench.config.loader import load_experiment
from ovbench.pipeline import Pipeline

app = typer.Typer(
    name="ovbench",
    help="End-to-end benchmarking pipeline for OpenVINO on mobile devices",
    add_completion=False,
)
console = Console()


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
    console.print("[bold green]✓ Build completed[/bold green]")


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
    console.print("[bold green]✓ Package created[/bold green]")


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
    console.print("[bold green]✓ Deployment completed[/bold green]")


@app.command()
def run(
    config: Path = typer.Option(..., "-c", "--config", help="Experiment config YAML file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run without actual execution"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Timeout in seconds"),
    cooldown: Optional[int] = typer.Option(None, "--cooldown", help="Cooldown between runs"),
):
    """Execute benchmark matrix on device(s)."""
    console.print("[bold blue]Running benchmarks...[/bold blue]")
    cfg = load_experiment(config)
    pipeline = Pipeline(cfg, verbose=verbose, dry_run=dry_run)
    pipeline.run(timeout=timeout, cooldown=cooldown)
    console.print("[bold green]✓ Benchmarks completed[/bold green]")


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
    console.print("[bold green]✓ Reports generated[/bold green]")


@app.command()
def all(
    config: Path = typer.Option(..., "-c", "--config", help="Experiment config YAML file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry run without actual execution"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Timeout in seconds"),
    cooldown: Optional[int] = typer.Option(None, "--cooldown", help="Cooldown between runs"),
):
    """Execute complete pipeline: build, package, deploy, run, and report."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        cfg = load_experiment(config)
        pipeline = Pipeline(cfg, verbose=verbose, dry_run=dry_run)
        
        stages = [
            ("Building OpenVINO runtime...", pipeline.build),
            ("Packaging bundle...", pipeline.package),
            ("Deploying to device(s)...", pipeline.deploy),
            ("Running benchmarks...", lambda: pipeline.run(timeout, cooldown)),
            ("Generating reports...", pipeline.report),
        ]
        
        for description, stage_func in stages:
            task = progress.add_task(description, total=None)
            try:
                stage_func()
                progress.update(task, completed=True)
            except Exception as e:
                console.print(f"[bold red]✗ {description} failed: {e}[/bold red]")
                raise
    
    console.print("[bold green]✓ Pipeline completed successfully[/bold green]")


@app.command()
def list_devices():
    """List available ADB devices."""
    from ovbench.devices.android import list_android_devices
    
    devices = list_android_devices()
    if not devices:
        console.print("[yellow]No devices found[/yellow]")
        return
    
    console.print("[bold]Available devices:[/bold]")
    for serial, status in devices:
        console.print(f"  • {serial} [{status}]")


if __name__ == "__main__":
    app()