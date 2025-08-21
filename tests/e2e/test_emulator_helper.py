#!/usr/bin/env python3
"""
Helper functions for Android emulator management.
"""

import argparse
import logging
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_avd(api_level: int, avd_name: str = None):
    """Create Android Virtual Device."""
    if not avd_name:
        avd_name = f"test_avd_api{api_level}"

    logger.info(f"Creating AVD '{avd_name}' for API {api_level}...")

    cmd = [
        "avdmanager",
        "create",
        "avd",
        "-n",
        avd_name,
        "-k",
        f"system-images;android-{api_level};google_apis;arm64-v8a",
        "-d",
        "pixel_5",
        "--force",
    ]

    subprocess.run(cmd, input="no\n", text=True, check=True)
    logger.info(f"AVD '{avd_name}' created successfully")


def start_emulator(avd_name: str = None, api_level: int = 30):
    """Start Android emulator in background."""
    if not avd_name:
        avd_name = f"test_avd_api{api_level}"

    logger.info(f"Starting emulator '{avd_name}'...")

    cmd = [
        "emulator",
        "-avd",
        avd_name,
        "-no-window",
        "-no-audio",
        "-no-boot-anim",
        "-gpu",
        "swiftshader_indirect",
    ]

    # Add platform-specific acceleration
    import platform

    if platform.system() == "Linux":
        cmd.extend(["-accel", "on", "-qemu", "-enable-kvm"])
    elif platform.system() == "Darwin":  # macOS
        cmd.extend(["-accel", "on"])

    subprocess.Popen(cmd)
    logger.info("Emulator started in background")


def wait_for_boot(timeout: int = 300):
    """Wait for emulator to finish booting."""
    logger.info("Waiting for emulator to boot...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        result = subprocess.run(["adb", "wait-for-device"], capture_output=True, timeout=30)

        if result.returncode == 0:
            # Check if boot completed
            boot_result = subprocess.run(
                ["adb", "shell", "getprop", "sys.boot_completed"], capture_output=True, text=True
            )

            if boot_result.returncode == 0 and "1" in boot_result.stdout:
                logger.info("Emulator booted successfully!")
                return True

        time.sleep(5)

    logger.error("Emulator failed to boot within timeout")
    return False


def stop_emulator():
    """Stop running emulator."""
    logger.info("Stopping emulator...")
    subprocess.run(["adb", "emu", "kill"], check=False)
    time.sleep(2)
    logger.info("Emulator stopped")


def delete_avd(avd_name: str = None, api_level: int = 30):
    """Delete Android Virtual Device."""
    if not avd_name:
        avd_name = f"test_avd_api{api_level}"

    logger.info(f"Deleting AVD '{avd_name}'...")
    subprocess.run(["avdmanager", "delete", "avd", "-n", avd_name], check=False)


def main():
    parser = argparse.ArgumentParser(description="Android emulator helper")
    subparsers = parser.add_subparsers(dest="command")

    # Create AVD
    create_parser = subparsers.add_parser("create-avd")
    create_parser.add_argument("--api", type=int, default=30)
    create_parser.add_argument("--name", help="AVD name")

    # Start emulator
    start_parser = subparsers.add_parser("start-emulator")
    start_parser.add_argument("--name", help="AVD name")
    start_parser.add_argument("--api", type=int, default=30)

    # Wait for boot
    subparsers.add_parser("wait-for-boot")

    # Stop emulator
    subparsers.add_parser("stop-emulator")

    # Delete AVD
    delete_parser = subparsers.add_parser("delete-avd")
    delete_parser.add_argument("--name", help="AVD name")
    delete_parser.add_argument("--api", type=int, default=30)

    args = parser.parse_args()

    if args.command == "create-avd":
        create_avd(args.api, args.name)
    elif args.command == "start-emulator":
        start_emulator(args.name, args.api)
    elif args.command == "wait-for-boot":
        if not wait_for_boot():
            sys.exit(1)
    elif args.command == "stop-emulator":
        stop_emulator()
    elif args.command == "delete-avd":
        delete_avd(args.name, args.api)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
