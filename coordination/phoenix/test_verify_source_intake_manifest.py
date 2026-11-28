"""Offline synthetic tests; never require a live router or finance backend."""
import copy
import unittest
from verify_source_intake_manifest import verify

BLOB_A = "a" * 40
BLOB_B = "b" * 40
BASE = {
    "summary": {
        "original_rootfs_file_count": 2,
        "recovered_rootfs_file_count": 2,
        "recovered_byte_identical_count": 1,
        "locally_derived_files": 1,
        "unrecovered_rootfs_file_count": 0,
    },
    "runtime": [
        {"path": "a/file", "source_git_blob": BLOB_A, "destination_git_blob": BLOB_A, "status": "byte_identical"},
        {
            "path": "b/file",
            "source_git_blob": BLOB_A,
            "destination_git_blob": BLOB_B,
            "status": "derived_cleanup_review_required_real_router_test",
        },
    ],
}


class ManifestGateTests(unittest.TestCase):
    def test_valid_synthetic(self):
        self.assertEqual(verify(copy.deepcopy(BASE)), [])

    def test_non_object_root(self):
        self.assertTrue(any("root must be an object" in e for e in verify([])))

    def test_stale_counts(self):
        obj = copy.deepcopy(BASE)
        obj["summary"]["recovered_byte_identical_count"] = 2
        self.assertTrue(any("recovered_byte_identical_count" in e for e in verify(obj)))

    def test_status_lie(self):
        obj = copy.deepcopy(BASE)
        obj["runtime"][1]["status"] = "byte_identical"
        self.assertTrue(any("contradicts" in e for e in verify(obj)))

    def test_unknown_status_rejected(self):
        obj = copy.deepcopy(BASE)
        obj["runtime"][1]["status"] = "derived_typo"
        self.assertTrue(any("unknown status" in e for e in verify(obj)))

    def test_missing_status_rejected(self):
        obj = copy.deepcopy(BASE)
        del obj["runtime"][1]["status"]
        self.assertTrue(any("unknown status" in e for e in verify(obj)))

    def test_escape_path(self):
        obj = copy.deepcopy(BASE)
        obj["runtime"][1]["path"] = "../secret"
        self.assertTrue(any("unsafe" in e for e in verify(obj)))

    def test_control_character_path_rejected(self):
        obj = copy.deepcopy(BASE)
        obj["runtime"][1]["path"] = "folder/bad\nname"
        self.assertTrue(any("unsafe" in e for e in verify(obj)))

    def test_duplicate_path(self):
        obj = copy.deepcopy(BASE)
        obj["runtime"][1]["path"] = "a/file"
        self.assertIn("duplicate runtime path", verify(obj))

    def test_bad_blob(self):
        obj = copy.deepcopy(BASE)
        obj["runtime"][1]["source_git_blob"] = "xyz"
        self.assertTrue(any("invalid blob" in e for e in verify(obj)))

    def test_original_count_reconciles_with_recovered_and_unrecovered(self):
        obj = copy.deepcopy(BASE)
        obj["summary"]["original_rootfs_file_count"] = 3
        self.assertTrue(any("original_rootfs_file_count" in e for e in verify(obj)))


if __name__ == "__main__":
    unittest.main()
