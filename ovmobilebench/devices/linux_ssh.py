"""Linux SSH device implementation."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import paramiko
import os
from .base import Device
from ..core.errors import DeviceError
from ..core.logging import get_logger

logger = get_logger(__name__)


class LinuxSSHDevice(Device):
    """Linux device accessed via SSH."""

    def __init__(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        port: int = 22,
        push_dir: str = "/tmp/ovmobilebench",
    ):
        """Initialize SSH device.

        Args:
            host: Hostname or IP address
            username: SSH username
            password: SSH password (optional if using key)
            key_filename: Path to private key file (optional)
            port: SSH port (default 22)
            push_dir: Remote directory for deployment
        """
        super().__init__(f"{username}@{host}:{port}")
        self.serial = f"{username}@{host}:{port}"
        self.host = host
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.push_dir = push_dir
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self._connect()

    def _connect(self):
        """Establish SSH connection."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Prepare connection kwargs
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
            }

            if self.key_filename:
                # Expand ~ in key path
                key_path = os.path.expanduser(self.key_filename)
                if os.path.exists(key_path):
                    connect_kwargs["key_filename"] = key_path
                else:
                    logger.warning(f"Key file not found: {key_path}, trying password auth")
                    if self.password:
                        connect_kwargs["password"] = self.password
            elif self.password:
                connect_kwargs["password"] = self.password
            else:
                # Try to use SSH agent or default keys
                connect_kwargs["look_for_keys"] = True
                connect_kwargs["allow_agent"] = True

            self.client.connect(**connect_kwargs)
            self.sftp = self.client.open_sftp()
            logger.info(f"Connected to {self.serial}")
        except Exception as e:
            raise DeviceError(f"Failed to connect to {self.serial}: {e}")

    def push(self, local: Path, remote: str) -> None:
        """Push file to device via SFTP."""
        if not self.sftp:
            raise DeviceError("SFTP connection not established")

        try:
            # Create remote directory if needed
            remote_dir = str(Path(remote).parent)
            self._mkdir_p(remote_dir)

            # Upload file
            self.sftp.put(str(local), remote)
            logger.debug(f"Pushed {local} to {remote}")

            # Make executable if it's a binary
            if local.suffix in ["", ".sh"]:
                self.shell(f"chmod +x {remote}")
        except Exception as e:
            raise DeviceError(f"Failed to push {local}: {e}")

    def pull(self, remote: str, local: Path) -> None:
        """Pull file from device via SFTP."""
        if not self.sftp:
            raise DeviceError("SFTP connection not established")

        try:
            # Create local directory if needed
            local.parent.mkdir(parents=True, exist_ok=True)

            # Download file
            self.sftp.get(remote, str(local))
            logger.debug(f"Pulled {remote} to {local}")
        except Exception as e:
            raise DeviceError(f"Failed to pull {remote}: {e}")

    def shell(self, cmd: str, timeout: Optional[int] = 120) -> tuple[int, str, str]:
        """Execute command on device via SSH."""
        if not self.client:
            raise DeviceError("SSH connection not established")

        try:
            # Execute command
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)

            # Read output
            stdout_text = stdout.read().decode("utf-8", errors="replace")
            stderr_text = stderr.read().decode("utf-8", errors="replace")
            returncode = stdout.channel.recv_exit_status()

            logger.debug(f"Command: {cmd}")
            logger.debug(f"Return code: {returncode}")

            return returncode, stdout_text, stderr_text
        except Exception as e:
            raise DeviceError(f"Failed to execute command: {e}")

    def exists(self, remote_path: str) -> bool:
        """Check if file/directory exists on device."""
        try:
            if self.sftp:
                self.sftp.stat(remote_path)
                return True
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Error checking {remote_path}: {e}")
        return False

    def mkdir(self, path: str) -> None:
        """Create directory on device."""
        self._mkdir_p(path)

    def _mkdir_p(self, path: str) -> None:
        """Create directory recursively (like mkdir -p)."""
        if not self.sftp:
            raise DeviceError("SFTP connection not established")

        try:
            # Check if already exists
            self.sftp.stat(path)
            return
        except FileNotFoundError:
            # Create parent first
            parent = str(Path(path).parent)
            if parent != "/" and parent != ".":
                self._mkdir_p(parent)

            # Create this directory
            try:
                self.sftp.mkdir(path)
                logger.debug(f"Created directory: {path}")
            except Exception:
                # May already exist due to race condition
                pass

    def rm(self, path: str, recursive: bool = False) -> None:
        """Remove file or directory from device."""
        if recursive:
            cmd = f"rm -rf {path}"
        else:
            cmd = f"rm -f {path}"

        returncode, _, stderr = self.shell(cmd)
        if returncode != 0 and stderr:
            logger.warning(f"Failed to remove {path}: {stderr}")

    def info(self) -> Dict[str, Any]:
        """Get device information."""
        info = {
            "type": "linux_ssh",
            "host": self.host,
            "port": self.port,
            "username": self.username,
        }

        # Get system info
        try:
            # OS info
            ret, stdout, _ = self.shell("uname -a")
            if ret == 0:
                info["kernel"] = stdout.strip()

            # CPU info
            ret, stdout, _ = self.shell("nproc")
            if ret == 0:
                info["cpu_cores"] = int(stdout.strip())

            # Memory info
            ret, stdout, _ = self.shell("free -h | grep Mem | awk '{print $2}'")
            if ret == 0:
                info["memory"] = stdout.strip()

            # Architecture
            ret, stdout, _ = self.shell("uname -m")
            if ret == 0:
                info["arch"] = stdout.strip()

            # Hostname
            ret, stdout, _ = self.shell("hostname")
            if ret == 0:
                info["hostname"] = stdout.strip()
        except Exception as e:
            logger.warning(f"Failed to get device info: {e}")

        return info

    def is_available(self) -> bool:
        """Check if device is available."""
        try:
            if self.client:
                transport = self.client.get_transport()
                if transport:
                    return bool(transport.is_active())
        except Exception:
            pass
        return False

    def get_env(self) -> Dict[str, str]:
        """Get environment variables for benchmark execution."""
        env = super().get_env()

        # Add LD_LIBRARY_PATH for shared libraries
        lib_path = f"{self.push_dir}/lib"
        env["LD_LIBRARY_PATH"] = f"{lib_path}:$LD_LIBRARY_PATH"

        return env

    def __del__(self):
        """Clean up SSH connection."""
        try:
            if self.sftp:
                self.sftp.close()
            if self.client:
                self.client.close()
        except Exception:
            pass


def list_ssh_devices(config_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """List configured SSH devices.

    Args:
        config_file: Optional path to SSH hosts config file

    Returns:
        List of SSH device info dictionaries
    """
    devices = []

    # Try to connect to localhost as a test
    try:
        import socket

        hostname = socket.gethostname()
        username = os.environ.get("USER", "user")

        devices.append(
            {
                "serial": f"{username}@localhost:22",
                "host": "localhost",
                "port": 22,
                "username": username,
                "status": "available",
                "type": "linux_ssh",
            }
        )

        # Also add actual hostname
        if hostname != "localhost":
            devices.append(
                {
                    "serial": f"{username}@{hostname}:22",
                    "host": hostname,
                    "port": 22,
                    "username": username,
                    "status": "available",
                    "type": "linux_ssh",
                }
            )
    except Exception as e:
        logger.warning(f"Failed to detect SSH devices: {e}")

    return devices
