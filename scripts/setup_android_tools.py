#!/usr/bin/env python3
"""
Setup Android SDK and NDK for different platforms.
Supports Windows, macOS, and Linux.
"""

import os
import sys
import platform
import subprocess
import zipfile
import tarfile
import shutil
from pathlib import Path
from urllib.request import urlretrieve, urlopen
import argparse
import ssl

# Fix SSL certificate verification on macOS
if platform.system() == "Darwin":
    try:
        import certifi

        ssl._create_default_https_context = lambda: ssl.create_default_context(
            cafile=certifi.where()
        )
    except ImportError:
        # If certifi is not available, try to use system certificates
        pass


class AndroidToolsInstaller:
    """Install Android SDK and NDK across different platforms."""

    # Download URLs
    SDK_BASE_URL = "https://dl.google.com/android/repository"
    NDK_BASE_URL = "https://dl.google.com/android/repository"
    REPOSITORY_URL = "https://dl.google.com/android/repository/repository2-3.xml"

    @classmethod
    def fetch_available_versions(cls):
        """Fetch available versions from Google's repository."""
        import xml.etree.ElementTree as ET

        versions = {"sdk_tools": [], "ndk": [], "build_tools": [], "platforms": []}

        try:
            # Fetch repository XML
            print("Fetching latest version information from Google...")
            response = urlopen(cls.REPOSITORY_URL)
            xml_data = response.read()

            # Parse XML without namespace prefixes for simplicity
            root = ET.fromstring(xml_data)

            # Find all remote packages
            for elem in root.iter():
                if "remotePackage" in elem.tag and elem.get("path"):
                    path = elem.get("path")

                    # Command line tools
                    if "cmdline-tools" in path:
                        # Try to find revision
                        for child in elem.iter():
                            if "major" in child.tag and child.text:
                                versions["sdk_tools"].append(child.text)
                                break

                    # NDK versions
                    elif path.startswith("ndk;"):
                        version = path.split(";")[1]
                        # Convert numeric version to r-format if needed
                        if "." in version:
                            # Like 26.1.10909125 -> r26
                            major = version.split(".")[0]
                            versions["ndk"].append(f"r{major}")
                        else:
                            versions["ndk"].append(version)

                    # Build tools
                    elif path.startswith("build-tools;"):
                        version = path.split(";")[1]
                        versions["build_tools"].append(version)

                    # Platforms
                    elif path.startswith("platforms;android-"):
                        api_level = path.replace("platforms;android-", "")
                        if api_level.isdigit():
                            versions["platforms"].append(api_level)

            # Remove duplicates and sort
            for key in versions:
                versions[key] = sorted(set(versions[key]), reverse=True)

            # If we didn't find anything, use fallback
            if not any(versions.values()):
                raise ValueError("No versions found in XML")

            return versions

        except Exception as e:
            print(f"Warning: Could not fetch latest versions: {e}")
            print("Using fallback versions...")

            # Fallback to known good versions
            return {
                "sdk_tools": ["11076708", "10406996", "9477386"],
                "ndk": ["r27", "r26d", "r26c", "r25c", "r24"],
                "build_tools": ["35.0.0", "34.0.0", "33.0.2", "32.0.0"],
                "platforms": ["35", "34", "33", "32", "31", "30"],
            }

    def __init__(
        self,
        install_dir=None,
        ndk_only=False,
        sdk_version=None,
        ndk_version=None,
        build_tools_version=None,
        platform_version=None,
        fetch_latest=True,
    ):
        """Initialize installer.

        Args:
            install_dir: Installation directory (default: ~/android-sdk)
            ndk_only: Install only NDK without SDK
            sdk_version: SDK command line tools version (default: latest)
            ndk_version: NDK version (default: latest)
            build_tools_version: Build tools version (default: latest)
            platform_version: Android platform/API level (default: latest)
            fetch_latest: Fetch latest versions from Google (default: True)
        """
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.ndk_only = ndk_only

        # Fetch available versions if requested
        if fetch_latest:
            self.available_versions = self.fetch_available_versions()
        else:
            # Use fallback versions
            self.available_versions = {
                "sdk_tools": ["11076708"],
                "ndk": ["r26d"],
                "build_tools": ["34.0.0"],
                "platforms": ["34"],
            }

        # Set versions (use latest from fetched if not specified)
        if sdk_version and sdk_version in self.available_versions["sdk_tools"]:
            self.SDK_TOOLS_VERSION = sdk_version
        else:
            self.SDK_TOOLS_VERSION = (
                self.available_versions["sdk_tools"][0]
                if self.available_versions["sdk_tools"]
                else "11076708"
            )

        if ndk_version and ndk_version in self.available_versions["ndk"]:
            self.NDK_VERSION = ndk_version
        else:
            self.NDK_VERSION = (
                self.available_versions["ndk"][0] if self.available_versions["ndk"] else "r26d"
            )

        if build_tools_version and build_tools_version in self.available_versions["build_tools"]:
            self.BUILD_TOOLS_VERSION = build_tools_version
        else:
            self.BUILD_TOOLS_VERSION = (
                self.available_versions["build_tools"][0]
                if self.available_versions["build_tools"]
                else "34.0.0"
            )

        if platform_version and platform_version in self.available_versions["platforms"]:
            self.PLATFORM_VERSION = platform_version
        else:
            self.PLATFORM_VERSION = (
                self.available_versions["platforms"][0]
                if self.available_versions["platforms"]
                else "34"
            )

        # Set installation directory
        if install_dir:
            self.install_dir = Path(install_dir).expanduser().absolute()
        else:
            self.install_dir = Path.home() / "android-sdk"

        self.sdk_dir = self.install_dir / "sdk"
        self.ndk_dir = self.install_dir / "ndk" / self.NDK_VERSION
        self.cmdline_tools_dir = self.sdk_dir / "cmdline-tools" / "latest"

        # Platform-specific settings
        self.setup_platform_specific()

    def setup_platform_specific(self):
        """Setup platform-specific configurations."""
        if self.system == "windows":
            self.sdk_tools_file = f"commandlinetools-win-{self.SDK_TOOLS_VERSION}_latest.zip"
            self.ndk_file = f"android-ndk-{self.NDK_VERSION}-windows.zip"
            self.sdkmanager_cmd = "sdkmanager.bat"
            self.adb_cmd = "adb.exe"
        elif self.system == "darwin":  # macOS
            self.sdk_tools_file = f"commandlinetools-mac-{self.SDK_TOOLS_VERSION}_latest.zip"
            if "arm" in self.arch or "aarch64" in self.arch:
                # Apple Silicon
                self.ndk_file = f"android-ndk-{self.NDK_VERSION}-darwin.dmg"
            else:
                # Intel Mac
                self.ndk_file = f"android-ndk-{self.NDK_VERSION}-darwin.dmg"
            self.sdkmanager_cmd = "sdkmanager"
            self.adb_cmd = "adb"
        else:  # Linux
            self.sdk_tools_file = f"commandlinetools-linux-{self.SDK_TOOLS_VERSION}_latest.zip"
            self.ndk_file = f"android-ndk-{self.NDK_VERSION}-linux.zip"
            self.sdkmanager_cmd = "sdkmanager"
            self.adb_cmd = "adb"

    def download_file(self, url, dest_path, desc=""):
        """Download file with progress indicator."""
        print(f"Downloading {desc or url}...")

        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            sys.stdout.write(
                f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)"
            )
            sys.stdout.flush()

        try:
            urlretrieve(url, dest_path, reporthook=download_progress)
            print()  # New line after progress
            return True
        except Exception as e:
            print(f"\n  Error downloading: {e}")
            return False

    def extract_archive(self, archive_path, dest_dir):
        """Extract zip or tar archive."""
        print(f"Extracting {archive_path.name}...")

        dest_dir.mkdir(parents=True, exist_ok=True)

        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(dest_dir)
        elif archive_path.suffix in [".tar", ".gz", ".bz2", ".xz"]:
            with tarfile.open(archive_path, "r:*") as tar_ref:
                # Use data filter for Python 3.12+ to avoid deprecation warning
                if hasattr(tarfile, "data_filter"):
                    tar_ref.extractall(dest_dir, filter="data")
                else:
                    tar_ref.extractall(dest_dir)
        elif archive_path.suffix == ".dmg":
            # macOS DMG handling
            if self.system == "darwin":
                self.extract_dmg(archive_path, dest_dir)
            else:
                raise ValueError("DMG files can only be extracted on macOS")
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")

    def extract_dmg(self, dmg_path, dest_dir):
        """Extract DMG file on macOS."""
        print("Mounting DMG file...")

        # Mount DMG
        mount_cmd = ["hdiutil", "attach", str(dmg_path), "-nobrowse", "-quiet"]
        result = subprocess.run(mount_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to mount DMG: {result.stderr}")

        # Find mount point
        mount_point = None
        for line in result.stdout.splitlines():
            if "/Volumes/" in line:
                parts = line.split("\t")
                mount_point = parts[-1].strip()
                break

        if not mount_point:
            raise RuntimeError("Could not find DMG mount point")

        try:
            # Copy contents
            src = Path(mount_point) / f"AndroidNDK{self.NDK_VERSION[1:]}.app/Contents/NDK"
            if src.exists():
                shutil.copytree(src, dest_dir / f"android-ndk-{self.NDK_VERSION}")
            else:
                # Try alternative structure
                for item in Path(mount_point).iterdir():
                    if item.is_dir() and "ndk" in item.name.lower():
                        shutil.copytree(item, dest_dir / item.name)
                        break
        finally:
            # Unmount DMG
            subprocess.run(["hdiutil", "detach", mount_point, "-quiet"], check=False)

    def install_sdk_tools(self):
        """Install Android SDK command line tools."""
        if self.ndk_only:
            print("Skipping SDK installation (NDK only mode)")
            return True

        print("\n=== Installing Android SDK Command Line Tools ===")

        # Download URL
        url = f"{self.SDK_BASE_URL}/{self.sdk_tools_file}"
        download_path = self.install_dir / self.sdk_tools_file

        # Download if not exists
        if not download_path.exists():
            if not self.download_file(url, download_path, "SDK Command Line Tools"):
                return False
        else:
            print(f"Using cached {download_path.name}")

        # Extract
        self.extract_archive(download_path, self.sdk_dir)

        # Move to correct location
        extracted_dir = self.sdk_dir / "cmdline-tools"
        if extracted_dir.exists() and not self.cmdline_tools_dir.exists():
            latest_dir = self.sdk_dir / "cmdline-tools" / "latest"
            latest_dir.parent.mkdir(parents=True, exist_ok=True)

            # Find the actual tools directory
            for item in extracted_dir.iterdir():
                if item.is_dir() and (item / "bin" / self.sdkmanager_cmd).exists():
                    shutil.move(str(item), str(latest_dir))
                    break

        return True

    def install_sdk_packages(self):
        """Install SDK packages using sdkmanager."""
        if self.ndk_only:
            return True

        print("\n=== Installing SDK Packages ===")

        sdkmanager = self.cmdline_tools_dir / "bin" / self.sdkmanager_cmd

        if not sdkmanager.exists():
            print(f"Error: sdkmanager not found at {sdkmanager}")
            return False

        # Set ANDROID_SDK_ROOT
        env = os.environ.copy()
        env["ANDROID_SDK_ROOT"] = str(self.sdk_dir)

        # Accept licenses
        print("Accepting licenses...")
        yes_input = "y\n" * 10  # Accept multiple licenses
        subprocess.run(
            [str(sdkmanager), "--licenses"],
            input=yes_input,
            text=True,
            env=env,
            capture_output=True,
        )

        # Install packages
        packages = [
            "platform-tools",
            f"platforms;android-{self.PLATFORM_VERSION}",
            f"build-tools;{self.BUILD_TOOLS_VERSION}",
        ]

        for package in packages:
            print(f"Installing {package}...")
            result = subprocess.run(
                [str(sdkmanager), package], env=env, capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  Warning: Failed to install {package}")
                print(f"  Error: {result.stderr}")

        return True

    def install_ndk(self):
        """Install Android NDK."""
        print(f"\n=== Installing Android NDK {self.NDK_VERSION} ===")

        # Download URL
        url = f"{self.NDK_BASE_URL}/{self.ndk_file}"
        download_path = self.install_dir / self.ndk_file

        # Download if not exists
        if not download_path.exists():
            if not self.download_file(url, download_path, f"Android NDK {self.NDK_VERSION}"):
                return False
        else:
            print(f"Using cached {download_path.name}")

        # Extract
        ndk_parent = self.install_dir / "ndk"
        ndk_parent.mkdir(parents=True, exist_ok=True)
        self.extract_archive(download_path, ndk_parent)

        # Rename to version-specific directory if needed
        extracted_ndk = ndk_parent / f"android-ndk-{self.NDK_VERSION}"
        if extracted_ndk.exists() and not self.ndk_dir.exists():
            shutil.move(str(extracted_ndk), str(self.ndk_dir))

        return True

    def setup_environment(self):
        """Setup environment variables."""
        print("\n=== Setting up environment variables ===")

        env_vars = {}

        if not self.ndk_only:
            env_vars["ANDROID_SDK_ROOT"] = str(self.sdk_dir)
            env_vars["ANDROID_HOME"] = str(self.sdk_dir)

            # Add to PATH
            platform_tools = self.sdk_dir / "platform-tools"
            if platform_tools.exists():
                env_vars["PATH_ADDITIONS"] = [
                    str(platform_tools),
                    str(self.cmdline_tools_dir / "bin"),
                ]

        env_vars["ANDROID_NDK_ROOT"] = str(self.ndk_dir)
        env_vars["ANDROID_NDK_HOME"] = str(self.ndk_dir)
        env_vars["NDK_ROOT"] = str(self.ndk_dir)

        # Print environment setup instructions
        print("\nAdd the following to your shell configuration:")
        print("-" * 50)

        if self.system == "windows":
            # Windows (PowerShell)
            print("# PowerShell:")
            for key, value in env_vars.items():
                if key == "PATH_ADDITIONS":
                    for path in value:
                        print(f'$env:Path += ";{path}"')
                else:
                    print(f'$env:{key} = "{value}"')

            print("\n# Command Prompt:")
            for key, value in env_vars.items():
                if key == "PATH_ADDITIONS":
                    for path in value:
                        print(f"set PATH=%PATH%;{path}")
                else:
                    print(f"set {key}={value}")
        else:
            # Unix-like (bash/zsh)
            for key, value in env_vars.items():
                if key == "PATH_ADDITIONS":
                    paths = ":".join(value)
                    print(f'export PATH="${paths}:$PATH"')
                else:
                    print(f'export {key}="{value}"')

        print("-" * 50)

        # Save to file
        env_file = self.install_dir / "android_env.sh"
        with open(env_file, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# Android SDK/NDK environment variables\n\n")

            for key, value in env_vars.items():
                if key == "PATH_ADDITIONS":
                    paths = ":".join(value)
                    f.write(f'export PATH="{paths}:$PATH"\n')
                else:
                    f.write(f'export {key}="{value}"\n')

        print(f"\nEnvironment script saved to: {env_file}")
        print(f"Source it with: source {env_file}")

        return env_vars

    def verify_installation(self):
        """Verify the installation."""
        print("\n=== Verifying installation ===")

        success = True

        # Check NDK
        ndk_build = self.ndk_dir / "ndk-build"
        if self.system == "windows":
            ndk_build = self.ndk_dir / "ndk-build.cmd"

        if ndk_build.exists():
            print(f"✓ NDK found at: {self.ndk_dir}")
        else:
            print(f"✗ NDK not found at: {self.ndk_dir}")
            success = False

        if not self.ndk_only:
            # Check ADB
            adb = self.sdk_dir / "platform-tools" / self.adb_cmd
            if adb.exists():
                print(f"✓ ADB found at: {adb}")

                # Try to run ADB version
                try:
                    result = subprocess.run(
                        [str(adb), "version"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        version_line = result.stdout.split("\n")[0]
                        print(f"  {version_line}")
                except Exception as e:
                    print(f"  Warning: Could not run adb: {e}")
            else:
                print(f"✗ ADB not found at: {adb}")
                success = False

            # Check sdkmanager
            sdkmanager = self.cmdline_tools_dir / "bin" / self.sdkmanager_cmd
            if sdkmanager.exists():
                print(f"✓ sdkmanager found at: {sdkmanager}")
            else:
                print(f"✗ sdkmanager not found at: {sdkmanager}")
                success = False

        return success

    def cleanup(self):
        """Clean up downloaded files."""
        print("\n=== Cleaning up ===")

        # Remove downloaded archives
        for pattern in ["*.zip", "*.dmg", "*.tar.gz"]:
            for file in self.install_dir.glob(pattern):
                print(f"Removing {file.name}")
                file.unlink()

    @classmethod
    def list_available_versions(cls):
        """List all available versions."""
        versions = cls.fetch_available_versions()

        print("\n=== Available Versions (fetched from Google) ===\n")

        print("SDK Command Line Tools:")
        for i, version in enumerate(versions["sdk_tools"][:10]):  # Show top 10
            if i == 0:
                print(f"  {version} (latest)")
            else:
                print(f"  {version}")
        if len(versions["sdk_tools"]) > 10:
            print(f"  ... and {len(versions['sdk_tools']) - 10} more")

        print("\nNDK Versions:")
        for i, version in enumerate(versions["ndk"][:10]):  # Show top 10
            if i == 0:
                print(f"  {version} (latest)")
            else:
                print(f"  {version}")
        if len(versions["ndk"]) > 10:
            print(f"  ... and {len(versions['ndk']) - 10} more")

        print("\nBuild Tools Versions:")
        for i, version in enumerate(versions["build_tools"][:10]):  # Show top 10
            if i == 0:
                print(f"  {version} (latest)")
            else:
                print(f"  {version}")
        if len(versions["build_tools"]) > 10:
            print(f"  ... and {len(versions['build_tools']) - 10} more")

        print("\nAndroid Platform Versions:")
        android_names = {
            "35": "Android 15",
            "34": "Android 14",
            "33": "Android 13",
            "32": "Android 12L",
            "31": "Android 12",
            "30": "Android 11",
            "29": "Android 10",
            "28": "Android 9 (Pie)",
            "27": "Android 8.1 (Oreo)",
            "26": "Android 8.0 (Oreo)",
            "25": "Android 7.1 (Nougat)",
            "24": "Android 7.0 (Nougat)",
            "23": "Android 6.0 (Marshmallow)",
            "22": "Android 5.1 (Lollipop)",
            "21": "Android 5.0 (Lollipop)",
        }

        for i, version in enumerate(versions["platforms"][:15]):  # Show top 15
            name = android_names.get(version, "")
            if i == 0:
                print(f"  {version} - {name} (latest)" if name else f"  {version} (latest)")
            else:
                print(f"  {version} - {name}" if name else f"  {version}")
        if len(versions["platforms"]) > 15:
            print(f"  ... and {len(versions['platforms']) - 15} more")

    def install(self):
        """Run the complete installation process."""
        print(f"Installing Android tools to: {self.install_dir}")
        print(f"Platform: {self.system} ({self.arch})")
        print("Versions:")
        print(f"  SDK Tools: {self.SDK_TOOLS_VERSION}")
        print(f"  NDK: {self.NDK_VERSION}")
        if not self.ndk_only:
            print(f"  Build Tools: {self.BUILD_TOOLS_VERSION}")
            print(f"  Platform API: {self.PLATFORM_VERSION}")
        print(f"NDK only mode: {self.ndk_only}")

        # Create installation directory
        self.install_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Install SDK tools
            if not self.install_sdk_tools():
                print("Failed to install SDK tools")
                return False

            # Install SDK packages
            if not self.install_sdk_packages():
                print("Failed to install SDK packages")
                return False

            # Install NDK
            if not self.install_ndk():
                print("Failed to install NDK")
                return False

            # Setup environment
            self.setup_environment()

            # Verify installation
            if not self.verify_installation():
                print("\nInstallation completed with warnings")
                return False

            # Cleanup
            self.cleanup()

            print("\n✅ Installation completed successfully!")
            return True

        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Install Android SDK and NDK for mobile development"
    )
    parser.add_argument("--install-dir", help="Installation directory (default: ~/android-sdk)")
    parser.add_argument("--ndk-only", action="store_true", help="Install only NDK without SDK")
    parser.add_argument(
        "--list-versions", action="store_true", help="List all available versions and exit"
    )
    parser.add_argument("--sdk-version", help="SDK command line tools version (default: latest)")
    parser.add_argument("--ndk-version", help="NDK version to install (default: latest)")
    parser.add_argument("--build-tools-version", help="Build tools version (default: latest)")
    parser.add_argument("--platform-version", help="Android platform/API level (default: latest)")
    parser.add_argument(
        "--skip-cleanup", action="store_true", help="Skip cleanup of downloaded files"
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Don't fetch latest versions from Google (use fallback versions)",
    )

    args = parser.parse_args()

    # List versions if requested
    if args.list_versions:
        AndroidToolsInstaller.list_available_versions()
        sys.exit(0)

    # Create installer with specified versions
    installer = AndroidToolsInstaller(
        install_dir=args.install_dir,
        ndk_only=args.ndk_only,
        sdk_version=args.sdk_version,
        ndk_version=args.ndk_version,
        build_tools_version=args.build_tools_version,
        platform_version=args.platform_version,
        fetch_latest=not args.no_fetch,
    )

    # Run installation
    success = installer.install()

    # Skip cleanup if requested
    if not args.skip_cleanup and success:
        installer.cleanup()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
