"""Configuration schema definitions using Pydantic."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Toolchain(BaseModel):
    """Toolchain configuration for building."""

    android_ndk: str | None = Field(None, description="Path to Android NDK")
    abi: str | None = Field("arm64-v8a", description="Target ABI")
    api_level: int | None = Field(24, description="Android API level")


class BuildOptions(BaseModel):
    """Build configuration options - all CMake options go here."""

    # Build type
    CMAKE_BUILD_TYPE: Literal["Release", "RelWithDebInfo", "Debug"] = "Release"

    # Compiler options
    CMAKE_C_COMPILER_LAUNCHER: str | None = None  # e.g., "ccache"
    CMAKE_CXX_COMPILER_LAUNCHER: str | None = None  # e.g., "ccache"

    # Generator
    CMAKE_GENERATOR: str | None = None  # e.g., "Ninja"

    # Android toolchain options
    CMAKE_TOOLCHAIN_FILE: str | None = None
    ANDROID_ABI: str | None = None  # e.g., "arm64-v8a"
    ANDROID_PLATFORM: str | None = None  # e.g., "android-30"
    ANDROID_STL: str | None = None  # e.g., "c++_shared"

    # OpenVINO component options
    ENABLE_INTEL_GPU: Literal["ON", "OFF"] = "OFF"
    ENABLE_ONEDNN_FOR_ARM: Literal["ON", "OFF"] = "OFF"
    ENABLE_PYTHON: Literal["ON", "OFF"] = "OFF"
    BUILD_SHARED_LIBS: Literal["ON", "OFF"] = "ON"
    ENABLE_TESTS: Literal["ON", "OFF"] = "OFF"
    ENABLE_FUNCTIONAL_TESTS: Literal["ON", "OFF"] = "OFF"
    ENABLE_SAMPLES: Literal["ON", "OFF"] = "ON"  # We need benchmark_app
    ENABLE_OPENCV: Literal["ON", "OFF"] = "OFF"


class OpenVINOConfig(BaseModel):
    """OpenVINO distribution configuration."""

    mode: Literal["build", "install", "link"] = Field(
        "build",
        description="How to obtain OpenVINO: build from source, use install dir, or download archive",
    )

    # For 'build' mode
    source_dir: str | None = Field(
        None, description="Path to OpenVINO source code (for build mode)"
    )
    commit: str = Field("HEAD", description="Git commit/tag to build (for build mode)")

    # For 'install' mode
    install_dir: str | None = Field(
        None, description="Path to OpenVINO install directory (for install mode)"
    )

    # For 'link' mode
    archive_url: str | None = Field(
        None, description="URL to OpenVINO archive (for link mode). Use 'latest' for auto-detection"
    )

    # Common build options (for build mode)
    toolchain: Toolchain = Field(
        default_factory=lambda: Toolchain(android_ndk=None, abi="arm64-v8a", api_level=24)
    )
    options: BuildOptions = Field(default_factory=lambda: BuildOptions())

    @model_validator(mode="after")
    def validate_mode_config(self):
        """Validate that required fields are set based on mode."""
        # source_dir is now optional for build mode - will be auto-set if not provided
        if self.mode == "install" and not self.install_dir:
            raise ValueError("install_dir is required when mode is 'install'")
        elif self.mode == "link" and not self.archive_url:
            raise ValueError("archive_url is required when mode is 'link'")
        return self


class PackageConfig(BaseModel):
    """Package configuration."""

    include_symbols: bool = Field(default=False, description="Include debug symbols")
    extra_files: list[str] = Field(default_factory=list, description="Additional files to include")


class DeviceConfig(BaseModel):
    """Device configuration."""

    kind: Literal["android", "linux_ssh", "ios"] = Field("android", description="Device type")
    type: Literal["android", "linux_ssh", "ios"] | None = Field(
        None, description="Alternative type field"
    )
    serials: list[str] = Field(default_factory=list, description="Device serials (Android)")
    host: str | None = Field(None, description="SSH host (Linux)")
    username: str | None = Field(None, description="SSH username (Linux)")
    user: str | None = Field(None, description="SSH user (Linux) - deprecated, use username")
    password: str | None = Field(None, description="SSH password (Linux)")
    key_filename: str | None = Field(None, description="SSH key file path (Linux)")
    key_path: str | None = Field(
        None, description="SSH key path (Linux) - deprecated, use key_filename"
    )
    port: int | None = Field(22, description="SSH port (Linux)")
    push_dir: str = Field(default="/data/local/tmp/ovmobilebench", description="Remote directory")
    use_root: bool = Field(default=False, description="Use root access")

    @model_validator(mode="after")
    def validate_device(self):
        # Support both 'kind' and 'type' fields
        if self.type and not self.kind:
            self.kind = self.type
        elif self.kind and not self.type:
            self.type = self.kind

        # Support deprecated field names
        if self.user and not self.username:
            self.username = self.user
        if self.key_path and not self.key_filename:
            self.key_filename = self.key_path

        # Validate based on device type
        if self.kind == "android" and not self.serials:
            # For Android, allow empty serials (will auto-detect)
            pass
        elif self.kind == "linux_ssh" or self.type == "linux_ssh":
            # For SSH, create a dummy serial if not provided
            if not self.serials:
                if self.host and self.username:
                    self.serials = [f"{self.username}@{self.host}:{self.port}"]
                elif self.host:
                    self.serials = [f"{self.host}:{self.port}"]
        return self


class ModelItem(BaseModel):
    """Model configuration."""

    name: str = Field(..., description="Model name")
    path: str = Field(..., description="Path to model XML file")
    precision: str | None = Field(None, description="Model precision")
    tags: dict[str, Any] = Field(default_factory=dict, description="Additional tags")

    @field_validator("path")
    @classmethod
    def validate_model_path(cls, v):
        if not v.endswith(".xml"):
            raise ValueError("Model path must be an XML file")
        return v


class ModelsConfig(BaseModel):
    """Models configuration - supports both individual models and directories."""

    directories: list[str] | None = Field(None, description="Directories to scan for models")
    extensions: list[str] = Field(
        default=[".xml", ".onnx", ".pb", ".tflite", ".bin"],
        description="Model file extensions to search for",
    )
    models: list[ModelItem] | None = Field(None, description="Individual model configurations")

    @model_validator(mode="after")
    def validate_models_config(self):
        if not self.directories and not self.models:
            raise ValueError("Either 'directories' or 'models' must be specified")
        return self


class RunMatrix(BaseModel):
    """Run matrix configuration."""

    niter: list[int] = Field([200], description="Number of iterations")
    api: list[Literal["sync", "async"]] = Field(["sync"], description="API mode")
    hint: list[Literal["latency", "throughput", "none"]] = Field(
        ["latency"], description="Performance hint"
    )
    device: list[str] = Field(["CPU"], description="Target device")
    infer_precision: list[str] = Field(["FP16"], description="Inference precision")
    # Legacy fields - kept for backward compatibility but not used with hint
    nireq: list[int] = Field(default=[1], description="Number of infer requests (use hint instead)")
    nstreams: list[str] = Field(default=["1"], description="Number of streams (use hint instead)")
    threads: list[int] = Field(default=[4], description="Number of threads (use hint instead)")


class RunConfig(BaseModel):
    """Run configuration."""

    repeats: int = Field(default=3, description="Number of repeats per configuration")
    matrix: RunMatrix = Field(
        default_factory=lambda: RunMatrix(
            niter=[200],
            api=["sync"],
            hint=["latency"],
            device=["CPU"],
            infer_precision=["FP16"],
        )
    )
    cooldown_sec: int = Field(default=0, description="Cooldown between runs in seconds")
    timeout_sec: int | None = Field(None, description="Timeout per run in seconds")
    warmup: bool = Field(default=False, description="Perform warmup run")


class SinkItem(BaseModel):
    """Report sink configuration."""

    type: Literal["json", "csv", "sqlite"] = Field(..., description="Sink type")
    path: str = Field(..., description="Output path")


class ReportConfig(BaseModel):
    """Report configuration."""

    sinks: list[SinkItem] = Field(..., description="Output sinks")
    tags: dict[str, Any] = Field(default_factory=dict, description="Additional tags")
    aggregate: bool = Field(default=True, description="Aggregate results")
    include_raw: bool = Field(default=False, description="Include raw output")


class EnvironmentConfig(BaseModel):
    """Environment configuration."""

    java_home: str | None = Field(
        None, description="Path to Java installation (required for Android)"
    )
    sdk_root: str | None = Field(
        None, description="Android SDK root path (will use cache_dir/android-sdk if not set)"
    )
    avd_home: str | None = Field(
        None, description="Android AVD home path (will use sdk_root/.android/avd if not set)"
    )


class ProjectConfig(BaseModel):
    """Project configuration."""

    name: str = Field(..., description="Project name")
    run_id: str = Field(..., description="Run identifier")
    description: str | None = Field(None, description="Run description")
    cache_dir: str = Field(
        "ovmb_cache", description="Cache directory for repositories, installations, and downloads"
    )


class Experiment(BaseModel):
    """Complete experiment configuration."""

    project: ProjectConfig
    environment: EnvironmentConfig = Field(default_factory=lambda: EnvironmentConfig())
    openvino: OpenVINOConfig
    package: PackageConfig = Field(default_factory=lambda: PackageConfig())
    device: DeviceConfig
    models: ModelsConfig | list[ModelItem]
    run: RunConfig = Field(
        default_factory=lambda: RunConfig(
            repeats=3,
            matrix=RunMatrix(
                niter=[200],
                api=["sync"],
                nireq=[1],
                nstreams=["1"],
                device=["CPU"],
                infer_precision=["FP16"],
                threads=[4],
            ),
            cooldown_sec=0,
            timeout_sec=None,
            warmup=False,
        )
    )
    report: ReportConfig

    def get_model_list(self) -> list[ModelItem]:
        """Get list of models, handling both formats."""
        if isinstance(self.models, list):
            # Legacy format - list of ModelItem
            return self.models
        elif isinstance(self.models, ModelsConfig):
            # New format - ModelsConfig
            model_list = []
            if self.models.models:
                model_list.extend(self.models.models)
            # Directory scanning will be handled by the loader
            return model_list
        return []

    def expand_matrix_for_model(self, model: ModelItem) -> list[dict[str, Any]]:
        """Expand run matrix for a specific model."""
        combos = []
        matrix = self.run.matrix

        for dev in matrix.device:
            for api in matrix.api:
                for niter in matrix.niter:
                    for hint in matrix.hint:
                        for precision in matrix.infer_precision:
                            combos.append(
                                {
                                    "model_name": model.name,
                                    "model_xml": model.path,
                                    "device": dev,
                                    "api": api,
                                    "niter": niter,
                                    "hint": hint,
                                    "infer_precision": precision,
                                }
                            )
        return combos

    def get_total_runs(self) -> int:
        """Calculate total number of benchmark runs."""
        total = 0
        model_list = self.get_model_list()
        for model in model_list:
            total += len(self.expand_matrix_for_model(model)) * self.run.repeats
        return total * len(self.device.serials or ["default"])
