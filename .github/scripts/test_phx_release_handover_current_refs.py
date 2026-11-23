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


def _section_after_marker(content: str, marker: str) -> str:
    if marker not in content:
        return ""
    return content.split(marker, 1)[1].split("\n## ", 1)[0]


def _utc20_section(content: str) -> str:
    return _section_after_marker(content, UTC20_MARKER)


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

    def test_utc20_section_stops_at_next_heading(self):
        sample = f"{UTC20_MARKER}\nkeep-this\n## NEXT SECTION\nleaked-sentinel"
        self.assertEqual(_utc20_section(sample), "\nkeep-this")


UTC21_MARKER = "## PHX-RELEASE UTC21 — exact live refs and CI reconciliation"
MASTER288_HEAD_UTC21 = "5c5988e43d3f392c31117fa34bf7bb49bcc02fc3"
OWNERSHIP_ROUTES_BLOB_UTC21 = "e4db324315a1b3543fec17a148fbf960170fcb29"
PR242_HEAD_UTC21 = "734b89d9e7792247e8376335c3f3685500ab3f89"
PR291_OBSERVED_HEAD_UTC21 = "6d4a95edeeaa57c47ea6c897ad53f17b9fb4396a"
PR291_BASE_SHA_UTC21 = "734b89d9e7792247e8376335c3f3685500ab3f89"
COE26_HEAD_UTC21 = "b382d233ff06c8791b1028bed3c617cc7b670d12"
COE26_BASE_SHA_UTC21 = "a6513ab4412b4c014eee2863e45cbe32d06cb243"
COE31_HEAD_UTC21 = "59ed44d0b911e176f1a95b9cf5585ef811ffd31b"
COE31_BASE_SHA_UTC21 = "b382d233ff06c8791b1028bed3c617cc7b670d12"
COE35_HEAD_UTC21 = "edb4eb482dfa94bbad2dcf29b90b8463a2165fa5"
COE35_BASE_SHA_UTC21 = "59ed44d0b911e176f1a95b9cf5585ef811ffd31b"


def _utc21_section(content: str) -> str:
    return _section_after_marker(content, UTC21_MARKER)


class ReleaseHandoverUTC21CurrentRefsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = HANDOVER.read_text(encoding="utf-8")
        cls.section = _utc21_section(cls.content)

    def test_utc21_section_exists_and_is_not_empty(self):
        self.assertIn(UTC21_MARKER, self.content)
        self.assertTrue(self.section)

    def test_master_head_and_review_only_route_are_pinned(self):
        self.assertIn(MASTER288_HEAD_UTC21, self.section)
        self.assertIn(OWNERSHIP_ROUTES_BLOB_UTC21, self.section)
        self.assertIn("DRAFT_REVIEW_ONLY", self.section)
        self.assertIn("reimplementation-review", self.section)

    def test_release_and_coe_refs_are_pinned(self):
        for ref in (
            PR242_HEAD_UTC21,
            PR291_OBSERVED_HEAD_UTC21,
            PR291_BASE_SHA_UTC21,
            COE26_HEAD_UTC21,
            COE26_BASE_SHA_UTC21,
            COE31_HEAD_UTC21,
            COE31_BASE_SHA_UTC21,
            COE35_HEAD_UTC21,
            COE35_BASE_SHA_UTC21,
        ):
            with self.subTest(ref=ref):
                self.assertIn(ref, self.section)

    def test_exact_ci_outcomes_are_recorded(self):
        for evidence in (
            "45065978550",
            "45065978506",
            "45065978523",
            "45054914749",
            "45054914752",
            "45054914784",
            "44222517263",
            "40882814472",
            "190 PASS / 2 intentional skips",
            "37/37 host-preflight tests PASS",
            "10/10 appliance profiles",
        ):
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, self.section)

    def test_mixed_owner_paths_are_not_claimed_as_release_owned(self):
        self.assertIn("27 accumulated changed paths", self.section)
        self.assertIn("22 RELEASE / 3 CORE / 2 PISONET", self.section)
        self.assertIn("No inherited CORE/PISONET path was edited", self.section)

    def test_release_gate_and_private_registry_limit_are_explicit(self):
        self.assertIn("PRODUCTION NO-GO", self.section)
        self.assertIn("registry v11", self.section)
        self.assertIn("not available", self.section.lower())
        self.assertIn("150 physical power cuts", self.section)
        self.assertIn("30-device/24-hour soak", self.section)

    def test_utc21_section_stops_at_next_heading(self):
        sample = f"{UTC21_MARKER}\nkeep-this\n## NEXT SECTION\nleaked-sentinel"
        self.assertEqual(_utc21_section(sample), "\nkeep-this")



