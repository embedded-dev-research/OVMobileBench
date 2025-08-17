"""Android device implementation using adbutils."""

import time
from pathlib import Path
from typing import Any

import adbutils
from adbutils import AdbDevice, AdbError

from ovmobilebench.core.errors import DeviceError
from ovmobilebench.devices.base import Device


def list_android_devices() -> list[tuple[str, str]]:
    """List available Android devices.

    Returns:
        List of (serial, status) tuples
    """
    try:
        adb = adbutils.AdbClient()
        devices = []
        for device in adb.device_list():
            # Get device state (device, offline, unauthorized)
            status = "device" if device.get_state() == "device" else device.get_state()
            devices.append((device.serial, status))
        return devices
    except Exception:
        return []


class AndroidDevice(Device):
    """Android device accessed via adbutils."""

    def __init__(self, serial: str, push_dir: str = "/data/local/tmp/ovmobilebench"):
        super().__init__(name=serial)
        self.serial = serial
        self.push_dir = push_dir
        self._device: AdbDevice | None = None
        self._connect()

    def _connect(self) -> None:
        """Connect to the device."""
        try:
            adb = adbutils.AdbClient()
            self._device = adb.device(self.serial)
            if not self._device:
                raise DeviceError(f"Device not found: {self.serial}")
        except Exception as e:
            raise DeviceError(f"Failed to connect to device {self.serial}: {e}")

    @property
    def device(self) -> AdbDevice:
        """Get the connected device instance."""
        if not self._device:
            self._connect()
        return self._device

    def push(self, local: Path, remote: str) -> None:
        """Push file or directory to device."""
        try:
            if local.is_dir():
                # Push directory recursively
                self.device.push(str(local), remote)
            else:
                # Push single file
                self.device.push(str(local), remote)
        except AdbError as e:
            raise DeviceError(f"Failed to push {local} to {remote}: {e}")
        except Exception as e:
            raise DeviceError(f"Failed to push {local} to {remote}: {e}")

    def pull(self, remote: str, local: Path) -> None:
        """Pull file or directory from device."""
        try:
            # Ensure local parent directory exists
            local.parent.mkdir(parents=True, exist_ok=True)
            self.device.pull(remote, str(local))
        except AdbError as e:
            raise DeviceError(f"Failed to pull {remote} to {local}: {e}")
        except Exception as e:
            raise DeviceError(f"Failed to pull {remote} to {local}: {e}")

    def shell(self, cmd: str, timeout: int | None = None) -> tuple[int, str, str]:
        """Execute shell command on device."""
        try:
            # adbutils returns output as string directly
            # It doesn't separate stdout/stderr, so we'll put everything in stdout
            output = self.device.shell(cmd, timeout=timeout)
            # adbutils doesn't return exit code directly for shell command
            # We'll check if the command succeeded by looking for typical error patterns
            # or by running echo $? after the command

            # Run command and get exit code
            full_cmd = f"{cmd}; echo __EXIT_CODE__$?"
            result = self.device.shell(full_cmd, timeout=timeout)

            # Parse output and exit code
            if "__EXIT_CODE__" in result:
                parts = result.split("__EXIT_CODE__")
                output = parts[0]
                try:
                    exit_code = int(parts[1].strip())
                except (ValueError, IndexError):
                    exit_code = 0
            else:
                output = result
                exit_code = 0

            return exit_code, output, ""
        except AdbError as e:
            return 1, "", str(e)
        except Exception as e:
            return 1, "", str(e)

    def exists(self, remote_path: str) -> bool:
        """Check if path exists on device."""
        try:
            # Use shell command to check existence
            output = self.device.shell(f"test -e {remote_path} && echo 1 || echo 0")
            return "1" in output
        except Exception:
            return False

    def mkdir(self, remote_path: str) -> None:
        """Create directory on device."""
        try:
            self.device.shell(f"mkdir -p {remote_path}")
        except AdbError as e:
            raise DeviceError(f"Failed to create directory {remote_path}: {e}")
        except Exception as e:
            raise DeviceError(f"Failed to create directory {remote_path}: {e}")

    def rm(self, remote_path: str, recursive: bool = False) -> None:
        """Remove file or directory from device."""
        try:
            flags = "-rf" if recursive else "-f"
            self.device.shell(f"rm {flags} {remote_path}")
        except AdbError as e:
            raise DeviceError(f"Failed to remove {remote_path}: {e}")
        except Exception as e:
            raise DeviceError(f"Failed to remove {remote_path}: {e}")

    def info(self) -> dict[str, Any]:
        """Get device information."""
        info: dict[str, Any] = {
            "serial": self.serial,
            "os": "Android",
        }

        try:
            # Get Android version
            android_version = self.device.shell("getprop ro.build.version.release").strip()
            if android_version:
                info["android_version"] = android_version

            # Get device model
            model = self.device.shell("getprop ro.product.model").strip()
            if model:
                info["model"] = model

            # Get CPU info
            cpu_info = self.device.shell("cat /proc/cpuinfo | grep 'Hardware' | head -1")
            if cpu_info and ":" in cpu_info:
                info["cpu"] = cpu_info.split(":")[-1].strip()

            # Get memory info
            mem_info = self.device.shell("cat /proc/meminfo | grep 'MemTotal'")
            if mem_info and "MemTotal:" in mem_info:
                mem_kb = int(mem_info.split()[1])
                info["memory_gb"] = round(mem_kb / 1024 / 1024, 2)

            # Get ABI
            abi = self.device.shell("getprop ro.product.cpu.abi").strip()
            if abi:
                info["abi"] = abi

            # Get device properties using adbutils built-in methods
            props = self.device.get_properties()
            if "ro.build.version.sdk" in props:
                info["sdk_version"] = props["ro.build.version.sdk"]
            if "ro.product.manufacturer" in props:
                info["manufacturer"] = props["ro.product.manufacturer"]

        except Exception as e:
            # If we can't get some info, just continue with what we have
            info["error"] = str(e)

        return info

    def is_available(self) -> bool:
        """Check if device is available and connected."""
        try:
            # Check if device is in device list and has "device" state
            state = self.device.get_state()
            return bool(state == "device")
        except Exception:
            return False

    def get_temperature(self) -> float | None:
        """Get device temperature if available."""
        try:
            # Try thermal zones
            temp_output = self.device.shell("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
            if temp_output and temp_output.strip():
                try:
                    return float(temp_output.strip()) / 1000.0  # Convert from millidegrees
                except ValueError:
                    pass

            # Try battery temperature
            battery_output = self.device.shell("dumpsys battery | grep temperature")
            if battery_output and "temperature:" in battery_output:
                try:
                    temp_str = battery_output.split(":")[-1].strip()
                    return float(temp_str) / 10.0  # Battery temp is in tenths of degree
                except (ValueError, IndexError):
                    pass

        except Exception:
            pass

        return None

    def set_cpu_governor(self, governor: str = "performance") -> bool:
        """Set CPU governor (requires root)."""
        try:
            self.device.shell(
                f"echo {governor} > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
            )
            return True
        except Exception:
            return False

    def disable_thermal_throttling(self) -> bool:
        """Attempt to disable thermal throttling (requires root)."""
        try:
            self.device.shell("stop thermal-engine")
            return True
        except Exception:
            return False

    def screen_off(self) -> None:
        """Turn screen off to reduce heat and interference."""
        try:
            self.device.shell("input keyevent 26")  # KEYCODE_POWER
        except Exception:
            pass

    def airplane_mode(self, enable: bool = True) -> None:
        """Enable/disable airplane mode."""
        try:
            value = "1" if enable else "0"
            self.device.shell(f"settings put global airplane_mode_on {value}")
            self.device.shell(
                f"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state {str(enable).lower()}"
            )
        except Exception:
            pass

    def disable_animations(self) -> None:
        """Disable system animations for consistent benchmarking."""
        try:
            self.device.shell("settings put global window_animation_scale 0")
            self.device.shell("settings put global transition_animation_scale 0")
            self.device.shell("settings put global animator_duration_scale 0")
        except Exception:
            pass

    def take_screenshot(self, local_path: Path) -> None:
        """Take a screenshot and save to local path."""
        try:
            # Take screenshot on device
            remote_path = "/sdcard/screenshot.png"
            self.device.shell(f"screencap -p {remote_path}")

            # Pull screenshot to local
            self.pull(remote_path, local_path)

            # Clean up remote screenshot
            self.rm(remote_path)
        except Exception as e:
            raise DeviceError(f"Failed to take screenshot: {e}")

    def start_screenrecord(
        self, remote_path: str = "/sdcard/screenrecord.mp4", time_limit: int = 180
    ) -> None:
        """Start screen recording (runs in background)."""
        try:
            # Start recording in background
            self.device.shell(f"screenrecord --time-limit {time_limit} {remote_path} &")
        except Exception as e:
            raise DeviceError(f"Failed to start screen recording: {e}")

    def stop_screenrecord(self) -> None:
        """Stop screen recording."""
        try:
            # Kill all screenrecord processes
            self.device.shell("pkill -f screenrecord")
        except Exception:
            pass

    def get_screenrecord(
        self, local_path: Path, remote_path: str = "/sdcard/screenrecord.mp4"
    ) -> None:
        """Get the recorded video file."""
        try:
            # Stop recording if still running
            self.stop_screenrecord()

            # Wait a bit for file to be finalized
            time.sleep(2)

            # Pull video to local
            self.pull(remote_path, local_path)

            # Clean up remote video
            self.rm(remote_path)
        except Exception as e:
            raise DeviceError(f"Failed to get screen recording: {e}")

    def install_apk(self, apk_path: Path) -> None:
        """Install an APK on the device."""
        try:
            self.device.install(str(apk_path))
        except Exception as e:
            raise DeviceError(f"Failed to install APK {apk_path}: {e}")

    def uninstall_package(self, package_name: str) -> None:
        """Uninstall a package from the device."""
        try:
            self.device.uninstall(package_name)
        except Exception as e:
            raise DeviceError(f"Failed to uninstall package {package_name}: {e}")

    def list_packages(self) -> list[str]:
        """List installed packages."""
        try:
            output = self.device.shell("pm list packages")
            packages = []
            for line in output.strip().split("\n"):
                if line.startswith("package:"):
                    packages.append(line.replace("package:", ""))
            return packages
        except Exception:
            return []

    def forward_port(self, local_port: int, remote_port: int) -> None:
        """Forward a local port to a remote port on the device."""
        try:
            self.device.forward(f"tcp:{local_port}", f"tcp:{remote_port}")
        except Exception as e:
            raise DeviceError(f"Failed to forward port {local_port} to {remote_port}: {e}")

    def reverse_port(self, remote_port: int, local_port: int) -> None:
        """Reverse forward a remote port to a local port."""
        try:
            self.device.reverse(f"tcp:{remote_port}", f"tcp:{local_port}")
        except Exception as e:
            raise DeviceError(f"Failed to reverse port {remote_port} to {local_port}: {e}")
