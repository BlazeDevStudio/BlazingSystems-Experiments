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
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "blaze.phx-release.build-provenance/v1"
HEX_SHA = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


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
    )


def _run(command: list[str], *, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ProvenanceError(
            f"command failed ({completed.returncode}): {' '.join(command)}: {detail}"
        )
    return completed.stdout.strip()


def _same_file_state(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
        and left.st_ctime_ns == right.st_ctime_ns
    )


def _open_regular(path: Path) -> tuple[int, os.stat_result]:
    try:
        before = path.lstat()
    except OSError as exc:
        raise ProvenanceError(f"cannot stat {path}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise ProvenanceError(f"expected a regular non-symlink file: {path}")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ProvenanceError("O_NOFOLLOW is unavailable; refusing artifact admission")
    try:
        fd = os.open(path, os.O_RDONLY | nofollow)
        opened = os.fstat(fd)
    except OSError as exc:
        raise ProvenanceError(f"cannot safely open {path}: {exc}") from exc
    if not stat.S_ISREG(opened.st_mode) or not _same_file_state(before, opened):
        os.close(fd)
        raise ProvenanceError(f"file identity changed while opening: {path}")
    return fd, opened


def _read_regular(path: Path) -> bytes:
    fd, before = _open_regular(path)
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
        path_after = path.lstat()
    except OSError as exc:
        raise ProvenanceError(f"cannot read {path}: {exc}") from exc
    finally:
        os.close(fd)
    if not _same_file_state(before, after) or not _same_file_state(after, path_after):
        raise ProvenanceError(f"file changed while reading: {path}")
    if total != after.st_size:
        raise ProvenanceError(f"short or changing read: {path}")
    return b"".join(chunks)


def _hash_regular(path: Path) -> tuple[str, int]:
    fd, before = _open_regular(path)
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
        path_after = path.lstat()
    except OSError as exc:
        raise ProvenanceError(f"cannot hash {path}: {exc}") from exc
    finally:
        os.close(fd)
    if not _same_file_state(before, after) or not _same_file_state(after, path_after):
        raise ProvenanceError(f"file changed while hashing: {path}")
    if total != after.st_size:
        raise ProvenanceError(f"short or changing hash read: {path}")
    return digest.hexdigest(), total


def _require_directory(path: Path, label: str) -> Path:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ProvenanceError(f"{label} is unavailable: {path}: {exc}") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise ProvenanceError(f"{label} must be a real directory, not a symlink: {path}")
    return path


def _normalize_checksum_path(name: str) -> str:
    if name.startswith("./"):
        name = name[2:]
    if not name or "\\" in name or "\n" in name or "\r" in name or "\x00" in name:
        raise ProvenanceError(f"unsafe checksum path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
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


def _inventory(root: Path) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        base = Path(current)
        dirnames.sort()
        filenames.sort()
        for dirname in dirnames:
            directory = base / dirname
            try:
                metadata = directory.lstat()
            except OSError as exc:
                raise ProvenanceError(f"cannot inspect artifact directory {directory}: {exc}") from exc
            if not stat.S_ISDIR(metadata.st_mode):
                raise ProvenanceError(f"symlink or non-directory inside artifact tree: {directory}")
        for filename in filenames:
            path = base / filename
            relative = path.relative_to(root).as_posix()
            if relative == "SHA256SUMS":
                continue
            _normalize_checksum_path(relative)
            digest, size = _hash_regular(path)
            files[relative] = {"path": relative, "size_bytes": size, "sha256": digest}
    if not files:
        raise ProvenanceError("artifact directory contains no payload files")
    return dict(sorted(files.items()))


def _verify_checksum_manifest(root: Path, files: dict[str, dict[str, Any]]) -> None:
    checksum_path = root / "SHA256SUMS"
    entries = _parse_checksum_text(_read_regular(checksum_path), "SHA256SUMS")
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
    official_sums = _parse_checksum_text(_read_regular(workdir / "sha256sums"), "ImageBuilder sha256sums")
    archive_name = archive.name
    if archive_name not in official_sums:
        raise ProvenanceError("official OpenWrt sha256sums does not contain the selected archive")
    archive_sha, _ = _hash_regular(archive)
    if official_sums[archive_name] != archive_sha:
        raise ProvenanceError("ImageBuilder archive does not match the official OpenWrt sha256sums entry")

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
        "compiler_version_note": "not separately emitted by the current ImageBuilder build script",
    }
    source_paths = [
        "experiment/openwrt/BlazePwifi/build/build-openwrt-image.sh",
        "experiment/openwrt/BlazePwifi/VERSION",
    ]
    return toolchain, source_paths


def _arduino_toolchain(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    required = ("core_package", "core_version", "fqbn", "sketch")
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
    toolchain = {
        "name": "Arduino CLI",
        "arduino_cli_version": match.group(1),
        "arduino_cli_version_output": cli_output,
        "board_core": f"{args.core_package}@{args.core_version}",
        "fqbn": args.fqbn,
        "sketch": sketch,
        "compiler_version": None,
        "compiler_version_note": "board package compiler subversion is not separately emitted by this workflow",
    }
    source_paths = [
        sketch,
        "experiment/openwrt/BlazePwifi/tools/package-vendo-source.py",
    ]
    return toolchain, source_paths


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_new_json(path: Path, payload: dict[str, Any]) -> None:
    if os.path.lexists(path):
        raise ProvenanceError(f"refusing to overwrite existing provenance file: {path}")
    data = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".BUILD-PROVENANCE.", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # A hard link is an atomic create-if-absent operation on this filesystem.
        os.link(temp_path, path, follow_symlinks=False)
        temp_path.unlink()
        _fsync_directory(path.parent)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _write_checksums(path: Path, root: Path, files: dict[str, dict[str, Any]]) -> None:
    if os.path.lexists(path):
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise ProvenanceError("SHA256SUMS must remain a regular non-symlink file")
    rows = [f"{record['sha256']}  {name}" for name, record in sorted(files.items())]
    data = ("\n".join(rows) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".SHA256SUMS.", dir=root)
    temp_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
        _fsync_directory(root)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def write_provenance(args: argparse.Namespace, env: dict[str, str] | None = None) -> dict[str, Any]:
    environment = dict(os.environ if env is None else env)
    root = _require_directory(Path(args.artifact_dir), "artifact directory")
    provenance_path = root / "BUILD-PROVENANCE.json"
    if os.path.lexists(provenance_path):
        raise ProvenanceError("BUILD-PROVENANCE.json already exists; refusing to overwrite it")
    checksum_path = root / "SHA256SUMS"
    if not os.path.lexists(checksum_path):
        raise ProvenanceError("existing SHA256SUMS is required before provenance admission")

    initial_files = _inventory(root)
    _verify_checksum_manifest(root, initial_files)

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

    _write_new_json(provenance_path, manifest)
    final_files = _inventory(root)
    _write_checksums(checksum_path, root, final_files)
    _verify_checksum_manifest(root, final_files)
    checksum_sha, _ = _hash_regular(checksum_path)
    print(
        "RELEASE-PROVENANCE-PASS: "
        f"target={args.target} source={source['commit']} "
        f"payload_files={len(initial_files)} checksum_entries={len(final_files)} "
        f"SHA256SUMS={checksum_sha}"
    )
    return manifest


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
