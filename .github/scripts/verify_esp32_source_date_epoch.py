#!/usr/bin/env python3
"""Verify the pinned Arduino-ESP32 compile-time date/time producer and GCC epoch support."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


_EXPECTED_CORE_BLOBS = {
    "3.3.13": {
        "cores/esp32/chip-debug-report.cpp": "c462e8a8bab21910c6e499d7450c3e8903196836",
        "cores/esp32/main.cpp": "fee28f101a5ce8ba686bba518f1f964ff5a485f9",
    },
    "4.0.0": {
        "cores/esp32/chip-debug-report.cpp": "c462e8a8bab21910c6e499d7450c3e8903196836",
        "cores/esp32/main.cpp": "fee28f101a5ce8ba686bba518f1f964ff5a485f9",
    },
}
_DATE_DECLARATION = re.compile(
    r'^\s*const\s+char\s+phx_compile_date\[\]\s*=\s*"([^"]*)"\s*;\s*$',
    re.MULTILINE,
)
_TIME_DECLARATION = re.compile(
    r'^\s*const\s+char\s+phx_compile_time\[\]\s*=\s*"([^"]*)"\s*;\s*$',
    re.MULTILINE,
)


def parse_source_date_epoch(value: str) -> int:
    """Parse a decimal, nonnegative SOURCE_DATE_EPOCH value."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value):
        raise ValueError("SOURCE_DATE_EPOCH must be nonnegative decimal seconds")
    return int(value, 10)


def expected_compile_metadata(epoch: int) -> dict[str, str]:
    """Return GCC's locale-independent C-locale UTC __DATE__ and __TIME__ spellings."""
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 0:
        raise ValueError("epoch must be a nonnegative integer")
    try:
        moment = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("epoch is outside the supported UTC datetime range") from exc
    month_abbreviations = (
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    )
    return {
        "date": (
            f"{month_abbreviations[moment.month - 1]} "
            f"{moment.day:2d} {moment.year:04d}"
        ),
        "time": f"{moment.hour:02d}:{moment.minute:02d}:{moment.second:02d}",
    }


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def inspect_core_time_source(
    core_root: Path | str,
    core_version: str | None = None,
) -> dict[str, Any]:
    """Confirm the exact core source embeds DATE/TIME and main.cpp calls its reporter."""
    root = Path(core_root).resolve()
    report_rel = "cores/esp32/chip-debug-report.cpp"
    main_rel = "cores/esp32/main.cpp"
    report_path = root / report_rel
    main_path = root / main_rel

    try:
        report_bytes = report_path.read_bytes()
        main_bytes = main_path.read_bytes()
        report_text = report_bytes.decode("utf-8")
        main_text = main_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read pinned core metadata sources: {exc}") from exc

    source_lines = [
        index
        for index, line in enumerate(report_text.splitlines(), start=1)
        if "__DATE__" in line and "__TIME__" in line
    ]
    if not source_lines:
        raise ValueError("chip-debug-report.cpp no longer embeds both __DATE__ and __TIME__")
    main_reference_lines = [
        index
        for index, line in enumerate(main_text.splitlines(), start=1)
        if "printBeforeSetupInfo" in line and "(" in line and ")" in line
    ]
    if not main_reference_lines:
        raise ValueError("main.cpp no longer calls printBeforeSetupInfo")

    report_blob = _git_blob_sha1(report_bytes)
    main_blob = _git_blob_sha1(main_bytes)
    if core_version is not None:
        expected = _EXPECTED_CORE_BLOBS.get(core_version)
        if expected is None:
            raise ValueError(f"unsupported ESP32 core version: {core_version}")
        if report_blob != expected[report_rel]:
            raise ValueError(
                "unexpected chip-debug-report.cpp Git blob: "
                f"{report_blob} != {expected[report_rel]}"
            )
        if main_blob != expected[main_rel]:
            raise ValueError(
                f"unexpected main.cpp Git blob: {main_blob} != {expected[main_rel]}"
            )

    return {
        "source_path": report_rel,
        "source_lines": source_lines,
        "source_blob": report_blob,
        "main_path": main_rel,
        "main_reference_lines": main_reference_lines,
        "main_blob": main_blob,
    }


