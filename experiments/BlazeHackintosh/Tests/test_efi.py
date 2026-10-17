"""Read-only EFI structural inspection regression tests (no macOS binaries)."""
import importlib.util
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("efi_validator", PROJECT / "efi_validator.py")
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)

def sample_config():
    return {section: {} for section in validator.SECTIONS}


class EfiStructureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.oc = self.root / "EFI" / "OC"
        self.oc.mkdir(parents=True)
        (self.oc / "OpenCore.efi").write_bytes(b"non-bootable-test-fixture")

    def store(self, config):
        with (self.oc / "config.plist").open("wb") as stream:
            plistlib.dump(config, stream)

    def test_minimal_references_pass_but_no_boot_claim(self):
        cfg = sample_config()
        self.store(cfg)
        report = validator.validate_efi(self.root)
        self.assertTrue(report["structural_checks_passed"])
        self.assertFalse(report["boot_verified"])
        self.assertFalse(report["ocvalidate_passed"])
        self.assertFalse(report["efi_generated"])
        self.assertTrue(report["warnings"])
        self.assertEqual(len(report["config_sha256"]), 64)

    def test_absent_loader_is_blocker(self):
        self.store(sample_config())
        (self.oc / "OpenCore.efi").unlink()
        report = validator.validate_efi(self.root)
        self.assertFalse(report["structural_checks_passed"])
        self.assertTrue(any("OpenCore loader" in e for e in report["errors"]))

    def test_malformed_plist_is_blocker(self):
        (self.oc / "config.plist").write_bytes(b"not valid plist")
        report = validator.validate_efi(self.root)
        self.assertFalse(report["structural_checks_passed"])

    def test_missing_kext_payload_is_blocker(self):
        cfg = sample_config()
        cfg["Kernel"]["Add"] = [{
            "Enabled": True, "BundlePath": "VirtualSMC.kext",
            "ExecutablePath": "Contents/MacOS/VirtualSMC",
            "PlistPath": "Contents/Info.plist"
        }]
        self.store(cfg)
        report = validator.validate_efi(self.root)
        self.assertFalse(report["structural_checks_passed"])
        self.assertTrue(any("bundle directory" in x for x in report["errors"]))

    def test_existing_kext_references_validate_without_boot_claim(self):
        kext = self.oc / "Kexts" / "Lilu.kext"
        (kext / "Contents" / "MacOS").mkdir(parents=True)
        (kext / "Contents" / "Info.plist").write_bytes(b"fixture-data")
        (kext / "Contents" / "MacOS" / "Lilu").write_bytes(b"fixture-data")
        cfg = sample_config()
        cfg["Kernel"]["Add"] = [{
            "Enabled": True, "BundlePath": "Lilu.kext",
            "ExecutablePath": "Contents/MacOS/Lilu",
            "PlistPath": "Contents/Info.plist"
        }]
        self.store(cfg)
        report = validator.validate_efi(self.root)
        self.assertTrue(report["structural_checks_passed"])
        self.assertTrue(report["ocvalidate_required"])

    def test_parent_traversal_is_rejected(self):
        cfg = sample_config()
        cfg["UEFI"]["Drivers"] = [{"Enabled": True, "Path": "../OpenCore.efi"}]
        self.store(cfg)
        report = validator.validate_efi(self.root)
        self.assertFalse(report["structural_checks_passed"])
        self.assertTrue(any("unsafe" in x for x in report["errors"]))

    def test_absolute_path_is_rejected(self):
        cfg = sample_config()
        cfg["UEFI"]["Drivers"] = [{"Enabled": True, "Path": "C:\\Users\\root\\driver.efi"}]
        self.store(cfg)
        report = validator.validate_efi(self.root)
        self.assertFalse(report["structural_checks_passed"])
        self.assertTrue(any("absolute" in x for x in report["errors"]))

    def test_disabled_entry_does_not_require_file(self):
        cfg = sample_config()
        cfg["ACPI"]["Add"] = [{"Enabled": False, "Path": "Missing.aml"}]
        self.store(cfg)
        self.assertTrue(validator.validate_efi(self.root)["structural_checks_passed"])

    def test_duplicate_enabled_driver_rejected(self):
        folder = self.oc / "Drivers"
        folder.mkdir()
        (folder / "OpenRuntime.efi").write_bytes(b"fixture")
        cfg = sample_config()
        cfg["UEFI"]["Drivers"] = [{"Enabled": True, "Path": "OpenRuntime.efi"},
                                   {"Enabled": True, "Path": "OpenRuntime.efi"}]
        self.store(cfg)
        report = validator.validate_efi(self.root)
        self.assertFalse(report["structural_checks_passed"])
        self.assertTrue(any("duplicate" in e for e in report["errors"]))

    def test_untyped_enabled_flag_is_error(self):
        cfg = sample_config()
        cfg["ACPI"]["Add"] = [{"Enabled": 1, "Path": "test.aml"}]
        self.store(cfg)
        self.assertFalse(validator.validate_efi(self.root)["structural_checks_passed"])

    def test_unknown_efi_directory_fails(self):
        report = validator.validate_efi(self.root / "no-such-location")
        self.assertFalse(report["structural_checks_passed"])


if __name__ == "__main__":
    unittest.main()
