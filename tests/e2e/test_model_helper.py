#!/usr/bin/env python3
"""
Helper for downloading and managing models.
"""

import argparse
import logging
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_resnet50():
    """Download ResNet-50 model to cache directory."""
    project_root = Path(__file__).parent.parent.parent
    cache_dir = project_root / "ovmb_cache" / "models"
    cache_dir.mkdir(parents=True, exist_ok=True)

    base_url = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2023.0/models_bin/1"
    model_name = "resnet-50-pytorch"
    precision = "FP16"

    files = [
        (f"{model_name}.xml", f"{model_name}/{precision}/{model_name}.xml"),
        (f"{model_name}.bin", f"{model_name}/{precision}/{model_name}.bin"),
    ]

    for filename, url_path in files:
        filepath = cache_dir / filename

        if filepath.exists():
            logger.info(f"Model file {filename} already cached")
            continue

        url = f"{base_url}/{url_path}"
        logger.info(f"Downloading {filename} from {url}...")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end="")

        print()  # New line after progress
        logger.info(f"Downloaded {filename} successfully")

    logger.info(f"ResNet-50 model ready at {cache_dir}")
    return cache_dir / f"{model_name}.xml"


def download_mobilenet():
    """Download MobileNet model to cache directory."""
    project_root = Path(__file__).parent.parent.parent
    cache_dir = project_root / "ovmb_cache" / "models"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Similar implementation for MobileNet
    logger.info("MobileNet download not implemented yet")
    return None


def list_cached_models():
    """List all cached models."""
    project_root = Path(__file__).parent.parent.parent
    cache_dir = project_root / "ovmb_cache" / "models"

    if not cache_dir.exists():
        logger.info("No cached models found")
        return []

    models = list(cache_dir.glob("*.xml"))

    logger.info(f"Found {len(models)} cached models:")
    for model in models:
        logger.info(f"  - {model.name}")

    return models


def main():
    parser = argparse.ArgumentParser(description="Model download helper")
    subparsers = parser.add_subparsers(dest="command")

    # Download commands
    subparsers.add_parser("download-resnet50", help="Download ResNet-50 model")
    subparsers.add_parser("download-mobilenet", help="Download MobileNet model")
    subparsers.add_parser("list", help="List cached models")

    args = parser.parse_args()

    if args.command == "download-resnet50":
        download_resnet50()
    elif args.command == "download-mobilenet":
        download_mobilenet()
    elif args.command == "list":
        list_cached_models()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
