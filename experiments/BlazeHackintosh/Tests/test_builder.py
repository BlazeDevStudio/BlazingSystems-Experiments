"""Research-only Haswell stage builder safety tests. Synthetic files are never real EFI bootloaders."""
import json
import plistlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import efi_builder as builder
from efi_validator import SECTIONS

def sample():
    c = {section: {} for section in SECTIONS}
    c["Kernel"]["Add"] = [
        {"BundlePath": n, "Enabled": False, "PlistPath": "Contents/Info.plist",
         "ExecutablePath": f"Contents/MacOS/{n[:-5]}", "Arch": "Any"}
        for n in builder.KEXTS
    ]
    c["Misc"]["Security"] = {"Vault": "Secure"}
    c["PlatformInfo"]["Generic"] = {}
    return c


class CandidateBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.kexts = self.root / "kexts"
        self.acpi = self.root / "acpi"
        self.kexts.mkdir()
        self.acpi.mkdir()
        for name in builder.KEXTS:
            bundle = self.kexts / name / "Contents"
            (bundle / "MacOS").mkdir(parents=True)
            exec_name = name[:-5]
            (bundle / "MacOS" / exec_name).write_bytes(b"fake-binary-not-for-boot")
            with (bundle / "Info.plist").open("wb") as f:
                plistlib.dump({"CFBundleExecutable": exec_name,
                               "CFBundleIdentifier": "org.example." + exec_name}, f)
        for name in builder.ACPIS:
            (self.acpi / name).write_bytes(b"FAKE-AML-NOT-TO-BOOT")
        self.hfs = self.root / "HfsPlus.efi"
        self.hfs.write_bytes(b"FAKE-HFS-NOT-TO-BOOT")
        self.report = self.root / "report.json"
        self.smbios = self.root / "smbios.json"
        self.zip = self.root / "OpenCore-1.0.8-RELEASE.zip"
        self.output = self.root / "BlazeEFI-Haswell"
        self.manifest = self.root / "components.json"
        self.report.write_text(json.dumps({
            "format_version": 2, "read_only": True, "hardware": {
                "cpu": {"name": "Intel Core i5-4570"}, "motherboard": {"model": "Example Deskboard"},
                "firmware": "UEFI", "gpus": [{"name": "Intel HD Graphics 4600", "pci_id": "8086:0412"}]}}))
        self.smbios.write_text(json.dumps({
            "SystemProductName": "iMac14,2", "SystemSerialNumber": "TEST12345678",
            "MLB": "EXPERIMENTAL00001", "SystemUUID": "be01ea11-abcd-4f29-b65d-118ee1d92c51",
            "ROM": "000000000002"}))
        with zipfile.ZipFile(self.zip, "w", zipfile.ZIP_STORED) as z:
            z.writestr("X64/EFI/BOOT/BOOTx64.efi", b"sample-fake-boot")
            z.writestr("X64/EFI/OC/OpenCore.efi", b"sample-fake-opencore")
            z.writestr("X64/EFI/OC/Drivers/OpenRuntime.efi", b"sample-fake-driver")
            z.writestr("Docs/Sample.plist", plistlib.dumps(sample()))
        self.write_manifest()

    def write_manifest(self):
        from component_manifest import input_files, sha256
        entries = [{"path": name, "sha256": sha256(path),
                    "source_url": "https://example.org/nonbootable-ci-fixtures",
                    "license_id": "MIT", "release": "synthetic-fixture-v1"}
                   for name, path in sorted(
                       input_files(self.kexts, self.acpi, self.hfs).items())]
        self.manifest.write_text(
            json.dumps({"schema_version": 1, "files": entries}), encoding="utf-8")

    def kwargs(self):
        return dict(hardware_report=self.report, official_zip=self.zip,
                    kext_dir=self.kexts, acpi_dir=self.acpi, hfs_driver=self.hfs,
                    smbios_json=self.smbios, component_manifest=self.manifest,
                    output_dir=self.output,
                    macos="12", consent=True)

    def test_approval_required_no_output(self):
        with self.assertRaisesRegex(ValueError, "explicitly acknowledge"):
            builder.build_candidate(**dict(self.kwargs(), consent=False))
        self.assertFalse(self.output.exists())

    def test_unknown_gpu_fail_closed_no_output(self):
        report = json.loads(self.report.read_text())
        report["hardware"]["gpus"][0]["pci_id"] = "10DE:2684"
        self.report.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "8086:0412"):
            builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_unknown_firmware_fail_closed_no_output(self):
        report = json.loads(self.report.read_text())
        report["hardware"]["firmware"] = "Unknown"
        self.report.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "UEFI"):
            builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_unrecognized_cpu_fail_closed(self):
        report = json.loads(self.report.read_text())
        report["hardware"]["cpu"]["name"] = "AMD Ryzen 5 3600"
        self.report.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "Haswell"):
            builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_no_output_without_verified_upstream_archive(self):
        with patch.object(builder, "verify_archive", return_value={"verified": False, "error": "bad sha"}):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_no_output_if_ocvalidate_rejects(self):
        with patch.object(builder, "verify_archive", return_value={"verified": True}), \
             patch.object(builder, "run_official_ocvalidate",
                          return_value={"passed": False, "error": "fixture rejected", "checker_output": ""}):
            with self.assertRaisesRegex(ValueError, "did not pass"):
                builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())
        self.assertFalse(any(p.name.startswith(".blazehackintosh-stage-") for p in self.root.iterdir()))

    def test_honest_research_candidate_with_all_gates_mocked(self):
        with patch.object(builder, "verify_archive", return_value={"verified": True}), \
             patch.object(builder, "run_official_ocvalidate", return_value={"passed": True}):
            report = builder.build_candidate(**self.kwargs())
        self.assertTrue(report["ocvalidate_passed"])
        self.assertFalse(report["boot_verified"])
        self.assertFalse(report["ready_for_internal_esp"])
        self.assertTrue((self.output / "EFI/OC/config.plist").is_file())
        config = plistlib.loads((self.output / "EFI/OC/config.plist").read_bytes())
        self.assertEqual(config["PlatformInfo"]["Generic"]["SystemProductName"], "iMac14,2")
        self.assertEqual(len(config["Kernel"]["Add"]), 3)
        self.assertEqual(len(config["ACPI"]["Add"]), 2)
        self.assertEqual(len(config["UEFI"]["Drivers"]), 2)
        self.assertNotIn("#WARNING - 1", config)
        manifest = json.loads((self.output / "RESEARCH-ONLY.json").read_text())
        self.assertFalse(manifest["hardware_boot_verified"])
        self.assertFalse(manifest["usable_installer"])
        self.assertNotIn("EXPERIMENTAL00001", json.dumps(manifest))
        self.assertIn("DO-NOT-INSTALL", "\n".join(p.name for p in self.output.iterdir()))
        self.assertEqual(len(manifest["files"]), report["file_count"])

    def test_never_overwrite_existing_output(self):
        self.output.mkdir()
        secret = self.output / "original.txt"
        secret.write_text("never-overwrite")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            builder.build_candidate(**self.kwargs())
        self.assertEqual(secret.read_text(), "never-overwrite")

    def test_reject_kext_symlink_before_stage(self):
        (self.kexts / "Lilu.kext" / "Contents" / "MacOS" / "external").symlink_to(self.hfs)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_reject_sample_invalid_identity(self):
        data = json.loads(self.smbios.read_text())
        data["SystemUUID"] = "00000000-0000-0000-0000-000000000000"
        self.smbios.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "All-zero"):
            builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_source_member_path_ambiguous_is_rejected(self):
        with zipfile.ZipFile(self.zip, "a") as z:
            z.writestr("Another/Docs/Sample.plist", plistlib.dumps(sample()))
        with zipfile.ZipFile(self.zip) as z:
            with self.assertRaisesRegex(ValueError, "exactly one"):
                builder._archive_payload(z, "Docs/Sample.plist")

    def test_reject_unsafe_destination_name(self):
        with self.assertRaisesRegex(ValueError, "NEW directory"):
            builder.build_candidate(**dict(self.kwargs(), output_dir=self.root / "EFI"))


    def test_reject_tampered_component_before_output(self):
        (self.kexts / "Lilu.kext" / "Contents" / "MacOS" / "Lilu").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_reject_missing_component_manifest(self):
        self.manifest.unlink()
        with self.assertRaisesRegex(ValueError, "Manifest must be"):
            builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_reject_manifest_missing_single_component(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["files"].pop()
        self.manifest.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            builder.build_candidate(**self.kwargs())
        self.assertFalse(self.output.exists())

    def test_reject_component_without_declared_license(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["files"][0]["license_id"] = ""
        self.manifest.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "license_id"):
            builder.build_candidate(**self.kwargs())

    def test_reject_extra_unreviewed_acpi_file(self):
        (self.acpi / "Unknown-SSDT.aml").write_bytes(b"unreviewed")
        with self.assertRaisesRegex(ValueError, "Unexpected/missing ACPI"):
            builder.build_candidate(**self.kwargs())

    def test_candidate_records_declared_integrity_without_publisher_claim(self):
        with patch.object(builder, "verify_archive", return_value={"verified": True}), \
             patch.object(builder, "run_official_ocvalidate", return_value={"passed": True}):
            builder.build_candidate(**self.kwargs())
        manifest = json.loads((self.output / "RESEARCH-ONLY.json").read_text())
        integrity = manifest["component_integrity"]
        self.assertGreater(integrity["file_count"], 5)
        self.assertEqual(len(integrity["manifest_sha256"]), 64)
        self.assertIn("NOT verified", integrity["trust"])
        self.assertFalse(manifest["hardware_boot_verified"])

if __name__ == "__main__":
    unittest.main()
