"""OpenVINO build system."""

import logging
from pathlib import Path

from ovmobilebench.config.schema import OpenVINOConfig
from ovmobilebench.core.errors import BuildError
from ovmobilebench.core.fs import ensure_dir
from ovmobilebench.core.shell import run

logger = logging.getLogger(__name__)


class OpenVINOBuilder:
    """Build OpenVINO runtime and benchmark_app for target platform."""

    def __init__(self, config: OpenVINOConfig, build_dir: Path, verbose: bool = False):
        self.config = config
        self.build_dir = ensure_dir(build_dir)
        self.verbose = verbose

    def build(self) -> Path:
        """Build OpenVINO and return path to build artifacts."""
        if self.config.mode != "build":
            raise ValueError(
                f"OpenVINOBuilder can only be used with mode='build', got '{self.config.mode}'"
            )

        if not self.config.source_dir:
            raise ValueError("source_dir must be specified for build mode")

        logger.info(f"Building OpenVINO from {self.config.source_dir}")

        # Checkout specific commit
        self._checkout_commit()

        # Configure CMake
        self._configure_cmake()

        # Build
        self._build()

        return self.build_dir / "bin"

    def _checkout_commit(self):
        """Checkout specific commit if needed."""
        if self.config.commit != "HEAD":
            run(
                f"git checkout {self.config.commit}",
                cwd=Path(self.config.source_dir),
                check=True,
                verbose=self.verbose,
            )
            logger.info(f"Checked out commit: {self.config.commit}")

    def _configure_cmake(self):
        """Configure CMake for Android build."""
        cmake_args = [
            "cmake",
            "-S",
            self.config.source_dir,
            "-B",
            str(self.build_dir),
            "-GNinja",
            f"-DCMAKE_BUILD_TYPE={self.config.build_type}",
        ]

        # Android-specific configuration
        if self.config.toolchain.android_ndk:
            cmake_args.extend(
                [
                    f"-DCMAKE_TOOLCHAIN_FILE={self.config.toolchain.android_ndk}/build/cmake/android.toolchain.cmake",
                    f"-DANDROID_ABI={self.config.toolchain.abi}",
                    f"-DANDROID_PLATFORM=android-{self.config.toolchain.api_level}",
                    "-DANDROID_STL=c++_shared",
                ]
            )

        # OpenVINO options
        for key, value in self.config.options.model_dump().items():
            cmake_args.append(f"-D{key}={value}")

        # Disable unnecessary components for mobile
        cmake_args.extend(
            [
                "-DENABLE_TESTS=OFF",
                "-DENABLE_FUNCTIONAL_TESTS=OFF",
                "-DENABLE_SAMPLES=ON",  # We need benchmark_app
                "-DENABLE_OPENCV=OFF",
                "-DENABLE_PYTHON=OFF",
            ]
        )

        result = run(
            cmake_args,
            check=True,
            verbose=self.verbose,
        )

        if result.returncode != 0:
            raise BuildError(f"CMake configuration failed: {result.stderr}")

        logger.info("CMake configuration completed")

    def _build(self):
        """Build OpenVINO using Ninja."""
        targets = ["benchmark_app", "openvino"]

        for target in targets:
            logger.info(f"Building target: {target}")
            result = run(
                ["ninja", "-C", str(self.build_dir), target],
                check=False,
                verbose=self.verbose,
            )

            if result.returncode != 0:
                raise BuildError(f"Build failed for {target}: {result.stderr}")

        logger.info("Build completed successfully")

    def get_artifacts(self) -> dict[str, Path]:
        """Get paths to build artifacts."""
        artifacts = {
            "benchmark_app": self.build_dir / "bin" / "arm64-v8a" / "benchmark_app",
            "libs": self.build_dir / "bin" / "arm64-v8a",
        }

        # Verify artifacts exist
        for name, path in artifacts.items():
            if not path.exists():
                raise BuildError(f"Build artifact not found: {name} at {path}")

        return artifacts
