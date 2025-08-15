"""Android device implementation using ADB."""

import subprocess
import shlex
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from ovbench.devices.base import Device


def list_android_devices() -> List[Tuple[str, str]]:
    """List available Android devices.

    Returns:
        List of (serial, status) tuples
    """
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)

        devices = []
        for line in result.stdout.strip().split("\n")[1:]:
            if line:
                parts = line.split("\t")
                if len(parts) == 2:
                    devices.append((parts[0], parts[1]))
        return devices
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


class AndroidDevice(Device):
    """Android device accessed via ADB."""

    def __init__(self, serial: str, push_dir: str = "/data/local/tmp/ovbench"):
        super().__init__(name=serial)
        self.serial = serial
        self.push_dir = push_dir

    def _adb(self, args: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute ADB command."""
        cmd = ["adb", "-s", self.serial] + args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)

    def push(self, local: Path, remote: str) -> None:
        """Push file or directory to device."""
        result = self._adb(["push", str(local), remote])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to push {local} to {remote}: {result.stderr}")

    def pull(self, remote: str, local: Path) -> None:
        """Pull file or directory from device."""
        result = self._adb(["pull", remote, str(local)])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to pull {remote} to {local}: {result.stderr}")

    def shell(self, cmd: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """Execute shell command on device."""
        result = self._adb(["shell", cmd], timeout=timeout)
        return result.returncode, result.stdout, result.stderr

    def exists(self, remote_path: str) -> bool:
        """Check if path exists on device."""
        rc, _, _ = self.shell(f"test -e {shlex.quote(remote_path)} && echo 1 || echo 0")
        return rc == 0 and "1" in _

    def mkdir(self, remote_path: str) -> None:
        """Create directory on device."""
        rc, _, err = self.shell(f"mkdir -p {shlex.quote(remote_path)}")
        if rc != 0:
            raise RuntimeError(f"Failed to create directory {remote_path}: {err}")

    def rm(self, remote_path: str, recursive: bool = False) -> None:
        """Remove file or directory from device."""
        flags = "-rf" if recursive else "-f"
        rc, _, err = self.shell(f"rm {flags} {shlex.quote(remote_path)}")
        if rc != 0:
            raise RuntimeError(f"Failed to remove {remote_path}: {err}")

    def info(self) -> Dict[str, Any]:
        """Get device information."""
        info = {
            "serial": self.serial,
            "os": "Android",
        }

        # Get Android version
        rc, out, _ = self.shell("getprop ro.build.version.release")
        if rc == 0:
            info["android_version"] = out.strip()

        # Get device model
        rc, out, _ = self.shell("getprop ro.product.model")
        if rc == 0:
            info["model"] = out.strip()

        # Get CPU info
        rc, out, _ = self.shell("cat /proc/cpuinfo | grep 'Hardware' | head -1")
        if rc == 0 and out:
            info["cpu"] = out.split(":")[-1].strip()

        # Get memory info
        rc, out, _ = self.shell("cat /proc/meminfo | grep 'MemTotal'")
        if rc == 0 and out:
            mem_kb = int(out.split()[1])
            info["memory_gb"] = round(mem_kb / 1024 / 1024, 2)

        # Get ABI
        rc, out, _ = self.shell("getprop ro.product.cpu.abi")
        if rc == 0:
            info["abi"] = out.strip()

        return info

    def is_available(self) -> bool:
        """Check if device is available and connected."""
        devices = list_android_devices()
        for serial, status in devices:
            if serial == self.serial and status == "device":
                return True
        return False

    def get_temperature(self) -> Optional[float]:
        """Get device temperature if available."""
        # Try thermal zones
        rc, out, _ = self.shell("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
        if rc == 0 and out:
            try:
                return float(out.strip()) / 1000.0  # Convert from millidegrees
            except ValueError:
                pass

        # Try battery temperature
        rc, out, _ = self.shell("dumpsys battery | grep temperature")
        if rc == 0 and out:
            try:
                temp_str = out.split(":")[-1].strip()
                return float(temp_str) / 10.0  # Battery temp is in tenths of degree
            except (ValueError, IndexError):
                pass

        return None

    def set_cpu_governor(self, governor: str = "performance") -> bool:
        """Set CPU governor (requires root)."""
        rc, _, _ = self.shell(
            f"echo {governor} > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        )
        return rc == 0

    def disable_thermal_throttling(self) -> bool:
        """Attempt to disable thermal throttling (requires root)."""
        rc, _, _ = self.shell("stop thermal-engine")
        return rc == 0

    def screen_off(self) -> None:
        """Turn screen off to reduce heat and interference."""
        self.shell("input keyevent 26")  # KEYCODE_POWER

    def airplane_mode(self, enable: bool = True) -> None:
        """Enable/disable airplane mode."""
        value = "1" if enable else "0"
        self.shell(f"settings put global airplane_mode_on {value}")
        self.shell(
            f"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state {str(enable).lower()}"
        )

    def disable_animations(self) -> None:
        """Disable system animations for consistent benchmarking."""
        self.shell("settings put global window_animation_scale 0")
        self.shell("settings put global transition_animation_scale 0")
        self.shell("settings put global animator_duration_scale 0")
