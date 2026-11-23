"""Shared build/run mechanics for source-extracted PHX-HARDWARE C++ fixtures.

Board-specific extraction, fixture assembly, expected exit codes, and assertions
stay in each lab. This module owns only temporary files and compiler/process
execution so those mechanics remain consistent and easy to debug.
"""

from pathlib import Path
import math
from numbers import Real
import subprocess
import tempfile


DEFAULT_COMPILE_TIMEOUT_SECONDS = 30
DEFAULT_RUN_TIMEOUT_SECONDS = 10


def _validate_timeout(name, value):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite positive number of seconds")
    try:
        valid = value > 0 and math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError(f"{name} must be a finite positive number of seconds")


def run_cpp_fixture(
    source,
    *,
    prefix,
    stem,
    extra_flags=(),
    compile_timeout=DEFAULT_COMPILE_TIMEOUT_SECONDS,
    run_timeout=DEFAULT_RUN_TIMEOUT_SECONDS,
    context="C++ fixture",
):
    """Compile and execute one fixture, returning its CompletedProcess result.

    Every caller gets bounded compile/execution time. A lab may choose a
    different finite positive timeout for a known slower fixture.
    """
    _validate_timeout("compile_timeout", compile_timeout)
    _validate_timeout("run_timeout", run_timeout)

    with tempfile.TemporaryDirectory(prefix=prefix) as folder:
        cpp = Path(folder) / f"{stem}.cpp"
        binary = Path(folder) / stem
        cpp.write_text(source, encoding="utf-8")

        command = [
            "g++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            *extra_flags,
            str(cpp),
            "-o",
            str(binary),
        ]
        try:
            compiled = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=compile_timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f"{context}: compile timed out") from error

        if compiled.returncode:
            raise RuntimeError(
                f"{context}: compile failed:\n{compiled.stderr[-3000:]}"
            )

        try:
            return subprocess.run(
                [str(binary)],
                capture_output=True,
                text=True,
                check=False,
                timeout=run_timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f"{context}: execution timed out") from error
