"""Configuration loader utilities."""

import os
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


def resolve_path(path: str, project_root: Path) -> str:
    """Resolve relative paths to absolute paths based on project root.

    Args:
        path: Path string that may be relative or absolute
        project_root: Root directory of the project

    Returns:
        Absolute path string
    """
    if not path:
        return path

    path_obj = Path(path)
    if path_obj.is_absolute():
        return str(path_obj)

    # Resolve relative to project root
    resolved = project_root / path_obj
    # Normalize the path (resolve .. and .)
    # Use os.path.normpath to normalize without checking existence

    normalized = os.path.normpath(str(resolved))
    return normalized


def resolve_paths_in_config(data: dict[str, Any], project_root: Path) -> dict[str, Any]:
    """Resolve all relative paths in configuration to absolute paths.

    Args:
        data: Configuration dictionary
        project_root: Root directory of the project

    Returns:
        Configuration dictionary with resolved paths
    """
    # Deep copy to avoid modifying original
    import copy

    data = copy.deepcopy(data)

    # Resolve OpenVINO paths
    if "openvino" in data:
        if "source_dir" in data["openvino"] and data["openvino"]["source_dir"]:
            data["openvino"]["source_dir"] = resolve_path(
                data["openvino"]["source_dir"], project_root
            )
        if "install_dir" in data["openvino"] and data["openvino"]["install_dir"]:
            data["openvino"]["install_dir"] = resolve_path(
                data["openvino"]["install_dir"], project_root
            )
        if "toolchain" in data["openvino"]:
            if (
                "android_ndk" in data["openvino"]["toolchain"]
                and data["openvino"]["toolchain"]["android_ndk"]
            ):
                data["openvino"]["toolchain"]["android_ndk"] = resolve_path(
                    data["openvino"]["toolchain"]["android_ndk"], project_root
                )

    # Resolve model paths
    if "models" in data:
        if isinstance(data["models"], list):
            for model in data["models"]:
                if "path" in model and model["path"]:
                    model["path"] = resolve_path(model["path"], project_root)
        elif isinstance(data["models"], dict):
            if "directories" in data["models"] and data["models"]["directories"]:
                data["models"]["directories"] = [
                    resolve_path(d, project_root) for d in data["models"]["directories"]
                ]
            if "models" in data["models"] and data["models"]["models"]:
                for model in data["models"]["models"]:
                    if "path" in model and model["path"]:
                        model["path"] = resolve_path(model["path"], project_root)

    # Resolve project cache_dir
    if "project" in data and "cache_dir" in data["project"] and data["project"]["cache_dir"]:
        data["project"]["cache_dir"] = resolve_path(data["project"]["cache_dir"], project_root)

    # Resolve report sink paths
    if "report" in data and "sinks" in data["report"]:
        for sink in data["report"]["sinks"]:
            if "path" in sink and sink["path"]:
                sink["path"] = resolve_path(sink["path"], project_root)

    return data


def get_project_root() -> Path:
    """Get the project root directory.

    Looks for the directory containing pyproject.toml or setup.py,
    starting from the current working directory and going up.

    Returns:
        Path to project root directory
    """
    current = Path.cwd()

    # Look for project markers
    markers = ["pyproject.toml", "setup.py", ".git"]

    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    # If no marker found, use current working directory
    return Path.cwd()


def setup_environment(data: dict[str, Any], project_root: Path) -> dict[str, Any]:
    """Setup environment variables from config.

    Args:
        data: Configuration dictionary
        project_root: Root directory of the project

    Returns:
        Configuration dictionary with environment setup
    """
    import copy

    data = copy.deepcopy(data)

    # Ensure environment section exists
    if "environment" not in data:
        data["environment"] = {}

    env = data["environment"]

    # Auto-detect JAVA_HOME if not specified
    if not env.get("java_home"):
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            env["java_home"] = java_home
            print(f"INFO: Auto-detected Java from JAVA_HOME: {java_home}")

    # Set JAVA_HOME if specified or detected
    if env.get("java_home"):
        os.environ["JAVA_HOME"] = env["java_home"]
        # Also add to PATH
        java_bin = os.path.join(env["java_home"], "bin")
        if java_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{java_bin}:{os.environ.get('PATH', '')}"

    # Auto-detect or default SDK root if not specified
    if not env.get("sdk_root"):
        # Check if ANDROID_HOME is set
        android_home = os.environ.get("ANDROID_HOME")
        if android_home:
            env["sdk_root"] = android_home
            print(f"INFO: Auto-detected Android SDK from ANDROID_HOME: {android_home}")
        else:
            # Use default in cache directory
            cache_dir = data.get("project", {}).get("cache_dir", "ovmb_cache")
            cache_path = Path(cache_dir)
            if not cache_path.is_absolute():
                cache_path = project_root / cache_path
            env["sdk_root"] = str(cache_path / "android-sdk")
            print(f"INFO: Using default Android SDK location: {env['sdk_root']}")

    # Set Android SDK environment variables
    if env.get("sdk_root"):
        os.environ["ANDROID_HOME"] = env["sdk_root"]
        os.environ["ANDROID_SDK_ROOT"] = env["sdk_root"]

    return data


