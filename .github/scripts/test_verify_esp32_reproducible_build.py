#!/usr/bin/env python3
"""Failure-injected descriptor cleanup tests for the ESP32 image comparator."""
from __future__ import annotations

import os
import sys
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import verify_esp32_reproducible_build as reproducibility


class ReproducibleImageDescriptorCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        first_dir = root / "first"
        second_dir = root / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        self.first_image = first_dir / "BlazePwifiVendo32.ino.bin"
        self.second_image = second_dir / "BlazePwifiVendo32.ino.bin"
        payload = b"synthetic identical image bytes"
        self.first_image.write_bytes(payload)
        self.second_image.write_bytes(payload)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assert_descriptors_closed(self, descriptors: list[int]) -> None:
        self.assertEqual(len(descriptors), 2, "both owned descriptors must receive a close attempt")
        for descriptor in descriptors:
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_primary_read_error_survives_both_close_failures(self) -> None:
        real_close = os.close
        close_calls: list[int] = []

        def close_then_fail(descriptor: int) -> None:
            close_calls.append(descriptor)
            real_close(descriptor)
            raise OSError(f"injected cleanup failure {len(close_calls)}")

        def fail_read(_descriptor: int, _size: int) -> bytes:
            raise RuntimeError("primary image comparison read failure")

        with patch.object(reproducibility.os, "read", side_effect=fail_read), patch.object(
            reproducibility.os, "close", side_effect=close_then_fail
        ):
            with self.assertRaisesRegex(
                RuntimeError, "primary image comparison read failure"
            ) as raised:
                reproducibility.compare_application_images(
                    self.first_image, self.second_image, "BlazePwifiVendo32"
                )

        self.assert_descriptors_closed(close_calls)
        notes = getattr(raised.exception, "__notes__", [])
        self.assertTrue(any("injected cleanup failure 1" in note for note in notes))
        self.assertTrue(any("injected cleanup failure 2" in note for note in notes))

    def test_cleanup_only_failures_attempt_both_and_raise_first(self) -> None:
        real_close = os.close
        close_calls: list[int] = []

        def close_then_fail(descriptor: int) -> None:
            close_calls.append(descriptor)
            real_close(descriptor)
            raise OSError(f"injected cleanup failure {len(close_calls)}")

        with patch.object(reproducibility.os, "close", side_effect=close_then_fail):
            with self.assertRaisesRegex(OSError, "injected cleanup failure 1") as raised:
                reproducibility.compare_application_images(
                    self.first_image, self.second_image, "BlazePwifiVendo32"
                )

        self.assert_descriptors_closed(close_calls)
        notes = getattr(raised.exception, "__notes__", [])
        self.assertTrue(any("injected cleanup failure 2" in note for note in notes))


    def test_fallback_read_restores_cursor_after_success(self) -> None:
        calls: list[tuple[int, int, int]] = []

        def fake_lseek(descriptor: int, offset: int, whence: int) -> int:
            calls.append((descriptor, offset, whence))
            if len(calls) == 1:
                return 19
            return offset

        fake_os = SimpleNamespace(
            lseek=fake_lseek,
            read=lambda _descriptor, _size: b"fallback bytes",
            SEEK_CUR=os.SEEK_CUR,
            SEEK_SET=os.SEEK_SET,
        )
        with patch.object(reproducibility, "os", fake_os):
            result = reproducibility._read_at(7, 4, 3)

        self.assertEqual(result, b"fallback bytes")
        self.assertEqual(
            calls,
            [
                (7, 0, os.SEEK_CUR),
                (7, 3, os.SEEK_SET),
                (7, 19, os.SEEK_SET),
            ],
        )

    def test_fallback_restore_failure_does_not_mask_primary_read_error(self) -> None:
        calls: list[tuple[int, int, int]] = []

        def fake_lseek(descriptor: int, offset: int, whence: int) -> int:
            calls.append((descriptor, offset, whence))
            if len(calls) == 1:
                return 19
            if len(calls) == 2:
                return offset
            raise OSError("injected cursor restoration failure")

        def fail_read(_descriptor: int, _size: int) -> bytes:
            raise RuntimeError("primary fallback read failure")

        fake_os = SimpleNamespace(
            lseek=fake_lseek,
            read=fail_read,
            SEEK_CUR=os.SEEK_CUR,
            SEEK_SET=os.SEEK_SET,
        )
        with patch.object(reproducibility, "os", fake_os):
            with self.assertRaisesRegex(
                RuntimeError, "primary fallback read failure"
            ) as raised:
                reproducibility._read_at(7, 4, 3)

        self.assertEqual(len(calls), 3)
        notes = getattr(raised.exception, "__notes__", [])
        self.assertTrue(
            any(
                "cursor restoration" in note
                and "injected cursor restoration failure" in note
                for note in notes
            )
        )

    def test_fallback_restore_failure_is_reported_after_successful_read(self) -> None:
        calls: list[tuple[int, int, int]] = []

        def fake_lseek(descriptor: int, offset: int, whence: int) -> int:
            calls.append((descriptor, offset, whence))
            if len(calls) == 1:
                return 19
            if len(calls) == 2:
                return offset
            raise OSError("injected cursor restoration failure")

        fake_os = SimpleNamespace(
            lseek=fake_lseek,
            read=lambda _descriptor, _size: b"fallback bytes",
            SEEK_CUR=os.SEEK_CUR,
            SEEK_SET=os.SEEK_SET,
        )
        with patch.object(reproducibility, "os", fake_os):
            with self.assertRaisesRegex(
                OSError, "injected cursor restoration failure"
            ):
                reproducibility._read_at(7, 4, 3)

        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ReproducibleImageDescriptorCleanupTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(f"PHX-ESP32-REPRODUCIBLE-CLEANUP-PASS: {result.testsRun} tests")
        raise SystemExit(0)
    raise SystemExit(1)
