#!/usr/bin/env python3
"""Synthetic tests for ESP32 compile-time date/time reproducibility verification."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from verify_esp32_source_date_epoch import (  # noqa: E402
    expected_compile_metadata,
    inspect_core_time_source,
    parse_macro_output,
    parse_source_date_epoch,
)


class Esp32SourceDateEpochTests(unittest.TestCase):
    def test_epoch_requires_nonnegative_decimal_seconds(self) -> None:
        self.assertEqual(parse_source_date_epoch("946684800"), 946684800)
        for value in ("", "-1", "+1", "1.0", "1 2", "epoch"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_source_date_epoch(value)

    def test_expected_metadata_uses_utc_and_c_locale_format(self) -> None:
        self.assertEqual(
            expected_compile_metadata(946684800),
            {"date": "Jan  1 2000", "time": "00:00:00"},
        )
        self.assertEqual(
            expected_compile_metadata(946684860),
            {"date": "Jan  1 2000", "time": "00:01:00"},
        )

    def test_finds_core_compile_time_metadata_source_and_live_call(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            core_root = Path(temporary)
            esp32 = core_root / "cores" / "esp32"
            esp32.mkdir(parents=True)
            (esp32 / "chip-debug-report.cpp").write_text(
                'chip_report_printf("Compile Date/Time: %s %s\\n", __DATE__, __TIME__);\n',
                encoding="utf-8",
            )
            (esp32 / "main.cpp").write_text(
                "void loopTask() { printBeforeSetupInfo(); }\n",
                encoding="utf-8",
            )
            result = inspect_core_time_source(core_root)
            self.assertEqual(result["source_path"], "cores/esp32/chip-debug-report.cpp")
            self.assertEqual(result["source_lines"], [1])
            self.assertEqual(result["main_reference_lines"], [1])

    def test_rejects_core_without_both_date_and_time_macros(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            core_root = Path(temporary)
            esp32 = core_root / "cores" / "esp32"
            esp32.mkdir(parents=True)
            (esp32 / "chip-debug-report.cpp").write_text(
                'chip_report_printf("Compile Date: %s\\n", __DATE__);\n',
                encoding="utf-8",
            )
            (esp32 / "main.cpp").write_text(
                "void loopTask() { printBeforeSetupInfo(); }\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                inspect_core_time_source(core_root)

    def test_parses_only_the_two_named_macro_values(self) -> None:
        output = (
            'const char phx_compile_date[] = "Jan  1 2000";\n'
            'const char phx_compile_time[] = "00:00:00";\n'
        )
        self.assertEqual(
            parse_macro_output(output),
            {"date": "Jan  1 2000", "time": "00:00:00"},
        )

    def test_rejects_missing_or_duplicate_macro_output(self) -> None:
        with self.assertRaises(ValueError):
            parse_macro_output('const char phx_compile_date[] = "Jan  1 2000";\n')
        with self.assertRaises(ValueError):
            parse_macro_output(
                'const char phx_compile_date[] = "Jan  1 2000";\n'
                'const char phx_compile_date[] = "Jan  1 2000";\n'
                'const char phx_compile_time[] = "00:00:00";\n'
            )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Esp32SourceDateEpochTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(f"PHX-ESP32-SOURCE-DATE-EPOCH-TESTS-PASS: {result.testsRun} synthetic cases")
        raise SystemExit(0)
    raise SystemExit(1)
