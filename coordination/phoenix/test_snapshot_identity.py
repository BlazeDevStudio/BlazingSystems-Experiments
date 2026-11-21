#!/usr/bin/env python3
"""Fail-closed snapshot identity regressions for Phoenix routing.

Run from repository root:
    python3 -m unittest discover -s coordination/phoenix -p 'test_*.py' -v

These assertions inspect targeted diagnostics, not overall validation success:
full route validation also requires the historical source tree to be present.
No network, payments, firmware, or hardware access is used.
"""
import copy
import json
import unittest

from verify_coordination import HERE, REPO_ROOT, validate_routes


class SnapshotIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (HERE / "OWNERSHIP_ROUTES.json").read_text(encoding="utf-8")
        )

    def errors_for(self, field, value):
        manifest = copy.deepcopy(self.manifest)
        manifest[field] = value
        return validate_routes(manifest, REPO_ROOT)

    def test_canonical_snapshot_has_no_identity_diagnostics(self):
        errors = validate_routes(self.manifest, REPO_ROOT)
        identity_errors = [
            error for error in errors
            if "full lowercase 40-character Git SHA" in error
            or "repository identity" in error
        ]
        self.assertEqual(identity_errors, [])

    def test_source_sha_rejects_ambiguous_or_malformed_values(self):
        for value in (None, "", "deadbeef", "A" * 40, "g" * 40, 123):
            with self.subTest(value=value):
                self.assertIn(
                    "source_ref must be a full lowercase 40-character Git SHA",
                    self.errors_for("source_ref", value),
                )

    def test_destination_sha_rejects_ambiguous_or_malformed_values(self):
        for value in (None, "", "deadbeef", "F" * 40, "z" * 40, 123):
            with self.subTest(value=value):
                self.assertIn(
                    "destination_candidate_sha must be a full lowercase 40-character Git SHA",
                    self.errors_for("destination_candidate_sha", value),
                )

    def test_source_repository_cannot_be_retargeted(self):
        self.assertIn(
            "Unexpected source repository identity",
            self.errors_for("source_repository", "other-owner/BlazingSystems-Experiments"),
        )

    def test_destination_pr_cannot_be_retargeted_or_coerced(self):
        for value in (None, 0, 27, "26", True, 26.0):
            with self.subTest(value=value):
                self.assertIn(
                    "Unexpected destination candidate PR identity",
                    self.errors_for("destination_candidate_pr", value),
                )

    def test_destination_repository_cannot_be_retargeted(self):
        self.assertIn(
            "Unexpected destination repository identity",
            self.errors_for("destination_repository", "other-owner/CoinOperatedEcosystem"),
        )


if __name__ == "__main__":
    unittest.main()