def parse_macro_output(output: str) -> dict[str, str]:
    """Parse exactly one date and one time declaration from GCC preprocessor output."""
    if not isinstance(output, str):
        raise ValueError("compiler preprocessor output must be text")
    dates = _DATE_DECLARATION.findall(output)
    times = _TIME_DECLARATION.findall(output)
    if len(dates) != 1 or len(times) != 1:
        raise ValueError(
            "compiler output must contain exactly one phx_compile_date and "
            "one phx_compile_time declaration"
        )
    return {"date": dates[0], "time": times[0]}


def _probe_compiler(compiler: Path, epoch: int) -> dict[str, str]:
    expected = expected_compile_metadata(epoch)
    with tempfile.TemporaryDirectory(prefix="phx-source-date-epoch-") as temporary:
        source = Path(temporary) / "source_date_epoch_probe.c"
        source.write_text(
            "const char phx_compile_date[] = __DATE__;\n"
            "const char phx_compile_time[] = __TIME__;\n",
            encoding="ascii",
        )
        environment = os.environ.copy()
        environment["SOURCE_DATE_EPOCH"] = str(epoch)
        environment["LC_ALL"] = "C"
        environment["TZ"] = "UTC"
        result = subprocess.run(
            [str(compiler), "-E", "-P", "-x", "c", str(source)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "pinned Xtensa compiler preprocessor failed: "
                f"exit={result.returncode}; stderr={result.stderr[-1200:]}"
            )
        actual = parse_macro_output(result.stdout)
        if actual != expected:
            raise ValueError(
                "pinned compiler did not honor SOURCE_DATE_EPOCH: "
                f"expected={expected!r}, actual={actual!r}"
            )
        return actual


def verify_source_date_epoch(
    compiler: Path | str,
    core_root: Path | str,
    core_version: str,
    source_date_epoch: str,
) -> dict[str, Any]:
    compiler_path = Path(compiler).resolve()
    if not compiler_path.is_file() or not os.access(compiler_path, os.X_OK):
        raise ValueError(f"pinned Xtensa compiler is not executable: {compiler_path}")
    epoch = parse_source_date_epoch(source_date_epoch)
    core = inspect_core_time_source(core_root, core_version)

    # Distinct fixed epochs prove the compiler is using the environment variable,
    # rather than coincidentally returning the runner's current wall-clock time.
    probe_epochs = (946684800, 946684860, epoch)
    probe_results = [_probe_compiler(compiler_path, probe) for probe in probe_epochs]
    if probe_results[0] == probe_results[1]:
        raise ValueError("different SOURCE_DATE_EPOCH values produced identical metadata")
    return {
        "compiler": compiler_path.name,
        "core_version": core_version,
        "core_source": core,
        "source_date_epoch": epoch,
        "probe_count": len(probe_results),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", required=True, type=Path)
    parser.add_argument("--core-root", required=True, type=Path)
    parser.add_argument("--core-version", required=True)
    parser.add_argument("--source-date-epoch", required=True)
    args = parser.parse_args(argv)

    try:
        result = verify_source_date_epoch(
            args.compiler,
            args.core_root,
            args.core_version,
            args.source_date_epoch,
        )
    except (OSError, UnicodeError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"PHX-ESP32-SOURCE-DATE-EPOCH-RED: {exc}")
        return 1

    source = result["core_source"]
    print(
        "PHX-ESP32-SOURCE-DATE-EPOCH-PASS: "
        f"core={result['core_version']} compiler={result['compiler']} "
        f"source={source['source_path']}:{','.join(map(str, source['source_lines']))} "
        f"source_blob={source['source_blob']} "
        f"main_call_lines={','.join(map(str, source['main_reference_lines']))} "
        f"main_blob={source['main_blob']} "
        f"source_epoch={result['source_date_epoch']} "
        f"probes={result['probe_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
