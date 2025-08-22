"""SDK Manager wrapper for Android SDK operations."""

import os
import ssl
import subprocess
import zipfile
from contextlib import nullcontext
from pathlib import Path

from .detect import detect_host, get_sdk_tools_filename
from .errors import ComponentNotFoundError, DownloadError, SdkManagerError
from .logging import StructuredLogger
from .types import Arch, SdkComponent, Target

try:
    import certifi

    _has_certifi = True
except ImportError:
    _has_certifi = False


def _create_ssl_context():
    """Create SSL context with proper certificate verification."""
    if _has_certifi:
        context = ssl.create_default_context(cafile=certifi.where())
    else:
        context = ssl.create_default_context()
    return context


def _secure_urlretrieve(url, filename):
    """Download file with proper SSL verification."""
    context = _create_ssl_context()

    # Use urllib with SSL context
    import shutil
    import urllib.request

    with urllib.request.urlopen(url, context=context) as response:
        with open(filename, "wb") as out_file:
            shutil.copyfileobj(response, out_file)


class SdkManager:
    """Wrapper for Android SDK Manager operations."""

    SDK_BASE_URL = "https://dl.google.com/android/repository"
    DEFAULT_SDK_TOOLS_VERSION = "11076708"  # Latest as of 2024

    def __init__(self, sdk_root: Path, logger: StructuredLogger | None = None):
        """Initialize SDK Manager.

        Args:
            sdk_root: Root directory for Android SDK
            logger: Optional logger instance
        """
        self.sdk_root = sdk_root.absolute()
        self.logger = logger
        self.cmdline_tools_dir = self.sdk_root / "cmdline-tools" / "latest"
        self.sdkmanager_path = self._get_sdkmanager_path()

    def _get_sdkmanager_path(self) -> Path:
        """Get path to sdkmanager executable."""
        host = detect_host()
        if host.os == "windows":
            return self.cmdline_tools_dir / "bin" / "sdkmanager.bat"
        else:
            return self.cmdline_tools_dir / "bin" / "sdkmanager"

    def _run_sdkmanager(
        self, args: list[str], input_text: str | None = None, timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """Run sdkmanager command.

        Args:
            args: Command arguments
            input_text: Optional input text
            timeout: Command timeout in seconds

        Returns:
            Completed process result
        """
        if not self.sdkmanager_path.exists():
            raise ComponentNotFoundError("sdkmanager", self.sdkmanager_path.parent)

        cmd = [str(self.sdkmanager_path)] + args

        # Set up environment
        env = os.environ.copy()
        env["ANDROID_SDK_ROOT"] = str(self.sdk_root)

        if self.logger:
            self.logger.debug(f"Running: {' '.join(cmd)}", command=cmd)

        try:
            result = subprocess.run(
                cmd,
                input=input_text,
                text=True,
                capture_output=True,
                timeout=timeout,
                env=env,
            )

            if result.returncode != 0 and "Warning:" not in result.stderr:
                raise SdkManagerError(" ".join(cmd), result.returncode, result.stderr)

            return result

        except subprocess.TimeoutExpired:
            raise SdkManagerError(" ".join(cmd), -1, f"Command timed out after {timeout}s")

    def ensure_cmdline_tools(self, version: str | None = None) -> Path:
        """Ensure command-line tools are installed.

        Args:
            version: SDK tools version (default: latest)

        Returns:
            Path to cmdline-tools directory
        """
        if self.cmdline_tools_dir.exists() and self.sdkmanager_path.exists():
            if self.logger:
                self.logger.debug("Command-line tools already installed")
            return self.cmdline_tools_dir

        with (
            self.logger.step("Installing SDK command-line tools") if self.logger else nullcontext()
        ):
            version = version or self.DEFAULT_SDK_TOOLS_VERSION

            # Download command-line tools
            filename = get_sdk_tools_filename(version)
            url = f"{self.SDK_BASE_URL}/{filename}"
            download_path = self.sdk_root / filename

            self.sdk_root.mkdir(parents=True, exist_ok=True)

            if not download_path.exists():
                if self.logger:
                    self.logger.info(f"Downloading: {url}")
                try:
                    _secure_urlretrieve(url, download_path)
                except Exception as e:
                    raise DownloadError(url, str(e))

            # Extract
            if self.logger:
                self.logger.info(f"Extracting: {download_path.name}")

            with zipfile.ZipFile(download_path, "r") as zip_ref:
                zip_ref.extractall(self.sdk_root)

            # Move to correct location
            extracted_dir = self.sdk_root / "cmdline-tools"
            if extracted_dir.exists():
                latest_dir = self.sdk_root / "cmdline-tools" / "latest"

                # Check if tools are directly in cmdline-tools/ (new format)
                if (extracted_dir / "bin").exists():
                    import shutil
                    import tempfile

                    # Create temporary directory to move files
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir) / "cmdline-tools-backup"

                        # Move everything to temp
                        shutil.move(str(extracted_dir), str(temp_path))

                        # Recreate cmdline-tools and latest directories
                        extracted_dir.mkdir(exist_ok=True)
                        latest_dir.mkdir(parents=True, exist_ok=True)

                        # Move everything from temp to latest
                        for item in temp_path.iterdir():
                            shutil.move(str(item), str(latest_dir / item.name))
                else:
                    # Old format - find subdirectory with bin
                    for item in extracted_dir.iterdir():
                        if item.is_dir() and (item / "bin").exists():
                            if latest_dir.exists():
                                import shutil

                                shutil.rmtree(latest_dir)
                            item.rename(latest_dir)
                            break

            # Clean up download
            download_path.unlink()

            # Update sdkmanager path
            self.sdkmanager_path = self._get_sdkmanager_path()

            if not self.sdkmanager_path.exists():
                raise ComponentNotFoundError("sdkmanager", self.cmdline_tools_dir)

            # Make all scripts in bin directory executable
            bin_dir = self.sdk_root / "cmdline-tools" / "latest" / "bin"
            if bin_dir.exists():
                for script in bin_dir.iterdir():
                    if script.is_file():
                        script.chmod(0o755)

            if self.logger:
                self.logger.success("Command-line tools installed")

        return self.cmdline_tools_dir

    def ensure_platform_tools(self) -> Path:
        """Ensure platform-tools are installed.

        Returns:
            Path to platform-tools directory
        """
        platform_tools_dir = self.sdk_root / "platform-tools"

        if platform_tools_dir.exists():
            if self.logger:
                self.logger.debug("Platform-tools already installed")
            return platform_tools_dir

        with self.logger.step("Installing platform-tools") if self.logger else nullcontext():
            self._run_sdkmanager(["platform-tools"])

            if not platform_tools_dir.exists():
                raise ComponentNotFoundError("platform-tools", self.sdk_root)

            if self.logger:
                self.logger.success("Platform-tools installed")

        return platform_tools_dir

    def ensure_platform(self, api: int) -> Path:
        """Ensure Android platform is installed.

        Args:
            api: API level

        Returns:
            Path to platform directory
        """
        platform_id = f"platforms;android-{api}"
        platform_dir = self.sdk_root / "platforms" / f"android-{api}"

        if platform_dir.exists():
            if self.logger:
                self.logger.debug(f"Platform API {api} already installed")
            return platform_dir

        with self.logger.step(f"Installing platform API {api}") if self.logger else nullcontext():
            self._run_sdkmanager([platform_id])

            if not platform_dir.exists():
                raise ComponentNotFoundError(f"platform API {api}", self.sdk_root)

            if self.logger:
                self.logger.success(f"Platform API {api} installed")

        return platform_dir

    def ensure_build_tools(self, version: str = "34.0.0") -> Path:
        """Ensure build-tools are installed.

        Args:
            version: Build tools version

        Returns:
            Path to build-tools directory
        """
        build_tools_id = f"build-tools;{version}"
        build_tools_dir = self.sdk_root / "build-tools" / version

        if build_tools_dir.exists():
            if self.logger:
                self.logger.debug(f"Build-tools {version} already installed")
            return build_tools_dir

        with (
            self.logger.step(f"Installing build-tools {version}") if self.logger else nullcontext()
        ):
            self._run_sdkmanager([build_tools_id])

            if not build_tools_dir.exists():
                raise ComponentNotFoundError(f"build-tools {version}", self.sdk_root)

            if self.logger:
                self.logger.success(f"Build-tools {version} installed")

        return build_tools_dir

    def ensure_system_image(self, api: int, target: Target, arch: Arch) -> Path:
        """Ensure system image is installed.

        Args:
            api: API level
            target: System image target
            arch: Architecture

        Returns:
            Path to system image directory
        """
        package_id = f"system-images;android-{api};{target};{arch}"
        system_image_dir = self.sdk_root / "system-images" / f"android-{api}" / target / arch

        if system_image_dir.exists():
            if self.logger:
                self.logger.debug(f"System image {package_id} already installed")
            return system_image_dir

        with (
            self.logger.step(f"Installing system image: {package_id}")
            if self.logger
            else nullcontext()
        ):
            self._run_sdkmanager([package_id])

            if not system_image_dir.exists():
                raise ComponentNotFoundError(package_id, self.sdk_root)

            if self.logger:
                self.logger.success(f"System image installed: {package_id}")

        return system_image_dir

    def ensure_emulator(self) -> Path:
        """Ensure emulator is installed.

        Returns:
            Path to emulator directory
        """
        emulator_dir = self.sdk_root / "emulator"

        if emulator_dir.exists():
            if self.logger:
                self.logger.debug("Emulator already installed")
            return emulator_dir

        with self.logger.step("Installing emulator") if self.logger else nullcontext():
            self._run_sdkmanager(["emulator"])

            if not emulator_dir.exists():
                raise ComponentNotFoundError("emulator", self.sdk_root)

            if self.logger:
                self.logger.success("Emulator installed")

        return emulator_dir

    def ensure_cmake(self) -> Path:
        """Ensure CMake is installed.

        Returns:
            Path to cmake directory
        """
        cmake_dir = self.sdk_root / "cmake"

        if cmake_dir.exists():
            if self.logger:
                self.logger.debug("CMake already installed")
            return cmake_dir

        with self.logger.step("Installing CMake") if self.logger else nullcontext():
            # Install latest CMake version
            self._run_sdkmanager(["cmake;3.22.1"])

            if not cmake_dir.exists():
                raise ComponentNotFoundError("cmake", self.sdk_root)

            if self.logger:
                self.logger.success("CMake installed")

        return cmake_dir

    def accept_licenses(self) -> None:
        """Accept all Android SDK licenses."""
        if self.logger:
            self.logger.info("Accepting Android SDK licenses")

        # Send 'y' multiple times to accept all licenses
        yes_input = "y\n" * 10

        try:
            self._run_sdkmanager(["--licenses"], input_text=yes_input)
            if self.logger:
                self.logger.success("Licenses accepted")
        except SdkManagerError:
            # Licenses might already be accepted
            if self.logger:
                self.logger.debug("Licenses already accepted or no new licenses")

    def list_installed(self) -> list[SdkComponent]:
        """List installed SDK components.

        Returns:
            List of installed components
        """
        try:
            result = self._run_sdkmanager(["--list_installed"])
            components = []

            for line in result.stdout.split("\n"):
                line = line.strip()
                if not line or line.startswith("Path") or line.startswith("-"):
                    continue

                parts = line.split("|")
                if len(parts) >= 3:
                    path = parts[0].strip()
                    version = parts[1].strip()
                    description = parts[2].strip() if len(parts) > 2 else ""

                    components.append(
                        SdkComponent(
                            name=description or path,
                            package_id=path,
                            installed=True,
                            version=version,
                            path=self.sdk_root / path.replace(";", "/"),
                        )
                    )

            return components

        except SdkManagerError:
            return []

    def update_all(self) -> None:
        """Update all installed SDK packages."""
        if self.logger:
            self.logger.info("Updating all SDK packages")

        self._run_sdkmanager(["--update"])

        if self.logger:
            self.logger.success("SDK packages updated")
