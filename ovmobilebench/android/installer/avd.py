"""AVD (Android Virtual Device) management utilities."""

import os
import subprocess
from contextlib import nullcontext
from pathlib import Path
from typing import List, Optional

from .detect import detect_host
from .errors import AvdManagerError, ComponentNotFoundError
from .logging import StructuredLogger
from .types import Arch, Target


class AvdManager:
    """Manage Android Virtual Devices."""

    def __init__(self, sdk_root: Path, logger: Optional[StructuredLogger] = None):
        """Initialize AVD Manager.

        Args:
            sdk_root: Root directory for Android SDK
            logger: Optional logger instance
        """
        self.sdk_root = sdk_root.absolute()
        self.logger = logger
        self.avdmanager_path = self._get_avdmanager_path()

    def _get_avdmanager_path(self) -> Path:
        """Get path to avdmanager executable."""
        host = detect_host()
        if host.os == "windows":
            return self.sdk_root / "cmdline-tools" / "latest" / "bin" / "avdmanager.bat"
        else:
            return self.sdk_root / "cmdline-tools" / "latest" / "bin" / "avdmanager"

    def _run_avdmanager(
        self, args: List[str], input_text: Optional[str] = None, timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """Run avdmanager command.

        Args:
            args: Command arguments
            input_text: Optional input text
            timeout: Command timeout in seconds

        Returns:
            Completed process result
        """
        if not self.avdmanager_path.exists():
            raise ComponentNotFoundError("avdmanager", self.avdmanager_path.parent)

        cmd = [str(self.avdmanager_path)] + args

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

            if result.returncode != 0:
                # Check for common errors
                if "Package path is not valid" in result.stderr:
                    raise AvdManagerError(
                        "create", args[0] if args else "unknown", "System image not installed"
                    )
                raise AvdManagerError(
                    " ".join(args[:2]) if len(args) >= 2 else "unknown",
                    args[0] if args else "unknown",
                    result.stderr,
                )

            return result

        except subprocess.TimeoutExpired:
            raise AvdManagerError(
                " ".join(args[:2]) if len(args) >= 2 else "unknown",
                args[0] if args else "unknown",
                f"Command timed out after {timeout}s",
            )

    def list(self) -> List[str]:
        """List all AVDs.

        Returns:
            List of AVD names
        """
        try:
            result = self._run_avdmanager(["list", "avd", "-c"])
            avds = []
            for line in result.stdout.strip().split("\n"):
                if line and not line.startswith("*"):
                    avds.append(line.strip())
            return avds
        except (AvdManagerError, ComponentNotFoundError):
            return []

    def create(
        self,
        name: str,
        api: int,
        target: Target,
        arch: Arch,
        device: Optional[str] = None,
        force: bool = True,
    ) -> bool:
        """Create an AVD.

        Args:
            name: AVD name
            api: API level
            target: System image target
            arch: Architecture
            device: Device profile (default: pixel_5)
            force: Force overwrite if exists

        Returns:
            True if created successfully
        """
        # Check if already exists
        existing_avds = self.list()
        if name in existing_avds:
            if not force:
                if self.logger:
                    self.logger.info(f"AVD '{name}' already exists")
                return True
            else:
                # Delete existing
                self.delete(name)

        # Build package ID
        package_id = f"system-images;android-{api};{target};{arch}"

        # Build command
        args = ["create", "avd", "-n", name, "-k", package_id]

        # Add device profile if specified
        if device:
            args.extend(["-d", device])
        else:
            # Use default device
            args.extend(["-d", "pixel_5"])

        # Force creation
        if force:
            args.append("-f")

        with self.logger.step(f"Creating AVD: {name}") if self.logger else nullcontext():
            # Send 'no' to custom hardware profile prompt
            input_text = "no\n"

            try:
                self._run_avdmanager(args, input_text=input_text)

                # Verify creation
                if name not in self.list():
                    raise AvdManagerError("create", name, "AVD not found after creation")

                if self.logger:
                    self.logger.success(f"AVD '{name}' created successfully")
                return True

            except AvdManagerError as e:
                if self.logger:
                    self.logger.error(f"Failed to create AVD: {e}")
                raise

    def delete(self, name: str) -> bool:
        """Delete an AVD.

        Args:
            name: AVD name

        Returns:
            True if deleted successfully
        """
        if name not in self.list():
            if self.logger:
                self.logger.debug(f"AVD '{name}' does not exist")
            return True

        try:
            self._run_avdmanager(["delete", "avd", "-n", name])
            if self.logger:
                self.logger.info(f"AVD '{name}' deleted")
            return True
        except AvdManagerError:
            return False

    def get_info(self, name: str) -> Optional[dict]:
        """Get AVD information.

        Args:
            name: AVD name

        Returns:
            Dictionary with AVD info or None
        """
        try:
            result = self._run_avdmanager(["list", "avd"])

            # Parse output to find AVD info
            lines = result.stdout.split("\n")
            avd_info = {}
            in_avd = False

            for line in lines:
                line = line.strip()
                if f"Name: {name}" in line:
                    in_avd = True
                    avd_info["name"] = name
                elif in_avd:
                    if line.startswith("Name:") and name not in line:
                        # Started next AVD
                        break
                    elif ":" in line:
                        key, value = line.split(":", 1)
                        avd_info[key.strip().lower().replace(" ", "_")] = value.strip()

            return avd_info if avd_info else None

        except (AvdManagerError, ComponentNotFoundError):
            return None

    def list_devices(self) -> List[str]:
        """List available device profiles.

        Returns:
            List of device profile names
        """
        try:
            result = self._run_avdmanager(["list", "device", "-c"])
            devices = []
            for line in result.stdout.strip().split("\n"):
                if line and not line.startswith("id:"):
                    devices.append(line.strip())
            return devices
        except (AvdManagerError, ComponentNotFoundError):
            return []

    def list_targets(self) -> List[str]:
        """List available system image targets.

        Returns:
            List of target IDs
        """
        try:
            result = self._run_avdmanager(["list", "target", "-c"])
            targets = []
            for line in result.stdout.strip().split("\n"):
                if line and "android-" in line:
                    targets.append(line.strip())
            return targets
        except (AvdManagerError, ComponentNotFoundError):
            return []
