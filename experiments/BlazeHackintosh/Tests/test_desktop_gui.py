"""Headless regression suite for the experimental native GUI controller."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("desktop_gui", ROOT / "desktop_gui.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample():
    return {"read_only": True, "host_os": "Windows", "hardware": {
        "cpu": {"name": "Intel Core i5-4570"}, "motherboard": {"model": "Example"},
        "firmware": "UEFI", "gpus": [{"pci_id": "8086:0412"}],
        "storage": [], "network_adapters": []}}


def evaluation(*args):
    return {"boot_verified": False, "can_generate_efi": False,
            "classification": "Research Only", "cpu_family": "intel-haswell",
            "missing_inventory_evidence": ["storage-inventory"]}


def snapshot():
    return mod.make_snapshot(sample, lambda: {"families": []}, evaluation)


class GuiControllerTests(unittest.TestCase):
    def test_readonly_snapshot(self):
        s = snapshot()
        self.assertFalse(s["boot_verified"])
        self.assertFalse(s["can_generate_efi"])
        self.assertEqual(s["status"], "Research Only")
        self.assertEqual(s["scan"]["host_os"], "Windows")

    def test_rejects_untrusted_scan_readonly_flag(self):
        report = sample(); report["read_only"] = False
        with self.assertRaisesRegex(ValueError, "read-only"):
            mod.make_snapshot(lambda: report, lambda: {}, evaluation)

    def test_rejects_missing_hardware(self):
        report = sample(); report.pop("hardware")
        with self.assertRaisesRegex(ValueError, "inventory"):
            mod.make_snapshot(lambda: report, lambda: {}, evaluation)

    def test_rejects_non_mapping_scan(self):
        with self.assertRaises(ValueError):
            mod.make_snapshot(lambda: [], lambda: {}, evaluation)

    def test_rejects_boot_claim(self):
        def unsafe(*args):
            result = evaluation(); result["boot_verified"] = True; return result
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            mod.make_snapshot(sample, lambda: {}, unsafe)

    def test_rejects_efi_claim(self):
        def unsafe(*args):
            result = evaluation(); result["can_generate_efi"] = True; return result
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            mod.make_snapshot(sample, lambda: {}, unsafe)

    def test_rejects_unrecognized_classification(self):
        def unsafe(*args):
            result = evaluation(); result["classification"] = "Boot Ready"; return result
        with self.assertRaisesRegex(ValueError, "classification"):
            mod.make_snapshot(sample, lambda: {}, unsafe)

    def test_rejects_malformed_evaluation(self):
        with self.assertRaises(ValueError):
            mod.make_snapshot(sample, lambda: {}, lambda *a: [])

    def test_extra_sensitive_scanner_fields_are_not_exported(self):
        report = sample()
        report["hostname"] = "SECRET-HOST"
        report["hardware"]["serial_number"] = "SECRET-SERIAL"
        report["hardware"]["cpu"]["uuid"] = "SECRET-UUID"
        report["hardware"]["gpus"][0]["mac_address"] = "SECRET-MAC"
        report["hardware"]["network_adapters"].append({
            "name": "NIC", "pci_id": "8086:1234", "ip_address": "SECRET-IP"})
        s = mod.make_snapshot(lambda: report, lambda: {}, evaluation)
        payload = json.dumps(s)
        for marker in ("SECRET-HOST", "SECRET-SERIAL", "SECRET-UUID", "SECRET-MAC", "SECRET-IP"):
            self.assertNotIn(marker, payload)

    def test_unexpected_evaluation_metadata_is_not_exported(self):
        def unsafe(*args):
            result = evaluation()
            result["user_account"] = "SECRET-ACCOUNT"
            return result
        s = mod.make_snapshot(sample, lambda: {}, unsafe)
        self.assertNotIn("SECRET-ACCOUNT", json.dumps(s))

    def test_rejects_malformed_nested_device_lists(self):
        report = sample(); report["hardware"]["gpus"] = "malformed"
        with self.assertRaisesRegex(ValueError, "device list"):
            mod.make_snapshot(lambda: report, lambda: {}, evaluation)

    def test_rejects_unbounded_device_lists(self):
        report = sample(); report["hardware"]["gpus"] = [{}] * 257
        with self.assertRaisesRegex(ValueError, "safety limit"):
            mod.make_snapshot(lambda: report, lambda: {}, evaluation)

    def test_rejects_malformed_evaluation_list(self):
        def malformed(*args):
            result = evaluation(); result["checks_required"] = ["valid", {"secret": "bad"}]
            return result
        with self.assertRaisesRegex(ValueError, "evaluation list"):
            mod.make_snapshot(sample, lambda: {}, malformed)

    def test_export_new_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "report.json"
            self.assertEqual(mod.export_new_json(p, snapshot()), p)
            data = json.loads(p.read_text(encoding="utf-8"))
            self.assertFalse(data["boot_verified"])
            self.assertTrue(data["read_only"])

    def test_existing_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "report.json"
            p.write_text("important", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                mod.export_new_json(p, snapshot())
            self.assertEqual(p.read_text(), "important")

    def test_symlink_not_followed(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "important"
            dest.write_text("untouched")
            link = Path(d) / "report.json"
            try: link.symlink_to(dest)
            except (OSError, NotImplementedError): self.skipTest("Symlinks unavailable")
            with self.assertRaises(OSError):
                mod.export_new_json(link, snapshot())
            self.assertEqual(dest.read_text(), "untouched")

    def test_export_rejects_missing_parent(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                mod.export_new_json(Path(d) / "missing" / "report.json", snapshot())

    def test_export_rejects_unsafe_report(self):
        with tempfile.TemporaryDirectory() as d:
            s = snapshot(); s["boot_verified"] = True
            with self.assertRaises(ValueError):
                mod.export_new_json(Path(d) / "report.json", s)

    def test_export_rejects_unexpected_nested_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            s = snapshot()
            s["scan"]["hardware"]["cpu"]["serial_number"] = "SECRET-SERIAL"
            with self.assertRaisesRegex(ValueError, "unexpected metadata"):
                mod.export_new_json(Path(d) / "report.json", s)
            self.assertFalse((Path(d) / "report.json").exists())

    def test_export_rejects_unexpected_top_level_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            s = snapshot(); s["user_account"] = "SECRET-ACCOUNT"
            with self.assertRaisesRegex(ValueError, "unexpected research"):
                mod.export_new_json(Path(d) / "report.json", s)

    def test_export_large_unexpected_payload_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            s = snapshot(); s["padding"] = "x" * (mod.MAX_JSON_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "unexpected research"):
                mod.export_new_json(Path(d) / "report.json", s)

    def test_snapshot_unexpected_large_field_not_exported(self):
        report = sample(); report["large"] = "SECRET-LARGE" * (mod.MAX_JSON_BYTES // 5)
        s = mod.make_snapshot(lambda: report, lambda: {}, evaluation)
        self.assertNotIn("SECRET-LARGE", json.dumps(s))

    def test_scalar_length_and_integer_bounds(self):
        report = sample()
        report["hardware"]["cpu"]["name"] = "X" * 10000
        report["hardware"]["memory_bytes"] = 2**99999
        s = mod.make_snapshot(lambda: report, lambda: {}, evaluation)
        self.assertEqual(len(s["scan"]["hardware"]["cpu"]["name"]), 240)
        self.assertIsNone(s["scan"]["hardware"]["memory_bytes"])

    def test_summary_explains_unverified(self):
        summary = "\n".join(mod.summary_lines(snapshot()))
        self.assertIn("Boot verified: NO", summary)
        self.assertIn("Research Only", summary)
        self.assertIn("storage-inventory", summary)

    def test_allowed_name_fields_cannot_leak_common_identifiers(self):
        for secret in (
            "MAC 00:11:22:33:44:55", "GPU 192.168.1.42", "UUID 550e8400-e29b-41d4-a716-446655440000",
            "hostname=private-box", "DESKTOP-A1B2C3D4", "C:\\Users\\alice\\Documents",
            "Serial Number: SN1234567",
        ):
            with self.subTest(secret=secret):
                report = sample()
                report["hardware"]["gpus"][0]["name"] = secret
                output = mod.make_snapshot(lambda: report, lambda: {}, evaluation)
                self.assertNotIn(secret, json.dumps(output))
                self.assertIn("redacted", output["scan"]["hardware"]["gpus"][0]["name"])

    def test_allowed_evaluation_list_cannot_leak_sensitive_strings(self):
        def malicious(*args):
            result = evaluation()
            result["checks_required"] = ["Check 10.0.0.7", "UUID 550e8400-e29b-41d4-a716-446655440000"]
            return result
        output = mod.make_snapshot(sample, lambda: {}, malicious)
        self.assertNotIn("10.0.0.7", json.dumps(output))
        self.assertNotIn("550e8400", json.dumps(output))

    def test_bidi_and_control_characters_not_exported(self):
        for unsafe in ("GPU\u202eEXE", "GPU\nserial", "GPU\x00hidden"):
            with self.subTest(unsafe=unsafe):
                report = sample()
                report["hardware"]["gpus"][0]["name"] = unsafe
                output = mod.make_snapshot(lambda: report, lambda: {}, evaluation)
                self.assertNotIn(unsafe, json.dumps(output))

    def test_export_rejects_forged_status_notice_and_schema(self):
        for field, bad in (("status", "Production Ready"), ("notice", "Ready to boot"),
                           ("schema_version", 2)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as d:
                report = snapshot()
                report[field] = bad
                dest = Path(d) / "report.json"
                with self.assertRaisesRegex(ValueError, "forged"):
                    mod.export_new_json(dest, report)
                self.assertFalse(dest.exists())

    def test_export_rejects_forged_evaluation_capability(self):
        for field, bad in (("classification", "Boot Ready"), ("boot_verified", True),
                           ("can_generate_efi", True)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as d:
                report = snapshot()
                report["evaluation"][field] = bad
                dest = Path(d) / "report.json"
                with self.assertRaisesRegex(ValueError, "unsafe research evaluation"):
                    mod.export_new_json(dest, report)
                self.assertFalse(dest.exists())

    def test_exported_file_contains_no_sensitive_pattern(self):
        report = sample()
        report["hardware"]["motherboard"]["model"] = "Example serial=ABC12345"
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "report.json"
            mod.export_new_json(dest, mod.make_snapshot(lambda: report, lambda: {}, evaluation))
            self.assertNotIn("ABC12345", dest.read_text(encoding="utf-8"))

    def test_gui_import_is_headless(self):
        self.assertTrue(callable(mod.launch))
        self.assertNotIn("tkinter", mod.__dict__)


if __name__ == "__main__":
    unittest.main()
