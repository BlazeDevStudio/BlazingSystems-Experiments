#!/usr/bin/env python3
"""Regression for OpenWrt fwtool-signed compressed disk images."""
import gzip
import zlib
import struct
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CHECKER = Path(__file__).resolve().parents[1] / "tools" / "verify-firmware-gzip.py"

def fwtool_signed(data, payload=b"signed-by-lab-key"):
    before = data + payload
    crc = zlib.crc32(before) ^ 0xffffffff
    return before + struct.pack(">4sIB3sI", b"FWx0", crc, 0, b"\0\0\0", len(payload) + 16)


class ImageGzipChecks(unittest.TestCase):
    def check(self, path):
        return subprocess.run([sys.executable, str(CHECKER), str(path)], text=True,
                              capture_output=True)

    def test_plain_gzip_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "plain.img.gz"
            p.write_bytes(gzip.compress(b"disk image" * 100))
            self.assertEqual(self.check(p).returncode, 0)

    def test_valid_fwtool_trailer_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "signed.img.gz"
            p.write_bytes(fwtool_signed(gzip.compress(b"disk image" * 100)))
            self.assertEqual(self.check(p).returncode, 0)
            self.assertNotEqual(subprocess.run(["gzip", "-t", str(p)], capture_output=True).returncode, 0)

    def test_random_garbage_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "corrupt.img.gz"
            p.write_bytes(gzip.compress(b"disk") + b"garbage")
            self.assertNotEqual(self.check(p).returncode, 0)

    def test_wrong_fwtool_length_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "wrong-length.img.gz"
            invalid = bytearray(fwtool_signed(gzip.compress(b"disk")))
            invalid[-1] ^= 1
            p.write_bytes(invalid)
            self.assertNotEqual(self.check(p).returncode, 0)

    def test_bad_gzip_crc_rejected_even_with_fwtool(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad-crc.img.gz"
            compressed = bytearray(gzip.compress(b"disk"))
            compressed[-8] ^= 0xff
            p.write_bytes(fwtool_signed(compressed, b"proof"))
            self.assertNotEqual(self.check(p).returncode, 0)

    def test_fwtool_crc_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad-fwtool-crc.img.gz"
            signed = bytearray(fwtool_signed(gzip.compress(b"disk")))
            signed[-9] ^= 1  # change stored fwtool CRC, leave framing intact
            p.write_bytes(signed)
            self.assertNotEqual(self.check(p).returncode, 0)

    def test_two_valid_fwtool_records_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "two-extensions.img.gz"
            once = fwtool_signed(gzip.compress(b"disk"), b"first")
            p.write_bytes(fwtool_signed(once, b"second"))
            self.assertEqual(self.check(p).returncode, 0)

    def test_truncated_gzip_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "truncated.img.gz"
            p.write_bytes(gzip.compress(b"disk")[:-2])
            self.assertNotEqual(self.check(p).returncode, 0)

if __name__ == "__main__":
    unittest.main()
