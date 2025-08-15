"""Configuration loader utilities."""

import yaml
from pathlib import Path
from typing import Dict, Any
from ovbench.config.schema import Experiment


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML configuration file."""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_experiment(config_path: Path) -> Experiment:
    """Load and validate experiment configuration."""
    data = load_yaml(config_path)
    return Experiment(**data)


def save_experiment(experiment: Experiment, path: Path):
    """Save experiment configuration to YAML."""
    with open(path, 'w') as f:
        yaml.safe_dump(experiment.model_dump(), f, default_flow_style=False, sort_keys=False)