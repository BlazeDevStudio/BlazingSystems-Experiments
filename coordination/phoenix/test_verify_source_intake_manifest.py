"""Offline synthetic tests; never require a live router or finance backend."""
import copy
import unittest
from verify_source_intake_manifest import verify

BLOB_A = 'a' * 40
BLOB_B = 'b' * 40
BASE = {
    'summary': {'recovered_rootfs_file_count': 2, 'recovered_byte_identical_count': 1, 'locally_derived_files': 1},
    'runtime': [
        {'path': 'a/file', 'source_git_blob': BLOB_A, 'destination_git_blob': BLOB_A, 'status': 'byte_identical'},
        {'path': 'b/file', 'source_git_blob': BLOB_A, 'destination_git_blob': BLOB_B, 'status': 'derived_cleanup_review_required_real_router_test'},
    ],
}

class ManifestGateTests(unittest.TestCase):
    def test_valid_synthetic(self):
        self.assertEqual(verify(copy.deepcopy(BASE)), [])

    def test_stale_counts(self):
        obj = copy.deepcopy(BASE)
        obj['summary']['recovered_byte_identical_count'] = 2
        self.assertTrue(any('recovered_byte_identical_count' in e for e in verify(obj)))

    def test_status_lie(self):
        obj = copy.deepcopy(BASE)
        obj['runtime'][1]['status'] = 'byte_identical'
        self.assertTrue(any('contradicts' in e for e in verify(obj)))

    def test_escape_path(self):
        obj = copy.deepcopy(BASE)
        obj['runtime'][1]['path'] = '../secret'
        self.assertTrue(any('unsafe' in e for e in verify(obj)))

    def test_duplicate_path(self):
        obj = copy.deepcopy(BASE)
        obj['runtime'][1]['path'] = 'a/file'
        self.assertIn('duplicate runtime path', verify(obj))

    def test_bad_blob(self):
        obj = copy.deepcopy(BASE)
        obj['runtime'][1]['source_git_blob'] = 'xyz'
        self.assertTrue(any('invalid blob' in e for e in verify(obj)))

if __name__ == '__main__':
    unittest.main()
