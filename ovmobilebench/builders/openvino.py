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

        # Clone OpenVINO if source directory doesn't exist
        source_path = Path(self.config.source_dir)
        if not source_path.exists():
            self._clone_openvino(source_path)
        else:
            # Initialize submodules if not already done
            self._init_submodules(source_path)

        logger.info(f"Building OpenVINO from {self.config.source_dir}")

        # Checkout specific commit
        self._checkout_commit()

        # Configure CMake
        self._configure_cmake()

        # Build
        self._build()

        # Return the build directory with proper artifact layout
        # Map Android ABI to CMake output directory
        arch = self._get_cmake_arch()
        build_type = self.config.options.CMAKE_BUILD_TYPE or "Release"
        return self.build_dir / "bin" / arch / build_type

    def _clone_openvino(self, source_path: Path):
        """Clone OpenVINO repository if it doesn't exist."""
        logger.info(f"OpenVINO source not found at {source_path}")
        logger.info("Cloning OpenVINO repository...")

        # Create parent directory if needed
        source_path.parent.mkdir(parents=True, exist_ok=True)

        # Clone the repository with submodules
        clone_cmd = f"git clone --recurse-submodules https://github.com/openvinotoolkit/openvino.git {source_path}"
        result = run(clone_cmd, check=False, verbose=self.verbose)

        if result.returncode != 0:
            raise BuildError(f"Failed to clone OpenVINO repository: {result.stderr}")

        logger.info("OpenVINO repository cloned successfully with submodules")

    def _init_submodules(self, source_path: Path):
        """Initialize git submodules for existing repository."""
        # Check if submodules are already initialized
        check_submodule = source_path / "third_party" / "pugixml" / "CMakeLists.txt"
        if check_submodule.exists():
            logger.debug("Submodules already initialized")
            return

        logger.info("Initializing git submodules...")

        # Initialize and update submodules
        init_cmd = "git submodule update --init --recursive"
        result = run(init_cmd, cwd=source_path, check=False, verbose=self.verbose)

        if result.returncode != 0:
            logger.warning(f"Failed to initialize submodules: {result.stderr}")
            # Try to continue anyway, some submodules might not be critical
        else:
            logger.info("Git submodules initialized successfully")

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
        # Use CMake from Android SDK if available, fallback to system cmake
        cmake_executable = self._get_cmake_executable()

        cmake_args = [
            cmake_executable,
            "-S",
            self.config.source_dir,
            "-B",
            str(self.build_dir),
            f"-DOUTPUT_ROOT={self.build_dir}",  # Set output root for proper artifact layout
            f"-DCMAKE_BUILD_TYPE={self.config.options.CMAKE_BUILD_TYPE}",
        ]

        # Enable ccache if available and not already set in options
        import shutil

        options_dict = self.config.options.model_dump()

        # Auto-detect ccache if not specified
        if options_dict.get("CMAKE_C_COMPILER_LAUNCHER") is None and shutil.which("ccache"):
            options_dict["CMAKE_C_COMPILER_LAUNCHER"] = "ccache"
            options_dict["CMAKE_CXX_COMPILER_LAUNCHER"] = "ccache"
            logger.info("Auto-detected ccache for compilation")

        # Set generator if specified
        if options_dict.get("CMAKE_GENERATOR"):
            cmake_args.extend(["-G", options_dict.pop("CMAKE_GENERATOR")])
        else:
            # Default to Ninja if available
            if shutil.which("ninja"):
                cmake_args.extend(["-G", "Ninja"])

        # Android-specific configuration from toolchain
        if self.config.toolchain.android_ndk:
            # Set toolchain file if not already in options
            if not options_dict.get("CMAKE_TOOLCHAIN_FILE"):
                options_dict["CMAKE_TOOLCHAIN_FILE"] = (
                    f"{self.config.toolchain.android_ndk}/build/cmake/android.toolchain.cmake"
                )

            # Set Android options from toolchain if not already in options
            if not options_dict.get("ANDROID_ABI"):
                options_dict["ANDROID_ABI"] = self.config.toolchain.abi
            if not options_dict.get("ANDROID_PLATFORM"):
                options_dict["ANDROID_PLATFORM"] = f"android-{self.config.toolchain.api_level}"
            if not options_dict.get("ANDROID_STL"):
                options_dict["ANDROID_STL"] = "c++_shared"

        # Add all options to cmake args
        for key, value in options_dict.items():
            if value is not None:
                cmake_args.append(f"-D{key}={value}")

        result = run(
            cmake_args,
            check=False,  # Don't raise immediately, check manually for better error message
            verbose=self.verbose,
        )

        if result.returncode != 0:
            logger.error(f"CMake configuration failed with error:\n{result.stderr}")
            raise BuildError(f"CMake configuration failed: {result.stderr}")

        logger.info("CMake configuration completed")

    def _get_cmake_executable(self) -> str:
        """Get CMake executable path, preferring Android SDK CMake."""
        # Check for CMake in Android SDK
        if self.config.toolchain.android_ndk:
            android_home = Path(self.config.toolchain.android_ndk).parent.parent
            cmake_versions_dir = android_home / "cmake"

            if cmake_versions_dir.exists():
                # Find the latest CMake version
                cmake_versions = [d for d in cmake_versions_dir.iterdir() if d.is_dir()]
                if cmake_versions:
                    # Sort versions and get the latest
                    latest_version = sorted(cmake_versions, key=lambda x: x.name)[-1]
                    cmake_executable = latest_version / "bin" / "cmake"

                    if cmake_executable.exists():
                        logger.info(f"Using CMake from Android SDK: {cmake_executable}")
                        return str(cmake_executable)

        # Fallback to system cmake
        logger.info("Using system CMake")
        return "cmake"

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

    def _get_cmake_arch(self) -> str:
        """Get the CMake output architecture directory name."""
        # Map Android ABI to CMake output directory name
        if self.config.toolchain and self.config.toolchain.abi:
            abi = self.config.toolchain.abi
            # OpenVINO CMake uses specific directory names for each architecture
            if abi == "arm64-v8a":
                return "aarch64"
            elif abi == "armeabi-v7a":
                return "armv7"
            elif abi == "x86":
                return "i386"
            elif abi == "x86_64":
                return "intel64"  # OpenVINO uses 'intel64' for x86_64 builds
            else:
                return abi
        return "aarch64"  # Default to aarch64

    def get_artifacts(self) -> dict[str, Path]:
        """Get paths to build artifacts."""
        # With OUTPUT_ROOT, artifacts are in bin/<arch>/<build_type>/
        arch = self._get_cmake_arch()
        build_type = self.config.options.CMAKE_BUILD_TYPE or "Release"

        artifacts = {
            "benchmark_app": self.build_dir / "bin" / arch / build_type / "benchmark_app",
            "libs": self.build_dir / "bin" / arch / build_type,
        }

        # Verify artifacts exist
        for name, path in artifacts.items():
            if not path.exists():
                raise BuildError(f"Build artifact not found: {name} at {path}")

        return artifacts
