"""Package OpenVINO runtime and models."""

import tarfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict

from ovmobilebench.config.schema import PackageConfig, ModelItem
from ovmobilebench.core.fs import ensure_dir, get_digest
from ovmobilebench.core.errors import OVMobileBenchError

logger = logging.getLogger(__name__)


class Packager:
    """Package runtime, libraries and models into deployable bundle."""

    def __init__(
        self,
        config: PackageConfig,
        models: List[ModelItem],
        output_dir: Path,
    ):
        self.config = config
        self.models = models
        self.output_dir = ensure_dir(output_dir)

    def create_bundle(
        self,
        artifacts: Dict[str, Path],
        bundle_name: str = "ovbundle",
    ) -> Path:
        """Create deployable bundle."""
        bundle_dir = self.output_dir / bundle_name
        ensure_dir(bundle_dir)

        # Copy binaries
        bin_dir = ensure_dir(bundle_dir / "bin")
        if "benchmark_app" in artifacts:
            shutil.copy2(artifacts["benchmark_app"], bin_dir / "benchmark_app")
            (bin_dir / "benchmark_app").chmod(0o755)

        # Copy libraries
        lib_dir = ensure_dir(bundle_dir / "lib")
        if "libs" in artifacts:
            self._copy_libs(artifacts["libs"], lib_dir)

        # Copy models
        models_dir = ensure_dir(bundle_dir / "models")
        self._copy_models(models_dir)

        # Add extra files
        for extra_file in self.config.extra_files:
            src = Path(extra_file)
            if src.exists():
                dst = bundle_dir / src.name
                shutil.copy2(src, dst)

        # Create README
        self._create_readme(bundle_dir)

        # Create archive
        archive_path = self._create_archive(bundle_dir, bundle_name)

        logger.info(f"Bundle created: {archive_path}")
        return archive_path

    def _copy_libs(self, libs_dir: Path, dest_dir: Path):
        """Copy required shared libraries."""
        lib_patterns = ["*.so", "*.so.*"]

        for pattern in lib_patterns:
            for lib in libs_dir.glob(pattern):
                if lib.is_file():
                    shutil.copy2(lib, dest_dir / lib.name)
                    logger.debug(f"Copied library: {lib.name}")

    def _copy_models(self, models_dir: Path):
        """Copy model files."""
        for model in self.models:
            xml_path = Path(model.path)
            bin_path = xml_path.with_suffix(".bin")

            if not xml_path.exists():
                raise OVMobileBenchError(f"Model XML not found: {xml_path}")
            if not bin_path.exists():
                raise OVMobileBenchError(f"Model BIN not found: {bin_path}")

            # Copy with model name prefix
            dst_xml = models_dir / f"{model.name}.xml"
            dst_bin = models_dir / f"{model.name}.bin"

            shutil.copy2(xml_path, dst_xml)
            shutil.copy2(bin_path, dst_bin)

            logger.info(f"Copied model: {model.name}")

    def _create_readme(self, bundle_dir: Path):
        """Create README with usage instructions."""
        readme_content = """# OVMobileBench Bundle

## Usage

1. Deploy to device:
   adb push ovbundle /data/local/tmp/

2. Set library path:
   export LD_LIBRARY_PATH=/data/local/tmp/ovbundle/lib:$LD_LIBRARY_PATH

3. Run benchmark:
   cd /data/local/tmp/ovbundle
   ./bin/benchmark_app -m models/<model>.xml -d CPU -niter 200

## Contents

- bin/         - Executable binaries
- lib/         - Shared libraries
- models/      - Model files (XML + BIN)

## Troubleshooting

- Permission denied: chmod +x bin/benchmark_app
- Library not found: Check LD_LIBRARY_PATH
- Model not found: Verify models/ directory
"""

        (bundle_dir / "README.txt").write_text(readme_content)

    def _create_archive(self, bundle_dir: Path, name: str) -> Path:
        """Create compressed archive."""
        archive_path = self.output_dir / f"{name}.tar.gz"

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(bundle_dir, arcname=name)

        # Calculate checksum
        checksum = get_digest(archive_path)
        checksum_file = archive_path.with_suffix(".tar.gz.sha256")
        checksum_file.write_text(f"{checksum}  {archive_path.name}\n")

        return archive_path
