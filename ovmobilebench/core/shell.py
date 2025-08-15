"""Shell command execution utilities."""

import subprocess
import shlex
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
    if isinstance(cmd, str):
        args = shlex.split(cmd)
        cmd_str = cmd
    else:
        args = list(cmd)
        cmd_str = " ".join(shlex.quote(arg) for arg in args)

    if verbose:
        print(f"Executing: {cmd_str}")

    start = time.time()

    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            env=env,
            cwd=cwd,
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            result = CommandResult(
                returncode=124,  # Standard timeout code
                stdout=stdout or "",
                stderr=f"TIMEOUT after {timeout}s\n{stderr or ''}",
                duration_sec=time.time() - start,
                cmd=cmd_str,
            )
            if check:
                raise TimeoutError(f"Command timed out after {timeout}s: {cmd_str}")
            return result

    except Exception as e:
        result = CommandResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            duration_sec=time.time() - start,
            cmd=cmd_str,
        )
        if check:
            raise
        return result

    result = CommandResult(
        returncode=proc.returncode,
        stdout=stdout or "",
        stderr=stderr or "",
        duration_sec=time.time() - start,
        cmd=cmd_str,
    )

    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode,
            cmd_str,
            output=stdout,
            stderr=stderr,
        )

    return result
