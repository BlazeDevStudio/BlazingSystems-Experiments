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
        self.assertIn("serial numbers", report["privacy"].lower())
        self.assertNotIn("serial_number", json.dumps(report).lower())


    def test_linux_pci_id_and_sensitive_instance_discard(self):
        text = "00:02.0 VGA compatible controller [0300]: Intel Graphics [8086:1912] (rev 06)"
        self.assertEqual(module._linux_pci_id(text), "8086:1912")
        self.assertIsNone(module._linux_pci_id("no device information"))

    def test_storage_size_safety(self):
        self.assertEqual(module._safe_size("102400"), 102400)
        for bad in ("nope", -1, 0, None, True, "inf"):
            self.assertIsNone(module._safe_size(bad))

    def test_inventory_gaps_are_explicit_not_compatibility_predictions(self):
        gaps = module.inventory_gaps({"hardware": {"cpu": {"name": "Intel Core i5-4570"},
                                                   "firmware": "UEFI", "gpus": []}})
        self.assertIn("gpu-pci-id", gaps)
        self.assertIn("motherboard-model", gaps)
        self.assertIn("storage-inventory", gaps)
        self.assertNotIn("exact-cpu", gaps)

    def test_windows_report_filters_sensitive_pnp_device_tail_and_mac(self):
        from unittest.mock import patch
        sensitive = "PCI\\VEN_8086&DEV_1912&SUBSYS_12345678\\SENSITIVE-INSTANCE-ID"
        def fake_powershell(command):
            if "Win32_Processor" in command:
                return {"Name": "Intel Core i7-6700", "Manufacturer": "GenuineIntel", "NumberOfCores": 4}
            if "Win32_BaseBoard" in command:
                return {"Manufacturer": "Example", "Product": "Board A"}
            if "Win32_VideoController" in command:
                return {"Name": "Intel HD Graphics", "PNPDeviceID": sensitive}
            if "Win32_NetworkAdapter" in command:
                return {"ProductName": "Intel Wired Adapter", "PNPDeviceID": "PCI\\VEN_8086&DEV_15B8\\MY-MAC"}
            if "Win32_DiskDrive" in command:
                return [{"Model": "NVMe Sample", "Size": "500000000000", "InterfaceType": "SCSI"}]
            if "Win32_ComputerSystem" in command:
                return {"TotalPhysicalMemory": "17179869184"}
            return None
        with patch.object(module.platform, "system", return_value="Windows"), \
             patch.object(module, "_powershell", side_effect=fake_powershell), \
             patch.object(module, "_win_firmware_type", return_value="UEFI"):
            report = module.scan_hardware()
        hw = report["hardware"]
        self.assertEqual(hw["gpus"][0]["pci_id"], "8086:1912")
        self.assertEqual(hw["network_adapters"][0]["pci_id"], "8086:15B8")
        self.assertEqual(hw["firmware"], "UEFI")
        self.assertEqual(hw["memory_bytes"], 17179869184)
        self.assertEqual(hw["storage"][0]["bytes"], 500000000000)
        self.assertEqual(module.inventory_gaps(report), [])
        payload = json.dumps(report).upper()
        self.assertNotIn("SENSITIVE-INSTANCE-ID", payload)
        self.assertNotIn("MY-MAC", payload)
        self.assertNotIn("SUBSYS_", payload)

    def test_stored_report_never_promises_efi(self):
        report = {"hardware": {"cpu": {"name": "Intel Core i7-6700"},
                               "gpus": [{"name": "Example", "pci_id": "8086:1912"}],
                               "firmware": "UEFI", "storage": [{"model": "Drive"}],
                               "network_adapters": [{"pci_id": "8086:15B8"}],
                               "motherboard": {"model": "Board"}}}
        result = module.evaluate(report, self.catalog)
        self.assertFalse(result["can_generate_efi"])
        self.assertFalse(result["boot_verified"])
        self.assertEqual(result["cpu_family"], "intel-skylake")

    def test_offline_ui_contains_import_and_no_remote_script(self):
        ui = (ROOT / "Setup-Assistant" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="import-report"', ui)
        self.assertNotIn("<script src=", ui)
        self.assertIn('can_generate_efi:false', ui)


if __name__ == "__main__":
    unittest.main()
