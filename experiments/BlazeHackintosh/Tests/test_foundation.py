"""Safety and correctness tests for BlazeHackintosh's research-only foundation."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("blazehackintosh", ROOT / "blazehackintosh.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = module.load_catalog()

    def test_at_least_25_families_remain_unverified(self):
        self.assertGreaterEqual(len(self.catalog["families"]), 25)
        self.assertTrue(all(f["classification"] == "Research Only" for f in self.catalog["families"]))
        self.assertTrue(all(f["validated_efi"] is False for f in self.catalog["families"]))

    def test_known_exact_cpu_maps_to_family_without_boot_claim(self):
        matched = module.lookup_cpu("Intel(R) Core(TM) i5-4570 CPU @ 3.20GHz", self.catalog)
        self.assertEqual(matched["family_id"], "intel-haswell")
        self.assertEqual(matched["classification"], "Research Only")

    def test_amd_exact_cpu(self):
        matched = module.lookup_cpu("AMD Ryzen 5 3600 6-Core Processor", self.catalog)
        self.assertEqual(matched["family_id"], "amd-zen-2")

    def test_unknown_cpu_never_gets_guessed_as_compatible(self):
        matched = module.lookup_cpu("Future Experimental Processor XYZ", self.catalog)
        self.assertIsNone(matched["family_id"])
        self.assertEqual(matched["classification"], "Unknown")

    def test_no_gpu_or_boot_assumption(self):
        report = {"hardware": {"cpu": {"name": "Intel Core i5-4570"}, "gpus": []}}
        result = module.evaluate(report, self.catalog)
        self.assertFalse(result["can_generate_efi"])
        self.assertFalse(result["boot_verified"])
        self.assertIn("GPU model and acceleration", result["checks_required"])

    def test_malformed_catalog_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            p.write_text(json.dumps({"schema_version": 1, "families": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                module.load_catalog(p)

    def test_device_code_discards_serial_suffix(self):
        self.assertEqual(module._device_code("PCI\\VEN_8086&DEV_1912&SUBSYS_12345678\\UNIQUE"), "8086:1912")
        self.assertIsNone(module._device_code("serial-only-secret"))

    def test_scan_report_privacy_and_read_only(self):
        report = module.scan_hardware()
        self.assertTrue(report["read_only"])
        self.assertIn("Serial numbers", report["privacy"])
        self.assertNotIn("serial_number", json.dumps(report).lower())


if __name__ == "__main__":
    unittest.main()
