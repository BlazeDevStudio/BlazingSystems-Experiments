#!/usr/bin/env python3
"""Verify installed Arduino CLI bytes against the exact upstream v1.6.0 archive."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import io
import os
import stat
import sys
import tarfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ARCHIVE_URL = (
    "https://github.com/arduino/arduino-cli/releases/download/v1.6.0/"
    "arduino-cli_1.6.0_Linux_64bit.tar.gz"
)
ARCHIVE_SIZE = 20111675
ARCHIVE_SHA256 = "321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250"
BINARY_MEMBER_NAMES = {"arduino-cli", "./arduino-cli"}
MAX_BINARY_SIZE = 200_000_000


class VerificationError(RuntimeError):
    """Raised when downloaded release bytes or the installed binary are not trusted."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _same_file_state(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
        and left.st_ctime_ns == right.st_ctime_ns
        and left.st_nlink == right.st_nlink
    )


def _read_installed_binary(path: Path, expected_info: os.stat_result) -> bytes:
    """Read a bounded executable through a stable no-follow file descriptor."""
    if expected_info.st_size <= 0 or expected_info.st_size > MAX_BINARY_SIZE:
        raise VerificationError(
            "installed Arduino CLI binary size is outside the allowed range: "
            f"{expected_info.st_size}"
        )

    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise VerificationError(
            "descriptor no-follow access is unavailable; refusing installed Arduino CLI admission"
        )

    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    fd = -1
    try:
        fd = os.open(path, flags)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise VerificationError("installed Arduino CLI path is not a regular file")
        if before.st_size <= 0 or before.st_size > MAX_BINARY_SIZE:
            raise VerificationError(
                "installed Arduino CLI binary size is outside the allowed range: "
                f"{before.st_size}"
            )
        if not _same_file_state(expected_info, before):
            raise VerificationError("installed Arduino CLI binary changed before reading")

        chunks: list[bytes] = []
        total = 0
        while True:
            read_limit = min(1024 * 1024, MAX_BINARY_SIZE + 1 - total)
            block = os.read(fd, read_limit)
            if not block:
                break
            total += len(block)
            if total > MAX_BINARY_SIZE:
                raise VerificationError(
                    f"installed Arduino CLI binary exceeds {MAX_BINARY_SIZE} bytes"
                )
            chunks.append(block)

        after = os.fstat(fd)
        path_after = os.stat(path, follow_symlinks=False)
        if not _same_file_state(before, after) or not _same_file_state(after, path_after):
            raise VerificationError("installed Arduino CLI binary changed while reading")
        if total != after.st_size:
            raise VerificationError("installed Arduino CLI binary size changed while reading")
        return b"".join(chunks)
    except VerificationError:
        raise
    except OSError as exc:
        raise VerificationError(
            f"cannot safely read installed Arduino CLI binary: {exc}"
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)


def _read_cli_member(archive_bytes: bytes) -> bytes:
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            matches = [
                member for member in archive.getmembers()
                if member.name in BINARY_MEMBER_NAMES
            ]
            if len(matches) != 1 or not matches[0].isfile():
                raise VerificationError(
                    "archive must contain exactly one regular arduino-cli member"
                )
            member = matches[0]
            if member.size <= 0 or member.size > MAX_BINARY_SIZE:
                raise VerificationError(
                    f"arduino-cli member size is outside the allowed range: {member.size}"
                )
            stream = archive.extractfile(member)
            if stream is None:
                raise VerificationError("cannot read regular arduino-cli archive member")
            with stream:
                payload = stream.read(member.size + 1)
    except VerificationError:
        raise
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise VerificationError(f"invalid Arduino CLI gzip/tar archive: {exc}") from exc

    if len(payload) != member.size:
        raise VerificationError(
            f"arduino-cli member size mismatch: header={member.size}, read={len(payload)}"
        )
    return payload


def verify_archive_payload(
    archive_bytes: bytes,
    installed_binary_bytes: bytes,
    *,
    expected_sha256: str = ARCHIVE_SHA256,
    expected_size: int = ARCHIVE_SIZE,
) -> str:
    """Verify exact archive size/digest and byte identity of the installed CLI."""
    if len(archive_bytes) != expected_size:
        raise VerificationError(
            f"archive size mismatch: expected={expected_size}, actual={len(archive_bytes)}"
        )

    actual_archive_sha256 = _sha256(archive_bytes)
    if not hmac.compare_digest(actual_archive_sha256, expected_sha256):
        raise VerificationError(
            "archive SHA-256 mismatch: "
            f"expected={expected_sha256}, actual={actual_archive_sha256}"
        )

    archived_binary = _read_cli_member(archive_bytes)
    archived_binary_sha256 = _sha256(archived_binary)
    installed_binary_sha256 = _sha256(installed_binary_bytes)
    if not hmac.compare_digest(archived_binary_sha256, installed_binary_sha256):
        raise VerificationError(
            "installed Arduino CLI binary differs from the checksum-verified archive: "
            f"archive={archived_binary_sha256}, installed={installed_binary_sha256}"
        )
    return archived_binary_sha256


def verify_downloaded_binary(binary_path: str | os.PathLike[str]) -> dict[str, str | int]:
    """Download the pinned public release asset and compare it to the installed CLI."""
    try:
        resolved = Path(binary_path).expanduser().resolve(strict=True)
        info = resolved.stat()
    except OSError as exc:
        raise VerificationError(f"cannot resolve installed Arduino CLI binary: {exc}") from exc

    if not stat.S_ISREG(info.st_mode) or not os.access(resolved, os.X_OK):
        raise VerificationError("installed Arduino CLI path is not an executable regular file")

    # Reject oversized or unstable installed files before downloading the reference archive.
    installed_binary_bytes = _read_installed_binary(resolved, info)

    request = Request(
        ARCHIVE_URL,
        headers={"User-Agent": "Project-Phoenix-Release-Integrity/1"},
    )
    try:
        with urlopen(request, timeout=90) as response:
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    reported_size = int(content_length)
                except ValueError as exc:
                    raise VerificationError("release server returned invalid Content-Length") from exc
                if reported_size != ARCHIVE_SIZE:
                    raise VerificationError(
                        f"release Content-Length mismatch: expected={ARCHIVE_SIZE}, "
                        f"actual={reported_size}"
                    )
            archive_bytes = response.read(ARCHIVE_SIZE + 1)
    except VerificationError:
        raise
    except (OSError, URLError, TimeoutError) as exc:
        raise VerificationError(f"cannot download pinned Arduino CLI release asset: {exc}") from exc

    binary_sha256 = verify_archive_payload(archive_bytes, installed_binary_bytes)
    return {
        "archive_sha256": ARCHIVE_SHA256,
        "archive_size": ARCHIVE_SIZE,
        "binary_sha256": binary_sha256,
        "binary_path": str(resolved),
    }

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Arduino CLI v1.6.0 installed bytes against the pinned upstream archive."
    )
    parser.add_argument("--binary", required=True, help="Installed arduino-cli executable path")
    args = parser.parse_args()

    try:
        result = verify_downloaded_binary(args.binary)
    except VerificationError as exc:
        print(f"RELEASE-ARDUINO-ARCHIVE-RED: {exc}", file=sys.stderr)
        return 1

    print(
        "RELEASE-ARDUINO-ARCHIVE-PASS: "
        f"size={result['archive_size']} "
        f"archive_sha256={result['archive_sha256']} "
        f"binary_sha256={result['binary_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
