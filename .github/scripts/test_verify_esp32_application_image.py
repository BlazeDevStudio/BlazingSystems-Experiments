#!/usr/bin/env python3
"""Regression tests for descriptor cleanup in ESP32 application-image admission."""
from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_esp32_application_image as verifier


class ApplicationImageDescriptorCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temporary.name) / "output"
        self.output_dir.mkdir()
        self.image = self.output_dir / "Sketch.ino.bin"
        self.image_bytes = b"SYNTHETIC-NOT-FIRMWARE"
        self.image.write_bytes(self.image_bytes)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_primary_read_error_is_preserved_when_image_close_raises(self) -> None:
        real_open = os.open
        real_read = os.read
        real_close = os.close
        image_descriptor: int | None = None
        close_attempts: list[int] = []

        def tracked_open(path, flags, *args, **kwargs):
            nonlocal image_descriptor
            descriptor = real_open(path, flags, *args, **kwargs)
            if os.fspath(path) == "Sketch.ino.bin":
                image_descriptor = descriptor
            return descriptor

        def fail_image_read(descriptor: int, size: int) -> bytes:
            if descriptor == image_descriptor:
                raise OSError("primary image read failure")
            return real_read(descriptor, size)

        def close_with_interruption(descriptor: int) -> None:
            close_attempts.append(descriptor)
            if descriptor == image_descriptor:
                real_close(descriptor)
                raise RuntimeError("simulated image descriptor close interruption")
            real_close(descriptor)

        with patch.object(verifier.os, "open", side_effect=tracked_open), patch.object(
            verifier.os, "read", side_effect=fail_image_read
        ), patch.object(verifier.os, "close", side_effect=close_with_interruption):
            with self.assertRaisesRegex(OSError, "primary image read failure") as raised:
                verifier.inspect_application_image(self.output_dir, "Sketch")

        self.assertIsNotNone(image_descriptor)
        self.assertIn(image_descriptor, close_attempts)
        notes = getattr(raised.exception, "__notes__", [])
        self.assertTrue(
            any("simulated image descriptor close interruption" in note for note in notes),
            "the secondary close failure must remain visible on the primary error",
        )

    def test_parent_directory_close_is_attempted_when_root_close_raises(self) -> None:
        real_open_output_directory = verifier._open_output_directory
        real_close = os.close
        descriptors: dict[str, int] = {}
        close_attempts: list[int] = []

        def tracked_open_output_directory(path):
            result = real_open_output_directory(path)
            descriptors["parent"] = result[1]
            descriptors["root"] = result[2]
            return result

        def close_with_root_interruption(descriptor: int) -> None:
            close_attempts.append(descriptor)
            if descriptor == descriptors.get("root"):
                real_close(descriptor)
                raise RuntimeError("simulated root directory close interruption")
            real_close(descriptor)

        try:
            with patch.object(
                verifier, "_open_output_directory", side_effect=tracked_open_output_directory
            ), patch.object(
                verifier.os, "close", side_effect=close_with_root_interruption
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "simulated root directory close interruption"
                ):
                    verifier.inspect_application_image(self.output_dir, "Sketch")

            self.assertIn(descriptors["root"], close_attempts)
            self.assertIn(
                descriptors["parent"],
                close_attempts,
                "parent descriptor must still receive a close attempt after root close fails",
            )
        finally:
            # The current implementation skips this close when root close raises.
            if "parent" in descriptors and descriptors["parent"] not in close_attempts:
                real_close(descriptors["parent"])

    def test_single_synthetic_image_returns_exact_size_and_digest(self) -> None:
        filename, size, digest = verifier.inspect_application_image(
            self.output_dir, "Sketch"
        )
        self.assertEqual(filename, "Sketch.ino.bin")
        self.assertEqual(size, len(self.image_bytes))
        self.assertEqual(digest, hashlib.sha256(self.image_bytes).hexdigest())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ApplicationImageDescriptorCleanupTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(f"RELEASE-ESP32-IMAGE-ADMISSION-PASS: {result.testsRun} tests")
        raise SystemExit(0)
    raise SystemExit(1)
