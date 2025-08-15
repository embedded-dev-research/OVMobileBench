"""Configuration module for OVBench."""

from .schema import Experiment, BuildConfig, DeviceConfig, RunConfig, ReportConfig
from .loader import load_experiment

__all__ = [
    "Experiment",
    "BuildConfig",
    "DeviceConfig",
    "RunConfig",
    "ReportConfig",
    "load_experiment",
]
