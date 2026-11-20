#!/usr/bin/env python3
"""Synthetic regression tests for exact ESP32 ELF section-byte comparison."""
from __future__ import annotations

import sys
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
            [{"start": 2, "end": 2}, {"start": 7, "end": 7}],
        )

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
        print("PHX-ESP32-ELF-SECTION-COMPARE-TESTS-PASS: 6 synthetic cases")
        raise SystemExit(0)
    raise SystemExit(1)
