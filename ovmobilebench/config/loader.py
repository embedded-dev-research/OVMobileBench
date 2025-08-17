"""Configuration loader utilities."""

from pathlib import Path
from typing import Any

import yaml

from ovmobilebench.config.schema import Experiment


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML configuration file."""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path.as_posix()}")

    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f)
        return data


def load_experiment(config_path: Path | str) -> Experiment:
    """Load and validate experiment configuration."""
    if isinstance(config_path, str):
        config_path = Path(config_path)
    data = load_yaml(config_path)
    return Experiment(**data)


def save_experiment(experiment: Experiment, path: Path):
    """Save experiment configuration to YAML."""
    with open(path, "w") as f:
        yaml.safe_dump(experiment.model_dump(), f, default_flow_style=False, sort_keys=False)
