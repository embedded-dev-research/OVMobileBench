"""Configuration schema definitions using Pydantic."""

from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional, Dict, Any
from pathlib import Path


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
    toolchain: Toolchain = Field(default_factory=Toolchain)
    options: BuildOptions = Field(default_factory=BuildOptions)


class PackageConfig(BaseModel):
    """Package configuration."""
    
    include_symbols: bool = Field(False, description="Include debug symbols")
    extra_files: List[str] = Field(default_factory=list, description="Additional files to include")


class DeviceConfig(BaseModel):
    """Device configuration."""
    
    kind: Literal["android", "linux_ssh", "ios"] = Field("android", description="Device type")
    serials: List[str] = Field(default_factory=list, description="Device serials (Android)")
    host: Optional[str] = Field(None, description="SSH host (Linux)")
    user: Optional[str] = Field(None, description="SSH user (Linux)")
    key_path: Optional[str] = Field(None, description="SSH key path (Linux)")
    push_dir: str = Field("/data/local/tmp/ovbench", description="Remote directory")
    use_root: bool = Field(False, description="Use root access")
    
    @validator("serials")
    def validate_serials(cls, v, values):
        if values.get("kind") == "android" and not v:
            raise ValueError("Android device requires at least one serial")
        return v


class ModelItem(BaseModel):
    """Model configuration."""
    
    name: str = Field(..., description="Model name")
    path: str = Field(..., description="Path to model XML file")
    precision: Optional[str] = Field(None, description="Model precision")
    tags: Dict[str, Any] = Field(default_factory=dict, description="Additional tags")
    
    @validator("path")
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
    
    repeats: int = Field(3, description="Number of repeats per configuration")
    matrix: RunMatrix = Field(default_factory=RunMatrix)
    cooldown_sec: int = Field(0, description="Cooldown between runs in seconds")
    timeout_sec: Optional[int] = Field(None, description="Timeout per run in seconds")
    warmup: bool = Field(False, description="Perform warmup run")


class SinkItem(BaseModel):
    """Report sink configuration."""
    
    type: Literal["json", "csv", "sqlite"] = Field(..., description="Sink type")
    path: str = Field(..., description="Output path")


class ReportConfig(BaseModel):
    """Report configuration."""
    
    sinks: List[SinkItem] = Field(..., description="Output sinks")
    tags: Dict[str, Any] = Field(default_factory=dict, description="Additional tags")
    aggregate: bool = Field(True, description="Aggregate results")
    include_raw: bool = Field(False, description="Include raw output")


class ProjectConfig(BaseModel):
    """Project configuration."""
    
    name: str = Field(..., description="Project name")
    run_id: str = Field(..., description="Run identifier")
    description: Optional[str] = Field(None, description="Run description")


class Experiment(BaseModel):
    """Complete experiment configuration."""
    
    project: ProjectConfig
    build: BuildConfig
    package: PackageConfig = Field(default_factory=PackageConfig)
    device: DeviceConfig
    models: List[ModelItem]
    run: RunConfig = Field(default_factory=RunConfig)
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
                                    combos.append({
                                        "model_name": model.name,
                                        "model_xml": model.path,
                                        "device": dev,
                                        "api": api,
                                        "niter": niter,
                                        "nireq": nireq,
                                        "nstreams": nstreams,
                                        "threads": threads,
                                        "infer_precision": precision,
                                    })
        return combos
    
    def get_total_runs(self) -> int:
        """Calculate total number of benchmark runs."""
        total = 0
        for model in self.models:
            total += len(self.expand_matrix_for_model(model)) * self.run.repeats
        return total * len(self.device.serials or [1])