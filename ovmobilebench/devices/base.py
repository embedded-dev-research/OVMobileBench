"""Base device interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Dict, Any, Optional


class Device(ABC):
    """Abstract base class for device implementations."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def push(self, local: Path, remote: str) -> None:
        """Push file or directory to device."""
        pass

    @abstractmethod
    def pull(self, remote: str, local: Path) -> None:
        """Pull file or directory from device."""
        pass

    @abstractmethod
    def shell(self, cmd: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """Execute shell command on device.

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """Check if path exists on device."""
        pass

    @abstractmethod
    def mkdir(self, remote_path: str) -> None:
        """Create directory on device."""
        pass

    @abstractmethod
    def rm(self, remote_path: str, recursive: bool = False) -> None:
        """Remove file or directory from device."""
        pass

    @abstractmethod
    def info(self) -> Dict[str, Any]:
        """Get device information."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if device is available and connected."""
        pass

    def cleanup(self, remote_path: str) -> None:
        """Clean up temporary files on device."""
        if self.exists(remote_path):
            self.rm(remote_path, recursive=True)
    
    def get_env(self) -> Dict[str, str]:
        """Get environment variables for benchmark execution."""
        return {}
