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
        self.assertIn("Activation", section)
        self.assertIn("COE #35", section)


if __name__ == "__main__":
    unittest.main(verbosity=2)

UTC20_MARKER = "## PHX-RELEASE UTC20 — exact live refs and CI reconciliation"
MASTER288_HEAD = "48d1d3afeb012d4b6fd466a4d6061bfd36210728"
OWNERSHIP_ROUTES_BLOB = "e4db324315a1b3543fec17a148fbf960170fcb29"
PR291_OBSERVED_HEAD = "11063a5bd5c744aef1f8dc6ca5fb4e06d6aa7882"
PR291_BASE_SHA = "734b89d9e7792247e8376335c3f3685500ab3f89"
PR242_HEAD = "734b89d9e7792247e8376335c3f3685500ab3f89"
COE26_HEAD = "b382d233ff06c8791b1028bed3c617cc7b670d12"
COE31_HEAD = "59ed44d0b911e176f1a95b9cf5585ef811ffd31b"
COE35_OBSERVED_HEAD = "edb4eb482dfa94bbad2dcf29b90b8463a2165fa5"
COE35_BASE_SHA = "59ed44d0b911e176f1a95b9cf5585ef811ffd31b"


def _utc20_section(content: str) -> str:
    if UTC20_MARKER not in content:
        return ""
    return content.split(UTC20_MARKER, 1)[1].split("\\n## ", 1)[0]


class ReleaseHandoverUTC20CurrentRefsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = HANDOVER.read_text(encoding="utf-8")
        cls.section = _utc20_section(cls.content)

    def test_utc20_section_exists_and_is_not_empty(self):
        self.assertIn(UTC20_MARKER, self.content)
        self.assertTrue(self.section)

    def test_master_head_and_review_only_route_are_pinned(self):
        self.assertIn(MASTER288_HEAD, self.section)
        self.assertIn(OWNERSHIP_ROUTES_BLOB, self.section)
        self.assertIn("DRAFT_REVIEW_ONLY", self.section)
        self.assertIn("reimplementation-review", self.section)

    def test_experiments_release_heads_and_base_are_pinned(self):
        self.assertIn(PR291_OBSERVED_HEAD, self.section)
        self.assertIn(PR291_BASE_SHA, self.section)
        self.assertIn(PR242_HEAD, self.section)

    def test_coe_integration_parent_and_child_heads_are_pinned(self):
        self.assertIn(COE26_HEAD, self.section)
        self.assertIn(COE31_HEAD, self.section)
        self.assertIn(COE35_OBSERVED_HEAD, self.section)
        self.assertIn(COE35_BASE_SHA, self.section)

    def test_release_gate_and_private_registry_limit_are_explicit(self):
        self.assertIn("PRODUCTION NO-GO", self.section)
        self.assertIn("registry v11", self.section)
        self.assertIn("not available", self.section.lower())
