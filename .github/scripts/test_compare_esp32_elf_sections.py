#!/usr/bin/env python3
"""Synthetic regression tests for exact ESP32 ELF section-byte comparison."""
from __future__ import annotations

import sys
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from compare_esp32_elf_sections import compare_section_bytes  # noqa: E402
from inspect_esp32_elf_sections import parse_objdump_sections  # noqa: E402


FIRST_OBJDUMP = """Sections:
Idx Name          Size      VMA       LMA       File off  Algn
  0 .flash.appdesc 00000008  3f4000a0  3f4000a0  00000010  2**4
  1 .flash.rodata  00000008  3f4000a8  3f4000a8  00000020  2**4
"""
SECOND_OBJDUMP = """Sections:
Idx Name          Size      VMA       LMA       File off  Algn
  0 .flash.appdesc 00000008  3f4000a0  3f4000a0  00000030  2**4
  1 .flash.rodata  00000008  3f4000a8  3f4000a8  00000040  2**4
"""


class ElfSectionByteComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.first_sections = parse_objdump_sections(FIRST_OBJDUMP)
        self.second_sections = parse_objdump_sections(SECOND_OBJDUMP)
        self.first_elf = bytearray(0x80)
        self.second_elf = bytearray(0x80)
        self.first_elf[0x10:0x18] = b"12345678"
        self.second_elf[0x30:0x38] = b"12345678"
        self.first_elf[0x20:0x28] = b"ABCDEFGH"
        self.second_elf[0x40:0x48] = b"ABCDEFGH"

    def test_identical_section_content_with_different_elf_file_offsets(self) -> None:
        result = compare_section_bytes(
            bytes(self.first_elf), bytes(self.second_elf),
            self.first_sections, self.second_sections, ".flash.rodata",
        )
        self.assertEqual(result["status"], "IDENTICAL")
        self.assertEqual(result["differing_bytes"], 0)
        self.assertEqual(result["difference_ranges"], [])
        self.assertEqual(result["first_file_offset"], 0x20)
        self.assertEqual(result["second_file_offset"], 0x40)

    def test_reports_exact_ranges_for_different_section_content(self) -> None:
        self.second_elf[0x40:0x48] = b"ABxDEFGy"
        result = compare_section_bytes(
            bytes(self.first_elf), bytes(self.second_elf),
            self.first_sections, self.second_sections, ".flash.rodata",
        )
        self.assertEqual(result["status"], "DIFFERENT")
        self.assertEqual(result["differing_bytes"], 2)
        self.assertEqual(
            result["difference_ranges"],
            [
                {
                    "start": 2, "end": 2,
                    "first_elf_offset": 0x22, "second_elf_offset": 0x42,
                    "first_bytes_prefix": "43", "second_bytes_prefix": "78",
                    "bytes_prefix_truncated": False,
                },
                {
                    "start": 7, "end": 7,
                    "first_elf_offset": 0x27, "second_elf_offset": 0x47,
                    "first_bytes_prefix": "48", "second_bytes_prefix": "79",
                    "bytes_prefix_truncated": False,
                },
            ],
        )


    def test_reports_time_candidates_without_neighboring_text(self) -> None:
        first_payload = b"label=build;time=29:39:32;secret=ABCD"
        second_payload = b"label=build;time=30:02:20;secret=WXYZ"
        first_elf = bytearray(0x100)
        second_elf = bytearray(0x100)
        first_elf[0x20:0x20 + len(first_payload)] = first_payload
        second_elf[0x60:0x60 + len(second_payload)] = second_payload
        first_sections = [{
            "name": ".flash.rodata", "size": len(first_payload),
            "vma": 0x3F400120, "lma": 0x3F400120, "file_offset": 0x20,
        }]
        second_sections = [{
            "name": ".flash.rodata", "size": len(second_payload),
            "vma": 0x3F400120, "lma": 0x3F400120, "file_offset": 0x60,
        }]

        result = compare_section_bytes(
            bytes(first_elf), bytes(second_elf),
            first_sections, second_sections, ".flash.rodata",
        )
        contexts = result["difference_context"]
        first_candidates = {
            value for item in contexts for value in item["first_time_candidates"]
        }
        second_candidates = {
            value for item in contexts for value in item["second_time_candidates"]
        }
        self.assertIn("29:39:32", first_candidates)
        self.assertIn("30:02:20", second_candidates)
        self.assertNotIn("ABCD", repr(result))
        self.assertNotIn("WXYZ", repr(result))
        self.assertTrue(all(item["window_bytes"] <= 64 for item in contexts))

    def test_time_candidate_scan_does_not_expose_plain_numeric_tokens(self) -> None:
        first_payload = b"build=1234567890"
        second_payload = b"build=2234567890"
        first_elf = bytearray(0x80)
        second_elf = bytearray(0x80)
        first_elf[0x20:0x20 + len(first_payload)] = first_payload
        second_elf[0x40:0x40 + len(second_payload)] = second_payload
        first_sections = [{
            "name": ".flash.rodata", "size": len(first_payload),
            "vma": 0x3F400120, "lma": 0x3F400120, "file_offset": 0x20,
        }]
        second_sections = [{
            "name": ".flash.rodata", "size": len(second_payload),
            "vma": 0x3F400120, "lma": 0x3F400120, "file_offset": 0x40,
        }]

        result = compare_section_bytes(
            bytes(first_elf), bytes(second_elf),
            first_sections, second_sections, ".flash.rodata",
        )
        self.assertTrue(result["difference_context"])
        self.assertTrue(all(not item["first_time_candidates"] for item in result["difference_context"]))
        self.assertTrue(all(not item["second_time_candidates"] for item in result["difference_context"]))

    def test_difference_context_is_bounded_for_large_drift(self) -> None:
        first_payload = b"A" * 96
        second_payload = b"B" * 96
        first_elf = bytearray(0x100)
        second_elf = bytearray(0x100)
        first_elf[0x20:0x20 + len(first_payload)] = first_payload
        second_elf[0x60:0x60 + len(second_payload)] = second_payload
        first_sections = [{
            "name": ".flash.rodata", "size": len(first_payload),
            "vma": 0x3F400120, "lma": 0x3F400120, "file_offset": 0x20,
        }]
        second_sections = [{
            "name": ".flash.rodata", "size": len(second_payload),
            "vma": 0x3F400120, "lma": 0x3F400120, "file_offset": 0x60,
        }]

        result = compare_section_bytes(
            bytes(first_elf), bytes(second_elf),
            first_sections, second_sections, ".flash.rodata",
        )
        self.assertEqual(len(result["difference_context"]), 1)
        context = result["difference_context"][0]
        self.assertLessEqual(context["window_bytes"], 64)
        self.assertTrue(context["window_truncated"])

    def test_difference_range_storage_is_bounded_for_many_disjoint_changes(self) -> None:
        section_size = 32768
        first_elf = bytearray(0x20 + section_size)
        second_elf = bytearray(0x20 + section_size)
        second_elf[0x20:0x20 + section_size] = bytes(
            1 if index % 2 == 0 else 0 for index in range(section_size)
        )
        first_bytes = bytes(first_elf)
        second_bytes = bytes(second_elf)
        sections = [{
            "name": ".flash.rodata",
            "size": section_size,
            "vma": 0x3F400120,
            "lma": 0x3F400120,
            "file_offset": 0x20,
        }]

        tracemalloc.start()
        try:
            result = compare_section_bytes(
                first_bytes, second_bytes, sections, sections, ".flash.rodata"
            )
            _, peak_bytes = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

        expected_ranges = section_size // 2
        self.assertEqual(result["difference_range_count"], expected_ranges)
        self.assertEqual(result["differing_bytes"], expected_ranges)
        self.assertEqual(len(result["difference_ranges"]), 64)
        self.assertTrue(result["difference_ranges_truncated"])
        self.assertLess(
            peak_bytes,
            1_000_000,
            f"comparison retained unbounded difference-range details: {peak_bytes} bytes",
        )

    def test_reports_app_descriptor_section_separately(self) -> None:
        self.second_elf[0x34] = ord("x")
        result = compare_section_bytes(
            bytes(self.first_elf), bytes(self.second_elf),
            self.first_sections, self.second_sections, ".flash.appdesc",
        )
        self.assertEqual(result["status"], "DIFFERENT")
        self.assertEqual(result["differing_bytes"], 1)
        self.assertEqual(result["difference_ranges"][0]["start"], 4)
        self.assertEqual(result["first_file_offset"], 0x10)
        self.assertEqual(result["second_file_offset"], 0x30)

    def test_rejects_missing_section(self) -> None:
        with self.assertRaises(ValueError):
            compare_section_bytes(
                bytes(self.first_elf), bytes(self.second_elf),
                self.first_sections, [], ".flash.rodata",
            )

    def test_rejects_duplicate_section_name(self) -> None:
        duplicate = self.first_sections + [dict(self.first_sections[1], index=2)]
        with self.assertRaises(ValueError):
            compare_section_bytes(
                bytes(self.first_elf), bytes(self.second_elf),
                duplicate, self.second_sections, ".flash.rodata",
            )

    def test_rejects_layout_mismatch(self) -> None:
        changed = [dict(section) for section in self.second_sections]
        changed[1]["size"] = 7
        with self.assertRaises(ValueError):
            compare_section_bytes(
                bytes(self.first_elf), bytes(self.second_elf),
                self.first_sections, changed, ".flash.rodata",
            )

    def test_rejects_truncated_second_section(self) -> None:
        with self.assertRaises(ValueError):
            compare_section_bytes(
                bytes(self.first_elf), bytes(self.second_elf[:0x44]),
                self.first_sections, self.second_sections, ".flash.rodata",
            )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ElfSectionByteComparisonTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(f"PHX-ESP32-ELF-SECTION-COMPARE-TESTS-PASS: {result.testsRun} synthetic cases")
        raise SystemExit(0)
    raise SystemExit(1)
