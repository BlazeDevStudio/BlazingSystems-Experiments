"""Digest-pinned official ocvalidate bridge tests; never run a real third-party binary."""
import hashlib
import importlib.util
import io
import json
import os
import plistlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import official_ocvalidate as official
from efi_validator import SECTIONS, validate_efi


class OfficialValidationBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.package = self.root / "official.zip"
        self.oc = self.root / "EFI" / "OC"
        self.oc.mkdir(parents=True)
        (self.oc / "OpenCore.efi").write_bytes(b"fixture-only-not-a-real-bootloader")
        with (self.oc / "config.plist").open("wb") as stream:
            plistlib.dump({name: {} for name in SECTIONS}, stream)
        with zipfile.ZipFile(self.package, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("Utilities/ocvalidate/ocvalidate.exe", os.urandom(4096))

    def checksum(self):
        return hashlib.sha256(self.package.read_bytes()).hexdigest()

    def test_wrong_hash_blocked_without_running_binary(self):
        with patch.object(official, "_invoke") as invocation:
            result = official.run_official_ocvalidate(self.root, self.package, consent=True)
            self.assertFalse(result["archive_verified"])
            self.assertFalse(result["attempted"])
            self.assertFalse(result["passed"])
            invocation.assert_not_called()

    def test_approval_required_before_file_verification(self):
        with patch.object(official, "verify_archive") as verification:
            report = official.run_official_ocvalidate(self.root, self.package)
            self.assertFalse(report["attempted"])
            verification.assert_not_called()

    def test_hash_pinned_archive_verifies_without_executing(self):
        with patch.object(official, "_invoke") as invocation:
            verified = official.verify_archive(self.package, expected_sha256=self.checksum())
            self.assertTrue(verified["verified"])
            self.assertEqual(verified["version"], "1.0.8")
            invocation.assert_not_called()

    def test_run_only_after_matching_version(self):
        fake = [(0, "REL-1.0.8\n"), (1, "validation failed on fixture")]
        with patch.object(official, "_invoke", side_effect=fake) as runner:
            result = official.run_official_ocvalidate(
                self.root, self.package, consent=True, system="Windows",
                expected_sha256=self.checksum())
        self.assertTrue(result["archive_verified"])
        self.assertTrue(result["version_matched"])
        self.assertTrue(result["attempted"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["boot_verified"])
        self.assertEqual(runner.call_count, 2)

    def test_mismatched_executable_version_is_rejected(self):
        with patch.object(official, "_invoke", return_value=(0, "REL-1.0.7")) as runner:
            result = official.run_official_ocvalidate(
                self.root, self.package, consent=True, system="Windows",
                expected_sha256=self.checksum())
        self.assertFalse(result["version_matched"])
        self.assertFalse(result["attempted"])
        self.assertEqual(runner.call_count, 1)

    def test_never_run_if_local_efi_structure_invalid(self):
        (self.oc / "config.plist").unlink()
        with patch.object(official, "_invoke") as runner:
            result = official.run_official_ocvalidate(
                self.root, self.package, consent=True, system="Windows",
                expected_sha256=self.checksum())
        self.assertFalse(result["attempted"])
        runner.assert_not_called()

    def test_unexpected_tool_location_or_host_rejected(self):
        with zipfile.ZipFile(self.package) as z:
            self.assertIsNotNone(official._tool_member(z, "Windows"))
            self.assertIsNone(official._tool_member(z, "Linux"))
            self.assertIsNone(official._tool_member(z, "UnknownOS"))

    def test_symlinked_config_rejected_without_leaking_external_content(self):
        (self.oc / "config.plist").unlink()
        secret = self.root / "outside.plist"
        secret.write_text("unique-private-test-value", encoding="utf-8")
        try:
            (self.oc / "config.plist").symlink_to(secret)
        except (OSError, NotImplementedError):
            self.skipTest("Operating system does not permit test symlinks")
        report = validate_efi(self.root)
        self.assertFalse(report["structural_checks_passed"])
        self.assertIsNone(report["config_sha256"])
        self.assertNotIn("unique-private-test-value", json.dumps(report))

    def test_duplicate_candidate_binary_rejected(self):
        with zipfile.ZipFile(self.package, "a") as z:
            z.writestr("Nested/Utilities/ocvalidate/ocvalidate.exe", b"extra")
        with zipfile.ZipFile(self.package) as z:
            self.assertIsNone(official._tool_member(z, "Windows"))


    def test_upstream_exact_banner_fallback_only_after_digest_approval(self):
        official_banner = ("NOTE: This version of ocvalidate is only compatible "
                           "with OpenCore version 1.0.8!\n\nFailed to read --version")
        with patch.object(official, "_invoke", side_effect=[
            (4294967295, official_banner), (4294967295, "fixture is not valid OpenCore config")
        ]) as runner:
            report = official.run_official_ocvalidate(
                self.root, self.package, consent=True, system="Windows",
                expected_sha256=self.checksum())
        self.assertTrue(report["version_matched"])
        self.assertTrue(report["attempted"])
        self.assertFalse(report["passed"])
        self.assertEqual(runner.call_count, 2)

    def test_wrong_banner_version_is_still_blocked(self):
        wrong = "NOTE: This version of ocvalidate is only compatible with OpenCore version 1.0.7!\nFailed to read --version"
        with patch.object(official, "_invoke", return_value=(4294967295, wrong)) as runner:
            report = official.run_official_ocvalidate(
                self.root, self.package, consent=True, system="Windows",
                expected_sha256=self.checksum())
        self.assertFalse(report["version_matched"])
        self.assertFalse(report["attempted"])
        self.assertEqual(runner.call_count, 1)

if __name__ == "__main__":
    unittest.main()
