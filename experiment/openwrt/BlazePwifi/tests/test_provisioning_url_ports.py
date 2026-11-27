#!/usr/bin/env python3
"""Provisioning tools must reject unusable URL ports before writing output."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INVALID_PORTS = ("abc", "-1", "65536", "99999")
VALID_AUTHORITIES = ("example.invalid", "example.invalid:443", "example.invalid:8443", "example.invalid:65535")


class ProvisioningUrlPortChecks(unittest.TestCase):
    def invoke(self, tool, apk_url, server_url="https://192.168.1.1:8443"):
        with tempfile.TemporaryDirectory() as td:
            apk = Path(td) / "fixture.apk"
            apk.write_bytes(b"stable dummy APK checksum input")
            output = Path(td) / "provisioning.out"
            args = [sys.executable, str(ROOT / "tools" / tool),
                    "--apk", str(apk), "--apk-url", apk_url, "--out", str(output)]
            if tool == "make-provisioning.py":
                args += ["--server-url", server_url, "--enrollment-token",
                         "000000000000.000000000000000000000000000000000000"]
            else:
                args += ["--template", str(ROOT / "tools" / "BlazeRental-QR-Setup.template.html"),
                         "--qrcode-js", str(ROOT / "ui" / "vendor" / "qrcode" / "qrcode.js")]
            result = subprocess.run(args, capture_output=True, text=True)
            return result, output.read_text(encoding="utf-8") if output.exists() else None

    def test_invalid_apk_ports_refused_without_output(self):
        for tool in ("make-provisioning.py", "build-rental-qr-tool.py"):
            for port in INVALID_PORTS:
                with self.subTest(tool=tool, port=port):
                    result, output = self.invoke(tool, f"https://example.invalid:{port}/rental.apk")
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("--apk-url", result.stderr)
                    self.assertIsNone(output)

    def test_invalid_server_ports_refused_without_output(self):
        for port in INVALID_PORTS:
            with self.subTest(port=port):
                result, output = self.invoke("make-provisioning.py", "https://example.invalid/rental.apk",
                                             f"https://example.invalid:{port}")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("--server-url", result.stderr)
                self.assertIsNone(output)

    def test_valid_apk_ports_preserved_in_json(self):
        for authority in VALID_AUTHORITIES:
            with self.subTest(authority=authority):
                url = f"https://{authority}/rental.apk"
                result, output = self.invoke("make-provisioning.py", url)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(output)["android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION"], url)

    def test_valid_server_ports_preserved_in_json(self):
        for authority in VALID_AUTHORITIES:
            with self.subTest(authority=authority):
                url = f"https://{authority}"
                result, output = self.invoke("make-provisioning.py", "https://example.invalid/rental.apk", url)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(output)["android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE"]["server_url"], url)

    def test_valid_apk_ports_preserved_in_html(self):
        for authority in VALID_AUTHORITIES:
            with self.subTest(authority=authority):
                url = f"https://{authority}/rental.apk"
                result, output = self.invoke("build-rental-qr-tool.py", url)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f'const APK_URL="{url}"', output)


if __name__ == "__main__":
    unittest.main()
