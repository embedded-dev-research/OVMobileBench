"""Additional tests for Device base class coverage gaps."""

from pathlib import Path

import pytest

from ovmobilebench.devices.base import Device


class TestDeviceBaseAdditional:
    """Test remaining gaps in Device base class."""

    def test_abstract_methods_not_implemented(self):
        """Test that Device cannot be instantiated without implementing abstract methods."""

        # Create a minimal concrete implementation that doesn't implement all methods
        class MinimalDevice(Device):
            pass

        # Should not be able to instantiate without implementing abstract methods
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            MinimalDevice("test_device")

    def test_cleanup_method(self):
        """Test the cleanup method implementation."""

        # Create a concrete implementation with minimal methods
        class TestDevice(Device):
            def __init__(self, name):
                super().__init__(name)
                self.removed_paths = []
                self.existing_paths = {"/test/path"}

            def push(self, local: Path, remote: str) -> None:
                pass

            def pull(self, remote: str, local: Path) -> None:
                pass

            def shell(self, cmd: str, timeout: int | None = None) -> tuple[int, str, str]:
                return (0, "", "")

            def exists(self, remote_path: str) -> bool:
                return remote_path in self.existing_paths

            def mkdir(self, remote_path: str) -> None:
                pass

            def rm(self, remote_path: str, recursive: bool = False) -> None:
                self.removed_paths.append((remote_path, recursive))
                self.existing_paths.discard(remote_path)

            def info(self) -> dict:
                return {"name": self.name}

            def is_available(self) -> bool:
                return True

        device = TestDevice("test_device")

        # Test cleanup when path exists
        device.cleanup("/test/path")
        assert ("/test/path", True) in device.removed_paths

        # Test cleanup when path doesn't exist
        device.cleanup("/nonexistent/path")
        # Should not try to remove non-existent path
        assert ("/nonexistent/path", True) not in device.removed_paths

    def test_get_env_default(self):
        """Test the get_env method returns empty dict by default."""

        class TestDevice(Device):
            def push(self, local: Path, remote: str) -> None:
                pass

            def pull(self, remote: str, local: Path) -> None:
                pass

            def shell(self, cmd: str, timeout: int | None = None) -> tuple[int, str, str]:
                return (0, "", "")

            def exists(self, remote_path: str) -> bool:
                return False

            def mkdir(self, remote_path: str) -> None:
                pass

            def rm(self, remote_path: str, recursive: bool = False) -> None:
                pass

            def info(self) -> dict:
                return {}

            def is_available(self) -> bool:
                return True

        device = TestDevice("test_device")
        assert device.get_env() == {}
