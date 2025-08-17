#!/usr/bin/env python3
"""Test SSH device connectivity in CI environment."""

import os
import sys
from pathlib import Path


def test_ssh_in_ci():
    """Test SSH connectivity in CI environment."""

    # Check if SSH is available
    ssh_dir = Path.home() / ".ssh"
    id_rsa = ssh_dir / "id_rsa"

    if not ssh_dir.exists():
        print(f"SSH directory not found: {ssh_dir}")
        return False

    if not id_rsa.exists():
        print(f"SSH key not found: {id_rsa}")
        return False

    print(f"SSH directory exists: {ssh_dir}")
    print(f"SSH key exists: {id_rsa}")

    # Always try to connect to localhost
    import subprocess

    username = os.environ.get("USER") or os.environ.get("USERNAME", "runner")

    # Build SSH command
    ssh_cmd = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "ConnectTimeout=5",
        "-i",
        str(id_rsa),
        f"{username}@localhost",
        "echo",
        "SSH_TEST_SUCCESS",
    ]

    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)

        if "SSH_TEST_SUCCESS" in result.stdout:
            print("SSH connection test successful!")
            return True
        else:
            print(f"SSH test failed. stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")

            # Show more diagnostic info
            if "Connection refused" in result.stderr:
                print("SSH server is not running or not accepting connections")
            elif "Permission denied" in result.stderr:
                print("SSH authentication failed - check keys and permissions")
            elif "Host key verification failed" in result.stderr:
                print("SSH host key verification issue")

            return False

    except subprocess.TimeoutExpired:
        print("SSH connection timed out")
        return False
    except Exception as e:
        print(f"SSH test error: {e}")
        return False


if __name__ == "__main__":
    success = test_ssh_in_ci()
    sys.exit(0 if success else 1)
