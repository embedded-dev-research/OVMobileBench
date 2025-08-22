#!/usr/bin/env python3
"""
Helper functions for Android emulator management.
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sdk_path_from_config(config_file=None):
    """Get Android SDK path from OVMobileBench config."""
    # Use provided config file or default
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = Path.cwd() / "experiments" / "android_example.yaml"

    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Get cache_dir from config
        cache_dir = config.get("project", {}).get("cache_dir", "ovmb_cache")

        # Resolve cache_dir path
        if not Path(cache_dir).is_absolute():
            cache_dir = Path.cwd() / cache_dir
        else:
            cache_dir = Path(cache_dir)

        # SDK is in cache_dir/android-sdk
        sdk_path = cache_dir / "android-sdk"

        # Also check environment section for sdk_root
        env_section = config.get("environment")
        if env_section and isinstance(env_section, dict):
            env_sdk = env_section.get("sdk_root")
        else:
            env_sdk = None
        if env_sdk:
            sdk_path = Path(env_sdk)

        logger.info(f"Using config: {config_path}")
        return str(sdk_path)

    # Fallback to default
    logger.warning(f"Config not found at {config_path}, using default path")
    return str(Path.cwd() / "ovmb_cache" / "android-sdk")


def get_avd_home_from_config(config_file=None):
    """Get AVD home directory - use .android/avd in SDK location."""
    sdk_path = get_sdk_path_from_config(config_file)
    # AVD home is in SDK_PATH/.android/avd
    avd_home = str(Path(sdk_path) / ".android" / "avd")
    logger.info(f"Using AVD home: {avd_home}")
    return avd_home


def get_arch_from_config(config_file=None):
    """Get architecture from OVMobileBench config."""
    # Use provided config file or default
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = Path.cwd() / "experiments" / "android_example.yaml"

    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Get architecture from openvino.toolchain.abi
        arch = config.get("openvino", {}).get("toolchain", {}).get("abi", "arm64-v8a")
        logger.info(f"Using architecture from config: {arch}")
        return arch

    # Fallback to default
    logger.warning(f"Config not found at {config_path}, using default architecture")
    return "arm64-v8a"


# Global variables that will be initialized in main()
ANDROID_HOME = None
AVD_HOME = None
ARCHITECTURE = None


def create_avd(api_level: int, avd_name: str = None):
    """Create Android Virtual Device."""
    if not avd_name:
        avd_name = f"ovmobilebench_avd_api{api_level}"

    logger.info(
        f"Creating AVD '{avd_name}' for API {api_level} with architecture {ARCHITECTURE}..."
    )

    avdmanager_path = Path(ANDROID_HOME) / "cmdline-tools" / "latest" / "bin" / "avdmanager"

    # Set environment variables for AVD creation
    env = os.environ.copy()
    env["ANDROID_SDK_ROOT"] = ANDROID_HOME
    env["ANDROID_HOME"] = ANDROID_HOME
    env["ANDROID_AVD_HOME"] = AVD_HOME

    # Create AVD directory if it doesn't exist
    Path(AVD_HOME).mkdir(parents=True, exist_ok=True)

    cmd = [
        str(avdmanager_path),
        "create",
        "avd",
        "-n",
        avd_name,
        "-k",
        f"system-images;android-{api_level};google_apis;{ARCHITECTURE}",
        "-d",
        "pixel_5",
        "--force",
    ]

    subprocess.run(cmd, input="no\n", text=True, check=True, env=env)
    logger.info(f"AVD '{avd_name}' created successfully in {AVD_HOME}")


def start_emulator(avd_name: str = None, api_level: int = 30):
    """Start Android emulator in background."""
    if not avd_name:
        avd_name = f"ovmobilebench_avd_api{api_level}"  # Use OVMobileBench AVD name

    logger.info(f"Starting emulator '{avd_name}'...")

    # Use full path to emulator
    emulator_path = Path(ANDROID_HOME) / "emulator" / "emulator"
    if not emulator_path.exists():
        logger.error(f"Emulator not found at {emulator_path}")
        sys.exit(1)

    cmd = [
        str(emulator_path),
        "-avd",
        avd_name,
        "-no-window",
        "-no-audio",
        "-no-boot-anim",
        "-gpu",
        "swiftshader_indirect",
        "-no-snapshot-save",  # Don't save snapshots
    ]

    # Add platform-specific acceleration
    import platform

    if platform.system() == "Linux":
        # Check if KVM is available
        if Path("/dev/kvm").exists():
            logger.info("KVM acceleration available, enabling...")
            cmd.extend(["-accel", "on", "-qemu", "-enable-kvm"])
        else:
            logger.warning("KVM not available, using software acceleration")
            cmd.extend(["-accel", "off"])
    elif platform.system() == "Darwin":  # macOS
        cmd.extend(["-accel", "on"])

    # Set environment variables for AVD location
    env = os.environ.copy()
    env["ANDROID_SDK_ROOT"] = ANDROID_HOME
    env["ANDROID_HOME"] = ANDROID_HOME
    env["ANDROID_AVD_HOME"] = AVD_HOME

    subprocess.Popen(cmd, env=env)
    logger.info("Emulator started in background")


def wait_for_boot(timeout: int = 300):
    """Wait for emulator to finish booting."""
    logger.info("Waiting for emulator to boot...")

    # Use full path to adb
    adb_path = Path(ANDROID_HOME) / "platform-tools" / "adb"
    if not adb_path.exists():
        logger.error(f"ADB not found at {adb_path}")
        sys.exit(1)

    # First, check if any device is available
    logger.info("Checking for available devices...")
    devices_result = subprocess.run(
        [str(adb_path), "devices"], capture_output=True, text=True, timeout=10
    )
    logger.info(f"ADB devices output: {devices_result.stdout}")

    start_time = time.time()
    device_found = False

    while time.time() - start_time < timeout:
        try:
            # Use a shorter timeout for wait-for-device and retry
            result = subprocess.run(
                [str(adb_path), "wait-for-device"], capture_output=True, timeout=10
            )

            if result.returncode == 0:
                device_found = True
                # Check if boot completed
                boot_result = subprocess.run(
                    [str(adb_path), "shell", "getprop", "sys.boot_completed"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if boot_result.returncode == 0 and "1" in boot_result.stdout.strip():
                    logger.info("Emulator booted successfully!")
                    return True
                else:
                    logger.info(
                        f"Device found but not fully booted yet (boot_completed={boot_result.stdout.strip()})"
                    )
        except subprocess.TimeoutExpired:
            logger.info("wait-for-device timed out, retrying...")
            # Check devices again
            devices_result = subprocess.run(
                [str(adb_path), "devices"], capture_output=True, text=True, timeout=5
            )
            if "emulator" in devices_result.stdout or "device" in devices_result.stdout:
                logger.info(f"Devices found: {devices_result.stdout.strip()}")
            else:
                logger.warning("No devices found yet, emulator may still be starting...")

        time.sleep(5)

    if not device_found:
        logger.error("No emulator device was detected. The emulator may have failed to start.")
    else:
        logger.error("Emulator was detected but failed to complete boot within timeout")

    return False


def stop_emulator():
    """Stop running emulator."""
    logger.info("Stopping emulator...")
    adb_path = Path(ANDROID_HOME) / "platform-tools" / "adb"
    subprocess.run([str(adb_path), "emu", "kill"], check=False)
    time.sleep(2)
    logger.info("Emulator stopped")


def delete_avd(avd_name: str = None, api_level: int = 30):
    """Delete Android Virtual Device."""
    if not avd_name:
        avd_name = f"ovmobilebench_avd_api{api_level}"

    logger.info(f"Deleting AVD '{avd_name}'...")
    avdmanager_path = Path(ANDROID_HOME) / "cmdline-tools" / "latest" / "bin" / "avdmanager"

    # Set environment variables for AVD deletion
    env = os.environ.copy()
    env["ANDROID_SDK_ROOT"] = ANDROID_HOME
    env["ANDROID_HOME"] = ANDROID_HOME
    env["ANDROID_AVD_HOME"] = AVD_HOME

    subprocess.run([str(avdmanager_path), "delete", "avd", "-n", avd_name], check=False, env=env)


def main():
    parser = argparse.ArgumentParser(description="Android emulator helper")
    # Add global config argument
    parser.add_argument(
        "-c",
        "--config",
        help="Path to OVMobileBench config file",
        default="experiments/android_example.yaml",
    )

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

    # Initialize ANDROID_HOME, AVD_HOME and ARCHITECTURE from config
    global ANDROID_HOME, AVD_HOME, ARCHITECTURE
    ANDROID_HOME = get_sdk_path_from_config(args.config)
    AVD_HOME = get_avd_home_from_config(args.config)
    ARCHITECTURE = get_arch_from_config(args.config)
    os.environ["ANDROID_HOME"] = ANDROID_HOME
    os.environ["ANDROID_SDK_ROOT"] = ANDROID_HOME
    os.environ["ANDROID_AVD_HOME"] = AVD_HOME
    logger.info(f"Using Android SDK: {ANDROID_HOME}")
    logger.info(f"Using AVD home: {AVD_HOME}")
    logger.info(f"Using architecture: {ARCHITECTURE}")

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
