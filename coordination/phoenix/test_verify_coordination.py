#!/usr/bin/env python3
"""Negative regression tests for Project Phoenix coordination-only validation.

Run: python3 -m unittest discover -s coordination/phoenix -p 'test_verify_coordination.py' -v
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from verify_coordination import HERE, REPO_ROOT, safe_repo_path, validate_envelope, validate_routes


class CoordinationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes = json.loads((HERE / "OWNERSHIP_ROUTES.json").read_text(encoding="utf-8"))
        cls.example = json.loads((HERE / "COMMUNICATION_EXAMPLE.json").read_text(encoding="utf-8"))

    def test_real_routes_pass_static_validation(self):
        self.assertEqual(validate_routes(self.routes, REPO_ROOT), [])

    def test_source_path_rejects_traversal_and_windows_separator(self):
        for path in ("/absolute", "../up", "one/../other", "one//other", "one\\other"):
            with self.subTest(path=path):
                self.assertFalse(safe_repo_path(path))
        self.assertTrue(safe_repo_path("experiment/openwrt/BlazePwifi/"))

    def test_master_must_not_claim_runtime_destination(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][0]["target"] = "Pisowifi/"
        errors = validate_routes(modified, REPO_ROOT)
        self.assertTrue(any("MASTER is coordination-only" in e for e in errors))

    def test_draft_route_must_not_authorize_recursive_copy(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["copy_permitted"] = True
        errors = validate_routes(modified, REPO_ROOT)
        self.assertTrue(any("DRAFT route cannot authorize copy" in e for e in errors))

    def test_redundant_trailing_path_separators_are_rejected(self):
        for path in ("coordination/phoenix//", "Rental///"):
            with self.subTest(path=path):
                self.assertFalse(safe_repo_path(path))

    def test_duplicate_source_claim_fails(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["source"] = modified["routes"][2]["source"]
        self.assertTrue(any("overlapping ownership" in s for s in validate_routes(modified, REPO_ROOT)))

    def test_parent_directory_claim_collision_fails(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["source"] = "experiment/openwrt/BlazePwifi/"
        self.assertTrue(any("overlapping ownership" in s for s in validate_routes(modified, REPO_ROOT)))

    def test_source_symlink_escape_fails_closed(self):
        # Synthetic checkout: no customer files or real migration operations.
        with tempfile.TemporaryDirectory() as base:
            root = Path(base) / "repo"
            outside = Path(base) / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "escape").symlink_to(outside, target_is_directory=True)
            modified = copy.deepcopy(self.routes)
            modified["routes"][1]["source"] = "escape/"
            errors = validate_routes(modified, root)
            self.assertTrue(any("resolves outside checkout" in e for e in errors), errors)

    def test_source_internal_symlink_is_contained(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base) / "repo"
            real = root / "real"
            real.mkdir(parents=True)
            (root / "alias").symlink_to(real, target_is_directory=True)
            modified = copy.deepcopy(self.routes)
            modified["routes"][1]["source"] = "alias/"
            errors = validate_routes(modified, root)
            self.assertFalse(any("resolves outside checkout" in e for e in errors), errors)

    def test_source_broken_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base) / "repo"
            root.mkdir()
            (root / "broken").symlink_to(root / "missing", target_is_directory=True)
            modified = copy.deepcopy(self.routes)
            modified["routes"][1]["source"] = "broken/"
            errors = validate_routes(modified, root)
            self.assertTrue(any("cannot resolve" in e for e in errors), errors)

    def test_source_absent_fails(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["source"] = "no_such_source_folder/"
        self.assertTrue(any("does not exist" in s for s in validate_routes(modified, REPO_ROOT)))

    def test_unknown_owner_fails(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["role"] = "PHX-UNKNOWN"
        self.assertTrue(any("unknown role" in s for s in validate_routes(modified, REPO_ROOT)))

    def test_destination_parent_requires_manual_mapping(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][4]["kind"] = "selective-review"
        errors = validate_routes(modified, REPO_ROOT)
        self.assertTrue(any("Unreviewed destination claims overlap" in e for e in errors))

    def test_overlapping_parent_must_deny_recursive_copy(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][4]["copy_permitted"] = True
        errors = validate_routes(modified, REPO_ROOT)
        self.assertTrue(any("Unreviewed destination claims overlap" in e for e in errors))

    def test_cross_role_destination_overlap_is_rejected(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][3]["role"] = "PHX-CORE"
        errors = validate_routes(modified, REPO_ROOT)
        self.assertTrue(any("Cross-role destination claims overlap" in e for e in errors))

    def test_duplicate_destination_is_rejected(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][4]["target"] = "Rental/android/"
        errors = validate_routes(modified, REPO_ROOT)
        self.assertTrue(any("Duplicate destination claim" in e for e in errors))

    def test_example_protocol_passes(self):
        self.assertEqual(validate_envelope(self.example), [])

    def test_known_recipient_and_all_are_accepted(self):
        for recipient in ("ALL", "PHX-MASTER", "PHX-QA", "PHX-RENTAL"):
            with self.subTest(recipient=recipient):
                modified = copy.deepcopy(self.example)
                modified["to"] = recipient
                self.assertEqual(validate_envelope(modified), [])

    def test_unknown_or_ambiguous_recipient_is_rejected(self):
        for recipient in ("PHX-UNKNOWN", "PHX-QA;PHX-UNKNOWN",
                          "PHX-QA;PHX-CORE", "ALL;PHX-QA",
                          " PHX-QA", "PHX-QA ", "all"):
            with self.subTest(recipient=recipient):
                modified = copy.deepcopy(self.example)
                modified["to"] = recipient
                self.assertTrue(any("Invalid recipient" in e for e in validate_envelope(modified)))

    def test_bad_protocol_and_missing_fields_fail(self):
        modified = copy.deepcopy(self.example)
        modified["protocol"] = "NOT-A-PROTOCOL"
        modified.pop("task_id")
        errors = validate_envelope(modified)
        self.assertTrue(any("Wrong protocol" in e for e in errors))
        self.assertTrue(any("Missing envelope key: task_id" in e for e in errors))

    def test_malformed_sha_timestamp_and_arrays_fail(self):
        modified = copy.deepcopy(self.example)
        modified["base_sha"] = "short"
        modified["updated_utc"] = "2026-11-15T00:00:00+08:00"
        modified["evidence"] = "not an array"
        errors = validate_envelope(modified)
        self.assertTrue(any("base_sha" in e for e in errors))
        self.assertTrue(any("updated_utc" in e for e in errors))
        self.assertTrue(any("evidence" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
