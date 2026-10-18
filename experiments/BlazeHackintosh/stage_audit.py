"""Read-only local staged EFI readback check.

This compares a research directory against its self-declared SHA-256 manifest.
No publisher authenticity, physical boot or safe disk migration is established.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from efi_builder import RESEARCH_NOTICE

MAX_FILES = 2048
MAX_BYTES = 512 * 1024 * 1024

def _unsafe_link(path: Path) -> bool:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) &
                    getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except OSError:
        return True

def _regular(path: Path, max_bytes: int) -> int:
    if _unsafe_link(path):
        raise ValueError("Symlink/reparse point in staged output")
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or not 0 < st.st_size <= max_bytes:
        raise ValueError("Missing/special/oversized staged file")
    return st.st_size

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def audit_candidate(folder: str | Path) -> dict:
    result = {"integrity_passed": False, "boot_verified": False,
              "publisher_authenticity_verified": False,
              "ready_for_internal_esp": False, "files_checked": 0,
              "errors": [], "notice": "Unsigned local consistency only; NOT a boot or publisher trust test"}
    try:
        root = Path(folder)
        if _unsafe_link(root) or not root.is_dir() or not root.name.startswith("BlazeEFI-"):
            raise ValueError("Expected a non-linked BlazeEFI-* research directory")
        ledger, marker = root / "RESEARCH-ONLY.json", root / "DO-NOT-INSTALL.txt"
        _regular(ledger, 1024 * 1024)
        _regular(marker, 4096)
        if marker.read_text(encoding="utf-8") != RESEARCH_NOTICE + "\n":
            raise ValueError("Research-only safety marker changed")
        doc = json.loads(ledger.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or doc.get("classification") != "Structurally Validated Only" or (
                doc.get("ocvalidate_passed") is not True or
                doc.get("hardware_boot_verified") is not False or
                doc.get("usable_installer") is not False or
                doc.get("notice") != RESEARCH_NOTICE):
            raise ValueError("Research-only safety assertions changed")
        rows = doc.get("files")
        if not isinstance(rows, list) or not 0 < len(rows) <= MAX_FILES:
            raise ValueError("Missing/excessive file ledger")
        expected, directories = {}, set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Invalid ledger row")
            name, digest = row.get("path"), row.get("sha256")
            if not isinstance(name, str) or len(name) > 500 or not name.startswith("EFI/") or (
                    "\\" in name or ":" in name or any(ord(c) < 32 for c in name) or
                    any(x in ("", ".", "..") for x in name.split("/"))):
                raise ValueError("Unsafe ledger path")
            if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
                raise ValueError("Invalid ledger digest")
            key = name.casefold()
            if key in expected:
                raise ValueError("Duplicate ledger path")
            expected[key] = (name, digest)
            directories.update(str(p).casefold() for p in PurePosixPath(name).parents if str(p) != ".")
        actual, actual_dirs, total = {}, set(), 0
        for here, dirs, files in os.walk(root, followlinks=False):
            for name in dirs:
                path = Path(here) / name
                if _unsafe_link(path) or not path.is_dir():
                    raise ValueError("Linked/special staged directory")
                key = path.relative_to(root).as_posix().casefold()
                if key in actual_dirs:
                    raise ValueError("Duplicate staged directory")
                actual_dirs.add(key)
            for name in files:
                path = Path(here) / name
                total += _regular(path, 32 * 1024 * 1024)
                if total > MAX_BYTES or len(actual) >= MAX_FILES + 2:
                    raise ValueError("Excessive staged file size/count")
                key = path.relative_to(root).as_posix().casefold()
                if key in actual:
                    raise ValueError("Duplicate staged file")
                actual[key] = path
        if actual_dirs != directories:
            raise ValueError("Unexpected/missing staged directories")
        if set(actual) != set(expected) | {"research-only.json", "do-not-install.txt"}:
            raise ValueError("Unexpected/missing staged files")
        for key, (name, digest) in expected.items():
            if actual[key].relative_to(root).as_posix() != name or _sha256(actual[key]) != digest:
                raise ValueError("Staged file hash/path mismatch: " + name)
            result["files_checked"] += 1
        result["integrity_passed"] = True
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        result["errors"].append(str(exc))
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Read-only research EFI staging consistency audit")
    parser.add_argument("--folder", required=True)
    args = parser.parse_args()
    report = audit_candidate(args.folder)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["integrity_passed"] else 2)
