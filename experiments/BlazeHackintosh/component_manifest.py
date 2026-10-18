"""Offline SHA-256 ledger for user-supplied EFI components.

Hashes detect substitution, not publisher authenticity. Source and license fields
are OPERATOR-DECLARED; never claim cryptographic upstream authentication.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path

MAX_FILES = 512
MAX_FILE_BYTES = 32 * 1024 * 1024
REQUIRED_KEXTS = ("Lilu.kext", "VirtualSMC.kext", "WhateverGreen.kext")
REQUIRED_ACPI = ("SSDT-PLUG.aml", "SSDT-EC.aml")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def input_files(kext_dir, acpi_dir, hfs_driver) -> dict[str, Path]:
    sources = {}
    kroot, aroot, hfs = Path(kext_dir), Path(acpi_dir), Path(hfs_driver)
    for base in (kroot, aroot):
        if base.is_symlink() or not base.is_dir():
            raise ValueError("A component source directory is absent or symlinked")
    for bundle in REQUIRED_KEXTS:
        root = kroot / bundle
        if root.is_symlink() or not root.is_dir():
            raise ValueError("Missing or symlinked component bundle: " + bundle)
        for directory, dirs, files in os.walk(root, topdown=True, followlinks=False):
            for name in dirs:
                if (Path(directory) / name).is_symlink():
                    raise ValueError("Symlink inside kext bundle")
            for name in files:
                p = Path(directory) / name
                key = "Kexts/" + p.relative_to(kroot).as_posix()
                if key.casefold() in (s.casefold() for s in sources):
                    raise ValueError("Duplicate component file path")
                sources[key] = p
    for aml in REQUIRED_ACPI:
        sources["ACPI/" + aml] = aroot / aml
    actual_acpi = {p.name for p in aroot.iterdir()}
    if actual_acpi != set(REQUIRED_ACPI):
        raise ValueError("Unexpected/missing ACPI inputs; permit only required SSDTs")
    sources["Drivers/HfsPlus.efi"] = hfs
    total = 0
    if len(sources) > MAX_FILES:
        raise ValueError("Too many component files")
    for label, path in sources.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing/symlinked component file: " + label)
        size = path.stat().st_size
        total += size
        if not 0 < size <= MAX_FILE_BYTES or total > 256 * 1024 * 1024:
            raise ValueError("Component file size/cumulative bytes outside allowed bounds")
    return sources


def verify_manifest(manifest_file, *, kext_dir, acpi_dir, hfs_driver) -> dict:
    file = Path(manifest_file)
    if file.is_symlink() or not file.is_file() or not 0 < file.stat().st_size <= 1024 * 1024:
        raise ValueError("Manifest must be a regular JSON file at most 1 MiB")
    try:
        doc = json.loads(file.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed component manifest") from exc
    if not isinstance(doc, dict) or doc.get("schema_version") != 1 or not isinstance(doc.get("files"), list):
        raise ValueError("Unsupported component manifest schema")
    rows = doc["files"]
    if not 0 < len(rows) <= MAX_FILES:
        raise ValueError("Manifest file entries empty or excessive")
    declared = {}
    for entry in rows:
        if not isinstance(entry, dict):
            raise ValueError("Invalid component manifest entry")
        name, digest = entry.get("path"), entry.get("sha256")
        if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_+./-]{1,300}", name)
            or any(x in (".", "..", "") for x in name.split("/"))
            or name.split("/")[0] not in ("Kexts", "ACPI", "Drivers")):
            raise ValueError("Unsafe manifest component path")
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid SHA-256 manifest value")
        url, license_id, release = (entry.get(x) for x in ("source_url", "license_id", "release"))
        if not isinstance(url, str) or not re.fullmatch(r"https://[A-Za-z0-9][A-Za-z0-9._~:/?%#@&=+-]{3,450}", url):
            raise ValueError("Explicit upstream HTTPS source_url required")
        if not isinstance(license_id, str) or not re.fullmatch(r"[A-Za-z0-9.+-]{2,60}", license_id):
            raise ValueError("Explicit license_id required (operator must independently verify)")
        if not isinstance(release, str) or not 1 <= len(release) <= 100:
            raise ValueError("Explicit release identifier required")
        key = name.casefold()
        if key in declared:
            raise ValueError("Duplicate component manifest name")
        declared[key] = entry
    actual = input_files(kext_dir, acpi_dir, hfs_driver)
    if {k.casefold() for k in actual} != set(declared):
        raise ValueError("Component manifest coverage mismatch: every source file requires one entry")
    for path, source in actual.items():
        if sha256(source) != declared[path.casefold()]["sha256"]:
            raise ValueError("Component SHA-256 mismatch: " + path)
    return {
        "manifest_sha256": sha256(file),
        "file_count": len(actual),
        "sources_declared": sorted({row["source_url"] for row in declared.values()}),
        "trust": "Only operator-declared SHA-256 matched local files; upstream authenticity and licensing NOT verified",
    }
