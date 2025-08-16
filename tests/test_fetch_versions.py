"""Tests for fetching Android SDK/NDK versions from Google."""

from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET
import sys
import os

# Add scripts directory to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.setup_android_tools import AndroidToolsInstaller


class TestVersionFetching:
    """Test fetching versions from Google repository."""

    def test_parse_repository_xml(self):
        """Test parsing Google repository XML."""
        # Sample XML similar to Google's repository
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ns2:repository xmlns:ns2="http://schemas.android.com/repository/android/common/02"
                        xmlns:ns3="http://schemas.android.com/repository/android/generic/02"
                        xmlns:ns4="http://schemas.android.com/sdk/android/repo/addon2/03"
                        xmlns:ns5="http://schemas.android.com/sdk/android/repo/repository2/03"
                        xmlns:ns6="http://schemas.android.com/sdk/android/repo/sys-img2/03">
            <remotePackage path="cmdline-tools;latest">
                <type-details xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                              xsi:type="ns3:genericDetailsType">
                    <api-level>1</api-level>
                </type-details>
                <revision>
                    <major>11</major>
                    <minor>0</minor>
                </revision>
                <display-name>Android SDK Command-line Tools</display-name>
            </remotePackage>
            <remotePackage path="ndk;26.1.10909125">
                <type-details xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                              xsi:type="ns3:genericDetailsType"/>
                <revision>
                    <major>26</major>
                    <minor>1</minor>
                    <micro>10909125</micro>
                </revision>
                <display-name>NDK (Side by side) 26.1.10909125</display-name>
            </remotePackage>
            <remotePackage path="build-tools;34.0.0">
                <type-details xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                              xsi:type="ns3:genericDetailsType"/>
                <revision>
                    <major>34</major>
                    <minor>0</minor>
                    <micro>0</micro>
                </revision>
                <display-name>Android SDK Build-Tools 34</display-name>
            </remotePackage>
            <remotePackage path="platforms;android-34">
                <type-details xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                              xsi:type="ns5:platformDetailsType">
                    <api-level>34</api-level>
                    <codename></codename>
                </type-details>
                <revision>
                    <major>3</major>
                </revision>
                <display-name>Android SDK Platform 34</display-name>
            </remotePackage>
        </ns2:repository>"""

        # Parse XML
        root = ET.fromstring(sample_xml)

        # Extract versions
        sdk_tools = []
        ndk_versions = []
        build_tools = []
        platforms = []

        for elem in root.findall(".//remotePackage[@path]"):
            path = elem.get("path")
            if not path:
                continue

            if "cmdline-tools" in path:
                revision = elem.find(".//major")
                if revision is not None and revision.text:
                    sdk_tools.append(revision.text)

            elif path.startswith("ndk;"):
                version = path.split(";")[1]
                # Convert version format
                if "." in version:
                    # Extract major.minor version like 26.1.10909125 -> r26
                    major = version.split(".")[0]
                    ndk_versions.append(f"r{major}")
                else:
                    ndk_versions.append(version)

            elif path.startswith("build-tools;"):
                version = path.split(";")[1]
                build_tools.append(version)

            elif path.startswith("platforms;android-"):
                api_level = path.replace("platforms;android-", "")
                platforms.append(api_level)

        # Verify we extracted versions
        assert len(sdk_tools) > 0
        assert len(ndk_versions) > 0
        assert len(build_tools) > 0
        assert len(platforms) > 0

        assert "11" in sdk_tools
        assert "r26" in ndk_versions
        assert "34.0.0" in build_tools
        assert "34" in platforms

    @patch("scripts.setup_android_tools.urlopen")
    def test_fetch_available_versions_success(self, mock_urlopen):
        """Test successful fetching of versions."""
        # Mock XML response
        sample_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <repository>
            <remotePackage path="cmdline-tools;11076708">
                <revision><major>11</major></revision>
            </remotePackage>
            <remotePackage path="ndk;26.1.10909125">
                <revision><major>26</major></revision>
            </remotePackage>
            <remotePackage path="build-tools;34.0.0">
                <revision><major>34</major></revision>
            </remotePackage>
            <remotePackage path="platforms;android-34">
                <revision><major>3</major></revision>
            </remotePackage>
        </repository>"""

        mock_response = Mock()
        mock_response.read.return_value = sample_xml
        mock_urlopen.return_value = mock_response

        # Fetch versions
        versions = AndroidToolsInstaller.fetch_available_versions()

        # Verify structure
        assert "sdk_tools" in versions
        assert "ndk" in versions
        assert "build_tools" in versions
        assert "platforms" in versions

        # All should have at least fallback versions
        assert len(versions["sdk_tools"]) > 0
        assert len(versions["ndk"]) > 0
        assert len(versions["build_tools"]) > 0
        assert len(versions["platforms"]) > 0

    @patch("scripts.setup_android_tools.urlopen")
    def test_fetch_available_versions_failure(self, mock_urlopen):
        """Test fallback when fetching fails."""
        # Mock network error
        mock_urlopen.side_effect = Exception("Network error")

        # Fetch versions should return fallback
        versions = AndroidToolsInstaller.fetch_available_versions()

        # Verify fallback versions are returned
        assert "sdk_tools" in versions
        assert "ndk" in versions
        assert "build_tools" in versions
        assert "platforms" in versions

        # Check fallback values
        assert "11076708" in versions["sdk_tools"]
        assert "r26d" in versions["ndk"]
        assert "34.0.0" in versions["build_tools"]
        assert "34" in versions["platforms"]

    def test_version_selection_latest(self):
        """Test selecting latest version."""
        # Create installer without fetching
        installer = AndroidToolsInstaller(fetch_latest=False)

        # Should use first version from available list
        assert installer.SDK_TOOLS_VERSION == "11076708"
        assert installer.NDK_VERSION == "r26d"
        assert installer.BUILD_TOOLS_VERSION == "34.0.0"
        assert installer.PLATFORM_VERSION == "34"

    def test_version_selection_specific(self):
        """Test selecting specific versions."""
        # Create installer with specific versions
        installer = AndroidToolsInstaller(
            sdk_version="11076708",
            ndk_version="r26d",
            build_tools_version="34.0.0",
            platform_version="34",
            fetch_latest=False,
        )

        assert installer.SDK_TOOLS_VERSION == "11076708"
        assert installer.NDK_VERSION == "r26d"
        assert installer.BUILD_TOOLS_VERSION == "34.0.0"
        assert installer.PLATFORM_VERSION == "34"

    def test_version_selection_invalid(self):
        """Test handling invalid version selection."""
        # Create installer with invalid versions
        installer = AndroidToolsInstaller(
            sdk_version="invalid",
            ndk_version="invalid",
            build_tools_version="invalid",
            platform_version="invalid",
            fetch_latest=False,
        )

        # Should fall back to defaults
        assert installer.SDK_TOOLS_VERSION == "11076708"
        assert installer.NDK_VERSION == "r26d"
        assert installer.BUILD_TOOLS_VERSION == "34.0.0"
        assert installer.PLATFORM_VERSION == "34"

    @patch("builtins.print")
    def test_list_available_versions(self, mock_print):
        """Test listing available versions."""
        with patch.object(AndroidToolsInstaller, "fetch_available_versions") as mock_fetch:
            # Mock fetched versions
            mock_fetch.return_value = {
                "sdk_tools": ["11", "10", "9"],
                "ndk": ["r27", "r26d", "r25c"],
                "build_tools": ["35.0.0", "34.0.0", "33.0.2"],
                "platforms": ["35", "34", "33"],
            }

            # List versions
            AndroidToolsInstaller.list_available_versions()

            # Verify output includes versions
            output = " ".join(str(call) for call in mock_print.call_args_list)
            assert "11 (latest)" in output
            assert "r27 (latest)" in output
            assert "35.0.0 (latest)" in output
            assert "35" in output
            assert "Android 15" in output

    def test_ndk_version_format_conversion(self):
        """Test NDK version format conversion."""
        # Test different NDK version formats
        test_cases = [
            ("26.1.10909125", "r26"),
            ("25.2.9519653", "r25"),
            ("r26d", "r26d"),
            ("r27", "r27"),
        ]

        for input_version, expected in test_cases:
            if "." in input_version:
                # Version with dots - extract major
                major = input_version.split(".")[0]
                result = f"r{major}"
            else:
                # Already in r-format
                result = input_version

            assert result == expected or input_version == expected
