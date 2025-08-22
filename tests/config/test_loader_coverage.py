"""Tests to improve loader coverage to 100%."""

import os
from unittest.mock import patch

from ovmobilebench.config.loader import setup_environment


def test_java_home_auto_detection_from_env(tmp_path):
    """Test auto-detection of JAVA_HOME from environment variable."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    config = {"environment": {}}

    # Save original JAVA_HOME
    original_java_home = os.environ.get("JAVA_HOME")

    try:
        # Set JAVA_HOME in environment
        test_java_home = "/usr/lib/jvm/java-11"
        os.environ["JAVA_HOME"] = test_java_home

        with patch("builtins.print") as mock_print:
            result = setup_environment(config, project_dir)

        # Check that JAVA_HOME was auto-detected
        assert result["environment"]["java_home"] == test_java_home
        # Check that info message was printed
        mock_print.assert_any_call(f"INFO: Auto-detected Java from JAVA_HOME: {test_java_home}")

    finally:
        # Restore original environment
        if original_java_home:
            os.environ["JAVA_HOME"] = original_java_home
        else:
            os.environ.pop("JAVA_HOME", None)


def test_sdk_root_default_with_relative_cache_dir(tmp_path):
    """Test default SDK root when no ANDROID_HOME is set and cache_dir is relative."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    config = {"environment": {}, "project": {"cache_dir": "my_cache"}}  # Relative path

    # Save original ANDROID_HOME
    original_android_home = os.environ.get("ANDROID_HOME")

    try:
        # Make sure ANDROID_HOME is not set
        if "ANDROID_HOME" in os.environ:
            del os.environ["ANDROID_HOME"]

        with patch("builtins.print") as mock_print:
            result = setup_environment(config, project_dir)

        # Check that SDK root was set to default location
        expected_sdk = str(project_dir / "my_cache" / "android-sdk")
        assert result["environment"]["sdk_root"] == expected_sdk
        # Check that info message was printed
        mock_print.assert_any_call(f"INFO: Using default Android SDK location: {expected_sdk}")

    finally:
        # Restore original environment
        if original_android_home:
            os.environ["ANDROID_HOME"] = original_android_home
        else:
            os.environ.pop("ANDROID_HOME", None)


def test_sdk_root_default_with_absolute_cache_dir(tmp_path):
    """Test default SDK root when no ANDROID_HOME is set and cache_dir is absolute."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    cache_dir = tmp_path / "absolute_cache"
    cache_dir.mkdir()

    config = {"environment": {}, "project": {"cache_dir": str(cache_dir)}}  # Absolute path

    # Save original ANDROID_HOME
    original_android_home = os.environ.get("ANDROID_HOME")

    try:
        # Make sure ANDROID_HOME is not set
        if "ANDROID_HOME" in os.environ:
            del os.environ["ANDROID_HOME"]

        with patch("builtins.print") as mock_print:
            result = setup_environment(config, project_dir)

        # Check that SDK root was set to default location
        expected_sdk = str(cache_dir / "android-sdk")
        assert result["environment"]["sdk_root"] == expected_sdk
        # Check that info message was printed
        mock_print.assert_any_call(f"INFO: Using default Android SDK location: {expected_sdk}")

    finally:
        # Restore original environment
        if original_android_home:
            os.environ["ANDROID_HOME"] = original_android_home
        else:
            os.environ.pop("ANDROID_HOME", None)
