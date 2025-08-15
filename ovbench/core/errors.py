"""Custom exception types."""


class OVBenchError(Exception):
    """Base exception for OVBench."""

    pass


class BuildError(OVBenchError):
    """Build-related errors."""

    pass


class DeviceError(OVBenchError):
    """Device-related errors."""

    pass


class RunError(OVBenchError):
    """Runtime errors during benchmark execution."""

    pass


class ConfigError(OVBenchError):
    """Configuration-related errors."""

    pass


class ParseError(OVBenchError):
    """Parser-related errors."""

    pass
