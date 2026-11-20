#!/usr/bin/env python3
"""Compare two clean ESP32 sketch builds byte-for-byte and report useful drift evidence."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import sys
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def _open_regular_image(path: str | Path, expected_name: str) -> tuple[Path, int, os.stat_result]:
    candidate = Path(path)
    if candidate.name != expected_name:
        raise ValueError(f"application image must be named {expected_name}; found {candidate.name}")

    before_path = candidate.lstat()
    if not stat.S_ISREG(before_path.st_mode):
        raise ValueError("application image must be a regular non-symlink file")
    if before_path.st_nlink != 1:
        raise ValueError("application image must not be hard-linked")
    if before_path.st_size <= 0:
        raise ValueError("application image must not be empty")

    descriptor = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before_open = os.fstat(descriptor)
        if not stat.S_ISREG(before_open.st_mode):
            raise ValueError("opened application image is not a regular file")
        if before_open.st_nlink != 1:
            raise ValueError("opened application image is hard-linked")
        if (before_open.st_dev, before_open.st_ino) != (before_path.st_dev, before_path.st_ino):
            raise ValueError("application image changed between path validation and open")
        if before_open.st_size != before_path.st_size:
            raise ValueError("application image size changed before comparison")
        return candidate, descriptor, before_open
    except Exception:
        os.close(descriptor)
        raise


def _verify_stable(path: Path, descriptor: int, before: os.stat_result) -> None:
    after_open = os.fstat(descriptor)
    after_path = path.lstat()
    stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
    if any(getattr(before, field) != getattr(after_open, field) for field in stable_fields):
        raise ValueError("application image changed while being compared")
    if (after_path.st_dev, after_path.st_ino) != (after_open.st_dev, after_open.st_ino):
        raise ValueError("application image path changed while being compared")
    if not stat.S_ISREG(after_path.st_mode) or after_path.st_nlink != 1:
        raise ValueError("application image path is no longer a unique regular file")


def compare_application_images(
    first_image: str | Path,
    second_image: str | Path,
    sketch_name: str,
) -> tuple[str, int, str]:
    """Return (filename, byte_length, sha256) only when two independent images match."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", sketch_name):
        raise ValueError("sketch name must be a simple filename stem")
    expected_name = f"{sketch_name}.ino.bin"

    first_path, first_fd, first_before = _open_regular_image(first_image, expected_name)
    try:
        second_path, second_fd, second_before = _open_regular_image(second_image, expected_name)
        try:
            if (first_before.st_dev, first_before.st_ino) == (second_before.st_dev, second_before.st_ino):
                raise ValueError("two builds must produce distinct application-image files")

            first_digest = hashlib.sha256()
            second_digest = hashlib.sha256()
            first_size = 0
            second_size = 0
            offset = 0
            first_differences: list[str] = []

            while True:
                first_chunk = os.read(first_fd, CHUNK_SIZE)
                second_chunk = os.read(second_fd, CHUNK_SIZE)
                first_digest.update(first_chunk)
                second_digest.update(second_chunk)
                first_size += len(first_chunk)
                second_size += len(second_chunk)

                if first_chunk != second_chunk:
                    common = min(len(first_chunk), len(second_chunk))
                    for index in range(common):
                        if first_chunk[index] != second_chunk[index] and len(first_differences) < 16:
                            first_differences.append(
                                f"{offset + index}:0x{first_chunk[index]:02x}/0x{second_chunk[index]:02x}"
                            )
                    if len(first_chunk) != len(second_chunk) and len(first_differences) < 16:
                        first_differences.append(
                            f"{offset + common}:chunk-length {len(first_chunk)}/{len(second_chunk)}"
                        )

                if not first_chunk and not second_chunk:
                    break
                offset += max(len(first_chunk), len(second_chunk))

            _verify_stable(first_path, first_fd, first_before)
            _verify_stable(second_path, second_fd, second_before)

            first_sha256 = first_digest.hexdigest()
            second_sha256 = second_digest.hexdigest()
            if first_size != second_size or first_sha256 != second_sha256:
                raise ValueError(
                    "non-reproducible ESP32 application image: "
                    f"first_size={first_size} second_size={second_size} "
                    f"first_sha256={first_sha256} second_sha256={second_sha256} "
                    f"first_differences={first_differences[:16]}"
                )

            return expected_name, first_size, first_sha256
        finally:
            os.close(second_fd)
    finally:
        os.close(first_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", required=True, type=Path)
    parser.add_argument("--second", required=True, type=Path)
    parser.add_argument("--sketch-name", required=True)
    args = parser.parse_args()

    try:
        filename, size, sha256 = compare_application_images(
            args.first, args.second, args.sketch_name
        )
    except (OSError, ValueError) as exc:
        print(f"PHX-ESP32-REPRODUCIBILITY-RED: {exc}", file=sys.stderr)
        return 1

    print(
        "PHX-ESP32-REPRODUCIBILITY-PASS: "
        f"filename={filename} size_bytes={size} sha256={sha256} builds=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
