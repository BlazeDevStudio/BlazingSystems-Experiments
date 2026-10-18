"""Explicit, digest-pinned official OpenCore 1.0.8 ocvalidate runner.

No downloads, installs, EFI writes or arbitrary executables. The operator must
supply an entire upstream RELEASE archive and explicitly consent to execution.
SHA-256 is pinned to the upstream GitHub release asset metadata (2026-09-27).
"""
from __future__ import annotations

import hashlib
import os
import platform
import re
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

OPENCORE_VERSION = "1.0.8"
OFFICIAL_RELEASE_SHA256 = "2011e8b7216ecb2645d97ea710df965947edd406846e92050b9bc4190be6d27b"
OFFICIAL_RELEASE_URL = (
    "https://github.com/acidanthera/OpenCorePkg/releases/download/"
    "1.0.8/OpenCore-1.0.8-RELEASE.zip"
)
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_TOOL_BYTES = 24 * 1024 * 1024


def verify_archive(path: str | Path, expected_sha256: str = OFFICIAL_RELEASE_SHA256) -> dict:
    """Verify a locally supplied, exact upstream artifact; never execute anything."""
    result = {"version": OPENCORE_VERSION, "sha256": None,
              "verified": False, "error": None, "source": OFFICIAL_RELEASE_URL}
    try:
        file = Path(path)
        if file.is_symlink() or not file.is_file():
            result["error"] = "Archive must be an existing regular file, not a symbolic link"
            return result
        size = file.stat().st_size
        if size < 1024 or size > MAX_ARCHIVE_BYTES:
            result["error"] = "Archive size outside allowed bounds"
            return result
        digest = hashlib.sha256()
        with file.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        result["sha256"] = digest.hexdigest()
        if not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
            result["error"] = "Invalid trusted checksum configuration"
        elif result["sha256"] != expected_sha256:
            result["error"] = "SHA-256 mismatch: archive is not the approved official OpenCore 1.0.8 RELEASE asset"
        elif not zipfile.is_zipfile(file):
            result["error"] = "Verified content is not a ZIP archive"
        else:
            result["verified"] = True
    except (OSError, ValueError, zipfile.BadZipFile):
        result["error"] = "Unable to verify the local archive"
    return result


def _tool_member(archive: zipfile.ZipFile, system: str) -> zipfile.ZipInfo | None:
    """Accept only the upstream Utilities/ocvalidate executable for this OS."""
    executable = {
        "Windows": "ocvalidate.exe",
        "Linux": "ocvalidate",
        "Darwin": "ocvalidate",
    }.get(system)
    if executable is None:
        return None
    matches = []
    for info in archive.infolist():
        parts = info.filename.replace("\\", "/").split("/")
        if info.is_dir() or len(parts) < 3:
            continue
        if tuple(parts[-3:]) == ("Utilities", "ocvalidate", executable):
            if (0 < info.file_size <= MAX_TOOL_BYTES and
                    not stat.S_ISLNK(info.external_attr >> 16)):
                matches.append(info)
    return matches[0] if len(matches) == 1 else None


def _invoke(args: list[str]) -> tuple[int | None, str]:
    try:
        proc = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, errors="replace", timeout=20, check=False)
        return proc.returncode, (proc.stdout + "\n" + proc.stderr)[:6000]
    except (OSError, subprocess.TimeoutExpired):
        return None, "ocvalidate could not execute or timed out"


def run_official_ocvalidate(
    efi_root: str | Path, archive_path: str | Path, *,
    consent: bool = False, system: str | None = None,
    expected_sha256: str = OFFICIAL_RELEASE_SHA256,
) -> dict:
    """Run pinned upstream verifier, only after caller explicitly opts in.

    Does not prove a system will boot or that firmware, GPU or kexts are usable.
    No download or write to EFI: only a temporary verified executable is created.
    """
    report = {"attempted": False, "passed": False, "version_matched": False,
              "archive_verified": False, "supported_version": OPENCORE_VERSION,
              "error": None, "checker_output": "",
              "boot_verified": False, "hardware_verified": False}
    if not consent:
        report["error"] = "Explicit --run-official-ocvalidate approval is required"
        return report
    check = verify_archive(archive_path, expected_sha256)
    report["archive_verified"] = check["verified"]
    if not check["verified"]:
        report["error"] = check["error"]
        return report

    # Local import prevents hidden executable invocation during normal scans.
    from efi_validator import _oc_directory, validate_efi
    structure = validate_efi(efi_root)
    if not structure["structural_checks_passed"]:
        report["error"] = "Local EFI structure failed; official checker was not executed"
        return report
    target = _oc_directory(Path(efi_root).expanduser()) / "config.plist"
    if target.is_symlink():
        report["error"] = "Refusing a symlinked config.plist"
        return report

    try:
        with zipfile.ZipFile(archive_path) as zf:
            chosen = _tool_member(zf, system or platform.system())
            if chosen is None:
                report["error"] = "No uniquely identifiable ocvalidate binary for this host in verified archive"
                return report
            binary = zf.read(chosen)
        with tempfile.TemporaryDirectory(prefix="blaze-ocvalidate-") as tmp:
            tool = Path(tmp) / chosen.filename.rsplit("/", 1)[-1]
            tool.write_bytes(binary)
            if platform.system() != "Windows":
                tool.chmod(0o700)
            version_code, version_output = _invoke([str(tool), "--version"])
            expected_banner = ("NOTE: This version of ocvalidate is only compatible "
                               "with OpenCore version 1.0.8!")
            # Upstream RELEASE 1.0.8 Windows binary presently prints its exact
            # version banner but interprets "--version" as an input filename.
            # Accept that *specific* observed legacy behavior only for the
            # cryptographically pinned archive. Any other mismatch fails closed.
            normal_version = (version_code == 0 and
                              bool(re.search(r"(?<!\d)1\.0\.8(?!\d)", version_output)))
            upstream_banner = (version_code is not None and
                               expected_banner in version_output and
                               "Failed to read --version" in version_output)
            if not (normal_version or upstream_banner):
                report["error"] = (f"ocvalidate --version could not confirm 1.0.8 "
                                   f"(exit={version_code}, output={version_output[:450]!r})")
                return report
            report["version_matched"] = True
            code, output = _invoke([str(tool), str(target)])
            report["attempted"] = True
            report["checker_output"] = output
            report["passed"] = code == 0
            if code != 0:
                report["error"] = "Official ocvalidate reported errors or could not complete"
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError):
        report["error"] = "Failed to prepare the verified ocvalidate executable"
    return report
