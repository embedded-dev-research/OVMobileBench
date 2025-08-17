"""Shell command execution utilities."""

import subprocess
import time
from dataclasses import dataclass
from typing import Optional, Dict, Union, List
from pathlib import Path


@dataclass
class CommandResult:
    """Result of command execution."""

    returncode: int
    stdout: str
    stderr: str
    duration_sec: float
    cmd: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run(
    cmd: Union[str, List[str]],
    timeout: Optional[int] = None,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[Path] = None,
    check: bool = False,
    capture: bool = True,
    verbose: bool = False,
) -> CommandResult:
    """Execute shell command with timeout and error handling.

    Args:
        cmd: Command to execute (string or list)
        timeout: Timeout in seconds
        env: Environment variables
        cwd: Working directory
        check: Raise exception on non-zero return code
        capture: Capture stdout/stderr
        verbose: Print command before execution

    Returns:
        CommandResult with execution details
    """
    # Convert to string for display
    cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)

    if verbose:
        print(f"Executing: {cmd_str}")

    start = time.time()

    try:
        # Use subprocess.run for simplicity and cross-platform compatibility
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            env=env,
            cwd=cwd,
            timeout=timeout,
            shell=isinstance(cmd, str),  # Use shell for string commands
            check=False,  # Handle errors ourselves for consistent behavior
        )

        duration = time.time() - start

        cmd_result = CommandResult(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            duration_sec=duration,
            cmd=cmd_str,
        )

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                cmd_str,
                output=result.stdout,
                stderr=result.stderr,
            )

        return cmd_result

    except subprocess.TimeoutExpired as e:
        duration = time.time() - start
        stdout_val = e.stdout if hasattr(e, "stdout") and e.stdout else b""
        stderr_val = e.stderr if hasattr(e, "stderr") and e.stderr else b""

        # Decode bytes to string
        stdout_str = (
            stdout_val.decode("utf-8", errors="replace")
            if isinstance(stdout_val, bytes)
            else stdout_val or ""
        )
        stderr_str = (
            stderr_val.decode("utf-8", errors="replace")
            if isinstance(stderr_val, bytes)
            else stderr_val or ""
        )

        cmd_result = CommandResult(
            returncode=124,  # Standard timeout code
            stdout=stdout_str,
            stderr=f"TIMEOUT after {timeout}s\n{stderr_str}",
            duration_sec=duration,
            cmd=cmd_str,
        )
        if check:
            raise TimeoutError(f"Command timed out after {timeout}s: {cmd_str}")
        return cmd_result

    except Exception as e:
        duration = time.time() - start
        cmd_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            duration_sec=duration,
            cmd=cmd_str,
        )
        if check:
            raise
        return cmd_result
