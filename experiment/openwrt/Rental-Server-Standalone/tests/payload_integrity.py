#!/usr/bin/env python3
"""Verify the exact payload accepted by the standalone installer's checksum gate."""
import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = {
    "root/www/cgi-bin/rental",
    "root/www/cgi-bin/rental-admin",
    "root/www/rental/index.html",
}


class PayloadIntegrity(unittest.TestCase):
    def test_release_manifest_matches_payload_bytes(self):
        self.check_payload((ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines())

    def test_installer_checksum_gate_accepts_current_payload(self):
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        writes = [line for line in installer.splitlines()
                  if re.search(r'>+ \"\$TMP/SHA256SUMS\"$', line)]
        records, modes = [], []
        for line in writes:
            match = re.fullmatch(r"echo '([^']+)' (>>?) \"\$TMP/SHA256SUMS\"", line)
            self.assertIsNotNone(match, "unrecognized installer checksum write")
            records.append(match[1])
            modes.append(match[2])
        self.assertEqual(modes, [">", ">>", ">>"], "installer must retain all three checksum records")
        self.check_payload(records)

    def check_payload(self, records):
        entries = {}
        for record in records:
            match = re.fullmatch(r"([0-9a-f]{64})  (.+)", record)
            self.assertIsNotNone(match, "malformed checksum record")
            expected, path = match.groups()
            self.assertNotIn(path, entries, f"duplicate checksum for {path}")
            entries[path] = expected
        self.assertEqual(set(entries), PAYLOAD, "payload pin list must be complete and exact")
        for path, expected in entries.items():
            with self.subTest(path=path):
                actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                self.assertEqual(actual, expected, f"checksum gate would reject {path}")


if __name__ == "__main__":
    unittest.main()
