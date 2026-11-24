#!/usr/bin/env python3
"""Emit fail-closed per-artifact provenance and refresh SHA256SUMS."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import secrets
import shlex
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "blaze.phx-release.build-provenance/v1"
HEX_SHA = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
PROVENANCE_COMMAND_TIMEOUT_SECONDS = 120


class ProvenanceError(RuntimeError):
    """An artifact cannot be admitted to a traceable CI preview package."""


def build_args(
    *,
    kind: str,
    target: str,
    artifact_dir: Path,
    imagebuilder_workdir: Path | None = None,
    core_package: str | None = None,
    core_version: str | None = None,
    fqbn: str | None = None,
    sketch: str | None = None,
    libraries: Path | None = None,
) -> argparse.Namespace:
    """Small argument factory used by the isolated regression suite."""
    return argparse.Namespace(
        kind=kind,
        target=target,
        artifact_dir=Path(artifact_dir),
        imagebuilder_workdir=Path(imagebuilder_workdir) if imagebuilder_workdir else None,
        core_package=core_package,
        core_version=core_version,
        fqbn=fqbn,
        sketch=sketch,
        libraries=Path(libraries) if libraries else None,
    )


def _run(command: list[str], *, cwd: Path = ROOT) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=PROVENANCE_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProvenanceError(
            "command timed out after "
            f"{PROVENANCE_COMMAND_TIMEOUT_SECONDS}s: {' '.join(command)}"
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ProvenanceError(
            f"command failed ({completed.returncode}): {' '.join(command)}: {detail}"
        )
    return completed.stdout.strip()


def _require_single_link(metadata: os.stat_result, display_path: str) -> None:
    """Reject artifact files that alias an inode outside their own tree entry."""
    if getattr(metadata, "st_nlink", None) != 1:
        raise ProvenanceError(
            f"hard-linked artifact file is not admitted: {display_path}"
        )


def _same_file_state(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
        and left.st_ctime_ns == right.st_ctime_ns
        and left.st_nlink == right.st_nlink
    )


def _record_cleanup_failure(primary_error: BaseException, detail: str) -> None:
    """Attach cleanup diagnostics without replacing the error being handled."""
    try:
        add_note = getattr(primary_error, "add_note", None)
        if callable(add_note):
            add_note(detail)
        else:
            sys.stderr.write(detail + "\n")
    except BaseException:
        # Cleanup diagnostics must never replace the operation or cleanup error.
        pass


def _close_file_and_parent_descriptors(
    fd: int,
    parent_fd: int,
    display_path: Path,
) -> None:
    """Attempt both descriptor closes and preserve the primary read/hash failure."""
    primary_error = sys.exc_info()[1]
    close_errors: list[tuple[str, OSError]] = []
    cleanup_interruptions: list[tuple[str, BaseException]] = []

    for descriptor, label in (
        (fd, "file descriptor"),
        (parent_fd, "parent-directory descriptor"),
    ):
        try:
            os.close(descriptor)
        except OSError as exc:
            close_errors.append((label, exc))
        except BaseException as exc:
            # A new interruption must not prevent the remaining descriptor
            # from receiving its one close attempt.
            cleanup_interruptions.append((label, exc))

    if cleanup_interruptions and primary_error is not None:
        # A cleanup interruption must not replace an already-active read/hash
        # failure. Record every cleanup diagnostic on the primary exception,
        # then return so the original exception continues propagating.
        for failed_label, interruption in cleanup_interruptions:
            _record_cleanup_failure(
                primary_error,
                f"provenance descriptor cleanup interruption for {failed_label} "
                f"on {display_path}: {type(interruption).__name__}: {interruption}",
            )
        for failed_label, error in close_errors:
            _record_cleanup_failure(
                primary_error,
                f"could not close {failed_label} for {display_path}: "
                f"{type(error).__name__}: {error}",
            )
        return

    if cleanup_interruptions:
        label, interruption = cleanup_interruptions[0]
        for failed_label, error in close_errors:
            _record_cleanup_failure(
                interruption,
                f"could not close {failed_label} for {display_path}: "
                f"{type(error).__name__}: {error}",
            )
        for failed_label, error in cleanup_interruptions[1:]:
            _record_cleanup_failure(
                interruption,
                f"additional {failed_label} cleanup interruption for {display_path}: "
                f"{type(error).__name__}: {error}",
            )
        raise interruption

    if close_errors:
        detail = "; ".join(
            f"{label}: {type(error).__name__}: {error}"
            for label, error in close_errors
        )
        if primary_error is not None:
            _record_cleanup_failure(
                primary_error,
                f"provenance descriptor cleanup also failed for {display_path}: {detail}",
            )
            return
        raise ProvenanceError(
            f"could not close provenance descriptors for {display_path}: {detail}"
        ) from close_errors[0][1]


def _open_regular(path: Path) -> tuple[int, os.stat_result, int, str]:
    """Open a regular file without following symlinks in any path component.

    Parent directory descriptors pin the traversal. O_NOFOLLOW on the final
    file alone is insufficient because it still follows symlinked parents.
    """
    candidate = Path(path)
    if ".." in candidate.parts:
        raise ProvenanceError(f"parent-directory traversal is not allowed: {path}")

    absolute = Path(os.path.abspath(candidate))
    parts = absolute.parts
    if not absolute.anchor or len(parts) < 2:
        raise ProvenanceError(f"expected a file path below a directory: {path}")

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    dir_fd_support = getattr(os, "supports_dir_fd", set())
    if (
        nofollow is None
        or directory is None
        or os.open not in dir_fd_support
        or os.stat not in dir_fd_support
    ):
        raise ProvenanceError(
            "descriptor-relative O_NOFOLLOW file access is unavailable; refusing artifact admission"
        )

    cloexec = getattr(os, "O_CLOEXEC", 0)
    directory_flags = os.O_RDONLY | directory | nofollow | cloexec
    file_flags = os.O_RDONLY | nofollow | cloexec
    parent_fd = -1
    fd = -1
    next_fd = -1
    try:
        parent_fd = os.open(absolute.anchor, directory_flags)
        for component in parts[1:-1]:
            next_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            metadata = os.fstat(next_fd)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(next_fd)
                next_fd = -1
                raise ProvenanceError(
                    f"expected a real directory path component: {component}"
                )
            os.close(parent_fd)
            parent_fd = next_fd
            next_fd = -1

        leaf = parts[-1]
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise ProvenanceError(f"expected a regular non-symlink file: {path}")

        fd = os.open(leaf, file_flags, dir_fd=parent_fd)
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or not _same_file_state(before, opened):
            os.close(fd)
            fd = -1
            raise ProvenanceError(f"file identity changed while opening: {path}")
        return fd, opened, parent_fd, leaf
    except OSError as exc:
        for descriptor in (fd, next_fd, parent_fd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        raise ProvenanceError(f"cannot safely open {path}: {exc}") from exc
    except BaseException:
        for descriptor in (fd, next_fd, parent_fd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        raise


def _read_regular(path: Path) -> bytes:
    fd, before, parent_fd, leaf = _open_regular(path)
    chunks: list[bytes] = []
    total = 0
    try:
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
            total += len(block)
        after = os.fstat(fd)
        path_after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as exc:
        raise ProvenanceError(f"cannot read {path}: {exc}") from exc
    finally:
        _close_file_and_parent_descriptors(fd, parent_fd, path)
    if not _same_file_state(before, after) or not _same_file_state(after, path_after):
        raise ProvenanceError(f"file changed while reading: {path}")
    if total != after.st_size:
        raise ProvenanceError(f"short or changing read: {path}")
    return b"".join(chunks)


def _hash_regular(path: Path) -> tuple[str, int]:
    fd, before, parent_fd, leaf = _open_regular(path)
    digest = hashlib.sha256()
    total = 0
    try:
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            digest.update(block)
            total += len(block)
        after = os.fstat(fd)
        path_after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as exc:
        raise ProvenanceError(f"cannot hash {path}: {exc}") from exc
    finally:
        _close_file_and_parent_descriptors(fd, parent_fd, path)
    if not _same_file_state(before, after) or not _same_file_state(after, path_after):
        raise ProvenanceError(f"file changed while hashing: {path}")
    if total != after.st_size:
        raise ProvenanceError(f"short or changing hash read: {path}")
    return digest.hexdigest(), total


def _open_directory(path: Path, label: str) -> tuple[Path, int]:
    """Open a directory through pinned no-follow descriptors for every component."""
    candidate = Path(path)
    if ".." in candidate.parts:
        raise ProvenanceError(f"{label} contains parent-directory traversal: {path}")

    absolute = Path(os.path.abspath(candidate))
    if not absolute.anchor:
        raise ProvenanceError(f"{label} must be an absolute directory path: {path}")

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if (
        nofollow is None
        or directory is None
        or os.open not in getattr(os, "supports_dir_fd", set())
    ):
        raise ProvenanceError(
            "descriptor-relative O_NOFOLLOW directory access is unavailable; refusing artifact admission"
        )

    flags = os.O_RDONLY | directory | nofollow | getattr(os, "O_CLOEXEC", 0)
    current_fd = -1
    next_fd = -1
    try:
        current_fd = os.open(absolute.anchor, flags)
        for component in absolute.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=current_fd)
            metadata = os.fstat(next_fd)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(next_fd)
                next_fd = -1
                raise ProvenanceError(
                    f"{label} path component must be a real directory: {component}"
                )
            os.close(current_fd)
            current_fd = next_fd
            next_fd = -1
        return absolute, current_fd
    except OSError as exc:
        for descriptor in (next_fd, current_fd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        raise ProvenanceError(
            f"{label} is unavailable or contains a symlink: {path}: {exc}"
        ) from exc
    except BaseException:
        for descriptor in (next_fd, current_fd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        raise


def _verify_directory_identity(path: Path, pinned_fd: int, label: str) -> None:
    """Fail if the admitted path no longer names the pinned directory inode."""
    current_path, current_fd = _open_directory(path, label)
    try:
        pinned = os.fstat(pinned_fd)
        current = os.fstat(current_fd)
        if (pinned.st_dev, pinned.st_ino) != (current.st_dev, current.st_ino):
            raise ProvenanceError(
                f"{label} changed during provenance admission: {current_path}"
            )
    finally:
        os.close(current_fd)


def _require_directory(path: Path, label: str) -> Path:
    absolute, directory_fd = _open_directory(path, label)
    os.close(directory_fd)
    return path


def _normalize_checksum_path(name: str) -> str:
    if name.startswith("./"):
        name = name[2:]
    # str.splitlines() treats these characters as record boundaries even though
    # POSIX permits them in filenames. Reject them before emitting SHA256SUMS so
    # one artifact path cannot be reinterpreted as multiple manifest records.
    forbidden = (
        "\\",
        "\n",
        "\r",
        "\x00",
        "\v",
        "\f",
        "\x1c",
        "\x1d",
        "\x1e",
        "\x85",
        "\u2028",
        "\u2029",
    )
    if not name or any(character in name for character in forbidden):
        raise ProvenanceError(f"unsafe checksum path: {name!r}")
    # A POSIX-relative path can still be drive-qualified when consumed on
    # Windows. Reject both drive-absolute (C:/x) and drive-relative (C:x)
    # spellings so SHA256SUMS remains portable and cannot escape its root.
    if re.match(r"^[A-Za-z]:", name):
        raise ProvenanceError(f"unsafe checksum path: {name!r}")
    # Validate raw separators before PurePosixPath can normalize aliases.
    # A single leading "./" is retained for sha256sum compatibility above;
    # interior dot segments, repeated separators and trailing separators are
    # not canonical artifact paths and must not collapse to another name.
    components = name.split("/")
    if name.startswith("/") or any(part in ("", ".", "..") for part in components):
        raise ProvenanceError(f"unsafe checksum path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute():
        raise ProvenanceError(f"unsafe checksum path: {name!r}")
    return path.as_posix()


def _parse_checksum_text(raw: bytes, label: str) -> dict[str, str]:
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProvenanceError(f"{label} is not UTF-8") from exc
    entries: dict[str, str] = {}
    for line_number, line in enumerate(content.splitlines(), start=1):
        if not line:
            continue
        if len(line) < 67 or line[64:66] not in ("  ", " *"):
            raise ProvenanceError(f"{label}:{line_number}: invalid sha256sum record")
        digest = line[:64]
        if not HEX_SHA.fullmatch(digest):
            raise ProvenanceError(f"{label}:{line_number}: invalid SHA-256 digest")
        name = _normalize_checksum_path(line[66:])
        if name in entries:
            raise ProvenanceError(f"{label}:{line_number}: duplicate path {name}")
        entries[name] = digest
    if not entries:
        raise ProvenanceError(f"{label} is empty")
    return entries


def _hash_regular_at(parent_fd: int, name: str, display_path: str) -> tuple[str, int]:
    """Hash one regular file relative to a pinned parent directory descriptor."""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None or os.open not in getattr(os, "supports_dir_fd", set()):
        raise ProvenanceError(
            "descriptor-relative O_NOFOLLOW file access is unavailable; refusing artifact admission"
        )
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise ProvenanceError(f"expected a regular non-symlink file: {display_path}")
        _require_single_link(before, display_path)
        fd = os.open(
            name,
            os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
    except OSError as exc:
        raise ProvenanceError(f"cannot safely open {display_path}: {exc}") from exc

    digest = hashlib.sha256()
    total = 0
    try:
        opened = os.fstat(fd)
        _require_single_link(opened, display_path)
        if not stat.S_ISREG(opened.st_mode) or not _same_file_state(before, opened):
            raise ProvenanceError(f"file identity changed while opening: {display_path}")
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            digest.update(block)
            total += len(block)
        after = os.fstat(fd)
        path_after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        _require_single_link(after, display_path)
        _require_single_link(path_after, display_path)
    except OSError as exc:
        raise ProvenanceError(f"cannot hash {display_path}: {exc}") from exc
    finally:
        os.close(fd)

    if not _same_file_state(before, after) or not _same_file_state(after, path_after):
        raise ProvenanceError(f"file changed while hashing: {display_path}")
    if total != after.st_size:
        raise ProvenanceError(f"short or changing hash read: {display_path}")
    return digest.hexdigest(), total


def _read_regular_at(parent_fd: int, name: str, display_path: str) -> bytes:
    """Read one regular file relative to a pinned parent directory descriptor."""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None or os.open not in getattr(os, "supports_dir_fd", set()):
        raise ProvenanceError(
            "descriptor-relative O_NOFOLLOW file access is unavailable; refusing artifact admission"
        )
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise ProvenanceError(f"expected a regular non-symlink file: {display_path}")
        _require_single_link(before, display_path)
        fd = os.open(
            name,
            os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
    except OSError as exc:
        raise ProvenanceError(f"cannot safely open {display_path}: {exc}") from exc

    chunks: list[bytes] = []
    total = 0
    try:
        opened = os.fstat(fd)
        _require_single_link(opened, display_path)
        if not stat.S_ISREG(opened.st_mode) or not _same_file_state(before, opened):
            raise ProvenanceError(f"file identity changed while opening: {display_path}")
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
            total += len(block)
        after = os.fstat(fd)
        path_after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        _require_single_link(after, display_path)
        _require_single_link(path_after, display_path)
    except OSError as exc:
        raise ProvenanceError(f"cannot read {display_path}: {exc}") from exc
    finally:
        os.close(fd)

    if not _same_file_state(before, after) or not _same_file_state(after, path_after):
        raise ProvenanceError(f"file changed while reading: {display_path}")
    if total != after.st_size:
        raise ProvenanceError(f"short or changing read: {display_path}")
    return b"".join(chunks)


def _inventory_at(root_fd: int) -> dict[str, dict[str, Any]]:
    """Inventory an artifact tree without resolving paths outside the pinned root."""
    files: dict[str, dict[str, Any]] = {}
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if (
        directory_flag is None
        or nofollow is None
        or os.open not in getattr(os, "supports_dir_fd", set())
        or os.stat not in getattr(os, "supports_dir_fd", set())
    ):
        raise ProvenanceError(
            "descriptor-relative directory inventory is unavailable; refusing artifact admission"
        )
    directory_flags = (
        os.O_RDONLY | directory_flag | nofollow | getattr(os, "O_CLOEXEC", 0)
    )

    def walk(directory_fd: int, prefix: str) -> None:
        before_directory = os.fstat(directory_fd)
        try:
            names = sorted(os.listdir(directory_fd))
        except OSError as exc:
            raise ProvenanceError(f"cannot list pinned artifact directory: {exc}") from exc

        for name in names:
            if name in ("", ".", "..") or "/" in name or "\x00" in name:
                raise ProvenanceError(f"unsafe artifact entry name: {name!r}")
            relative = f"{prefix}/{name}" if prefix else name
            try:
                metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                raise ProvenanceError(f"cannot inspect artifact entry {relative}: {exc}") from exc

            if stat.S_ISDIR(metadata.st_mode):
                try:
                    child_fd = os.open(name, directory_flags, dir_fd=directory_fd)
                except OSError as exc:
                    raise ProvenanceError(
                        f"cannot safely open artifact directory {relative}: {exc}"
                    ) from exc
                try:
                    opened = os.fstat(child_fd)
                    if (
                        not stat.S_ISDIR(opened.st_mode)
                        or (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino)
                    ):
                        raise ProvenanceError(
                            f"artifact directory changed while opening: {relative}"
                        )
                    walk(child_fd, relative)
                    after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    if not _same_file_state(metadata, after):
                        raise ProvenanceError(
                            f"artifact directory changed while inventorying: {relative}"
                        )
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(metadata.st_mode):
                if relative == "SHA256SUMS":
                    continue
                _normalize_checksum_path(relative)
                digest, size = _hash_regular_at(directory_fd, name, relative)
                files[relative] = {
                    "path": relative,
                    "size_bytes": size,
                    "sha256": digest,
                }
            else:
                raise ProvenanceError(
                    f"symlink or non-regular entry inside artifact tree: {relative}"
                )

        after_directory = os.fstat(directory_fd)
        if not _same_file_state(before_directory, after_directory):
            raise ProvenanceError("artifact directory changed during inventory")

    walk(root_fd, "")
    if not files:
        raise ProvenanceError("artifact directory contains no payload files")
    return dict(sorted(files.items()))


def _verify_checksum_manifest_at(
    root_fd: int, files: dict[str, dict[str, Any]]
) -> None:
    entries = _parse_checksum_text(
        _read_regular_at(root_fd, "SHA256SUMS", "SHA256SUMS"),
        "SHA256SUMS",
    )
    if set(entries) != set(files):
        missing = sorted(set(files) - set(entries))
        extra = sorted(set(entries) - set(files))
        raise ProvenanceError(
            f"SHA256SUMS file set mismatch; missing={missing}, extra={extra}"
        )
    for name, record in files.items():
        if entries[name] != record["sha256"]:
            raise ProvenanceError(f"SHA256SUMS digest mismatch: {name}")


def _source_context(env: dict[str, str], source_paths: list[str]) -> dict[str, Any]:
    commit = env.get("GITHUB_SHA", "")
    if not GIT_SHA.fullmatch(commit):
        raise ProvenanceError("GITHUB_SHA must be an exact 40-character commit SHA")
    workspace_commit = _run(["git", "rev-parse", "HEAD"])
    if workspace_commit != commit:
        raise ProvenanceError(
            f"checked-out HEAD {workspace_commit} does not match GITHUB_SHA {commit}"
        )
    required = (
        "GITHUB_REPOSITORY",
        "GITHUB_REF",
        "GITHUB_WORKFLOW",
        "GITHUB_RUN_ID",
        "GITHUB_RUN_ATTEMPT",
        "RUNNER_OS",
        "RUNNER_ARCH",
    )
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise ProvenanceError(f"missing GitHub build context: {', '.join(missing)}")
    source_head_sha = env.get("PHX_SOURCE_HEAD_SHA", "")
    source_base_sha = env.get("PHX_SOURCE_BASE_SHA", "")
    base_ref = env.get("GITHUB_BASE_REF", "")
    if not GIT_SHA.fullmatch(source_head_sha):
        raise ProvenanceError("PHX_SOURCE_HEAD_SHA must be an exact 40-character commit SHA")
    if base_ref:
        if not GIT_SHA.fullmatch(source_base_sha):
            raise ProvenanceError(
                "PHX_SOURCE_BASE_SHA must be an exact 40-character commit SHA for pull requests"
            )
    elif source_base_sha:
        raise ProvenanceError("PHX_SOURCE_BASE_SHA must be empty outside pull-request events")
    elif source_head_sha != commit:
        raise ProvenanceError("non-PR PHX_SOURCE_HEAD_SHA must equal GITHUB_SHA")

    paths = []
    for source_path in source_paths:
        relative = _normalize_checksum_path(source_path)
        source_file = ROOT / relative
        _hash_regular(source_file)
        try:
            _run(["git", "diff", "--quiet", "HEAD", "--", relative])
        except ProvenanceError as exc:
            raise ProvenanceError(
                f"source path differs from exact HEAD worktree content: {relative}"
            ) from exc
        blob = _run(["git", "rev-parse", f"HEAD:{relative}"])
        if not GIT_SHA.fullmatch(blob):
            raise ProvenanceError(f"invalid Git blob identity for {relative}")
        paths.append({"path": relative, "git_blob": blob})
    return {
        "repository": env["GITHUB_REPOSITORY"],
        "commit": commit,
        "source_head_sha": source_head_sha,
        "source_base_sha": source_base_sha or None,
        "ref": env["GITHUB_REF"],
        "pull_request_head": env.get("GITHUB_HEAD_REF") or None,
        "pull_request_base": env.get("GITHUB_BASE_REF") or None,
        "workflow": env["GITHUB_WORKFLOW"],
        "workflow_ref": env.get("GITHUB_WORKFLOW_REF") or None,
        "workflow_sha": env.get("GITHUB_WORKFLOW_SHA") or None,
        "run_id": env["GITHUB_RUN_ID"],
        "run_attempt": env["GITHUB_RUN_ATTEMPT"],
        "paths": paths,
    }


def _parse_build_manifest(path: Path) -> dict[str, str]:
    raw = _read_regular(path)
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProvenanceError("BUILD-MANIFEST.txt is not UTF-8") from exc
    fields: dict[str, str] = {}
    for line in content.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key in fields:
            raise ProvenanceError(f"duplicate BUILD-MANIFEST field: {key}")
        fields[key] = value
    required = (
        "BlazePwifi version",
        "OpenWrt version",
        "Target",
        "OpenWrt target",
        "Profile",
        "Capability",
        "Paid authority installed preview",
        "Paid v2 commit/replay authorized",
        "Customer install authorized",
    )
    missing = [key for key in required if not fields.get(key)]
    if missing:
        raise ProvenanceError(f"BUILD-MANIFEST.txt missing fields: {', '.join(missing)}")
    return fields


def _openwrt_toolchain_reference(
    official_sums: dict[str, str],
    *,
    version: str,
    openwrt_target: str,
    checksum_catalog_sha256: str,
) -> dict[str, Any]:
    """Record the upstream target toolchain reference without claiming it ran here."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*(?:/[A-Za-z0-9][A-Za-z0-9_-]*)*", openwrt_target):
        raise ProvenanceError(f"invalid OpenWrt target for toolchain reference: {openwrt_target!r}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+~-]*", version):
        raise ProvenanceError(f"invalid OpenWrt version for toolchain reference: {version!r}")
    if not HEX_SHA.fullmatch(checksum_catalog_sha256):
        raise ProvenanceError("OpenWrt checksum catalog SHA-256 is invalid")

    target_slug = openwrt_target.replace("/", "-")
    prefix = f"openwrt-toolchain-{version}-{target_slug}_gcc-"
    suffix = ".Linux-x86_64.tar.zst"
    matches = [
        (name, digest)
        for name, digest in official_sums.items()
        if name.startswith(prefix) and name.endswith(suffix)
    ]
    if len(matches) != 1:
        raise ProvenanceError(
            "expected exactly one OpenWrt target toolchain archive in official sha256sums; "
            f"found {len(matches)} for {openwrt_target}"
        )

    archive, digest = matches[0]
    pattern = re.compile(
        rf"^openwrt-toolchain-{re.escape(version)}-{re.escape(target_slug)}"
        r"_gcc-(?P<gcc_version>[0-9][0-9A-Za-z.+-]*)"
        r"_(?P<libc_abi>musl(?:_[A-Za-z0-9]+)?)"
        r"\.Linux-x86_64\.tar\.zst$"
    )
    match = pattern.fullmatch(archive)
    if not match:
        raise ProvenanceError(
            f"OpenWrt toolchain archive name is not a supported GCC/musl reference: {archive}"
        )
    if not HEX_SHA.fullmatch(digest):
        raise ProvenanceError(
            f"OpenWrt toolchain archive has an invalid SHA-256 catalog entry: {archive}"
        )

    return {
        "archive": archive,
        "sha256": digest,
        "gcc_version": match.group("gcc_version"),
        "libc_abi": match.group("libc_abi"),
        "checksum_catalog_sha256": checksum_catalog_sha256,
        "checksum_catalog_source": (
            "OpenWrt target release sha256sums; detached signature not verified by this workflow"
        ),
        "archive_downloaded": False,
        "archive_sha256_verified": False,
        "compiler_invoked": False,
    }


