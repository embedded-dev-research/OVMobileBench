"""Tests for SSH config generation script."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import yaml

from scripts.generate_ssh_config import (
    generate_ssh_config,
    generate_ssh_test_script,
    generate_ssh_setup_script,
    main,
)


class TestGenerateSSHConfig:
    """Test SSH config generation."""

    def test_generate_ssh_config(self):
        """Test SSH config file generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_config.yaml"

            with patch.dict(os.environ, {"USER": "testuser"}):
                result = generate_ssh_config(str(output_file))

            assert result == str(output_file)
            assert output_file.exists()

            # Load and verify config
            with open(output_file) as f:
                config = yaml.safe_load(f)

            assert config["project"]["name"] == "ssh-test"
            assert config["device"]["type"] == "linux_ssh"
            assert config["device"]["host"] == "localhost"
            assert config["device"]["username"] == "testuser"
            assert config["device"]["push_dir"] == "/tmp/ovmobilebench"
            assert config["build"]["enabled"] is False
            assert len(config["models"]) == 1
            assert config["models"][0]["name"] == "dummy"
            assert config["run"]["repeats"] == 1
            assert config["run"]["warmup"] is False
            assert len(config["report"]["sinks"]) == 2

    def test_generate_ssh_config_with_existing_key(self):
        """Test SSH config generation with existing SSH key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_config.yaml"
            ssh_dir = Path(tmpdir) / ".ssh"
            ssh_dir.mkdir()
            ssh_key = ssh_dir / "id_rsa"
            ssh_key.touch()

            with patch.dict(os.environ, {"USER": "testuser", "HOME": tmpdir}):
                with patch("scripts.generate_ssh_config.Path.home", return_value=Path(tmpdir)):
                    result = generate_ssh_config(str(output_file))

            assert result == str(output_file)
            assert output_file.exists()

            # Load and verify config has key_filename
            with open(output_file) as f:
                config = yaml.safe_load(f)
            assert "key_filename" in config["device"]
            assert config["device"]["key_filename"] == str(ssh_key)

    def test_generate_ssh_test_script(self):
        """Test SSH test script generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_script.py"

            with patch.dict(os.environ, {"USER": "testuser"}):
                result = generate_ssh_test_script(str(output_file))

            assert result == str(output_file)
            assert output_file.exists()
            assert output_file.stat().st_mode & 0o111  # Check executable

            # Verify script content
            content = output_file.read_text()
            assert "#!/usr/bin/env python3" in content
            assert "LinuxSSHDevice" in content
            assert 'username="testuser"' in content
            assert "test_ssh_device()" in content

    def test_generate_ssh_setup_script(self):
        """Test SSH setup script generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "setup.sh"

            result = generate_ssh_setup_script(str(output_file))

            assert result == str(output_file)
            assert output_file.exists()
            assert output_file.stat().st_mode & 0o111  # Check executable

            # Verify script content
            content = output_file.read_text()
            assert "#!/bin/bash" in content
            assert "Setting up SSH server for CI" in content
            assert "ssh-keygen" in content
            assert "authorized_keys" in content

    @patch("scripts.generate_ssh_config.argparse.ArgumentParser.parse_args")
    def test_main_config(self, mock_args):
        """Test main function with config generation."""
        mock_args.return_value.type = "config"
        mock_args.return_value.output = None

        with patch("scripts.generate_ssh_config.generate_ssh_config") as mock_gen:
            main()
            mock_gen.assert_called_once_with("experiments/ssh_localhost_ci.yaml")

    @patch("scripts.generate_ssh_config.argparse.ArgumentParser.parse_args")
    def test_main_test(self, mock_args):
        """Test main function with test script generation."""
        mock_args.return_value.type = "test"
        mock_args.return_value.output = None

        with patch("scripts.generate_ssh_config.generate_ssh_test_script") as mock_gen:
            main()
            mock_gen.assert_called_once_with("scripts/test_ssh_device_ci.py")

    @patch("scripts.generate_ssh_config.argparse.ArgumentParser.parse_args")
    def test_main_setup(self, mock_args):
        """Test main function with setup script generation."""
        mock_args.return_value.type = "setup"
        mock_args.return_value.output = None

        with patch("scripts.generate_ssh_config.generate_ssh_setup_script") as mock_gen:
            main()
            mock_gen.assert_called_once_with("scripts/setup_ssh_ci.sh")

    @patch("scripts.generate_ssh_config.argparse.ArgumentParser.parse_args")
    def test_main_all(self, mock_args):
        """Test main function with all generation."""
        mock_args.return_value.type = "all"
        mock_args.return_value.output = None

        with patch("scripts.generate_ssh_config.generate_ssh_config") as mock_config:
            with patch("scripts.generate_ssh_config.generate_ssh_test_script") as mock_test:
                with patch("scripts.generate_ssh_config.generate_ssh_setup_script") as mock_setup:
                    main()
                    mock_config.assert_called_once()
                    mock_test.assert_called_once()
                    mock_setup.assert_called_once()

    @patch("scripts.generate_ssh_config.argparse.ArgumentParser.parse_args")
    def test_main_with_custom_output(self, mock_args):
        """Test main function with custom output path."""
        mock_args.return_value.type = "config"
        mock_args.return_value.output = "/custom/path.yaml"

        with patch("scripts.generate_ssh_config.generate_ssh_config") as mock_gen:
            main()
            mock_gen.assert_called_once_with("/custom/path.yaml")
