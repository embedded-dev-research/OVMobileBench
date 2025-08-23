"""Package OpenVINO runtime and models."""

import logging
import shutil
import tarfile
from pathlib import Path

from ovmobilebench.config.schema import ModelItem, PackageConfig
from ovmobilebench.core.errors import OVMobileBenchError
from ovmobilebench.core.fs import ensure_dir, get_digest

logger = logging.getLogger(__name__)


class Packager:
    """Package runtime, libraries and models into deployable bundle."""

    def __init__(
        self,
        config: PackageConfig,
        models: list[ModelItem],
        output_dir: Path,
        android_abi: str = "arm64-v8a",
    ):
        self.config = config
        self.models = models
        self.output_dir = ensure_dir(output_dir)
        self.android_abi = android_abi

    def create_bundle(
        self,
        artifacts: dict[str, Path],
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
        """Copy all libraries from release directory recursively."""
        # Copy entire release directory structure
        if libs_dir.exists():
            # Copy all .so files recursively
            for src_file in libs_dir.rglob("*.so*"):
                if src_file.is_file():
                    # Preserve directory structure for plugins
                    rel_path = src_file.relative_to(libs_dir)
                    dst_file = dest_dir / rel_path
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    logger.debug(f"Copied library: {rel_path}")

            # Count total libraries copied
            total_libs = sum(1 for _ in dest_dir.rglob("*.so*"))
            logger.info(f"Copied {total_libs} libraries from {libs_dir}")
        else:
            logger.warning(f"Library directory not found: {libs_dir}")

        # Also copy libc++_shared.so from NDK if available
        self._copy_ndk_stl_lib(dest_dir)

    def _copy_ndk_stl_lib(self, dest_dir: Path):
        """Copy C++ standard library from Android NDK."""
        # Try to find NDK path from environment or common locations
        ndk_paths = [
            Path.home() / "ovmb_cache" / "android-sdk" / "ndk",
            Path.cwd() / "ovmb_cache" / "android-sdk" / "ndk",
            Path("/Users/anesterov/CLionProjects/OVMobileBench/ovmb_cache/android-sdk/ndk"),
        ]

        # Find NDK version directory
        ndk_root = None
        for ndk_path in ndk_paths:
            if ndk_path.exists():
                # Get the first NDK version directory
                ndk_versions = [d for d in ndk_path.iterdir() if d.is_dir()]
                if ndk_versions:
                    ndk_root = ndk_versions[0]
                    break

        if not ndk_root:
            logger.warning("Android NDK not found, libc++_shared.so will not be included")
            return

        # Map Android ABI to NDK arch directory name
        abi_to_arch = {
            "arm64-v8a": "aarch64-linux-android",
            "armeabi-v7a": "arm-linux-androideabi",
            "x86": "i686-linux-android",
            "x86_64": "x86_64-linux-android",
        }

        arch_dir = abi_to_arch.get(self.android_abi, "aarch64-linux-android")

        # Find libc++_shared.so for the target architecture
        stl_paths = [
            ndk_root
            / f"toolchains/llvm/prebuilt/darwin-x86_64/sysroot/usr/lib/{arch_dir}/libc++_shared.so",
            ndk_root
            / f"toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/{arch_dir}/libc++_shared.so",
            ndk_root
            / f"toolchains/llvm/prebuilt/windows-x86_64/sysroot/usr/lib/{arch_dir}/libc++_shared.so",
        ]

        for stl_path in stl_paths:
            if stl_path.exists():
                shutil.copy2(stl_path, dest_dir / "libc++_shared.so")
                logger.info(f"Copied libc++_shared.so for {self.android_abi} from Android NDK")
                return

        logger.warning(f"libc++_shared.so not found in Android NDK for {self.android_abi}")

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
