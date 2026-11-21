"""Regression checks for the live Phoenix poll/response architecture contract.

Run:
    python3 -m unittest discover -s coordination/phoenix -p 'test_architecture_contracts.py' -v

These tests guard coordination documentation; they do not replace firmware or QA tests.
"""
from pathlib import Path
import unittest

DOC = (Path(__file__).with_name("ARCHITECTURE_CONTRACTS.md")
       .read_text(encoding="utf-8"))


def between(start: str, end: str) -> str:
    first = DOC.index(start)
    last = DOC.index(end, first)
    return DOC[first:last]


class PollResponseArchitectureTests(unittest.TestCase):
    def test_section_22_records_current_deny_only_state(self):
        section = between("### 2.2 Client-side response trust boundary",
                          "### 2.3 Swallowed Coin Quarantine")
        self.assertIn("request tuple", section)
        self.assertIn("do not include `response_sig`", section)
        self.assertIn("hard-deny", section)
        self.assertNotIn("MUST verify `response_sig` returned", section)

    def test_old_section_63_is_explicitly_historical(self):
        section = between("### 6.3 Historical poll producer/consumer comparison",
                          "### 6.4 Remote configuration")
        self.assertIn("historical", section.lower())
        self.assertIn("current #323 deny-only candidate", section)

    def test_live_section_pins_source_and_destination_blobs(self):
        section = DOC[DOC.index("## 6.23 Exact poll response producer/consumer reconciliation"):]
        self.assertIn("not standard HMAC", section)
        for sha in (
            "a1c19180385e618c412b4af21c0e91c1f47da1dd",
            "0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e",
            "8e79b9eb8856e67d966f4c6385f89fccdc8be7fc",
            "bd74b11c1496b0943404ff387ee72bb45d4743e5",
            "c13dfb8d9b7ae83c15aa97c94842c339db8b8584",
        ):
            with self.subTest(sha=sha):
                self.assertIn(sha, section)

    def test_legacy_fixture_failure_is_not_an_admission_requirement(self):
        section = DOC[DOC.index("## 6.23 Exact poll response producer/consumer reconciliation"):]
        self.assertIn("v05_firmware_hardening_test.sh", section)
        self.assertIn("does not test the current intentional deny-only behavior", section)
        self.assertIn("PHX-QA", section)
        self.assertIn("negative behavior tests", section)

    def test_production_gate_remains_closed(self):
        section = DOC[DOC.index("## 6.23 Exact poll response producer/consumer reconciliation"):]
        self.assertIn("PRODUCTION NO-GO", section)
        self.assertIn("150 real power cuts", section)
        self.assertIn("30-device/24-hour soak", section)


    def test_hardware_323_destination_is_not_copy_ready(self):
        section = DOC[DOC.index("## 6.24 Current HARDWARE #323 to COE #26 provenance and test-identity hold"):]
        for sha in (
            "bd74b11c1496b0943404ff387ee72bb45d4743e5",
            "3cc7ec54b476943dc04a8d1af5e2df5fe054e422",
            "8e79b9eb8856e67d966f4c6385f89fccdc8be7fc",
            "c8be98f72596681e36a3ad1f8939bf8046c96887",
            "25f5e8bd1a344d69acc0505324156f66a1abffa4",
        ):
            with self.subTest(sha=sha):
                self.assertIn(sha, section)
        self.assertIn("not standard HMAC", section)
        self.assertIn("No copy/move", section)
        self.assertIn("PRODUCTION NO-GO", section)


    def test_ula_identity_is_site_scoped_not_per_appliance(self):
        section = between(
            "## 6.9 ULA prefix is installation identity, not hardware profile",
            "## 6.10 ImageBuilder build execution must actually be sandboxed — 2026-11-17 UTC13",
        )
        self.assertIn("installation means the LAN/site identity boundary", section)
        self.assertIn("per-appliance first-boot random generator is therefore a local allocation primitive only", section)
        self.assertIn("Two appliance instances attached to one site receive the same prefix", section)
        self.assertIn("Two independent sites receive distinct prefixes", section)
        self.assertIn("Concurrent first-boot attempts converge on one durable value or fail closed", section)


    def test_poll_fault_edge_count_is_first_latch_lower_bound(self):
        section = DOC[DOC.index("## 6.50 Poll-fault pulseEdges is a first-latch lower bound"):]
        for required in (
            "first-fault snapshot",
            "lower bound",
            "not an exact total",
            "never use this field to credit time",
            "no explicit completeness flag",
            "64ec57daf161a0b4517d350f4f08bee55c0cabec",
        ):
            with self.subTest(required=required):
                self.assertIn(required, section)

    def test_no_unreviewed_top_level_section_number_collisions(self):
        import re

        counts = {}
        for line in DOC.splitlines():
            match = re.match(r"^##\s+(?:§\s*)?(6\.\d+)\b", line)
            if match:
                number = match.group(1)
                counts[number] = counts.get(number, 0) + 1

        collisions = {number for number, count in counts.items() if count > 1}
        reviewed_legacy_collisions = {"6.9", "6.10", "6.11", "6.25", "6.38"}
        unexpected = collisions - reviewed_legacy_collisions
        self.assertFalse(
            unexpected,
            f"Unreviewed top-level architecture section-number collision(s): {sorted(unexpected)}",
        )


    def test_reviewed_legacy_section_collisions_are_exactly_two_each(self):
        import re

        counts = {}
        for line in DOC.splitlines():
            match = re.match(r"^##\\s+(?:§\\s*)?(6\\.\\d+)\\b", line)
            if match:
                number = match.group(1)
                counts[number] = counts.get(number, 0) + 1

        expected = {"6.9": 2, "6.10": 2, "6.11": 2, "6.25": 2, "6.38": 2}
        actual = {number: count for number, count in counts.items() if count > 1}
        self.assertEqual(
            actual,
            expected,
            "Reviewed legacy collision inventory changed; re-review historical references before changing the allowlist.",
        )

if __name__ == "__main__":
    unittest.main()
