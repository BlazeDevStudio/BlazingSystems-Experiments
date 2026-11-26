#!/usr/bin/env python3
"""Verify the pinned ESP32 package/toolchain lock and retain clean-build provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "phx/arduino-esp32-toolchain-lock/v1"
CHUNK_SIZE = 1024 * 1024


class ToolchainLockError(ValueError):
    """The observed ESP32 toolchain differs from the release-owned lock."""


def _read_regular_bytes(path: Path, label: str) -> bytes:
    path = Path(path)
    try:
        before_path = path.lstat()
    except OSError as exc:
        raise ToolchainLockError(f"{label} is unavailable: {path}: {exc}") from exc
    if not stat.S_ISREG(before_path.st_mode) or before_path.st_nlink != 1:
        raise ToolchainLockError(f"{label} must be a single-link regular file: {path}")

    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ToolchainLockError("O_NOFOLLOW is unavailable; refusing provenance read")
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise ToolchainLockError(f"cannot open {label} without following links: {path}: {exc}") from exc

    try:
        before_fd = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before_fd.st_mode)
            or before_fd.st_nlink != 1
            or (before_fd.st_dev, before_fd.st_ino)
            != (before_path.st_dev, before_path.st_ino)
        ):
            raise ToolchainLockError(f"{label} identity changed before read: {path}")

        chunks: list[bytes] = []
        while True:
            block = os.read(descriptor, CHUNK_SIZE)
            if not block:
                break
            chunks.append(block)

        after_fd = os.fstat(descriptor)
        after_path = path.lstat()
        stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
        if any(getattr(before_fd, field) != getattr(after_fd, field) for field in stable_fields):
            raise ToolchainLockError(f"{label} changed while being read: {path}")
        if (
            not stat.S_ISREG(after_path.st_mode)
            or after_path.st_nlink != 1
            or (after_path.st_dev, after_path.st_ino)
            != (after_fd.st_dev, after_fd.st_ino)
        ):
            raise ToolchainLockError(f"{label} path identity changed while being read: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def git_blob_sha1(payload: bytes) -> str:
    """Return the SHA-1 Git uses for a blob object, including its object header."""
    header = b"blob " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(header + payload).hexdigest()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _single_version_directory(root: Path, label: str, expected: str) -> Path:
    if not root.is_dir() or root.is_symlink():
        raise ToolchainLockError(f"installed package directory is missing: {label}: {root}")
    versions = sorted(
        child.name
        for child in root.iterdir()
        if child.is_dir() and not child.is_symlink()
    )
    if versions != [expected]:
        raise ToolchainLockError(
            f"{label} must have exactly installed version {expected}; found {versions}"
        )
    return root / expected


def _package_entry(index: dict[str, Any], packager: str) -> dict[str, Any]:
    matches = [item for item in index.get("packages", []) if item.get("name") == packager]
    if len(matches) != 1:
        raise ToolchainLockError(
            f"package index must contain exactly one packager {packager}; found {len(matches)}"
        )
    return matches[0]


def _find_archive(
    index: dict[str, Any],
    packager: str,
    name: str,
    version: str,
    host: str,
) -> dict[str, str]:
    package = _package_entry(index, packager)
    matches = [
        item for item in package.get("tools", [])
        if item.get("name") == name and item.get("version") == version
    ]
    if len(matches) != 1:
        raise ToolchainLockError(
            f"index must contain exactly one {packager}:{name}@{version}; found {len(matches)}"
        )
    systems = [item for item in matches[0].get("systems", []) if item.get("host") == host]
    if len(systems) != 1:
        raise ToolchainLockError(
            f"index must contain exactly one {packager}:{name}@{version} archive for {host}; found {len(systems)}"
        )
    item = systems[0]
    required = ("archiveFileName", "url", "checksum", "size")
    if any(not item.get(key) for key in required):
        raise ToolchainLockError(f"incomplete archive metadata for {packager}:{name}@{version}")
    return {
        "archive_file_name": str(item["archiveFileName"]),
        "url": str(item["url"]),
        "checksum": str(item["checksum"]),
        "size": str(item["size"]),
    }


def _compare_archive(
    observed: dict[str, str],
    expected: dict[str, Any],
    label: str,
) -> None:
    for key in ("archive_file_name", "url", "checksum", "size"):
        if str(observed.get(key)) != str(expected.get(key)):
            raise ToolchainLockError(
                f"{label} {key} differs from lock: expected {expected.get(key)!r}, "
                f"observed {observed.get(key)!r}"
            )
    if not str(expected.get("checksum", "")).startswith("SHA-256:"):
        raise ToolchainLockError(f"{label} does not have a SHA-256 archive checksum")


def _installed_versions(packages_root: Path, packager: str, group: str, name: str) -> Path:
    return packages_root / packager / group / name


def _parse_cli_version(output: str) -> str:
    matches = re.findall(r"\bVersion:\s*([0-9][A-Za-z0-9.+-]*)", output)
    if len(matches) != 1:
        raise ToolchainLockError(f"cannot uniquely parse Arduino CLI version: {output.strip()!r}")
    return matches[0]


def _parse_core_version(output: str, package: str) -> str:
    matches = []
    for line in output.splitlines():
        columns = line.split()
        if len(columns) >= 2 and columns[0] == package:
            matches.append(columns[1])
    if len(matches) != 1:
        raise ToolchainLockError(
            f"arduino-cli core list must contain exactly one {package}; found {matches}"
        )
    return matches[0]


def verify_toolchain_lock(
    lock: dict[str, Any],
    core_version: str,
    packages_root: Path,
    esp32_index_path: Path,
    arduino_index_path: Path,
    cli_version_output: str,
    core_list_output: str,
) -> dict[str, Any]:
    """Fail closed unless the exact package index, core and every dependency match."""
    if lock.get("schema") != SCHEMA:
        raise ToolchainLockError(f"unsupported ESP32 toolchain lock schema: {lock.get('schema')!r}")
    if core_version not in lock.get("cores", {}):
        raise ToolchainLockError(f"ESP32 core {core_version} is not present in the release lock")

    source = lock.get("source", {})
    esp32_bytes = _read_regular_bytes(Path(esp32_index_path), "Espressif package index")
    actual_blob = git_blob_sha1(esp32_bytes)
    expected_blob = source.get("git_blob_sha1")
    if actual_blob != expected_blob:
        raise ToolchainLockError(
            f"Espressif package index Git blob differs from lock: expected {expected_blob}, observed {actual_blob}"
        )
    try:
        esp32_index = json.loads(esp32_bytes)
    except json.JSONDecodeError as exc:
        raise ToolchainLockError(f"Espressif package index is invalid JSON: {exc}") from exc

    arduino_bytes = _read_regular_bytes(Path(arduino_index_path), "Arduino package index")
    try:
        arduino_index = json.loads(arduino_bytes)
    except json.JSONDecodeError as exc:
        raise ToolchainLockError(f"Arduino package index is invalid JSON: {exc}") from exc

    core_lock = lock["cores"][core_version]
    esp32_package = _package_entry(esp32_index, "esp32")
    platforms = [
        item for item in esp32_package.get("platforms", [])
        if item.get("name") == "esp32" and item.get("version") == core_version
    ]
    if len(platforms) != 1:
        raise ToolchainLockError(
            f"pinned Espressif index must contain one ESP32 core {core_version}; found {len(platforms)}"
        )
    platform_entry = platforms[0]
    observed_platform = {
        "archive_file_name": str(platform_entry.get("archiveFileName", "")),
        "url": str(platform_entry.get("url", "")),
        "checksum": str(platform_entry.get("checksum", "")),
        "size": str(platform_entry.get("size", "")),
    }
    _compare_archive(observed_platform, core_lock["platform"], f"esp32:esp32@{core_version}")

    actual_dependencies = sorted(
        (str(item.get("packager")), str(item.get("name")), str(item.get("version")))
        for item in platform_entry.get("toolsDependencies", [])
    )
    expected_dependencies = sorted(
        (str(item.get("packager")), str(item.get("name")), str(item.get("version")))
        for item in core_lock.get("tools", [])
    )
    if actual_dependencies != expected_dependencies:
        raise ToolchainLockError(
            f"ESP32 core {core_version} tool dependency set differs from lock: "
            f"expected {expected_dependencies}, observed {actual_dependencies}"
        )

    packages_root = Path(packages_root)
    core_directory = _single_version_directory(
        packages_root / "esp32" / "hardware" / "esp32",
        f"esp32:esp32@{core_version}",
        core_version,
    )
    observed_tools: list[dict[str, Any]] = []
    for tool in core_lock["tools"]:
        packager = str(tool["packager"])
        name = str(tool["name"])
        version = str(tool["version"])
        host = str(tool["host"])
        index = esp32_index if packager == "esp32" else arduino_index
        observed_archive = _find_archive(index, packager, name, version, host)
        _compare_archive(
            observed_archive,
            tool["archive"],
            f"{packager}:{name}@{version}",
        )
        installed_root = _installed_versions(packages_root, packager, "tools", name)
        installed_path = _single_version_directory(
            installed_root,
            f"{packager}:{name}",
            version,
        )
        observed_tools.append(
            {
                "packager": packager,
                "name": name,
                "version": version,
                "host": host,
                "archive": dict(tool["archive"]),
                "installed_path": installed_path.relative_to(packages_root).as_posix(),
            }
        )

    observed_builtins: list[dict[str, str]] = []
    for builtin in core_lock.get("builtins", []):
        packager = str(builtin["packager"])
        name = str(builtin["name"])
        version = str(builtin["version"])
        installed_root = _installed_versions(packages_root, packager, "tools", name)
        installed_path = _single_version_directory(
            installed_root,
            f"{packager}:{name}",
            version,
        )
        observed_builtins.append(
            {
                "packager": packager,
                "name": name,
                "version": version,
                "installed_path": installed_path.relative_to(packages_root).as_posix(),
            }
        )

    cli_version = _parse_cli_version(cli_version_output)
    expected_cli = str(lock["arduino_cli"]["version"])
    if cli_version != expected_cli:
        raise ToolchainLockError(
            f"Arduino CLI version differs from lock: expected {expected_cli}, observed {cli_version}"
        )
    core_list_version = _parse_core_version(core_list_output, "esp32:esp32")
    if core_list_version != core_version:
        raise ToolchainLockError(
            f"installed ESP32 core differs from requested matrix core: expected {core_version}, observed {core_list_version}"
        )

    return {
        "core_version": core_version,
        "core_path": core_directory.relative_to(packages_root).as_posix(),
        "arduino_cli": {
            "version": cli_version,
            "archive_file_name": lock["arduino_cli"]["archive_file_name"],
            "url": lock["arduino_cli"]["url"],
            "checksum_sha256": lock["arduino_cli"]["checksum_sha256"],
            "size_bytes": lock["arduino_cli"]["size_bytes"],
            "version_output": cli_version_output.strip(),
        },
        "core_list_output": core_list_output.strip(),
        "index": {
            "url": source["url"],
            "commit": source["commit"],
            "git_blob_sha1": actual_blob,
            "sha256": _sha256(esp32_bytes),
            "size_bytes": len(esp32_bytes),
        },
        "arduino_index": {
            "url": lock["arduino_package_index"]["url"],
            "sha256": _sha256(arduino_bytes),
            "size_bytes": len(arduino_bytes),
        },
        "platform": dict(core_lock["platform"]),
        "tools": observed_tools,
        "builtins": observed_builtins,
    }


def _run_command(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    output = result.stdout.strip()
    if not output:
        raise ToolchainLockError(f"command returned no version output: {command[0]}")
    return output


def _hash_regular_file(path: Path, label: str) -> dict[str, Any]:
    payload = _read_regular_bytes(Path(path), label)
    return {"sha256": _sha256(payload), "size_bytes": len(payload)}


def _write_private_file(path: Path, payload: bytes) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise ToolchainLockError(f"refusing to overwrite provenance output: {path}")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def capture_manifest(
    verified: dict[str, Any],
    lock: dict[str, Any],
    packages_root: Path,
    esp32_index_path: Path,
    arduino_index_path: Path,
    output_dir: Path,
    source_sha: str,
    sketch_path: str,
    sketch_blob: str,
    source_date_epoch: str,
    fqbn: str,
    first_bin: Path,
    second_bin: Path,
    first_elf: Path,
    second_elf: Path,
    runner_env: dict[str, str] | None = None,
    command_runner: Callable[[list[str]], str] | None = None,
) -> dict[str, Any]:
    """Copy immutable index inputs and record both clean-build outputs without publishing."""
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ToolchainLockError("source commit must be a full 40-character Git SHA")
    if not re.fullmatch(r"[0-9a-f]{40}", sketch_blob):
        raise ToolchainLockError("sketch blob must be a full 40-character Git SHA")
    if not str(source_date_epoch).isdigit():
        raise ToolchainLockError("SOURCE_DATE_EPOCH must be a non-negative integer")

    output_dir = Path(output_dir)
    if output_dir.exists() and (output_dir.is_symlink() or not output_dir.is_dir()):
        raise ToolchainLockError(f"provenance output root is not a real directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir = output_dir / "provenance"
    if provenance_dir.exists() and (provenance_dir.is_symlink() or not provenance_dir.is_dir()):
        raise ToolchainLockError(f"provenance input directory is not a real directory: {provenance_dir}")
    provenance_dir.mkdir(exist_ok=True)

    copied_indexes: dict[str, dict[str, Any]] = {}
    for source_path, name in (
        (Path(esp32_index_path), "package_esp32_index.json"),
        (Path(arduino_index_path), "package_index.json"),
    ):
        payload = _read_regular_bytes(source_path, name)
        destination = provenance_dir / name
        _write_private_file(destination, payload)
        copied_indexes[name] = {
            "sha256": _sha256(payload),
            "size_bytes": len(payload),
            "artifact_path": f"provenance/{name}",
        }

    outputs = {
        "first_binary": _hash_regular_file(Path(first_bin), "first clean-build binary"),
        "second_binary": _hash_regular_file(Path(second_bin), "second clean-build binary"),
        "first_elf": _hash_regular_file(Path(first_elf), "first clean-build ELF"),
        "second_elf": _hash_regular_file(Path(second_elf), "second clean-build ELF"),
    }

    packages_root = Path(packages_root)
    x32 = next(
        item for item in verified["tools"]
        if item["packager"] == "esp32" and item["name"] == "esp-x32"
    )
    compiler_root = packages_root / "esp32" / "tools" / "esp-x32" / x32["version"] / "bin"
    compiler_names = {
        "gcc": "xtensa-esp32-elf-gcc",
        "objdump": "xtensa-esp32-elf-objdump",
        "nm": "xtensa-esp32-elf-nm",
    }
    runner = command_runner or _run_command
    compiler_versions: dict[str, str] = {}
    for label, filename in compiler_names.items():
        executable = compiler_root / filename
        if not executable.is_file() or executable.is_symlink():
            raise ToolchainLockError(f"pinned compiler tool is missing or unsafe: {executable}")
        version_output = runner([str(executable), "--version"])
        compiler_versions[label] = next(
            (line.strip() for line in version_output.splitlines() if line.strip()),
            version_output.strip(),
        )

    env = dict(os.environ if runner_env is None else runner_env)
    runner_record = {
        "runner_os": env.get("RUNNER_OS"),
        "runner_arch": env.get("RUNNER_ARCH"),
        "image_os": env.get("ImageOS"),
        "image_version": env.get("ImageVersion"),
        "platform": platform.platform(),
    }
    os_release = Path("/etc/os-release")
    if os_release.is_file() and not os_release.is_symlink():
        try:
            os_release_text = _read_regular_bytes(os_release, "runner os-release").decode("utf-8", "replace")
            runner_record["os_release"] = {
                key: value.strip().strip('"')
                for line in os_release_text.splitlines()
                if "=" in line
                for key, value in [line.split("=", 1)]
                if key in {"ID", "VERSION_ID", "PRETTY_NAME"}
            }
        except (OSError, ToolchainLockError):
            runner_record["os_release"] = {"capture": "unavailable"}

    canonical_lock = json.dumps(lock, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest = {
        "schema": "phx/esp32-build-provenance/v1",
        "evidence_class": "HOSTED_CI_ONLY",
        "source": {
            "commit": source_sha,
            "sketch_path": sketch_path,
            "sketch_blob": sketch_blob,
        },
        "toolchain": {
            "lock_sha256": _sha256(canonical_lock),
            "arduino_cli": verified["arduino_cli"],
            "core": f"esp32:esp32@{verified['core_version']}",
            "platform_archive": verified["platform"],
            "esp32_package_index": verified["index"],
            "arduino_package_index": verified["arduino_index"],
            "installed_tools": verified["tools"],
            "installed_builtins": verified["builtins"],
            "compiler_versions": compiler_versions,
        },
        "build": {
            "fqbn": fqbn,
            "source_date_epoch": int(source_date_epoch),
            "locale": env.get("LC_ALL"),
            "timezone": env.get("TZ"),
            "runner": runner_record,
            "binary_identical": outputs["first_binary"]["sha256"] == outputs["second_binary"]["sha256"],
            "elf_identical": outputs["first_elf"]["sha256"] == outputs["second_elf"]["sha256"],
        },
        "inputs": copied_indexes,
        "outputs": outputs,
        "release_state": {
            "production_authorized": False,
            "signing_performed": False,
            "hardware_acceptance": False,
        },
    }
    manifest_path = output_dir / "toolchain-provenance.json"
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    _write_private_file(manifest_path, manifest_bytes)

    checksum_rows: list[str] = []
    roots = (
        output_dir / "first",
        output_dir / "second",
        provenance_dir,
        manifest_path,
    )
    for root in roots:
        candidates = [root] if root.is_file() else sorted(root.rglob("*")) if root.is_dir() else []
        for path in candidates:
            if not path.is_file() or path.is_symlink():
                continue
            digest = _hash_regular_file(path, "retained ESP32 CI artifact")["sha256"]
            checksum_rows.append(f"{digest}  {path.relative_to(output_dir).as_posix()}")
    checksum_rows.sort()
    _write_private_file(output_dir / "SHA256SUMS", ("\n".join(checksum_rows) + "\n").encode("utf-8"))
    return manifest


def _load_lock(path: Path) -> dict[str, Any]:
    payload = _read_regular_bytes(Path(path), "ESP32 toolchain lock")
    try:
        lock = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ToolchainLockError(f"ESP32 toolchain lock is invalid JSON: {exc}") from exc
    if lock.get("schema") != SCHEMA:
        raise ToolchainLockError(f"unsupported ESP32 toolchain lock schema: {lock.get('schema')!r}")
    return lock


def _cli_outputs(arduino_cli: str) -> tuple[str, str]:
    return (
        _run_command([arduino_cli, "version"]),
        _run_command([arduino_cli, "core", "list"]),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("verify", "capture"), required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--core-version", required=True)
    parser.add_argument("--packages-root", type=Path, required=True)
    parser.add_argument("--esp32-index", type=Path, required=True)
    parser.add_argument("--arduino-index", type=Path, required=True)
    parser.add_argument("--arduino-cli", default="arduino-cli")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--sketch-path")
    parser.add_argument("--sketch-blob")
    parser.add_argument("--source-date-epoch")
    parser.add_argument("--fqbn", default="esp32:esp32:esp32")
    parser.add_argument("--first-bin", type=Path)
    parser.add_argument("--second-bin", type=Path)
    parser.add_argument("--first-elf", type=Path)
    parser.add_argument("--second-elf", type=Path)
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        lock = _load_lock(args.lock)
        cli_version_output, core_list_output = _cli_outputs(args.arduino_cli)
        verified = verify_toolchain_lock(
            lock,
            args.core_version,
            args.packages_root,
            args.esp32_index,
            args.arduino_index,
            cli_version_output,
            core_list_output,
        )
        if args.phase == "verify":
            print(
                "PHX-ESP32-TOOLCHAIN-LOCK-PASS: "
                f"core={args.core_version} index_blob={verified['index']['git_blob_sha1']} "
                f"tools={len(verified['tools'])} builtins={len(verified['builtins'])}"
            )
            return 0

        required = (
            args.output_dir,
            args.source_sha,
            args.sketch_path,
            args.sketch_blob,
            args.source_date_epoch,
            args.first_bin,
            args.second_bin,
            args.first_elf,
            args.second_elf,
        )
        if any(value is None for value in required):
            raise ToolchainLockError("capture phase is missing one or more build/provenance arguments")
        manifest = capture_manifest(
            verified,
            lock,
            args.packages_root,
            args.esp32_index,
            args.arduino_index,
            args.output_dir,
            args.source_sha,
            args.sketch_path,
            args.sketch_blob,
            args.source_date_epoch,
            args.fqbn,
            args.first_bin,
            args.second_bin,
            args.first_elf,
            args.second_elf,
        )
        print(
            "PHX-ESP32-PROVENANCE-PASS: "
            f"core={args.core_version} binary_identical={manifest['build']['binary_identical']} "
            f"elf_identical={manifest['build']['elf_identical']} "
            f"manifest={args.output_dir / 'toolchain-provenance.json'}"
        )
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"PHX-ESP32-TOOLCHAIN-RED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
