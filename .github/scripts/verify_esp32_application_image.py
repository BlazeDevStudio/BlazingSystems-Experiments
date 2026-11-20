#!/usr/bin/env python3
"""Select and hash exactly one ESP32 sketch application image from an Arduino CLI output directory."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import sys
from pathlib import Path


def inspect_application_image(output_dir: str | Path, sketch_name: str) -> tuple[str, int, str]:
    """Return (filename, byte_length, sha256) for one verified sketch .ino.bin."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", sketch_name):
        raise ValueError("sketch name must be a simple filename stem")

    root = Path(output_dir)
    root_stat = root.lstat()
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("output directory must be a real directory, not a symlink")

    candidates = sorted(path for path in root.iterdir() if path.name.endswith(".ino.bin"))
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one sketch application candidate (*.ino.bin); found {len(candidates)}"
        )

    candidate = candidates[0]
    expected_name = f"{sketch_name}.ino.bin"
    if candidate.name != expected_name:
        raise ValueError(
            f"expected application image {expected_name}; found {candidate.name}"
        )

    before_path = candidate.lstat()
    if not stat.S_ISREG(before_path.st_mode):
        raise ValueError("application image must be a regular non-symlink file")
    if before_path.st_nlink != 1:
        raise ValueError("application image must not be hard-linked")
    if before_path.st_size <= 0:
        raise ValueError("application image must not be empty")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(candidate, flags)
    try:
        before_read = os.fstat(descriptor)
        if not stat.S_ISREG(before_read.st_mode):
            raise ValueError("opened application image is not a regular file")
        if before_read.st_nlink != 1:
            raise ValueError("opened application image is hard-linked")
        if (before_read.st_dev, before_read.st_ino) != (before_path.st_dev, before_path.st_ino):
            raise ValueError("application image changed between validation and open")
        if before_read.st_size != before_path.st_size:
            raise ValueError("application image size changed before hashing")

        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)

        after_read = os.fstat(descriptor)
        after_path = candidate.lstat()
        stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
        if any(getattr(before_read, field) != getattr(after_read, field) for field in stable_fields):
            raise ValueError("application image changed while hashing")
        if (after_path.st_dev, after_path.st_ino) != (after_read.st_dev, after_read.st_ino):
            raise ValueError("application image path changed while hashing")
        if total != after_read.st_size:
            raise ValueError("application image byte count changed while hashing")
    finally:
        os.close(descriptor)

    return candidate.name, total, digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--sketch-name", required=True)
    args = parser.parse_args()

    try:
        filename, size, sha256 = inspect_application_image(args.output_dir, args.sketch_name)
    except (OSError, ValueError) as exc:
        print(f"PHX-ESP32-APP-IMAGE-RED: {exc}", file=sys.stderr)
        return 1

    print(
        "PHX-ESP32-APP-IMAGE-PASS: "
        f"filename={filename} size_bytes={size} sha256={sha256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