def setup_default_paths(data: dict[str, Any], project_root: Path) -> dict[str, Any]:
    """Setup default paths for missing configuration.

    If source_dir or android_ndk are not specified, set them to default
    locations in the cache directory.

    Args:
        data: Configuration dictionary
        project_root: Root directory of the project

    Returns:
        Configuration dictionary with default paths
    """
    import copy

    data = copy.deepcopy(data)

    # Get cache directory (default to ovmb_cache)
    cache_dir = "ovmb_cache"
    if "project" in data and "cache_dir" in data["project"] and data["project"]["cache_dir"]:
        cache_dir = data["project"]["cache_dir"]

    # Resolve cache_dir to absolute path if relative
    cache_path = Path(cache_dir)
    if not cache_path.is_absolute():
        cache_path = project_root / cache_path

    # Setup OpenVINO paths if in build mode
    if "openvino" in data and data["openvino"].get("mode") == "build":
        # Set default source_dir if not specified
        if not data["openvino"].get("source_dir"):
            default_source = cache_path / "openvino_source"
            data["openvino"]["source_dir"] = str(default_source)
            print(f"INFO: No source_dir specified, using default: {data['openvino']['source_dir']}")

            # Check if OpenVINO needs to be cloned
            if not default_source.exists():
                print("INFO: OpenVINO source not found. Clone it with:")
                print(
                    f"      git clone https://github.com/openvinotoolkit/openvino.git {default_source}"
                )

        # Setup toolchain if needed
        if "toolchain" not in data["openvino"]:
            data["openvino"]["toolchain"] = {}

        # Set default android_ndk if not specified
        if not data["openvino"]["toolchain"].get("android_ndk"):
            # Check for existing NDK installations in cache
            ndk_base_path = cache_path / "android-sdk" / "ndk"
            ndk_version = None

            if ndk_base_path.exists():
                # Find the latest installed NDK version
                ndk_versions = [d.name for d in ndk_base_path.iterdir() if d.is_dir()]
                if ndk_versions:
                    # Sort versions and use the latest
                    ndk_version = sorted(ndk_versions)[-1]

            if ndk_version:
                # Use found NDK version
                ndk_path = ndk_base_path / ndk_version
                data["openvino"]["toolchain"]["android_ndk"] = str(ndk_path)
                print(
                    f"INFO: No android_ndk specified, using found NDK: {data['openvino']['toolchain']['android_ndk']}"
                )
            else:
                # No NDK found - will use latest available
                # For now, use a placeholder path that will be set after installation
                ndk_path = ndk_base_path / "latest"
                data["openvino"]["toolchain"]["android_ndk"] = str(ndk_path)
                print("INFO: No android_ndk specified and no NDK found")

                # Check if Android SDK needs to be installed
                if (
                    not ndk_base_path.exists() or not any(ndk_base_path.iterdir())
                    if ndk_base_path.exists()
                    else True
                ):
                    print("INFO: Android NDK not found. Install it with:")
                    print(
                        f"      python -m ovmobilebench.cli setup-android --sdk-root {cache_path}/android-sdk"
                    )
                    print("      # This will install the latest available NDK version")
                    print("      # Or specify a specific NDK version:")
                    print(
                        f"      python -m ovmobilebench.cli setup-android --sdk-root {cache_path}/android-sdk --ndk-version <version>"
                    )

    return data


def load_experiment(config_path: Path | str) -> Experiment:
    """Load and validate experiment configuration."""
    if isinstance(config_path, str):
        config_path = Path(config_path)

    # Get project root
    project_root = get_project_root()

    # Load raw data
    data = load_yaml(config_path)

    # Setup environment variables
    data = setup_environment(data, project_root)

    # Setup default paths for missing configuration
    data = setup_default_paths(data, project_root)

    # Resolve all paths relative to project root
    data = resolve_paths_in_config(data, project_root)

    # Create cache directory if it doesn't exist
    if "project" in data and "cache_dir" in data["project"] and data["project"]["cache_dir"]:
        cache_dir_path = Path(data["project"]["cache_dir"])
        if not cache_dir_path.exists():
            cache_dir_path.mkdir(parents=True, exist_ok=True)
            print(f"INFO: Created cache directory: {cache_dir_path}")

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
