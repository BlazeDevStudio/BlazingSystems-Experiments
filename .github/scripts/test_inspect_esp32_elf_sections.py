#!/usr/bin/env python3
"""Regression tests for the release-owned Xtensa ELF section mapper."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HELPER = ROOT / "inspect_esp32_elf_sections.py"

if not HELPER.is_file():
    print(
        "PHX-ESP32-ELF-SECTION-RED: missing release-owned ELF section inspector",
        file=sys.stderr,
    )
    raise SystemExit(1)

sys.path.insert(0, str(ROOT))
from inspect_esp32_elf_sections import map_address, parse_address_spec, parse_objdump_sections  # noqa: E402


SAMPLE_OBJDUMP = """Sections:
Idx Name          Size      VMA       LMA       File off  Algn
  0 .flash.text   00000010  400d0020  400d0020  00001000  2**4
                  CONTENTS, ALLOC, LOAD, READONLY, CODE
  1 .dram0.data   00000008  3f400020  3f800020  00002000  2**2
                  CONTENTS, ALLOC, LOAD, DATA
"""


class ElfSectionParserTests(unittest.TestCase):
    def test_parses_vma_lma_and_file_offset(self) -> None:
        sections = parse_objdump_sections(SAMPLE_OBJDUMP)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0]["name"], ".flash.text")
        self.assertEqual(sections[0]["size"], 0x10)
        self.assertEqual(sections[0]["vma"], 0x400D0020)
        self.assertEqual(sections[0]["lma"], 0x400D0020)
        self.assertEqual(sections[0]["file_offset"], 0x1000)

    def test_maps_vma_lma_and_half_open_end(self) -> None:
        sections = parse_objdump_sections(SAMPLE_OBJDUMP)
        vma = map_address(sections, 0x400D0025)
        lma = map_address(sections, 0x3F800023)
        boundary = map_address(sections, 0x3F800028)
        self.assertEqual([(item["name"], item["basis"], item["offset"]) for item in vma],
                         [(".flash.text", "VMA/LMA", 5)])
        self.assertEqual([(item["name"], item["basis"], item["offset"]) for item in lma],
                         [(".dram0.data", "LMA", 3)])
        self.assertEqual(boundary, [])

    def test_reports_overlapping_address_candidates(self) -> None:
        output = SAMPLE_OBJDUMP + (
            "  2 .overlay      00000010  400d0020  500d0020  00003000  2**4\n"
        )
        matches = map_address(parse_objdump_sections(output), 0x400D0028)
        self.assertEqual({item["name"] for item in matches}, {".flash.text", ".overlay"})

    def test_rejects_duplicate_section_indexes(self) -> None:
        output = SAMPLE_OBJDUMP + (
            "  1 .duplicate    00000008  50000000  50000000  00004000  2**2\n"
        )
        with self.assertRaises(ValueError):
            parse_objdump_sections(output)

    def test_rejects_output_without_section_rows(self) -> None:
        with self.assertRaises(ValueError):
            parse_objdump_sections("There are no sections in this file.\n")

    def test_parses_and_rejects_address_specs(self) -> None:
        self.assertEqual(
            parse_address_spec("segment0=0x3f4025c4"),
            {"label": "segment0", "address": 0x3F4025C4},
        )
        for invalid in ("=0x10", "bad label=0x10", "segment0=xyz", "segment0=-1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    parse_address_spec(invalid)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ElfSectionParserTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("PHX-ESP32-ELF-SECTION-TESTS-PASS: 6 synthetic parser and address-mapping cases")
        raise SystemExit(0)
    raise SystemExit(1)
