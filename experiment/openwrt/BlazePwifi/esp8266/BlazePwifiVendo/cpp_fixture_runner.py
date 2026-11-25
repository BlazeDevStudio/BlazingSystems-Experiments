"""Shared build/run mechanics for source-extracted PHX-HARDWARE C++ fixtures.

Board-specific extraction, fixture assembly, expected exit codes, and assertions
stay in each lab. This module owns only temporary files and compiler/process
execution so those mechanics remain consistent and easy to debug.
"""

from pathlib import Path, PureWindowsPath
import math
from numbers import Real
import subprocess
import tempfile


DEFAULT_COMPILE_TIMEOUT_SECONDS = 30
DEFAULT_RUN_TIMEOUT_SECONDS = 10
MAX_DIAGNOSTIC_TAIL_CHARS = 3000


def _diagnostic_tail(value):
    """Return a bounded UTF-8-safe tail for process diagnostics."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    else:
        value = str(value)
    return value[-MAX_DIAGNOSTIC_TAIL_CHARS:]


def _timeout_error_message(context, phase, error):
    """Keep the useful tail of output when a timed-out child emitted diagnostics."""
    sections = []
    for label, value in (("stdout", error.stdout), ("stderr", error.stderr)):
        tail = _diagnostic_tail(value)
        if tail:
            sections.append(f"{label} tail:\n{tail}")
    suffix = "\n" + "\n".join(sections) if sections else ""
    return f"{context}: {phase} timed out{suffix}"




def _validate_timeout(name, value):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite positive number of seconds")
    try:
        valid = value > 0 and math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError(f"{name} must be a finite positive number of seconds")


def _validate_stem(stem):
    """Reject stems that could escape the runner-owned temporary directory."""
    if (
        not isinstance(stem, str)
        or not stem
        or stem in {".", ".."}
        or Path(stem).is_absolute()
        or "/" in stem
        or "\\" in stem
        or "\x00" in stem
    ):
        raise ValueError("stem must be a single safe filename component")


def _validate_prefix(prefix):
    """Keep TemporaryDirectory prefixes inside its default temporary root."""
    if (
        not isinstance(prefix, str)
        or prefix in {".", ".."}
        or "\x00" in prefix
        or "/" in prefix
        or "\\" in prefix
        or Path(prefix).is_absolute()
        or PureWindowsPath(prefix).drive
    ):
        raise ValueError("prefix must be a safe filename prefix")


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
    _validate_prefix(prefix)
    _validate_stem(stem)

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
            raise RuntimeError(_timeout_error_message(context, "compile", error)) from error

        if compiled.returncode:
            raise RuntimeError(
                f"{context}: compile failed:\n{_diagnostic_tail(compiled.stderr)}"
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
            raise RuntimeError(_timeout_error_message(context, "execution", error)) from error
