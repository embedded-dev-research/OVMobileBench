"""Configuration schema definitions using Pydantic."""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Literal, Optional, Dict, Any


class Toolchain(BaseModel):
    """Toolchain configuration for building."""

    android_ndk: Optional[str] = Field(None, description="Path to Android NDK")
    abi: Optional[str] = Field("arm64-v8a", description="Target ABI")
    api_level: Optional[int] = Field(24, description="Android API level")
    cmake: str = Field("cmake", description="CMake executable path")
    ninja: str = Field("ninja", description="Ninja executable path")


class BuildOptions(BaseModel):
    """Build configuration options."""

    ENABLE_INTEL_GPU: Literal["ON", "OFF"] = "OFF"
    ENABLE_ONEDNN_FOR_ARM: Literal["ON", "OFF"] = "OFF"
    ENABLE_PYTHON: Literal["ON", "OFF"] = "OFF"
    BUILD_SHARED_LIBS: Literal["ON", "OFF"] = "ON"


class BuildConfig(BaseModel):
    """Build configuration."""

    enabled: bool = Field(True, description="Whether to build from source")
    openvino_repo: str = Field(..., description="Path to OpenVINO repository")
    openvino_commit: str = Field("HEAD", description="Git commit/tag to build")
    build_type: Literal["Release", "RelWithDebInfo", "Debug"] = "RelWithDebInfo"
    toolchain: Toolchain = Field(
        default_factory=lambda: Toolchain(
            android_ndk=None, abi="arm64-v8a", api_level=24, cmake="cmake", ninja="ninja"
        )
    )
    options: BuildOptions = Field(default_factory=lambda: BuildOptions())


class PackageConfig(BaseModel):
    """Package configuration."""

    include_symbols: bool = Field(default=False, description="Include debug symbols")
    extra_files: List[str] = Field(default_factory=list, description="Additional files to include")


class DeviceConfig(BaseModel):
    """Device configuration."""

    kind: Literal["android", "linux_ssh", "ios"] = Field("android", description="Device type")
    type: Optional[Literal["android", "linux_ssh", "ios"]] = Field(
        None, description="Alternative type field"
    )
    serials: List[str] = Field(default_factory=list, description="Device serials (Android)")
    host: Optional[str] = Field(None, description="SSH host (Linux)")
    username: Optional[str] = Field(None, description="SSH username (Linux)")
    user: Optional[str] = Field(None, description="SSH user (Linux) - deprecated, use username")
    password: Optional[str] = Field(None, description="SSH password (Linux)")
    key_filename: Optional[str] = Field(None, description="SSH key file path (Linux)")
    key_path: Optional[str] = Field(
        None, description="SSH key path (Linux) - deprecated, use key_filename"
    )
    port: Optional[int] = Field(22, description="SSH port (Linux)")
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
    precision: Optional[str] = Field(None, description="Model precision")
    tags: Dict[str, Any] = Field(default_factory=dict, description="Additional tags")

    @field_validator("path")
    @classmethod
    def validate_model_path(cls, v):
        if not v.endswith(".xml"):
            raise ValueError("Model path must be an XML file")
        return v


class RunMatrix(BaseModel):
    """Run matrix configuration."""

    niter: List[int] = Field([200], description="Number of iterations")
    api: List[Literal["sync", "async"]] = Field(["sync"], description="API mode")
    nireq: List[int] = Field([1], description="Number of infer requests")
    nstreams: List[str] = Field(["1"], description="Number of streams")
    device: List[str] = Field(["CPU"], description="Target device")
    infer_precision: List[str] = Field(["FP16"], description="Inference precision")
    threads: List[int] = Field([4], description="Number of threads")


class RunConfig(BaseModel):
    """Run configuration."""

    repeats: int = Field(default=3, description="Number of repeats per configuration")
    matrix: RunMatrix = Field(
        default_factory=lambda: RunMatrix(
            niter=[200],
            api=["sync"],
            nireq=[1],
            nstreams=["1"],
            device=["CPU"],
            infer_precision=["FP16"],
            threads=[4],
        )
    )
    cooldown_sec: int = Field(default=0, description="Cooldown between runs in seconds")
    timeout_sec: Optional[int] = Field(None, description="Timeout per run in seconds")
    warmup: bool = Field(default=False, description="Perform warmup run")


class SinkItem(BaseModel):
    """Report sink configuration."""

    type: Literal["json", "csv", "sqlite"] = Field(..., description="Sink type")
    path: str = Field(..., description="Output path")


class ReportConfig(BaseModel):
    """Report configuration."""

    sinks: List[SinkItem] = Field(..., description="Output sinks")
    tags: Dict[str, Any] = Field(default_factory=dict, description="Additional tags")
    aggregate: bool = Field(default=True, description="Aggregate results")
    include_raw: bool = Field(default=False, description="Include raw output")


class ProjectConfig(BaseModel):
    """Project configuration."""

    name: str = Field(..., description="Project name")
    run_id: str = Field(..., description="Run identifier")
    description: Optional[str] = Field(None, description="Run description")


class Experiment(BaseModel):
    """Complete experiment configuration."""

    project: ProjectConfig
    build: BuildConfig
    package: PackageConfig = Field(default_factory=lambda: PackageConfig())
    device: DeviceConfig
    models: List[ModelItem]
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

    def expand_matrix_for_model(self, model: ModelItem) -> List[Dict[str, Any]]:
        """Expand run matrix for a specific model."""
        combos = []
        matrix = self.run.matrix

        for dev in matrix.device:
            for api in matrix.api:
                for niter in matrix.niter:
                    for nireq in matrix.nireq:
                        for nstreams in matrix.nstreams:
                            for threads in matrix.threads:
                                for precision in matrix.infer_precision:
                                    combos.append(
                                        {
                                            "model_name": model.name,
                                            "model_xml": model.path,
                                            "device": dev,
                                            "api": api,
                                            "niter": niter,
                                            "nireq": nireq,
                                            "nstreams": nstreams,
                                            "threads": threads,
                                            "infer_precision": precision,
                                        }
                                    )
        return combos

    def get_total_runs(self) -> int:
        """Calculate total number of benchmark runs."""
        total = 0
        for model in self.models:
            total += len(self.expand_matrix_for_model(model)) * self.run.repeats
        return total * len(self.device.serials or ["default"])
