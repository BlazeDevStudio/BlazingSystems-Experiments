#!/usr/bin/env python3
"""Negative controls for the checksum-verified Arduino CLI release archive."""
from __future__ import annotations

import hashlib
import io
import tarfile
import unittest

from verify_arduino_cli_archive import (
    ARCHIVE_SHA256,
    ARCHIVE_SIZE,
    ARCHIVE_URL,
    VerificationError,
    verify_archive_payload,
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
