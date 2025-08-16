#!/usr/bin/env python3
"""Generate SSH configuration and test scripts for CI."""

import os
import yaml
from datetime import datetime
from pathlib import Path
import argparse


def generate_ssh_config(output_file: str = "experiments/ssh_localhost_ci.yaml"):
    """Generate SSH configuration for CI testing."""

    # Get current user
    username = os.environ.get("USER", "runner")

    # Generate run ID with timestamp
    run_id = f"ci-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    config = {
        "project": {
            "name": "ssh-test",
            "run_id": run_id,
            "description": "SSH localhost test for CI",
        },
        "device": {
            "type": "linux_ssh",
            "host": "localhost",
            "username": username,
            "push_dir": "/tmp/ovmobilebench",
        },
        "build": {
            "enabled": False,
            "openvino_repo": "/tmp/openvino",  # Dummy path, not used when disabled
        },
        "models": [{"name": "dummy", "path": "/tmp/dummy_model.xml", "precision": "FP32"}],
        "run": {
            "repeats": 1,
            "warmup": False,
            "cooldown_sec": 0,
            "matrix": {
                "niter": [10],
                "device": ["CPU"],
                "nstreams": ["1"],
                "api": ["sync"],
                "nireq": [1],
                "infer_precision": ["FP16"],
                "threads": [4],
            },
        },
        "report": {
            "sinks": [
                {"type": "csv", "path": "experiments/results/ssh_test.csv"},
                {"type": "json", "path": "experiments/results/ssh_test.json"},
            ],
            "aggregate": True,
            "tags": {"test_type": "ssh_localhost", "ci": True, "user": username},
        },
    }

    # Check if SSH key exists
    ssh_key_path = Path.home() / ".ssh" / "id_rsa"
    if ssh_key_path.exists():
        config["device"]["key_filename"] = str(ssh_key_path)

    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write configuration
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"Generated SSH config: {output_file}")
    print(f"  Username: {username}")
    print(f"  Run ID: {run_id}")
    if ssh_key_path.exists():
        print(f"  SSH Key: {ssh_key_path}")

    return output_file


def generate_ssh_test_script(output_file: str = "scripts/test_ssh_device.py"):
    """Generate SSH device test script."""

    username = os.environ.get("USER", "runner")

    script_content = f'''#!/usr/bin/env python3
"""Test SSH device functionality."""

from ovmobilebench.devices.linux_ssh import LinuxSSHDevice
import os
from pathlib import Path

def test_ssh_device():
    """Test SSH device operations."""
    
    # Connect to localhost
    device = LinuxSSHDevice(
        host="localhost",
        username="{username}",
        key_filename="~/.ssh/id_rsa",
        push_dir="/tmp/ovmobilebench_test"
    )
    
    # Test operations
    print(f"Device available: {{device.is_available()}}")
    print(f"Device info: {{device.info()}}")
    
    # Create test file
    test_file = Path("/tmp/test_file.txt")
    test_file.write_text("test content from CI")
    
    # Test push
    device.push(test_file, "/tmp/ovmobilebench_test/test.txt")
    
    # Test shell command
    ret, out, err = device.shell("cat /tmp/ovmobilebench_test/test.txt")
    print(f"File content: {{out.strip()}}")
    assert out.strip() == "test content from CI", "File content mismatch"
    
    # Test exists
    exists = device.exists("/tmp/ovmobilebench_test/test.txt")
    print(f"File exists: {{exists}}")
    assert exists, "File should exist"
    
    # Test pull
    pulled_file = Path("/tmp/pulled_test.txt")
    device.pull("/tmp/ovmobilebench_test/test.txt", pulled_file)
    assert pulled_file.read_text() == "test content from CI", "Pulled file content mismatch"
    
    # Cleanup
    device.rm("/tmp/ovmobilebench_test", recursive=True)
    test_file.unlink()
    pulled_file.unlink()
    
    print("All SSH tests passed!")

if __name__ == "__main__":
    test_ssh_device()
'''

    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write script
    with open(output_path, "w") as f:
        f.write(script_content)

    # Make executable
    output_path.chmod(0o755)

    print(f"Generated SSH test script: {output_file}")
    return output_file


def generate_ssh_setup_script(output_file: str = "scripts/setup_ssh_ci.sh"):
    """Generate SSH setup script for CI."""

    script_content = """#!/bin/bash
# Setup SSH for CI testing

set -e

echo "Setting up SSH server for CI..."

# Install SSH server if not present
if ! command -v sshd &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y openssh-server
fi

# Generate SSH key if not exists
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
fi

# Setup authorized keys
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Configure SSH client
cat > ~/.ssh/config << EOF
Host localhost
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    LogLevel ERROR
EOF
chmod 600 ~/.ssh/config

# Start SSH service
sudo service ssh start || sudo systemctl start sshd

# Wait for SSH to be ready
sleep 2

# Test connection
if ssh -o ConnectTimeout=5 localhost "echo 'SSH connection successful'"; then
    echo "SSH setup completed successfully"
else
    echo "SSH connection test failed"
    exit 1
fi
"""

    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write script
    with open(output_path, "w") as f:
        f.write(script_content)

    # Make executable
    output_path.chmod(0o755)

    print(f"Generated SSH setup script: {output_file}")
    return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate SSH test configurations and scripts")
    parser.add_argument(
        "--type",
        choices=["config", "test", "setup", "all"],
        default="config",
        help="Type of file to generate",
    )
    parser.add_argument("--output", help="Output file path (optional, uses defaults)")

    args = parser.parse_args()

    if args.type == "config" or args.type == "all":
        output = (
            args.output
            if args.output and args.type == "config"
            else "experiments/ssh_localhost_ci.yaml"
        )
        generate_ssh_config(output)

    if args.type == "test" or args.type == "all":
        output = (
            args.output if args.output and args.type == "test" else "scripts/test_ssh_device_ci.py"
        )
        generate_ssh_test_script(output)

    if args.type == "setup" or args.type == "all":
        output = args.output if args.output and args.type == "setup" else "scripts/setup_ssh_ci.sh"
        generate_ssh_setup_script(output)


if __name__ == "__main__":
    main()
