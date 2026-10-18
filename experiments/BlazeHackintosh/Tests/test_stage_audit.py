"""Read-only research stage consistency tests using disposable fixtures."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from efi_builder import RESEARCH_NOTICE
from stage_audit import audit_candidate

class StageAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "BlazeEFI-Fixture"
        self.file = self.root / "EFI" / "OC" / "config.plist"
        self.file.parent.mkdir(parents=True)
        self.file.write_bytes(b"TEST-ONLY-NOT-BOOTABLE")
        (self.root / "DO-NOT-INSTALL.txt").write_text(RESEARCH_NOTICE + "\n")
        self.doc = {
            "classification": "Structurally Validated Only",
            "ocvalidate_passed": True, "hardware_boot_verified": False,
            "usable_installer": False, "notice": RESEARCH_NOTICE,
            "files": [{"path": "EFI/OC/config.plist",
                       "sha256": hashlib.sha256(self.file.read_bytes()).hexdigest()}]}
        self.save()

    def save(self):
        (self.root / "RESEARCH-ONLY.json").write_text(json.dumps(self.doc))

    def test_good_fixture_is_only_locally_consistent(self):
        result = audit_candidate(self.root)
        self.assertTrue(result["integrity_passed"], result)
        self.assertEqual(result["files_checked"], 1)
        self.assertFalse(result["boot_verified"])
        self.assertFalse(result["publisher_authenticity_verified"])

    def test_modified_file_fails(self):
        self.file.write_bytes(b"modified")
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

    def test_missing_file_fails(self):
        self.file.unlink()
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

    def test_extra_file_fails(self):
        (self.file.parent / "extra.txt").write_bytes(b"extra")
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

    def test_extra_directory_fails(self):
        (self.file.parent / "extra").mkdir()
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

    def test_changed_marker_fails(self):
        (self.root / "DO-NOT-INSTALL.txt").write_text("changed")
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

    def test_promoted_status_fails(self):
        self.doc["hardware_boot_verified"] = True
        self.save()
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

    def test_duplicate_manifest_fails(self):
        self.doc["files"].append(dict(self.doc["files"][0]))
        self.save()
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

    def test_path_traversal_fails(self):
        self.doc["files"][0]["path"] = "EFI/../secret"
        self.save()
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

    def test_bad_digest_fails(self):
        self.doc["files"][0]["sha256"] = "f" * 63
        self.save()
        self.assertFalse(audit_candidate(self.root)["integrity_passed"])

if __name__ == "__main__":
    unittest.main()
