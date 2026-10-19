"""Read-only ZIP inspection for locally supplied third-party release archives.

A GitHub API digest is NOT a publisher signature. This module cannot authorize
component use, redistribution, extraction, EFI assembly, or production release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import zipfile

SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_ARCHIVE = 1024**3
MAX_ENTRIES = 10000
MAX_MEMBER = 512 * 1024**2
MAX_TOTAL = 2 * 1024**3
MAX_RATIO = 500
WIN_RESERVED = {"CON", "PRN", "AUX", "NUL"}


def _portable_name(name: str) -> bool:
    if not isinstance(name, str) or not 0 < len(name) <= 512:
        return False
    if name.startswith("/") or "\\" in name or ":" in name:
        return False
    if any(ord(c) < 32 or ord(c) > 126 for c in name):
        return False
    parts = name.rstrip("/").split("/")
    for item in parts:
        if item in ("", ".", "..") or item.startswith(" ") or item.endswith((" ", ".")):
            return False
        if any(c in item for c in '<>"|?*'):
            return False
        stem = item.split(".", 1)[0].upper()
        if stem in WIN_RESERVED or re.fullmatch(r"(?:COM|LPT)[1-9]", stem):
            return False
    return True


def _hash_stream(f):
    f.seek(0)
    h = hashlib.sha256()
    count = 0
    while data := f.read(1024 * 1024):
        count += len(data)
        if count > MAX_ARCHIVE:
            raise ValueError("Archive exceeds 1 GiB limit")
        h.update(data)
    return h.hexdigest(), count


def _fingerprint(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns,
            getattr(s, "st_ctime_ns", 0))


def _same_opened_file(before, opened):
    """Compare stable pre-open properties; Windows path stat inode is not portable.

    The opened handle is separately rechecked after reading, and a matching
    cryptographic digest and size are always required. No Windows symlink-race
    immunity is claimed; this checker never writes or executes input bytes.
    """
    if (not stat.S_ISREG(opened.st_mode) or opened.st_size != before.st_size or
            getattr(opened, "st_file_attributes", 0) &
            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
        return False
    if os.name != "nt" and (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
        return False
    return True


def _scan_zip(f):
    f.seek(0)
    with zipfile.ZipFile(f, "r") as archive:
        infos = archive.infolist()
        if not 0 < len(infos) <= MAX_ENTRIES:
            raise ValueError("ZIP entry count invalid")
        files = {i.filename.rstrip("/").casefold() for i in infos if not i.is_dir()}
        encountered = set()
        total = 0
        checked = 0
        for info in infos:
            name = info.filename
            if not _portable_name(name):
                raise ValueError("Unsafe ZIP path")
            normalized = name.rstrip("/").casefold()
            if normalized in encountered:
                raise ValueError("Duplicate or case-colliding ZIP entry")
            encountered.add(normalized)
            segments = normalized.split("/")
            if any("/".join(segments[:d]) in files for d in range(1, len(segments))):
                raise ValueError("ZIP entry nested inside regular file")
            mode = (info.external_attr >> 16) & 0o170000
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("ZIP link or special file rejected")
            if info.flag_bits & 1:
                raise ValueError("Encrypted ZIP entry rejected")
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError("Unsupported ZIP compression")
            if info.file_size < 0 or info.file_size > MAX_MEMBER:
                raise ValueError("ZIP member size outside limit")
            total += info.file_size
            if total > MAX_TOTAL:
                raise ValueError("ZIP expanded total outside limit")
            if info.file_size and (info.compress_size <= 0 or
                    info.file_size > MAX_RATIO * info.compress_size):
                raise ValueError("ZIP expansion ratio exceeds limit")
            if info.is_dir():
                if info.file_size or mode == stat.S_IFREG:
                    raise ValueError("Invalid ZIP directory record")
                continue
            if mode == stat.S_IFDIR:
                raise ValueError("Directory record missing slash")
            size = 0
            with archive.open(info, "r") as member:
                while chunk := member.read(1024 * 1024):
                    size += len(chunk)
                    if size > info.file_size or size > MAX_MEMBER:
                        raise ValueError("ZIP member exceeds declared size")
            if size != info.file_size:
                raise ValueError("ZIP member size mismatch")
            checked += 1
        return len(infos), checked


def audit_zip(path, expected_sha256, expected_size):
    """Fail-closed results; never extract, download or execute archive contents."""
    result = {"archive_hash_match": False, "zip_structure_valid": False,
              "zip_members_checked": 0, "publisher_identity_verified": False,
              "license_clearance_verified": False, "component_auth_gate_satisfied": False,
              "errors": []}
    try:
        if not isinstance(expected_sha256, str) or not SHA.fullmatch(expected_sha256):
            raise ValueError("Invalid SHA-256 pin")
        if type(expected_size) is not int or not 0 < expected_size <= MAX_ARCHIVE:
            raise ValueError("Invalid archive size pin")
        p = Path(path)
        if p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()):
            raise ValueError("Linked archive rejected")
        original = p.lstat()
        if (not stat.S_ISREG(original.st_mode) or original.st_size != expected_size or
                getattr(original, "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
            raise ValueError("Archive is not expected bounded regular file")
        fd = os.open(p, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) |
                     getattr(os, "O_BINARY", 0))
        with os.fdopen(fd, "rb") as f:
            opened = os.fstat(f.fileno())
            if not _same_opened_file(original, opened):
                raise ValueError("Archive changed while opening")
            before_hash, n = _hash_stream(f)
            if before_hash != expected_sha256 or n != expected_size:
                raise ValueError("Local ZIP differs from pinned digest/size")
            result["archive_hash_match"] = True
            count, checked = _scan_zip(f)
            after_hash, n = _hash_stream(f)
            if ((after_hash, n) != (before_hash, expected_size) or
                    _fingerprint(os.fstat(f.fileno())) != _fingerprint(opened)):
                raise ValueError("Archive changed during validation")
        result.update(zip_structure_valid=True, zip_members_checked=checked,
                      zip_entries_seen=count)
    except (OSError, ValueError, EOFError, RuntimeError, zipfile.BadZipFile,
            NotImplementedError, OverflowError) as exc:
        result["errors"] = [str(exc)]
    return result


def main():
    p = argparse.ArgumentParser(description="Read-only local ZIP integrity audit")
    p.add_argument("--archive", required=True)
    p.add_argument("--sha256", required=True, help="Operator-supplied SHA-256 pin")
    p.add_argument("--size", required=True, type=int)
    args = p.parse_args()
    result = audit_zip(args.archive, args.sha256, args.size)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["zip_structure_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
