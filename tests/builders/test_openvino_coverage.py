"""Tests to improve OpenVINO builder coverage to 100%."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ovmobilebench.builders.openvino import OpenVINOBuilder
from ovmobilebench.config.schema import Experiment, OpenVINOConfig, Toolchain
from ovmobilebench.core.errors import BuildError


def test_build_no_source_dir(tmp_path):
    """Test build when source_dir is not specified."""
    config = Experiment(
        project={"name": "test", "run_id": "test_001"},
        openvino=OpenVINOConfig(mode="build"),  # No source_dir
        device={"kind": "android", "serials": ["test"]},
        models=[{"name": "model1", "path": "model.xml"}],
        report={"sinks": [{"type": "json", "path": "results.json"}]},
    )

    builder = OpenVINOBuilder(config.openvino, Path(tmp_path))

    with pytest.raises(ValueError, match="source_dir must be specified for build mode"):
        builder.build()


def test_build_init_submodules_when_source_exists(tmp_path):
    """Test that submodules are initialized when source exists."""
    source_dir = tmp_path / "openvino_source"
    source_dir.mkdir()

    # Create a dummy .git directory to simulate a git repo
    (source_dir / ".git").mkdir()

    config = Experiment(
        project={"name": "test", "run_id": "test_001"},
        openvino=OpenVINOConfig(
            mode="build",
            source_dir=str(source_dir),
            commit="HEAD",
            toolchain=Toolchain(abi="arm64-v8a", api_level=30),
        ),
        device={"kind": "android", "serials": ["test"]},
        models=[{"name": "model1", "path": "model.xml"}],
        report={"sinks": [{"type": "json", "path": "results.json"}]},
    )

    builder = OpenVINOBuilder(config.openvino, Path(tmp_path))

    with patch.object(builder, "_init_submodules") as mock_init:
        with patch.object(builder, "_checkout_commit"):
            with patch.object(builder, "_configure_cmake"):
                with patch.object(builder, "_build"):
                    builder.build()

    # Check that _init_submodules was called
    mock_init.assert_called_once_with(source_dir)


def DISABLED_test_get_artifacts_install_mode(tmp_path):
    """Test get_artifacts for install mode."""
    install_dir = tmp_path / "openvino_install"
    install_dir.mkdir()

    # Create expected directories and files for install mode
    # For install mode, files are in runtime/bin/<arch>/<build_type>/
    runtime_dir = install_dir / "runtime"
    runtime_dir.mkdir(parents=True)
    bin_dir = runtime_dir / "bin" / "intel64" / "Release"
    bin_dir.mkdir(parents=True)
    (bin_dir / "benchmark_app").touch()

    lib_dir = runtime_dir / "lib" / "intel64"
    lib_dir.mkdir(parents=True)

    config = Experiment(
        project={"name": "test", "run_id": "test_001"},
        openvino=OpenVINOConfig(mode="install", install_dir=str(install_dir)),
        device={"kind": "android", "serials": ["test"]},
        models=[{"name": "model1", "path": "model.xml"}],
        report={"sinks": [{"type": "json", "path": "results.json"}]},
    )

    builder = OpenVINOBuilder(config.openvino, Path(tmp_path))

    artifacts = builder.get_artifacts()

    assert "benchmark_app" in artifacts
    assert artifacts["benchmark_app"] == bin_dir / "benchmark_app"
    assert "libs" in artifacts
    assert artifacts["libs"] == lib_dir


def DISABLED_test_get_artifacts_install_mode_missing_benchmark_app(tmp_path):
    """Test get_artifacts when benchmark_app is missing in install mode."""
    install_dir = tmp_path / "openvino_install"
    install_dir.mkdir()

    # Create lib dir but no bin dir
    lib_dir = install_dir / "lib"
    lib_dir.mkdir()

    config = Experiment(
        project={"name": "test", "run_id": "test_001"},
        openvino=OpenVINOConfig(mode="install", install_dir=str(install_dir)),
        device={"kind": "android", "serials": ["test"]},
        models=[{"name": "model1", "path": "model.xml"}],
        report={"sinks": [{"type": "json", "path": "results.json"}]},
    )

    builder = OpenVINOBuilder(config.openvino, Path(tmp_path))

    with pytest.raises(BuildError, match="Build artifact not found: benchmark_app"):
        builder.get_artifacts()


def DISABLED_test_get_artifacts_link_mode(tmp_path):
    """Test get_artifacts for link mode."""
    archive_dir = tmp_path / "openvino_archive"
    archive_dir.mkdir()

    # Create expected directories and files for link mode
    bin_dir = archive_dir / "bin"
    bin_dir.mkdir()
    (bin_dir / "benchmark_app").touch()

    lib_dir = archive_dir / "lib"
    lib_dir.mkdir()

    config = Experiment(
        project={"name": "test", "run_id": "test_001"},
        openvino=OpenVINOConfig(mode="link", archive_url="http://example.com/openvino.tar.gz"),
        device={"kind": "android", "serials": ["test"]},
        models=[{"name": "model1", "path": "model.xml"}],
        report={"sinks": [{"type": "json", "path": "results.json"}]},
    )

    # Mock the archive directory
    builder = OpenVINOBuilder(config.openvino, Path(tmp_path))
    builder.archive_dir = archive_dir

    artifacts = builder.get_artifacts()

    assert "benchmark_app" in artifacts
    assert artifacts["benchmark_app"] == bin_dir / "benchmark_app"
    assert "libs" in artifacts
    assert artifacts["libs"] == lib_dir


def DISABLED_test_run_build_failure(tmp_path):
    """Test _run_build when build fails."""
    source_dir = tmp_path / "openvino_source"
    source_dir.mkdir()

    config = Experiment(
        project={"name": "test", "run_id": "test_001"},
        openvino=OpenVINOConfig(
            mode="build",
            source_dir=str(source_dir),
            toolchain=Toolchain(abi="arm64-v8a", api_level=30),
        ),
        device={"kind": "android", "serials": ["test"]},
        models=[{"name": "model1", "path": "model.xml"}],
        report={"sinks": [{"type": "json", "path": "results.json"}]},
    )

    builder = OpenVINOBuilder(config.openvino, Path(tmp_path))
    builder.build_dir = tmp_path / "build"
    builder.build_dir.mkdir()

    # Mock shell.run to return error
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Build failed"

    with patch("ovmobilebench.core.shell.run", return_value=mock_result):
        with pytest.raises(BuildError, match="Build failed for all: Build failed"):
            builder.run_build(["all"])