UTC00_MARKER = "## PHX-RELEASE UTC00 — live exact refs and CI reconciliation"
MASTER288_HEAD_UTC00 = "d1cb7dfe8cac0c491c424a1ea24769be220b98e2"
OWNERSHIP_ROUTES_BLOB_UTC00 = "e4db324315a1b3543fec17a148fbf960170fcb29"
PR242_HEAD_UTC00 = "734b89d9e7792247e8376335c3f3685500ab3f89"
PR291_PRE_APPEND_HEAD_UTC00 = "cb5e5450a4fc2afc7f38cf426e51b390859a1dd0"
PR291_BASE_SHA_UTC00 = "734b89d9e7792247e8376335c3f3685500ab3f89"
COE26_HEAD_UTC00 = "b382d233ff06c8791b1028bed3c617cc7b670d12"
COE26_BASE_SHA_UTC00 = "a6513ab4412b4c014eee2863e45cbe32d06cb243"
COE31_HEAD_UTC00 = "59ed44d0b911e176f1a95b9cf5585ef811ffd31b"
COE31_BASE_SHA_UTC00 = "b382d233ff06c8791b1028bed3c617cc7b670d12"
COE35_HEAD_UTC00 = "16c0e140cbfd52d4cb572b7121189866763c77b2"
COE35_BASE_SHA_UTC00 = "59ed44d0b911e176f1a95b9cf5585ef811ffd31b"


def _utc00_section(content: str) -> str:
    return _section_after_marker(content, UTC00_MARKER)


class ReleaseHandoverUTC00CurrentRefsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = HANDOVER.read_text(encoding="utf-8")
        cls.section = _utc00_section(cls.content)

    def test_utc00_section_exists_and_is_not_empty(self):
        self.assertIn(UTC00_MARKER, self.content)
        self.assertTrue(self.section)

    def test_master_head_and_review_only_route_are_pinned(self):
        self.assertIn(MASTER288_HEAD_UTC00, self.section)
        self.assertIn(OWNERSHIP_ROUTES_BLOB_UTC00, self.section)
        self.assertIn("DRAFT_REVIEW_ONLY", self.section)
        self.assertIn("reimplementation-review", self.section)

    def test_release_and_coe_refs_are_pinned_to_their_observed_bases(self):
        for ref in (
            PR242_HEAD_UTC00,
            PR291_PRE_APPEND_HEAD_UTC00,
            PR291_BASE_SHA_UTC00,
            COE26_HEAD_UTC00,
            COE26_BASE_SHA_UTC00,
            COE31_HEAD_UTC00,
            COE31_BASE_SHA_UTC00,
            COE35_HEAD_UTC00,
            COE35_BASE_SHA_UTC00,
        ):
            with self.subTest(ref=ref):
                self.assertIn(ref, self.section)

    def test_exact_release_ci_outcomes_and_fail_closed_limits_are_recorded(self):
        for evidence in (
            "45071305854",
            "45071305811",
            "45071305891",
            "45082913881",
            "45082913844",
            "45082913966",
            "40882814472",
            "17/17 handover tests PASS",
            "14/14 target/platform jobs passed",
            "38/38 host-preflight tests PASS",
            "191 PASS / 2 intentional skips",
            "10/10 appliance profiles",
            "exit 125",
            "SKIPPED",
        ):
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, self.section)

    def test_mixed_owner_paths_are_not_claimed_as_release_owned(self):
        self.assertIn("27 accumulated paths", self.section)
        self.assertIn("22 RELEASE / 3 CORE / 2 PISONET", self.section)
        self.assertIn("No inherited CORE or PISONET path was changed by this task", self.section)

    def test_integration_and_provenance_blockers_remain_explicit(self):
        self.assertIn("five workflows queued", self.section)
        self.assertIn("zero jobs executed", self.section)
        self.assertIn("registry v11", self.section)
        self.assertIn("not available", self.section.lower())
        self.assertIn("Cleanup-first issue #266 remains OPEN", self.section)
        self.assertIn("0/7", self.section)

    def test_production_gate_remains_no_go(self):
        self.assertIn("PRODUCTION NO-GO", self.section)
        self.assertIn("150 physical power cuts", self.section)
        self.assertIn("30-device/24-hour soak", self.section)

    def test_utc00_section_stops_at_next_heading(self):
        sample = f"{UTC00_MARKER}\nkeep-this\n## NEXT SECTION\nleaked-sentinel"
        self.assertEqual(_utc00_section(sample), "\nkeep-this")

if __name__ == "__main__":
    unittest.main(verbosity=2)
