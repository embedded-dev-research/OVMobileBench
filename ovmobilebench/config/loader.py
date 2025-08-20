"""Configuration loader utilities."""

from pathlib import Path
from typing import Any

import yaml

from ovmobilebench.config.schema import Experiment, ModelItem, ModelsConfig


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML configuration file."""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path.as_posix()}")

    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f)
        return data


def scan_model_directories(models_config: ModelsConfig) -> list[ModelItem]:
    """Scan directories for model files based on configured extensions."""
    model_list = []

    # Add explicitly defined models first
    if models_config.models:
        model_list.extend(models_config.models)

    # Scan directories for models
    if models_config.directories:
        for directory in models_config.directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                print(f"Warning: Model directory '{directory}' does not exist, skipping...")
                continue

            # Search for models with specified extensions
            for ext in models_config.extensions:
                for model_file in dir_path.rglob(f"*{ext}"):
                    # Skip if it's already in explicit models list
                    if any(m.path == str(model_file) for m in model_list):
                        continue

                    # Create model item from discovered file
                    model_name = model_file.stem
                    # Try to infer precision from filename
                    precision = None
                    if "fp16" in model_name.lower() or "f16" in model_name.lower():
                        precision = "FP16"
                    elif "fp32" in model_name.lower() or "f32" in model_name.lower():
                        precision = "FP32"
                    elif "int8" in model_name.lower() or "i8" in model_name.lower():
                        precision = "INT8"

                    # Only add .xml files for now (OpenVINO format)
                    if ext == ".xml":
                        model_list.append(
                            ModelItem(
                                name=model_name,
                                path=str(model_file),
                                precision=precision,
                                tags={"source": "directory_scan", "directory": directory},
                            )
                        )

    return model_list


def load_experiment(config_path: Path | str) -> Experiment:
    """Load and validate experiment configuration."""
    if isinstance(config_path, str):
        config_path = Path(config_path)
    data = load_yaml(config_path)

    # Process models configuration if it's the new format
    if "models" in data and isinstance(data["models"], dict):
        # Convert dict to ModelsConfig
        models_config = ModelsConfig(**data["models"])
        # Scan directories and get full model list
        model_list = scan_model_directories(models_config)
        # Replace models section with the expanded list for backward compatibility
        data["models"] = [m.model_dump() for m in model_list]

    return Experiment(**data)


def save_experiment(experiment: Experiment, path: Path):
    """Save experiment configuration to YAML."""
    with open(path, "w") as f:
        yaml.safe_dump(experiment.model_dump(), f, default_flow_style=False, sort_keys=False)
