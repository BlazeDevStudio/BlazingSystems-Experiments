"""Synthetic fixtures only; archive audit must never extract or authorize boot."""
import hashlib
import io
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import archive_integrity as a


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.p = Path(self.temp.name) / "asset.zip"

    def put(self, names, compression=zipfile.ZIP_STORED):
        with zipfile.ZipFile(self.p, "w", compression=compression) as z:
            for name, content in names:
                z.writestr(name, content)
        return self.check()

    def check(self, **kwargs):
        b = self.p.read_bytes()
        return a.audit_zip(self.p, kwargs.get("digest", hashlib.sha256(b).hexdigest()),
                           kwargs.get("size", len(b)))

    def test_valid_archive(self):
        r = self.put([("EFI/BOOT/BOOTX64.EFI", b"synthetic-not-UEFI")])
        self.assertTrue(r["zip_structure_valid"], r)
        self.assertTrue(r["archive_hash_match"])
        self.assertEqual(r["zip_members_checked"], 1)
        self.assertFalse(r["publisher_identity_verified"])
        self.assertFalse(r["component_auth_gate_satisfied"])

    def test_tampered_digest(self):
        r = self.put([("f", b"bytes")])
        self.assertFalse(self.check(digest="0" * 64)["zip_structure_valid"])

    def test_tampered_size(self):
        self.put([("f", b"x")])
        self.assertFalse(self.check(size=self.p.stat().st_size + 1)["zip_structure_valid"])

    def test_empty(self):
        self.assertFalse(self.put([])["zip_structure_valid"])

    def test_non_zip(self):
        self.p.write_bytes(b"not a zip")
        self.assertFalse(self.check()["zip_structure_valid"])

    def test_traversal(self):
        self.assertFalse(self.put([("../evil", b"x")])["zip_structure_valid"])

    def test_absolute_path(self):
        self.assertFalse(self.put([("/EFI/boot", b"x")])["zip_structure_valid"])

    def test_windows_path(self):
        self.assertFalse(self.put([("C:\\temp\\evil", b"x")])["zip_structure_valid"])

    def test_reserved_windows_device(self):
        self.assertFalse(self.put([("EFI/CON.TXT", b"x")])["zip_structure_valid"])

    def test_case_collision(self):
        self.assertFalse(self.put([("Readme", b"1"), ("README", b"2")])["zip_structure_valid"])

    def test_file_as_parent(self):
        self.assertFalse(self.put([("EFI", b"1"), ("EFI/BOOT/a", b"2")])["zip_structure_valid"])

    def test_zip_bomb(self):
        self.assertFalse(self.put([("huge", b"X" * 70000)], zipfile.ZIP_DEFLATED)["zip_structure_valid"])

    def test_symlink_entry(self):
        zi = zipfile.ZipInfo("link")
        zi.create_system = 3
        zi.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(self.p, "w") as z:
            z.writestr(zi, "target")
        self.assertFalse(self.check()["zip_structure_valid"])

    def test_symlink_archive(self):
        self.put([("normal", b"x")])
        link = self.p.with_name("link.zip")
        try:
            link.symlink_to(self.p)
        except (OSError, NotImplementedError):
            self.skipTest("File symlinks unavailable")
        self.assertFalse(a.audit_zip(link, hashlib.sha256(self.p.read_bytes()).hexdigest(), self.p.stat().st_size)["zip_structure_valid"])

    def test_corrupt_zip_member(self):
        self.put([("normal", b"some fixed data")])
        raw = self.p.read_bytes()
        start = raw.index(b"some fixed data")
        raw = raw[:start] + b"changed content!" + raw[start+len(b"some fixed data"):]
        self.p.write_bytes(raw)
        self.assertFalse(self.check()["zip_structure_valid"])

    def test_bad_digest_pin(self):
        self.put([("f", b"x")])
        self.assertFalse(self.check(digest="z" * 64)["zip_structure_valid"])

    def test_bad_size_type(self):
        self.put([("f", b"x")])
        self.assertFalse(self.check(size=True)["zip_structure_valid"])


if __name__ == "__main__":
    unittest.main()
