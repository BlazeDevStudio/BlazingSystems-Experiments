#!/usr/bin/env python3
"""Regression tests for release-owned ESP32 ELF symbol attribution."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HELPER = ROOT / "inspect_esp32_elf_symbols.py"

if not HELPER.is_file():
    print(
        "PHX-ESP32-ELF-SYMBOL-RED: missing release-owned ELF symbol inspector",
        file=sys.stderr,
    )
    raise SystemExit(1)

sys.path.insert(0, str(ROOT))
from inspect_esp32_elf_symbols import (  # noqa: E402
    map_address,
    parse_address_spec,
    parse_nm_symbols,
    parse_objdump_sections,
)


SAMPLE_OBJDUMP = """Sections:
Idx Name          Size      VMA       LMA       File off  Algn
  0 .flash.appdesc 00000100  3f400000  3f400000  00001000  2**4
  1 .flash.rodata  00000080  3f400100  3f400100  00001100  2**4
  2 .flash.text    00000020  400d0020  400d0020  00002000  2**2
"""

SAMPLE_NM = """app_desc R 3f400000 00000100
rodata_table R 3f400110 00000020
rodata_alias R 3f400110 00000010
rodata_next R 3f400140 00000008
text_fn T 400d0020 00000020
"""


class ElfSymbolParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sections = parse_objdump_sections(SAMPLE_OBJDUMP)
        self.symbols = parse_nm_symbols(SAMPLE_NM)

    def test_parses_posix_nm_name_type_value_size(self) -> None:
        self.assertEqual(len(self.symbols), 5)
        self.assertEqual(
            self.symbols[1],
            {
                "name": "rodata_alias",
                "type": "R",
                "value": 0x3F400110,
                "size": 0x10,
            },
        )

    def test_maps_all_containing_aliases_inside_flash_rodata(self) -> None:
        result = map_address(self.sections, self.symbols, 0x3F400115)
        self.assertEqual(result["status"], "CONTAINED")
        self.assertEqual(result["section"]["name"], ".flash.rodata")
        self.assertEqual(
            {item["name"] for item in result["containing_symbols"]},
            {"rodata_table", "rodata_alias"},
        )
        self.assertEqual(
            {item["offset"] for item in result["containing_symbols"]},
            {5},
        )

    def test_symbol_ranges_are_half_open_and_report_nearest_predecessor(self) -> None:
        result = map_address(self.sections, self.symbols, 0x3F400130)
        self.assertEqual(result["status"], "NEAREST_ONLY")
        self.assertEqual(result["containing_symbols"], [])
        self.assertEqual(
            {item["name"] for item in result["nearest_preceding"]},
            {"rodata_table", "rodata_alias"},
        )
        self.assertEqual({item["distance"] for item in result["nearest_preceding"]}, {0x20})

    def test_exact_next_symbol_is_contained(self) -> None:
        result = map_address(self.sections, self.symbols, 0x3F400140)
        self.assertEqual(result["status"], "CONTAINED")
        self.assertEqual(
            [item["name"] for item in result["containing_symbols"]],
            ["rodata_next"],
        )

    def test_symbols_outside_selected_section_are_not_candidates(self) -> None:
        result = map_address(self.sections, self.symbols, 0x3F4000F0)
        self.assertEqual(result["status"], "ADDRESS_NOT_IN_SECTION")
        self.assertEqual(result["containing_symbols"], [])
        self.assertEqual(result["nearest_preceding"], [])

    def test_lma_symbols_map_to_the_same_section_relative_offset(self) -> None:
        objdump = """Sections:
Idx Name          Size      VMA       LMA       File off  Algn
  0 .flash.rodata  00000080  3f400100  3f800100  00001100  2**4
"""
        nm = "lma_table R 3f800110 00000020\n"
        result = map_address(
            parse_objdump_sections(objdump),
            parse_nm_symbols(nm),
            0x3F800115,
        )
        self.assertEqual(result["status"], "CONTAINED")
        self.assertEqual(result["section"]["basis"], "LMA")
        self.assertEqual(result["containing_symbols"][0]["offset"], 5)

    def test_unknown_size_is_only_a_nearest_predecessor(self) -> None:
        symbols = parse_nm_symbols("unknown_size R 3f400110 ?\n")
        result = map_address(self.sections, symbols, 0x3F400110)
        self.assertEqual(result["status"], "NEAREST_ONLY")
        self.assertIsNone(result["nearest_preceding"][0]["size"])
        self.assertEqual(result["nearest_preceding"][0]["distance"], 0)

    def test_accepts_posix_nm_row_without_size_field(self) -> None:
        symbols = parse_nm_symbols("zero_addr a 0\n")
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0]["name"], "zero_addr")
        self.assertEqual(symbols[0]["value"], 0)
        self.assertIsNone(symbols[0]["size"])

    def test_rejects_malformed_and_out_of_range_symbol_rows(self) -> None:
        for output in (
            "not a POSIX nm row\n",
            "bad_type TOO_LONG 3f400110 00000010\n",
            "overflow R 100000000 00000001\n",
            "overflow_size R 3f400110 100000000\n",
        ):
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    parse_nm_symbols(output)

    def test_rejects_empty_symbol_tables_and_bad_address_specs(self) -> None:
        with self.assertRaises(ValueError):
            parse_nm_symbols("\n")
        self.assertEqual(
            parse_address_spec("segment0=0x3f400115"),
            {"label": "segment0", "address": 0x3F400115},
        )
        for invalid in ("=0x10", "bad label=0x10", "segment0=xyz", "segment0=-1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    parse_address_spec(invalid)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ElfSymbolParserTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("PHX-ESP32-ELF-SYMBOL-TESTS-PASS: 10 synthetic nm/section/address attribution cases")
        raise SystemExit(0)
    raise SystemExit(1)
