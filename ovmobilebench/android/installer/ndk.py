"""NDK resolver and manager for Android NDK operations."""

import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.request import urlretrieve

from .detect import detect_host, get_ndk_filename
from .errors import ComponentNotFoundError, DownloadError, InvalidArgumentError, UnpackError
from .logging import StructuredLogger
from .sdkmanager import SdkManager
from .types import NdkSpec, NdkVersion


class NdkResolver:
    """Resolve and manage Android NDK installations."""

    NDK_BASE_URL = "https://dl.google.com/android/repository"

    def __init__(self, sdk_root: Path, logger: Optional[StructuredLogger] = None):
        """Initialize NDK resolver.

        Args:
            sdk_root: Root directory for Android SDK
            logger: Optional logger instance
        """
        self.sdk_root = sdk_root.absolute()
        self.ndk_dir = self.sdk_root / "ndk"
        self.logger = logger
        self.sdk_manager = SdkManager(sdk_root, logger)

    def resolve_path(self, spec: NdkSpec) -> Path:
        """Resolve NDK specification to a path.

        Args:
            spec: NDK specification

        Returns:
            Path to NDK installation

        Raises:
            InvalidArgumentError: If spec is invalid
            ComponentNotFoundError: If NDK not found
        """
        # If absolute path provided, validate and return it
        if spec.path:
            if not spec.path.exists():
                raise ComponentNotFoundError(f"NDK at {spec.path}")
            if not self._validate_ndk_path(spec.path):
                raise InvalidArgumentError("ndk_path", str(spec.path), "Not a valid NDK installation")
            return spec.path

        # Resolve alias to version
        if spec.alias:
            try:
                ndk_version = NdkVersion.from_alias(spec.alias)
            except ValueError:
                # Try as version string
                try:
                    ndk_version = NdkVersion.from_version(spec.alias)
                except ValueError:
                    raise InvalidArgumentError("ndk_alias", spec.alias, "Unknown NDK version")

            # Check if installed via sdkmanager
            ndk_path = self.ndk_dir / ndk_version.version
            if ndk_path.exists() and self._validate_ndk_path(ndk_path):
                return ndk_path

            # Check alternative location (r-style)
            ndk_path_alt = self.ndk_dir / spec.alias
            if ndk_path_alt.exists() and self._validate_ndk_path(ndk_path_alt):
                return ndk_path_alt

            raise ComponentNotFoundError(f"NDK {spec.alias}", self.ndk_dir)

        raise InvalidArgumentError("ndk_spec", str(spec), "No alias or path provided")

    def ensure(self, spec: NdkSpec) -> Path:
        """Ensure NDK is installed and return its path.

        Args:
            spec: NDK specification

        Returns:
            Path to NDK installation
        """
        # If path provided, just validate
        if spec.path:
            if not spec.path.exists():
                raise ComponentNotFoundError(f"NDK at {spec.path}")
            if not self._validate_ndk_path(spec.path):
                raise InvalidArgumentError("ndk_path", str(spec.path), "Not a valid NDK installation")
            if self.logger:
                self.logger.debug(f"Using NDK at: {spec.path}")
            return spec.path

        # Try to resolve existing installation
        try:
            path = self.resolve_path(spec)
            if self.logger:
                self.logger.debug(f"NDK {spec.alias} already installed at: {path}")
            return path
        except ComponentNotFoundError:
            # Need to install
            pass

        # Install NDK
        if spec.alias:
            return self._install_ndk(spec.alias)

        raise InvalidArgumentError("ndk_spec", str(spec), "No alias provided for installation")

    def _install_ndk(self, alias: str) -> Path:
        """Install NDK with given alias.

        Args:
            alias: NDK alias (e.g., "r26d")

        Returns:
            Path to installed NDK
        """
        with self.logger.step(f"Installing NDK {alias}") if self.logger else nullcontext():
            # Parse version
            try:
                ndk_version = NdkVersion.from_alias(alias)
            except ValueError:
                # Try via sdkmanager with version string
                return self._install_via_sdkmanager(alias)

            # Try sdkmanager first (preferred method)
            try:
                return self._install_via_sdkmanager(ndk_version.version)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to install via sdkmanager: {e}")
                # Fall back to direct download
                return self._install_via_download(alias)

    def _install_via_sdkmanager(self, version: str) -> Path:
        """Install NDK using sdkmanager.

        Args:
            version: NDK version string

        Returns:
            Path to installed NDK
        """
        # Ensure cmdline-tools are available
        self.sdk_manager.ensure_cmdline_tools()

        # Install NDK package
        package_id = f"ndk;{version}"
        if self.logger:
            self.logger.info(f"Installing NDK via sdkmanager: {package_id}")

        self.sdk_manager._run_sdkmanager([package_id])

        # Verify installation
        ndk_path = self.ndk_dir / version
        if not ndk_path.exists():
            raise ComponentNotFoundError(f"NDK {version}", self.ndk_dir)

        if self.logger:
            self.logger.success(f"NDK {version} installed via sdkmanager")

        return ndk_path

    def _install_via_download(self, alias: str) -> Path:
        """Install NDK via direct download.

        Args:
            alias: NDK alias (e.g., "r26d")

        Returns:
            Path to installed NDK
        """
        if self.logger:
            self.logger.info(f"Downloading NDK {alias}")

        # Get download URL
        filename = get_ndk_filename(alias)
        url = f"{self.NDK_BASE_URL}/{filename}"

        # Create NDK directory
        self.ndk_dir.mkdir(parents=True, exist_ok=True)

        # Download to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            download_path = Path(temp_dir) / filename

            if self.logger:
                self.logger.info(f"Downloading: {url}")

            try:
                urlretrieve(url, download_path)
            except Exception as e:
                raise DownloadError(url, str(e))

            # Extract based on file type
            if self.logger:
                self.logger.info(f"Extracting: {filename}")

            if download_path.suffix == ".zip":
                self._extract_zip(download_path, self.ndk_dir)
            elif download_path.suffix == ".dmg":
                self._extract_dmg(download_path, self.ndk_dir, alias)
            else:
                self._extract_tar(download_path, self.ndk_dir)

        # Find extracted NDK directory
        extracted_dir = self.ndk_dir / f"android-ndk-{alias}"
        if not extracted_dir.exists():
            # Try to find it
            for item in self.ndk_dir.iterdir():
                if item.is_dir() and alias in item.name:
                    extracted_dir = item
                    break

        if not extracted_dir.exists():
            raise UnpackError(Path(filename), "NDK directory not found after extraction")

        # Rename to version-specific directory
        try:
            ndk_version = NdkVersion.from_alias(alias)
            target_dir = self.ndk_dir / ndk_version.version
        except ValueError:
            target_dir = self.ndk_dir / alias

        if target_dir.exists():
            shutil.rmtree(target_dir)
        extracted_dir.rename(target_dir)

        if self.logger:
            self.logger.success(f"NDK {alias} installed via download")

        return target_dir

    def _extract_zip(self, archive_path: Path, dest_dir: Path) -> None:
        """Extract ZIP archive.

        Args:
            archive_path: Path to ZIP file
            dest_dir: Destination directory
        """
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(dest_dir)

    def _extract_tar(self, archive_path: Path, dest_dir: Path) -> None:
        """Extract TAR archive.

        Args:
            archive_path: Path to TAR file
            dest_dir: Destination directory
        """
        with tarfile.open(archive_path, "r:*") as tar_ref:
            # Use data filter for Python 3.12+ to avoid deprecation warning
            if hasattr(tarfile, "data_filter"):
                tar_ref.extractall(dest_dir, filter="data")
            else:
                tar_ref.extractall(dest_dir)

    def _extract_dmg(self, dmg_path: Path, dest_dir: Path, alias: str) -> None:
        """Extract DMG file on macOS.

        Args:
            dmg_path: Path to DMG file
            dest_dir: Destination directory
            alias: NDK alias for identifying content
        """
        host = detect_host()
        if host.os != "darwin":
            raise UnpackError(dmg_path, "DMG files can only be extracted on macOS")

        if self.logger:
            self.logger.info("Mounting DMG file")

        # Mount DMG
        mount_cmd = ["hdiutil", "attach", str(dmg_path), "-nobrowse", "-quiet"]
        result = subprocess.run(mount_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise UnpackError(dmg_path, f"Failed to mount DMG: {result.stderr}")

        # Find mount point
        mount_point = None
        for line in result.stdout.splitlines():
            if "/Volumes/" in line:
                parts = line.split("\t")
                mount_point = parts[-1].strip()
                break

        if not mount_point:
            raise UnpackError(dmg_path, "Could not find DMG mount point")

        try:
            # Look for NDK content
            mount_path = Path(mount_point)
            ndk_found = False

            # Try standard locations
            possible_paths = [
                mount_path / f"AndroidNDK{alias[1:]}.app/Contents/NDK",
                mount_path / f"android-ndk-{alias}",
                mount_path / "NDK",
            ]

            for src in possible_paths:
                if src.exists():
                    target = dest_dir / f"android-ndk-{alias}"
                    shutil.copytree(src, target)
                    ndk_found = True
                    break

            # If not found, look for any NDK-like directory
            if not ndk_found:
                for item in mount_path.iterdir():
                    if item.is_dir() and "ndk" in item.name.lower():
                        target = dest_dir / f"android-ndk-{alias}"
                        shutil.copytree(item, target)
                        ndk_found = True
                        break

            if not ndk_found:
                raise UnpackError(dmg_path, "No NDK content found in DMG")

        finally:
            # Unmount DMG
            subprocess.run(["hdiutil", "detach", mount_point, "-quiet"], check=False)

    def _validate_ndk_path(self, path: Path) -> bool:
        """Validate that a path contains a valid NDK installation.

        Args:
            path: Path to validate

        Returns:
            True if valid NDK installation
        """
        if not path.exists() or not path.is_dir():
            return False

        # Check for key NDK files/directories
        required_items = [
            "ndk-build",  # Unix
            "ndk-build.cmd",  # Windows
            "toolchains",
            "prebuilt",
        ]

        found_count = 0
        for item in required_items:
            if (path / item).exists():
                found_count += 1

        # Need at least 2 of the required items
        return found_count >= 2

    def list_installed(self) -> List[Tuple[str, Path]]:
        """List installed NDK versions.

        Returns:
            List of (version, path) tuples
        """
        installed: List[Tuple[str, Path]] = []

        if not self.ndk_dir.exists():
            return installed

        for item in self.ndk_dir.iterdir():
            if item.is_dir() and self._validate_ndk_path(item):
                version = item.name
                installed.append((version, item))

        return installed

    def get_version(self, ndk_path: Path) -> Optional[str]:
        """Get NDK version from installation.

        Args:
            ndk_path: Path to NDK

        Returns:
            Version string or None
        """
        # Try to read from source.properties
        source_props = ndk_path / "source.properties"
        if source_props.exists():
            with open(source_props, "r") as f:
                for line in f:
                    if line.startswith("Pkg.Revision"):
                        parts = line.split("=")
                        if len(parts) > 1:
                            return parts[1].strip()

        # Fall back to directory name
        return ndk_path.name


# Context manager for when logger is not available
class nullcontext:
    """Null context manager for when logger is not available."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass