#!/usr/bin/env python3
"""Negative controls for the checksum-verified Arduino CLI release archive."""
from __future__ import annotations

import hashlib
import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_arduino_cli_archive as verifier
from verify_arduino_cli_archive import (
    ARCHIVE_SHA256,
    ARCHIVE_SIZE,
    ARCHIVE_URL,
    MAX_BINARY_SIZE,
    VerificationError,
    verify_archive_payload,
    verify_downloaded_binary,
)


def make_archive(entries: list[tuple[str, bytes, str]]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, payload, kind in entries:
            member = tarfile.TarInfo(name)
            if kind == "file":
                member.size = len(payload)
                member.mode = 0o755
                archive.addfile(member, io.BytesIO(payload))
            elif kind == "symlink":
                member.type = tarfile.SYMTYPE
                member.linkname = "outside"
                archive.addfile(member)
            else:
                raise AssertionError(f"unknown fixture member kind: {kind}")
    return output.getvalue()


class FakeResponse:
    headers = {"Content-Length": str(ARCHIVE_SIZE)}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return b"synthetic archive response"


class ArduinoCliArchiveVerifierTests(unittest.TestCase):
    def test_release_asset_provenance_is_exactly_pinned(self):
        self.assertEqual(
            ARCHIVE_URL,
            "https://github.com/arduino/arduino-cli/releases/download/v1.6.0/"
            "arduino-cli_1.6.0_Linux_64bit.tar.gz",
        )
        self.assertEqual(
            ARCHIVE_SHA256,
            "321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250",
        )
        self.assertEqual(ARCHIVE_SIZE, 20111675)

    def test_accepts_matching_archive_and_installed_binary(self):
        binary = b"synthetic arduino-cli executable"
        archive = make_archive([("arduino-cli", binary, "file")])
        digest = verify_archive_payload(
            archive,
            binary,
            expected_sha256=hashlib.sha256(archive).hexdigest(),
            expected_size=len(archive),
        )
        self.assertEqual(digest, hashlib.sha256(binary).hexdigest())

    def test_rejects_archive_digest_mismatch(self):
        binary = b"synthetic arduino-cli executable"
        archive = make_archive([("arduino-cli", binary, "file")])
        with self.assertRaisesRegex(VerificationError, "archive SHA-256 mismatch"):
            verify_archive_payload(
                archive,
                binary,
                expected_sha256="0" * 64,
                expected_size=len(archive),
            )

    def test_rejects_truncated_or_oversized_archive(self):
        binary = b"synthetic arduino-cli executable"
        archive = make_archive([("arduino-cli", binary, "file")])
        with self.assertRaisesRegex(VerificationError, "archive size mismatch"):
            verify_archive_payload(
                archive,
                binary,
                expected_sha256=hashlib.sha256(archive).hexdigest(),
                expected_size=len(archive) + 1,
            )

    def test_rejects_archive_without_cli_member(self):
        archive = make_archive([("README.md", b"not the binary", "file")])
        with self.assertRaisesRegex(VerificationError, "exactly one regular arduino-cli member"):
            verify_archive_payload(
                archive,
                b"anything",
                expected_sha256=hashlib.sha256(archive).hexdigest(),
                expected_size=len(archive),
            )

    def test_rejects_duplicate_cli_members(self):
        binary = b"synthetic arduino-cli executable"
        archive = make_archive([
            ("arduino-cli", binary, "file"),
            ("arduino-cli", binary, "file"),
        ])
        with self.assertRaisesRegex(VerificationError, "exactly one regular arduino-cli member"):
            verify_archive_payload(
                archive,
                binary,
                expected_sha256=hashlib.sha256(archive).hexdigest(),
                expected_size=len(archive),
            )

    def test_rejects_symlinked_cli_member(self):
        archive = make_archive([("arduino-cli", b"", "symlink")])
        with self.assertRaisesRegex(VerificationError, "exactly one regular arduino-cli member"):
            verify_archive_payload(
                archive,
                b"anything",
                expected_sha256=hashlib.sha256(archive).hexdigest(),
                expected_size=len(archive),
            )

    def test_rejects_installed_binary_that_differs_from_verified_archive(self):
        archive_binary = b"verified archive binary"
        installed_binary = b"different installed binary"
        archive = make_archive([("arduino-cli", archive_binary, "file")])
        with self.assertRaisesRegex(VerificationError, "installed Arduino CLI binary differs"):
            verify_archive_payload(
                archive,
                installed_binary,
                expected_sha256=hashlib.sha256(archive).hexdigest(),
                expected_size=len(archive),
            )


    def test_rejects_oversized_installed_binary_before_network_or_unbounded_read(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "arduino-cli"
            with binary.open("wb") as stream:
                stream.truncate(MAX_BINARY_SIZE + 1)
            binary.chmod(0o755)

            with patch.object(
                verifier, "urlopen", return_value=FakeResponse()
            ) as download, patch.object(
                Path, "read_bytes", return_value=b"synthetic"
            ) as read_bytes, patch.object(
                verifier, "verify_archive_payload", return_value="a" * 64
            ):
                with self.assertRaisesRegex(
                    VerificationError,
                    "installed Arduino CLI binary size is outside the allowed range",
                ):
                    verify_downloaded_binary(binary)

            download.assert_not_called()
            read_bytes.assert_not_called()

    def test_rejects_hard_linked_installed_binary_before_network_download(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "arduino-cli"
            alias = Path(directory) / "operator-owned-alias"
            binary.write_bytes(b"synthetic executable bytes")
            binary.chmod(0o755)
            os.link(binary, alias)

            with patch.object(
                verifier, "urlopen", return_value=FakeResponse()
            ) as download, patch.object(
                verifier, "verify_archive_payload", return_value="a" * 64
            ):
                with self.assertRaisesRegex(
                    VerificationError,
                    "hard-linked installed Arduino CLI binary",
                ):
                    verify_downloaded_binary(binary)

            download.assert_not_called()

    def test_preserves_primary_read_failure_when_descriptor_close_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "arduino-cli"
            binary.write_bytes(b"synthetic executable bytes")
            binary.chmod(0o755)
            expected_info = binary.stat()
            real_close = os.close
            close_attempts = []

            def close_then_fail(fd):
                close_attempts.append(fd)
                real_close(fd)
                raise OSError("synthetic descriptor close failure")

            with patch.object(
                verifier.os, "read", side_effect=OSError("synthetic primary read failure")
            ), patch.object(verifier.os, "close", side_effect=close_then_fail):
                with self.assertRaisesRegex(
                    VerificationError,
                    "cannot safely read installed Arduino CLI binary: synthetic primary read failure",
                ):
                    verifier._read_installed_binary(binary, expected_info)

            self.assertEqual(len(close_attempts), 1)

    def test_surfaces_descriptor_close_failure_without_primary_error(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "arduino-cli"
            binary.write_bytes(b"synthetic executable bytes")
            binary.chmod(0o755)
            expected_info = binary.stat()
            real_close = os.close
            close_attempts = []

            def close_then_fail(fd):
                close_attempts.append(fd)
                real_close(fd)
                raise OSError("synthetic descriptor close failure")

            with patch.object(verifier.os, "close", side_effect=close_then_fail):
                with self.assertRaisesRegex(OSError, "synthetic descriptor close failure"):
                    verifier._read_installed_binary(binary, expected_info)

            self.assertEqual(len(close_attempts), 1)

    def test_rejects_installed_binary_changed_during_descriptor_read(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "arduino-cli"
            binary.write_bytes(b"synthetic executable bytes")
            binary.chmod(0o755)

            real_read = os.read
            changed = False

            def mutate_after_first_read(fd, size):
                nonlocal changed
                data = real_read(fd, size)
                if not changed:
                    changed = True
                    binary.write_bytes(b"replacement bytes with a different length")
                return data

            with patch.object(
                verifier, "urlopen", return_value=FakeResponse()
            ) as download, patch.object(
                verifier, "verify_archive_payload", return_value="a" * 64
            ), patch.object(verifier.os, "read", side_effect=mutate_after_first_read):
                with self.assertRaisesRegex(
                    VerificationError,
                    "installed Arduino CLI binary changed while reading",
                ):
                    verify_downloaded_binary(binary)

            download.assert_not_called()

if __name__ == "__main__":
    unittest.main(verbosity=2)
