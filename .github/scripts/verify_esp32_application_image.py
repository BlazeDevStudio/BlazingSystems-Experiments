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


def _same_file_state(left: os.stat_result, right: os.stat_result) -> bool:
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
    return all(getattr(left, field) == getattr(right, field) for field in fields)


def _same_directory_state(left: os.stat_result, right: os.stat_result) -> bool:
    fields = ("st_dev", "st_ino", "st_mtime_ns", "st_ctime_ns")
    return all(getattr(left, field) == getattr(right, field) for field in fields)


def _attach_cleanup_failure(primary: BaseException, cleanup_error: BaseException) -> None:
    """Record a secondary close failure without replacing the active exception."""
    try:
        primary.add_note(f"additional descriptor cleanup failure: {cleanup_error!r}")
    except AttributeError:
        pass


def _close_descriptors_once(descriptors: list[int]) -> BaseException | None:
    """Attempt every owned descriptor once; never retry an ambiguous close."""
    first_error: BaseException | None = None
    while descriptors:
        descriptor = descriptors.pop()
        try:
            os.close(descriptor)
        except BaseException as exc:
            if first_error is None:
                first_error = exc
            else:
                _attach_cleanup_failure(first_error, exc)
    return first_error


def _open_output_directory(path: str | Path) -> tuple[Path, int, int]:
    """Pin the output directory and parent without following path symlinks."""
    candidate = Path(path)
    if ".." in candidate.parts:
        raise ValueError("output directory path must not contain parent-directory traversal")

    absolute = Path(os.path.abspath(candidate))
    parts = absolute.parts
    if not absolute.anchor or len(parts) < 2:
        raise ValueError("output directory must be below a filesystem root")

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    dir_fd_support = getattr(os, "supports_dir_fd", set())
    fd_support = getattr(os, "supports_fd", set())
    if (
        nofollow is None
        or directory is None
        or os.open not in dir_fd_support
        or os.stat not in dir_fd_support
        or os.stat not in getattr(os, "supports_follow_symlinks", set())
        or os.listdir not in fd_support
    ):
        raise ValueError(
            "descriptor-relative no-follow directory access is unavailable; refusing image admission"
        )

    flags = os.O_RDONLY | directory | nofollow | getattr(os, "O_CLOEXEC", 0)
    opened: list[int] = []
    try:
        current_fd = os.open(absolute.anchor, flags)
        opened.append(current_fd)
        for component in parts[1:]:
            next_fd = os.open(component, flags, dir_fd=current_fd)
            opened.append(next_fd)
            metadata = os.fstat(next_fd)
            if not stat.S_ISDIR(metadata.st_mode):
                raise ValueError(f"output path component is not a real directory: {component}")
            current_fd = next_fd

        if len(opened) < 2:
            raise ValueError("output directory must have a pinned parent directory")

        root_fd = opened[-1]
        parent_fd = opened[-2]
        ancestor_descriptors = opened[:-2]
        # Keep parent/root ownership until every ancestor close has been attempted.
        opened[:] = [parent_fd, root_fd]
        ancestor_error = _close_descriptors_once(ancestor_descriptors)
        if ancestor_error is not None:
            cleanup_error = _close_descriptors_once(opened)
            if cleanup_error is not None:
                _attach_cleanup_failure(ancestor_error, cleanup_error)
            if isinstance(ancestor_error, OSError):
                raise ValueError(
                    f"cannot safely close output directory ancestors: {ancestor_error}"
                ) from ancestor_error
            raise ancestor_error

        # Transfer the two pinned descriptors to the caller only after cleanup succeeds.
        opened.clear()
        return absolute, parent_fd, root_fd
    except OSError as exc:
        cleanup_error = _close_descriptors_once(opened)
        if cleanup_error is not None:
            _attach_cleanup_failure(exc, cleanup_error)
        raise ValueError(
            f"cannot safely open output directory without following symlinks: {exc}"
        ) from exc
    except BaseException as exc:
        cleanup_error = _close_descriptors_once(opened)
        if cleanup_error is not None:
            _attach_cleanup_failure(exc, cleanup_error)
        raise

def _verify_output_directory_identity(
    directory: Path,
    parent_fd: int,
    root_fd: int,
    before: os.stat_result,
) -> None:
    """Reject a directory replaced or modified while its image is inspected."""
    opened = os.fstat(root_fd)
    current_path = os.stat(directory.name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISDIR(current_path.st_mode):
        raise ValueError("output directory path is no longer a real directory")
    if not _same_directory_state(before, opened) or not _same_directory_state(before, current_path):
        raise ValueError("output directory path or contents changed while inspecting the application image")


def inspect_application_image(output_dir: str | Path, sketch_name: str) -> tuple[str, int, str]:
    """Return (filename, byte_length, sha256) for one verified sketch .ino.bin."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", sketch_name):
        raise ValueError("sketch name must be a simple filename stem")

    directory, parent_fd, root_fd = _open_output_directory(output_dir)
    # This function owns all three descriptors after _open_output_directory returns.
    # Pop/close them together so one failed close cannot skip later descriptors.
    owned_descriptors = [parent_fd, root_fd]
    primary_error: BaseException | None = None
    try:
        root_before = os.fstat(root_fd)
        path_before = os.stat(directory.name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISDIR(path_before.st_mode) or not _same_directory_state(root_before, path_before):
            raise ValueError("output directory path changed before image inspection")

        candidates = sorted(
            name for name in os.listdir(root_fd) if name.endswith(".ino.bin")
        )
        if len(candidates) != 1:
            raise ValueError(
                f"expected exactly one sketch application candidate (*.ino.bin); found {len(candidates)}"
            )

        candidate_name = candidates[0]
        expected_name = f"{sketch_name}.ino.bin"
        if candidate_name != expected_name:
            raise ValueError(
                f"expected application image {expected_name}; found {candidate_name}"
            )

        before_path = os.stat(candidate_name, dir_fd=root_fd, follow_symlinks=False)
        if not stat.S_ISREG(before_path.st_mode):
            raise ValueError("application image must be a regular non-symlink file")
        if before_path.st_nlink != 1:
            raise ValueError("application image must not be hard-linked")
        if before_path.st_size <= 0:
            raise ValueError("application image must not be empty")

        file_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW") | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(candidate_name, file_flags, dir_fd=root_fd)
        owned_descriptors.append(descriptor)

        before_read = os.fstat(descriptor)
        if not stat.S_ISREG(before_read.st_mode) or before_read.st_nlink != 1:
            raise ValueError("opened application image is not a unique regular file")
        if not _same_file_state(before_path, before_read):
            raise ValueError("application image changed between validation and open")

        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)

        after_read = os.fstat(descriptor)
        after_path = os.stat(candidate_name, dir_fd=root_fd, follow_symlinks=False)
        if not _same_file_state(before_read, after_read) or not _same_file_state(after_read, after_path):
            raise ValueError("application image changed while hashing")
        if total != after_read.st_size:
            raise ValueError("application image byte count changed while hashing")
        _verify_output_directory_identity(directory, parent_fd, root_fd, root_before)
        return candidate_name, total, digest.hexdigest()
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        cleanup_error = _close_descriptors_once(owned_descriptors)
        if cleanup_error is not None:
            if primary_error is not None:
                _attach_cleanup_failure(primary_error, cleanup_error)
            else:
                raise cleanup_error



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
