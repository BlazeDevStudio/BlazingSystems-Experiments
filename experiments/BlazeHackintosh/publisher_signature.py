"""Fail-closed, read-only detached Ed25519 signature verification using OpenSSL.

Requires an independently authenticated public-key SHA-256 pin supplied OUTSIDE
of the untrusted component manifest. Verifying a signature with a pinned key
alone does not establish publisher identity, licensing or production readiness.

This module does not download files, execute component binaries or write disks.
It invokes a locally installed OpenSSL executable without a shell. The caller
must independently pin the OpenSSL executable SHA-256. Dynamic libraries,
runtime dependencies and key-pin distribution remain unverified.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from urllib.parse import urlsplit

DIGEST = re.compile(r"[a-fA-F0-9]{64}\Z")
LIMITS = {"artifact": 1024**3, "signature": 4096, "public_key": 8192,
          "openssl_executable": 256 * 1024**2}


def _read_regular(path: str | Path, maximum: int) -> bytes:
    p = Path(path)
    if p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()):
        raise ValueError("Linked input path rejected")
    before = p.lstat()
    if (not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum or
            getattr(before, "st_file_attributes", 0) &
            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
        raise ValueError("Input must be a bounded regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(p, flags)
    with os.fdopen(fd, "rb") as f:
        opened = os.fstat(f.fileno())
        if (not stat.S_ISREG(opened.st_mode) or
                (before.st_dev, before.st_ino, before.st_size) !=
                (opened.st_dev, opened.st_ino, opened.st_size)):
            raise ValueError("Input changed between inspection and opening")
        data = f.read(maximum + 1)
        after = os.fstat(f.fileno())
        if (len(data) != opened.st_size or len(data) > maximum or
                (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns)):
            raise ValueError("Input changed during read")
    return data


def _digest_regular(path: str | Path, maximum: int) -> str:
    """Hash a bounded regular file in fixed-size chunks, without buffering it all."""
    p = Path(path)
    if p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()):
        raise ValueError("Linked input path rejected")
    before = p.lstat()
    if (not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum or
            getattr(before, "st_file_attributes", 0) &
            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
        raise ValueError("Input must be a bounded regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(p, flags)
    with os.fdopen(fd, "rb") as f:
        opened = os.fstat(f.fileno())
        if (not stat.S_ISREG(opened.st_mode) or
                (before.st_dev, before.st_ino, before.st_size) !=
                (opened.st_dev, opened.st_ino, opened.st_size)):
            raise ValueError("Input changed between inspection and opening")
        digest = hashlib.sha256()
        count = 0
        while True:
            chunk = f.read(min(1024 * 1024, maximum + 1 - count))
            if not chunk:
                break
            count += len(chunk)
            if count > maximum:
                raise ValueError("Input exceeded maximum size")
            digest.update(chunk)
        after = os.fstat(f.fileno())
        if (count != opened.st_size or
                (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns,
                 getattr(opened, "st_ctime_ns", 0)) !=
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
                 getattr(after, "st_ctime_ns", 0))):
            raise ValueError("Input changed during digest")
    return digest.hexdigest()


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _valid_url(value: str) -> bool:
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        u = urlsplit(value)
        host = u.hostname or ""
        try:
            ipaddress.ip_address(host)
            return False  # publisher release identity must use a DNS name
        except ValueError:
            pass
        labels = host.split(".")
        dns_name = (len(labels) >= 2 and all(
            0 < len(label) <= 63 and
            re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?", label)
            for label in labels) and
            not host.lower().endswith((".local", ".localhost", ".internal")))
        return (u.scheme == "https" and dns_name and not u.username and
                not u.password and u.port in (None, 443) and not u.fragment)
    except ValueError:
        return False


def verify(*, artifact: str | Path, signature: str | Path, public_key: str | Path,
           expected_artifact_sha256: str, trusted_key_sha256: str,
           trusted_openssl_sha256: str, upstream_release_url: str,
           openssl: str = "openssl") -> dict:
    """Return explicit scope-limited evidence; never report production acceptance."""
    result = {"audit_complete": False, "artifact_digest_verified": False,
              "trusted_key_pin_verified": False, "openssl_binary_hash_verified": False,
              "openssl_runtime_dependencies_verified": False,
              "ed25519_signature_verified": False,
              "publisher_identity_independently_verified": False,
              "license_verified": False, "component_auth_gate_satisfied": False,
              "errors": [],
              "notice": "Pinned-key signature only; upstream key ownership, licenses and production remain unverified"}
    try:
        if not isinstance(expected_artifact_sha256, str) or not DIGEST.fullmatch(expected_artifact_sha256):
            raise ValueError("Independent artifact SHA-256 pin required")
        if not isinstance(trusted_key_sha256, str) or not DIGEST.fullmatch(trusted_key_sha256):
            raise ValueError("Independent publisher public-key SHA-256 pin required")
        if not isinstance(trusted_openssl_sha256, str) or not DIGEST.fullmatch(trusted_openssl_sha256):
            raise ValueError("Independent OpenSSL executable SHA-256 pin required")
        if not _valid_url(upstream_release_url):
            raise ValueError("HTTPS upstream release URL required")
        if not isinstance(openssl, str) or not openssl.strip() or any(c in openssl for c in '\r\n\x00'):
            raise ValueError("Invalid OpenSSL executable path")
        executable_name = shutil.which(openssl)
        if not executable_name:
            raise ValueError("OpenSSL executable not found")
        executable = Path(executable_name).absolute()
        if _digest_regular(executable, LIMITS["openssl_executable"]) != trusted_openssl_sha256.lower():
            raise ValueError("OpenSSL executable SHA-256 pin mismatch")
        result["openssl_binary_hash_verified"] = True
        artifact_digest = _digest_regular(artifact, LIMITS["artifact"])
        signature_bytes = _read_regular(signature, LIMITS["signature"])
        if len(signature_bytes) != 64:
            raise ValueError("Ed25519 detached signature must be exactly 64 bytes")
        key_bytes = _read_regular(public_key, LIMITS["public_key"])
        if artifact_digest != expected_artifact_sha256.lower():
            raise ValueError("Artifact SHA-256 mismatch")
        result["artifact_digest_verified"] = True
        if _hash(key_bytes) != trusted_key_sha256.lower():
            raise ValueError("Publisher key pin mismatch")
        result["trusted_key_pin_verified"] = True
        match = re.fullmatch(
            rb"-----BEGIN PUBLIC KEY-----\s+([A-Za-z0-9+/=\r\n]+)\s+-----END PUBLIC KEY-----\s*",
            key_bytes)
        if not match:
            raise ValueError("Expected exactly one PEM SubjectPublicKeyInfo")
        try:
            der = base64.b64decode(re.sub(rb"\s+", b"", match.group(1)), validate=True)
        except binascii.Error as exc:
            raise ValueError("Invalid public-key PEM encoding") from exc
        if len(der) != 44 or not der.startswith(bytes.fromhex("302a300506032b6570032100")):
            raise ValueError("Pinned public key is not Ed25519")
        try:
            completed = subprocess.run(
                [str(executable), "pkeyutl", "-verify", "-pubin", "-inkey", str(public_key),
                 "-sigfile", str(signature), "-rawin", "-in", str(artifact)],
                capture_output=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("Trusted local OpenSSL verification unavailable") from exc
        if completed.returncode != 0:
            raise ValueError("Detached Ed25519 signature verification failed")
        if (_digest_regular(executable, LIMITS["openssl_executable"]) != trusted_openssl_sha256.lower() or
                _digest_regular(artifact, LIMITS["artifact"]) != artifact_digest or
                _read_regular(signature, LIMITS["signature"]) != signature_bytes or
                _read_regular(public_key, LIMITS["public_key"]) != key_bytes):
            raise ValueError("Verification inputs or executable changed during verification")
        result["ed25519_signature_verified"] = True
        result["audit_complete"] = True
    except (ValueError, OSError) as exc:
        result["errors"].append(str(exc))
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only pinned-key detached signature verification")
    p.add_argument("--artifact", required=True)
    p.add_argument("--signature", required=True)
    p.add_argument("--public-key", required=True)
    p.add_argument("--expected-artifact-sha256", required=True)
    p.add_argument("--trusted-key-sha256", required=True)
    p.add_argument("--trusted-openssl-sha256", required=True)
    p.add_argument("--upstream-release-url", required=True)
    p.add_argument("--openssl", default="openssl")
    a = p.parse_args()
    result = verify(**vars(a))
    print(json.dumps(result, indent=2))
    return 0 if result["audit_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