def _openwrt_toolchain(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    fields = _parse_build_manifest(Path(args.artifact_dir) / "BUILD-MANIFEST.txt")
    if fields["Target"] != args.target:
        raise ProvenanceError(
            f"BUILD-MANIFEST target {fields['Target']} does not match requested {args.target}"
        )
    for field in (
        "Paid authority installed preview",
        "Paid v2 commit/replay authorized",
        "Customer install authorized",
    ):
        if fields[field] != "0":
            raise ProvenanceError(
                f"refusing nonstandard or paid preview artifact: {field}={fields[field]}"
            )

    workdir = _require_directory(Path(args.imagebuilder_workdir or "/tmp/blazepwifi-imagebuilder"), "ImageBuilder workdir")
    archives = []
    for path in sorted(workdir.iterdir()):
        if path.name.startswith("openwrt-imagebuilder-") and path.name.endswith(".tar.zst"):
            _hash_regular(path)
            archives.append(path)
    if len(archives) != 1:
        raise ProvenanceError(
            f"expected exactly one verified OpenWrt ImageBuilder archive, found {len(archives)}"
        )
    archive = archives[0]
    version = fields["OpenWrt version"]
    if not archive.name.startswith(f"openwrt-imagebuilder-{version}-"):
        raise ProvenanceError("ImageBuilder archive version does not match BUILD-MANIFEST.txt")
    checksum_catalog_bytes = _read_regular(workdir / "sha256sums")
    official_sums = _parse_checksum_text(checksum_catalog_bytes, "ImageBuilder sha256sums")
    checksum_catalog_sha256 = hashlib.sha256(checksum_catalog_bytes).hexdigest()
    archive_name = archive.name
    if archive_name not in official_sums:
        raise ProvenanceError("official OpenWrt sha256sums does not contain the selected archive")
    archive_sha, _ = _hash_regular(archive)
    if official_sums[archive_name] != archive_sha:
        raise ProvenanceError("ImageBuilder archive does not match the official OpenWrt sha256sums entry")

    upstream_toolchain = _openwrt_toolchain_reference(
        official_sums,
        version=version,
        openwrt_target=fields["OpenWrt target"],
        checksum_catalog_sha256=checksum_catalog_sha256,
    )

    host_tools = {}
    for name, command in (
        ("zstd", ["zstd", "--version"]),
        ("curl", ["curl", "--version"]),
        ("make", ["make", "--version"]),
    ):
        output = _run(command)
        host_tools[name] = output.splitlines()[0] if output else "version output unavailable"
    toolchain = {
        "name": "OpenWrt ImageBuilder",
        "imagebuilder_version": version,
        "imagebuilder_archive": archive_name,
        "imagebuilder_archive_sha256": archive_sha,
        "archive_checksum_source": "official OpenWrt sha256sums; rechecked by PHX-RELEASE",
        "openwrt_target": fields["OpenWrt target"],
        "profile": fields["Profile"],
        "capability": fields["Capability"],
        "host_tools": host_tools,
        "compiler_version": None,
        "compiler_version_note": (
            "ImageBuilder does not invoke the target compiler; the upstream GCC toolchain "
            "is referenced separately and was not downloaded or executed by this workflow"
        ),
        "upstream_toolchain": upstream_toolchain,
    }
    source_paths = [
        "experiment/openwrt/BlazePwifi/build/build-openwrt-image.sh",
        "experiment/openwrt/BlazePwifi/VERSION",
    ]
    return toolchain, source_paths


def _git_tree_blobs(relative_root: str) -> dict[str, str]:
    """Return every regular blob beneath a source directory in exact HEAD."""
    root = _normalize_checksum_path(relative_root)
    output = _run(
        ["git", "ls-tree", "-r", "-z", "--full-tree", "HEAD", "--", root]
    )
    entries: dict[str, str] = {}
    for record in output.split("\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition("\t")
        fields = metadata.split()
        if not separator or len(fields) != 3:
            raise ProvenanceError(f"malformed Git tree entry beneath {root}")
        mode, object_type, blob = fields
        path = _normalize_checksum_path(raw_path)
        if object_type != "blob" or mode not in ("100644", "100755"):
            raise ProvenanceError(
                f"non-regular or symlinked Arduino source entry is not admitted: {path}"
            )
        if not GIT_SHA.fullmatch(blob):
            raise ProvenanceError(f"invalid Git blob identity for {path}")
        if not path.startswith(root + "/"):
            raise ProvenanceError(f"Git tree path escaped expected source root: {path}")
        if path in entries:
            raise ProvenanceError(f"duplicate Git tree path: {path}")
        entries[path] = blob
    if not entries:
        raise ProvenanceError(f"exact Git source tree is empty: {root}")
    return dict(sorted(entries.items()))


def _inventory_directory(path: Path, label: str) -> dict[str, dict[str, Any]]:
    """Inventory one directory using a pinned no-follow descriptor."""
    absolute, directory_fd = _open_directory(path, label)
    try:
        inventory = _inventory_at(directory_fd)
        _verify_directory_identity(absolute, directory_fd, label)
        return inventory
    finally:
        os.close(directory_fd)


def _tree_file_set(root: str, inventory: dict[str, dict[str, Any]]) -> set[str]:
    return {f"{root}/{relative}" for relative in inventory}


def _require_matching_tree(
    label: str,
    source: dict[str, dict[str, Any]],
    staged: dict[str, dict[str, Any]],
) -> None:
    if source == staged:
        return
    source_names = set(source)
    staged_names = set(staged)
    missing = sorted(source_names - staged_names)
    extra = sorted(staged_names - source_names)
    changed = sorted(
        name
        for name in source_names & staged_names
        if source[name] != staged[name]
    )
    raise ProvenanceError(
        f"staged Arduino {label} tree differs from exact source; "
        f"missing={missing}, extra={extra}, changed={changed}"
    )


def _arduino_source_bundle(
    args: argparse.Namespace, sketch: str
) -> tuple[list[str], dict[str, Any]]:
    """Verify the complete staged compile bundle and enumerate its Git inputs."""
    kind = args.kind
    if args.target != kind:
        raise ProvenanceError(
            f"Arduino target {args.target!r} does not match artifact kind {kind!r}"
        )

    sketch_path = PurePosixPath(sketch)
    board_root = PurePosixPath("experiment/openwrt/BlazePwifi") / kind
    if sketch_path.parent.parent != board_root:
        raise ProvenanceError(
            f"Arduino sketch is outside the expected {kind} source tree: {sketch}"
        )
    sketch_name = sketch_path.parent.name
    if sketch_path.name != f"{sketch_name}.ino":
        raise ProvenanceError(
            f"Arduino sketch filename must match its project directory: {sketch}"
        )

    sketch_root = sketch_path.parent.as_posix()
    library_root = "experiment/openwrt/BlazePwifi/esp/libraries"
    rebuild_path = "experiment/openwrt/BlazePwifi/esp/REBUILD.md"
    package_script = "experiment/openwrt/BlazePwifi/tools/package-vendo-source.py"

    artifact_root = Path(args.artifact_dir)
    staged_source_root = artifact_root / "source"
    expected_libraries = staged_source_root / "libraries"
    supplied_libraries = getattr(args, "libraries", None)
    if not supplied_libraries:
        raise ProvenanceError("Arduino provenance requires the staged local library path")
    if Path(os.path.abspath(supplied_libraries)) != Path(
        os.path.abspath(expected_libraries)
    ):
        raise ProvenanceError(
            "Arduino --libraries path must be the exact staged source/libraries directory"
        )

    staged_root, staged_root_fd = _open_directory(
        staged_source_root, "staged Arduino source root"
    )
    try:
        expected_entries = sorted((sketch_name, "README.md", "libraries"))
        observed_entries = sorted(os.listdir(staged_root_fd))
        if observed_entries != expected_entries:
            raise ProvenanceError(
                "staged Arduino source root has unexpected entries; "
                f"expected={expected_entries}, observed={observed_entries}"
            )
        _verify_directory_identity(
            staged_root, staged_root_fd, "staged Arduino source root"
        )
    finally:
        os.close(staged_root_fd)

    source_sketch_tree = _inventory_directory(
        ROOT / sketch_root, "exact Arduino sketch source"
    )
    if any(
        relative == "build" or relative.startswith("build/")
        for relative in source_sketch_tree
    ):
        raise ProvenanceError(
            "Arduino source sketch uses the reserved compiler-output build/ directory"
        )
    staged_sketch_inventory = _inventory_directory(
        staged_root / sketch_name, "staged Arduino sketch"
    )
    if "build" in staged_sketch_inventory:
        # A regular file named build is not an output directory; leave it in
        # the comparison so it fails as an unexpected staged source entry.
        staged_sketch_tree = staged_sketch_inventory
        generated_build_output_count = 0
    else:
        generated_build_outputs = {
            relative: record
            for relative, record in staged_sketch_inventory.items()
            if relative.startswith("build/")
        }
        staged_sketch_tree = {
            relative: record
            for relative, record in staged_sketch_inventory.items()
            if not relative.startswith("build/")
        }
        # _inventory_directory has already traversed and validated every
        # generated output as a regular, single-link, non-symlink file. These
        # compiler intermediates remain in the artifact checksum manifest but
        # are not source inputs and must not be compared with Git HEAD.
        generated_build_output_count = len(generated_build_outputs)
    _require_matching_tree("sketch", source_sketch_tree, staged_sketch_tree)

    source_library_tree = _inventory_directory(
        ROOT / library_root, "exact Arduino local libraries"
    )
    staged_library_tree = _inventory_directory(
        expected_libraries, "staged Arduino local libraries"
    )
    _require_matching_tree("library", source_library_tree, staged_library_tree)

    sketch_git_tree = _git_tree_blobs(sketch_root)
    library_git_tree = _git_tree_blobs(library_root)
    if set(sketch_git_tree) != _tree_file_set(sketch_root, source_sketch_tree):
        missing = sorted(
            set(sketch_git_tree) - _tree_file_set(sketch_root, source_sketch_tree)
        )
        extra = sorted(
            _tree_file_set(sketch_root, source_sketch_tree) - set(sketch_git_tree)
        )
        raise ProvenanceError(
            f"Arduino sketch worktree does not match exact HEAD tree; "
            f"missing={missing}, extra={extra}"
        )
    if set(library_git_tree) != _tree_file_set(library_root, source_library_tree):
        missing = sorted(
            set(library_git_tree) - _tree_file_set(library_root, source_library_tree)
        )
        extra = sorted(
            _tree_file_set(library_root, source_library_tree) - set(library_git_tree)
        )
        raise ProvenanceError(
            f"Arduino library worktree does not match exact HEAD tree; "
            f"missing={missing}, extra={extra}"
        )

    source_readme = _read_regular(ROOT / rebuild_path)
    staged_readme = _read_regular(staged_root / "README.md")
    if staged_readme != source_readme:
        raise ProvenanceError(
            "staged Arduino rebuild README differs from exact source"
        )

    source_sketch = _read_regular(ROOT / sketch)
    compatibility_sketch = _read_regular(artifact_root / f"{sketch_name}.ino")
    if compatibility_sketch != source_sketch:
        raise ProvenanceError(
            "top-level Arduino sketch compatibility copy differs from exact source"
        )

    source_paths = {
        sketch,
        package_script,
        rebuild_path,
        *(
            f"{sketch_root}/{relative}"
            for relative in source_sketch_tree
        ),
        *(
            f"{library_root}/{relative}"
            for relative in source_library_tree
        ),
    }
    source_tree = {
        "staged_copy_verified": True,
        "sketch_root": sketch_root,
        "sketch_file_count": len(source_sketch_tree),
        "generated_build_output_file_count": generated_build_output_count,
        "generated_build_outputs_excluded_from_source_inputs": True,
        "library_root": library_root,
        "library_file_count": len(source_library_tree),
        "rebuild_instructions_path": rebuild_path,
        "rebuild_instructions_sha256": hashlib.sha256(source_readme).hexdigest(),
        "compatibility_sketch_sha256": hashlib.sha256(source_sketch).hexdigest(),
        "package_script_path": package_script,
        "git_tree_membership_verified": True,
    }
    return sorted(source_paths), source_tree


def _arduino_toolchain(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    required = ("core_package", "core_version", "fqbn", "sketch", "libraries")
    missing = [name for name in required if not getattr(args, name, None)]
    if missing:
        raise ProvenanceError(f"Arduino provenance arguments missing: {', '.join(missing)}")
    cli_output = _run(["arduino-cli", "version"])
    match = re.search(r"\bVersion:\s*([0-9][A-Za-z0-9.+-]*)", cli_output)
    if not match or match.group(1) != "1.6.0":
        raise ProvenanceError(f"expected observed Arduino CLI 1.6.0, got: {cli_output}")
    core_list = _run(["arduino-cli", "core", "list"])
    installed = []
    for line in core_list.splitlines():
        columns = line.split()
        if len(columns) >= 2 and columns[0] == args.core_package:
            installed.append(columns[1])
    if installed != [args.core_version]:
        raise ProvenanceError(
            f"expected exactly {args.core_package}@{args.core_version}; observed {installed}"
        )

    sketch = _normalize_checksum_path(args.sketch)
    sketch_path = ROOT / sketch
    _hash_regular(sketch_path)
    source_paths, source_tree = _arduino_source_bundle(args, sketch)

    # Capture the compiler selected by the exact FQBN, core and local library
    # search path used by the preceding build. --show-properties is read-only:
    # it resolves platform.txt properties without compiling or uploading.
    properties_command = [
        "arduino-cli",
        "compile",
        "--show-properties=expanded",
        "--fqbn",
        args.fqbn,
        "--libraries",
        str(args.libraries),
        sketch,
    ]
    properties_output = _run(properties_command)

    required_properties = ("compiler.path", "compiler.c.cmd", "compiler.cpp.cmd")
    properties: dict[str, str] = {}
    for line in properties_output.splitlines():
        key, separator, value = line.partition("=")
        if not separator or key not in required_properties:
            continue
        if key in properties:
            raise ProvenanceError(f"Arduino compiler property is duplicated: {key}")
        properties[key] = value.strip()
    missing_properties = [
        key for key in required_properties if not properties.get(key)
    ]
    if missing_properties:
        raise ProvenanceError(
            "Arduino compiler properties missing or empty: "
            + ", ".join(missing_properties)
        )

    compiler_dir = Path(properties["compiler.path"])
    if not compiler_dir.is_absolute():
        raise ProvenanceError("Arduino compiler.path must be an expanded absolute path")
    try:
        compiler_dir = compiler_dir.resolve(strict=True)
    except OSError as exc:
        raise ProvenanceError(
            f"Arduino compiler.path does not resolve: {properties['compiler.path']}"
        ) from exc
    if not compiler_dir.is_dir():
        raise ProvenanceError("Arduino compiler.path is not a directory")

    def observed_compiler(property_name: str) -> tuple[str, str]:
        raw_command = properties[property_name]
        try:
            command_parts = shlex.split(raw_command)
        except ValueError as exc:
            raise ProvenanceError(
                f"Arduino {property_name} is not a valid executable token"
            ) from exc
        if len(command_parts) != 1:
            raise ProvenanceError(
                f"Arduino {property_name} must resolve to exactly one executable"
            )
        executable = Path(command_parts[0])
        if not executable.is_absolute():
            executable = compiler_dir / executable
        try:
            executable = executable.resolve(strict=True)
        except OSError as exc:
            raise ProvenanceError(
                f"Arduino compiler executable is missing for {property_name}: {executable}"
            ) from exc
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise ProvenanceError(
                f"Arduino compiler executable is not a runnable regular file: {executable}"
            )
        version_output = _run([str(executable), "--version"])
        version = next(
            (line.strip() for line in version_output.splitlines() if line.strip()),
            "",
        )
        if not version:
            raise ProvenanceError(
                f"Arduino compiler returned no version for {property_name}: {executable.name}"
            )
        return executable.name, version

    compiler_c_binary, compiler_c_version = observed_compiler("compiler.c.cmd")
    compiler_cpp_binary, compiler_cpp_version = observed_compiler("compiler.cpp.cmd")

    toolchain = {
        "name": "Arduino CLI",
        "arduino_cli_version": match.group(1),
        "arduino_cli_version_output": cli_output,
        "board_core": f"{args.core_package}@{args.core_version}",
        "fqbn": args.fqbn,
        "sketch": sketch,
        "compiler_version": compiler_cpp_version,
        "compiler_c_version": compiler_c_version,
        "compiler_c_binary": compiler_c_binary,
        "compiler_cpp_binary": compiler_cpp_binary,
        "compiler_version_source": "arduino-cli compile --show-properties=expanded and compiler --version",
        "source_tree": source_tree,
    }
    return toolchain, source_paths

def _create_temp_file_at(directory_fd: int, prefix: str) -> tuple[int, str]:
    """Create a private temporary file relative to the pinned artifact directory."""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None or os.open not in getattr(os, "supports_dir_fd", set()):
        raise ProvenanceError(
            "descriptor-relative temporary-file creation is unavailable; refusing artifact admission"
        )
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | nofollow
        | getattr(os, "O_CLOEXEC", 0)
    )
    for _ in range(32):
        name = prefix + secrets.token_hex(12)
        try:
            return os.open(name, flags, 0o600, dir_fd=directory_fd), name
        except FileExistsError:
            continue
    raise ProvenanceError("could not allocate a unique artifact sidecar temporary file")


def _write_new_json(
    path: Path, payload: dict[str, Any], *, directory_fd: int
) -> None:
    try:
        os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise ProvenanceError(f"refusing to overwrite existing provenance file: {path}")

    data = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd, temporary_name = _create_temp_file_at(directory_fd, ".BUILD-PROVENANCE.")
    published_identity: tuple[int, int] | None = None
    published = False
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

        temporary_metadata = os.stat(
            temporary_name,
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
        if not stat.S_ISREG(temporary_metadata.st_mode):
            raise ProvenanceError("provenance temporary sidecar is not a regular file")
        published_identity = (temporary_metadata.st_dev, temporary_metadata.st_ino)

        # A descriptor-relative hard link is an atomic create-if-absent operation.
        os.link(
            temporary_name,
            path.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
            follow_symlinks=False,
        )
        published = True
        os.unlink(temporary_name, dir_fd=directory_fd)
        os.fsync(directory_fd)
    except BaseException as primary_error:
        cleanup_errors: list[BaseException] = []
        try:
            os.unlink(temporary_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        except BaseException as cleanup_error:
            cleanup_errors.append(cleanup_error)

        # If the directory fsync fails after the hard link was published, remove
        # only the same inode created from our temporary sidecar. Never unlink a
        # different file that may have appeared at the destination name.
        if published and published_identity is not None:
            try:
                current = os.stat(
                    path.name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                if (current.st_dev, current.st_ino) == published_identity:
                    os.unlink(path.name, dir_fd=directory_fd)
                    os.fsync(directory_fd)
                else:
                    cleanup_errors.append(
                        ProvenanceError(
                            "published provenance target changed before failed-publication cleanup"
                        )
                    )
            except FileNotFoundError:
                pass
            except BaseException as cleanup_error:
                cleanup_errors.append(cleanup_error)

        add_note = getattr(primary_error, "add_note", None)
        if callable(add_note):
            for cleanup_error in cleanup_errors:
                add_note(f"provenance publication cleanup failed: {cleanup_error}")
        raise


def _write_checksums(
    path: Path,
    root: Path,
    files: dict[str, dict[str, Any]],
    *,
    directory_fd: int,
) -> None:
    try:
        metadata = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        metadata = None
    if metadata is not None and not stat.S_ISREG(metadata.st_mode):
        raise ProvenanceError("SHA256SUMS must remain a regular non-symlink file")

    rows = [f"{record['sha256']}  {name}" for name, record in sorted(files.items())]
    data = ("\n".join(rows) + "\n").encode("utf-8")
    fd, temporary_name = _create_temp_file_at(directory_fd, ".SHA256SUMS.")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(
            temporary_name,
            path.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
    except BaseException as primary_error:
        try:
            os.unlink(temporary_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        except BaseException as cleanup_error:
            add_note = getattr(primary_error, "add_note", None)
            if callable(add_note):
                add_note(
                    f"temporary sidecar cleanup failed for {temporary_name}: {cleanup_error}"
                )
        raise


def write_provenance(args: argparse.Namespace, env: dict[str, str] | None = None) -> dict[str, Any]:
    environment = dict(os.environ if env is None else env)
    root, root_fd = _open_directory(Path(args.artifact_dir), "artifact directory")
    try:
        _verify_directory_identity(root, root_fd, "artifact directory")
        provenance_path = root / "BUILD-PROVENANCE.json"
        try:
            os.stat(provenance_path.name, dir_fd=root_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ProvenanceError(
                "BUILD-PROVENANCE.json already exists; refusing to overwrite it"
            )

        checksum_path = root / "SHA256SUMS"
        try:
            os.stat(checksum_path.name, dir_fd=root_fd, follow_symlinks=False)
        except FileNotFoundError as exc:
            raise ProvenanceError(
                "existing SHA256SUMS is required before provenance admission"
            ) from exc

        initial_files = _inventory_at(root_fd)
        _verify_checksum_manifest_at(root_fd, initial_files)
        _verify_directory_identity(root, root_fd, "artifact directory")

        if args.kind == "openwrt":
            toolchain, source_paths = _openwrt_toolchain(args)
            artifact_kind = "openwrt-imagebuilder-preview"
        elif args.kind in ("esp8266", "esp32"):
            toolchain, source_paths = _arduino_toolchain(args)
            artifact_kind = "arduino-firmware-preview"
        else:
            raise ProvenanceError(f"unsupported artifact kind: {args.kind}")

        source = _source_context(environment, source_paths)
        manifest: dict[str, Any] = {
            "schema": SCHEMA,
            "artifact": {
                "kind": artifact_kind,
                "target": args.target,
                "classification": "CI_PREVIEW_ONLY",
            },
            "source": source,
            "runner": {
                "os": environment["RUNNER_OS"],
                "arch": environment["RUNNER_ARCH"],
            },
            "toolchain": toolchain,
            "release_state": {
                "production_authorized": False,
                "signing": "NOT_PERFORMED",
                "hardware_acceptance": "NOT_TESTED",
                "financial_migration": "NOT_PERFORMED",
            },
            "files": list(initial_files.values()),
            "checksum_manifest": {
                "path": "SHA256SUMS",
                "covers_provenance": True,
                "entries": len(initial_files) + 1,
            },
        }

        # The directory path may have been replaced while source/toolchain
        # metadata was collected. Never let a path-based write follow that swap.
        _verify_directory_identity(root, root_fd, "artifact directory")
        _write_new_json(provenance_path, manifest, directory_fd=root_fd)

        final_files = _inventory_at(root_fd)
        final_payload_files = {
            name: record
            for name, record in final_files.items()
            if name != "BUILD-PROVENANCE.json"
        }
        if final_payload_files != initial_files:
            raise ProvenanceError(
                "artifact payload changed during provenance admission"
            )
        _verify_directory_identity(root, root_fd, "artifact directory")

        _write_checksums(
            checksum_path,
            root,
            final_files,
            directory_fd=root_fd,
        )
        verified_files = _inventory_at(root_fd)
        if verified_files != final_files:
            raise ProvenanceError(
                "artifact tree changed while writing checksum manifest"
            )
        _verify_checksum_manifest_at(root_fd, verified_files)
        checksum_sha, _ = _hash_regular_at(root_fd, "SHA256SUMS", "SHA256SUMS")
        _verify_directory_identity(root, root_fd, "artifact directory")
        print(
            "RELEASE-PROVENANCE-PASS: "
            f"target={args.target} source={source['commit']} "
            f"payload_files={len(initial_files)} checksum_entries={len(final_files)} "
            f"SHA256SUMS={checksum_sha}"
        )
        return manifest
    finally:
        os.close(root_fd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("openwrt", "esp8266", "esp32"), required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--imagebuilder-workdir", type=Path, default=Path("/tmp/blazepwifi-imagebuilder"))
    parser.add_argument("--core-package")
    parser.add_argument("--core-version")
    parser.add_argument("--fqbn")
    parser.add_argument("--sketch")
    parser.add_argument("--libraries", type=Path)
    return parser.parse_args()


def main() -> int:
    try:
        write_provenance(parse_args())
    except (ProvenanceError, OSError, ValueError) as exc:
        print(f"RELEASE-PROVENANCE-RED: {exc}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
