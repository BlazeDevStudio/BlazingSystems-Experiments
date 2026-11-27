#!/usr/bin/env python3
"""Synthetic failure-injection tests for the hardware change-ledger guard."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.handover_ledger_append_only_guard import check_append_only


class AppendOnlyLedgerGuardTests(unittest.TestCase):
    def test_accepts_exact_append(self) -> None:
        base = b"historic row one\nhistoric row two\n"
        candidate = base + b"new hardware checkpoint\n"
        self.assertTrue(check_append_only(base, candidate)[0])

    def test_accepts_unchanged_ledger(self) -> None:
        base = b"historic row one\n"
        self.assertTrue(check_append_only(base, base)[0])

    def test_rejects_truncation(self) -> None:
        base = b"historic row one\nhistoric row two\n"
        self.assertFalse(check_append_only(base, b"historic row one\n")[0])

    def test_rejects_middle_edit(self) -> None:
        base = b"historic row one\nhistoric row two\n"
        candidate = b"historic row ONE\nhistoric row two\nnew row\n"
        self.assertFalse(check_append_only(base, candidate)[0])

    def test_rejects_prepended_record(self) -> None:
        base = b"historic row one\n"
        self.assertFalse(check_append_only(base, b"new row\n" + base)[0])

    def test_rejects_empty_base(self) -> None:
        self.assertFalse(check_append_only(b"", b"new row\n")[0])

    def test_rejects_unseparated_append(self) -> None:
        base = b"historic row one"
        self.assertFalse(check_append_only(base, base + b"new row\n")[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
