#!/usr/bin/env python3
"""Guard exact source identity in the PHX-RELEASE handover snapshot."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOVER = ROOT / ".github" / "PHX_RELEASE_HANDOVER.md"
MARKER = "## PHX-RELEASE UTC19 — exact release source and COE head reconciliation"

BAD_TRANSPOSED_SHA = "1851f1d06648beed70695528f2799d57154a69237"
SOURCE_FIX_SHA = "185f1d06648beed70695528f2799d57154a69237"
STARTING_PR291_HEAD = "42797e2f3d65c30a1070caf49c93aebec149d897"
PR291_BASE_SHA = "734b89d9e7792247e8376335c3f3685500ab3f89"
COE35_HEAD = "edb4eb482dfa94bbad2dcf29b90b8463a2165fa5"
COE35_BASE_SHA = "59ed44d0b911e176f1a95b9cf5585ef811ffd31b"


class ReleaseHandoverCurrentRefsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = HANDOVER.read_text(encoding="utf-8")

    def current_section(self):
        self.assertIn(MARKER, self.content, "missing UTC19 exact-ref reconciliation section")
        if MARKER not in self.content:
            return ""
        return self.content.split(MARKER, 1)[1].split("\n## ", 1)[0]

    def test_transposed_nonexistent_source_sha_is_absent(self):
        self.assertNotIn(BAD_TRANSPOSED_SHA, self.content)
        self.assertIn(SOURCE_FIX_SHA, self.content)

    def test_pr291_starting_head_and_base_are_recorded(self):
        section = self.current_section()
        self.assertIn(STARTING_PR291_HEAD, section)
        self.assertIn(PR291_BASE_SHA, section)
        self.assertIn(SOURCE_FIX_SHA, section)

    def test_coe35_current_head_and_parent_are_recorded(self):
        section = self.current_section()
        self.assertIn(COE35_HEAD, section)
        self.assertIn(COE35_BASE_SHA, section)

    def test_snapshot_is_scoped_to_the_latest_utc19_section(self):
        section = self.current_section()
        self.assertTrue(section)
        self.assertIn("PHX-RELEASE", section)
        self.assertIn("COE #35", section)


if __name__ == "__main__":
    unittest.main(verbosity=2)
