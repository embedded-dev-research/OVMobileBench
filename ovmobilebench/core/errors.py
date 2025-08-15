"""Custom exception types."""


class OVMobileBenchError(Exception):
    """Base exception for OVMobileBench."""

    pass


class BuildError(OVMobileBenchError):
    """Build-related errors."""

    pass


class DeviceError(OVMobileBenchError):
    """Device-related errors."""

    pass


class RunError(OVMobileBenchError):
    """Runtime errors during benchmark execution."""

    pass


class ConfigError(OVMobileBenchError):
    """Configuration-related errors."""

    pass


class ParseError(OVMobileBenchError):
    """Parser-related errors."""

    pass
