#!/usr/bin/env python3
"""Negative regression tests for Project Phoenix coordination-only validation.

Run: python3 -m unittest discover -s coordination/phoenix -p 'test_verify_coordination.py' -v
"""
import copy
import json
import unittest

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

    def test_duplicate_source_claim_fails(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["source"] = modified["routes"][2]["source"]
        self.assertTrue(any("overlapping ownership" in s for s in validate_routes(modified, REPO_ROOT)))

    def test_parent_directory_claim_collision_fails(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["source"] = "experiment/openwrt/BlazePwifi/"
        self.assertTrue(any("overlapping ownership" in s for s in validate_routes(modified, REPO_ROOT)))

    def test_source_absent_fails(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["source"] = "no_such_source_folder/"
        self.assertTrue(any("does not exist" in s for s in validate_routes(modified, REPO_ROOT)))

    def test_unknown_owner_fails(self):
        modified = copy.deepcopy(self.routes)
        modified["routes"][1]["role"] = "PHX-UNKNOWN"
        self.assertTrue(any("unknown role" in s for s in validate_routes(modified, REPO_ROOT)))

    def test_example_protocol_passes(self):
        self.assertEqual(validate_envelope(self.example), [])

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
