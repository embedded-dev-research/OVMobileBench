#!/usr/bin/env python3
"""
Helper for downloading and managing models for E2E tests.
"""

import argparse
import logging
import subprocess
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_cache_dir_from_config(config_file=None):
    """Get cache directory from OVMobileBench config."""
    # Use provided config file or default
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = Path.cwd() / "experiments" / "android_example.yaml"

    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Get cache_dir from config
        cache_dir = config.get("project", {}).get("cache_dir", "ovmb_cache")

        # Resolve cache_dir path
        if not Path(cache_dir).is_absolute():
            cache_dir = Path.cwd() / cache_dir
        else:
            cache_dir = Path(cache_dir)

        logger.info(f"Using config: {config_path}")
        return cache_dir

    # Fallback to default
    logger.warning(f"Config not found at {config_path}, using default path")
    return Path.cwd() / "ovmb_cache"


def download_file(url: str, dest_path: Path) -> bool:
    """Download a file using curl (more reliable than requests for SSL issues)."""
    try:
        # Check if file already exists and is valid
        if dest_path.exists() and dest_path.stat().st_size > 1000:  # > 1KB
            logger.info(
                f"  ✓ {dest_path.name} already exists ({dest_path.stat().st_size / (1024*1024):.1f} MB)"
            )
            return True

        logger.info(f"  ↓ Downloading {dest_path.name}...")
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Use curl for download (handles SSL better)
        result = subprocess.run(
            ["curl", "-L", "-o", str(dest_path), url], capture_output=True, text=True
        )

        if result.returncode == 0 and dest_path.exists():
            size_mb = dest_path.stat().st_size / (1024 * 1024)
            logger.info(f"  ✓ Downloaded {dest_path.name} ({size_mb:.1f} MB)")
            return True
        else:
            logger.error(f"  ✗ Failed to download {dest_path.name}: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"  ✗ Error downloading {dest_path.name}: {e}")
        return False


def download_openvino_notebooks_models(config_file=None) -> dict[str, Path]:
    """Download classification and segmentation models from OpenVINO notebooks."""
    cache_dir = get_cache_dir_from_config(config_file) / "models"

    # Base URL for OpenVINO notebooks models
    base_url = "https://storage.openvinotoolkit.org/repositories/openvino_notebooks/models/002-example-models"

    models = {
        "classification": {
            "dir": cache_dir / "classification",
            "files": [
                ("classification.xml", f"{base_url}/classification.xml"),
                ("classification.bin", f"{base_url}/classification.bin"),
            ],
        },
        "segmentation": {
            "dir": cache_dir / "segmentation",
            "files": [
                ("segmentation.xml", f"{base_url}/segmentation.xml"),
                ("segmentation.bin", f"{base_url}/segmentation.bin"),
            ],
        },
    }

    downloaded_dirs = {}

    for model_type, model_info in models.items():
        logger.info(f"\n📦 Processing {model_type} models:")
        model_dir = model_info["dir"]
        model_dir.mkdir(parents=True, exist_ok=True)

        success = True
        for filename, url in model_info["files"]:
            dest_path = model_dir / filename
            if not download_file(url, dest_path):
                success = False

        if success:
            downloaded_dirs[model_type] = model_dir
            logger.info(f"✅ {model_type} models ready in {model_dir}")
        else:
            logger.warning(f"⚠️  Some {model_type} models failed to download")

    return downloaded_dirs


def download_detection_models(config_file=None) -> Path | None:
    """Download detection models from Open Model Zoo."""
    cache_dir = get_cache_dir_from_config(config_file) / "models" / "detection"
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info("\n📦 Processing detection models:")

    # Vehicle detection model from Open Model Zoo
    base_url = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.1/models_bin/3"
    model_name = "vehicle-detection-0200"
    precision = "FP16"

    files = [
        (f"{model_name}.xml", f"{base_url}/{model_name}/{precision}/{model_name}.xml"),
        (f"{model_name}.bin", f"{base_url}/{model_name}/{precision}/{model_name}.bin"),
    ]

    success = True
    for filename, url in files:
        dest_path = cache_dir / filename
        if not download_file(url, dest_path):
            success = False

    if success:
        logger.info(f"✅ Detection models ready in {cache_dir}")
        return cache_dir
    else:
        logger.warning("⚠️  Some detection models failed to download")
        return None


def download_resnet50(config_file=None):
    """Download ResNet-50 model to cache directory."""
    cache_dir = get_cache_dir_from_config(config_file) / "models" / "resnet"
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info("\n📦 Processing ResNet-50 model:")

    base_url = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.1/models_bin/3"
    model_name = "resnet-50-pytorch"
    precision = "FP16"

    files = [
        (f"{model_name}.xml", f"{base_url}/{model_name}/{precision}/{model_name}.xml"),
        (f"{model_name}.bin", f"{base_url}/{model_name}/{precision}/{model_name}.bin"),
    ]

    success = True
    for filename, url in files:
        dest_path = cache_dir / filename
        if not download_file(url, dest_path):
            success = False

    if success:
        logger.info(f"✅ ResNet-50 model ready at {cache_dir}")
        return cache_dir / f"{model_name}.xml"
    else:
        logger.warning("⚠️  ResNet-50 download incomplete")
        return None


def cleanup_invalid_models(config_file=None):
    """Remove invalid model files (e.g., HTML error pages)."""
    cache_dir = get_cache_dir_from_config(config_file) / "models"

    if not cache_dir.exists():
        return

    logger.info("\n🧹 Cleaning up invalid model files...")
    cleaned = 0

    # Check all XML and BIN files
    for pattern in ["**/*.xml", "**/*.bin"]:
        for file_path in cache_dir.glob(pattern):
            # Check if file is actually HTML (error page)
            try:
                with open(file_path, "rb") as f:
                    header = f.read(100)
                    is_html = b"<!DOCTYPE html" in header or b"<html" in header

                # Close file before attempting to delete on Windows
                if is_html:
                    logger.info(
                        f"  Removing invalid file (HTML): {file_path.relative_to(cache_dir)}"
                    )
                    file_path.unlink()
                    cleaned += 1
            except Exception as e:
                logger.warning(f"  Could not check file {file_path}: {e}")

    if cleaned > 0:
        logger.info(f"  Cleaned {cleaned} invalid files")
    else:
        logger.info("  No invalid files found")


def list_cached_models(config_file=None):
    """List all cached models organized by category."""
    cache_dir = get_cache_dir_from_config(config_file) / "models"

    if not cache_dir.exists():
        logger.info("No cached models found")
        return []

    logger.info("\n📋 Cached models:")

    # List models by directory
    for subdir in sorted(cache_dir.iterdir()):
        if subdir.is_dir():
            xml_files = list(subdir.glob("*.xml"))
            if xml_files:
                logger.info(f"\n  {subdir.name}/")
                for xml_file in xml_files:
                    bin_file = xml_file.with_suffix(".bin")
                    if bin_file.exists():
                        total_size = (xml_file.stat().st_size + bin_file.stat().st_size) / (
                            1024 * 1024
                        )
                        logger.info(f"    • {xml_file.stem} ({total_size:.1f} MB)")
                    else:
                        logger.info(f"    • {xml_file.stem} (missing .bin file)")

    # Also list any models in root models directory
    root_models = list(cache_dir.glob("*.xml"))
    if root_models:
        logger.info("\n  (root)/")
        for xml_file in root_models:
            logger.info(f"    • {xml_file.stem}")

    return list(cache_dir.glob("**/*.xml"))


def main():
    parser = argparse.ArgumentParser(description="Model download helper for E2E tests")
    # Add global config argument
    parser.add_argument(
        "-c",
        "--config",
        help="Path to OVMobileBench config file",
        default="experiments/android_example.yaml",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Download commands
    subparsers.add_parser(
        "download-all", help="Download all test models (classification, segmentation, detection)"
    )
    subparsers.add_parser(
        "download-notebooks",
        help="Download OpenVINO notebooks models (classification & segmentation)",
    )
    subparsers.add_parser("download-detection", help="Download detection models")
    subparsers.add_parser("download-resnet50", help="Download ResNet-50 model")
    subparsers.add_parser("cleanup", help="Remove invalid model files")
    subparsers.add_parser("list", help="List cached models")

    args = parser.parse_args()

    if args.command == "download-all":
        # Clean up first
        cleanup_invalid_models(args.config)
        # Download all model types
        download_openvino_notebooks_models(args.config)
        download_detection_models(args.config)
        download_resnet50(args.config)
        # List what we have
        list_cached_models(args.config)
    elif args.command == "download-notebooks":
        download_openvino_notebooks_models(args.config)
    elif args.command == "download-detection":
        download_detection_models(args.config)
    elif args.command == "download-resnet50":
        download_resnet50(args.config)
    elif args.command == "cleanup":
        cleanup_invalid_models(args.config)
    elif args.command == "list":
        list_cached_models(args.config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
