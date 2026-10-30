"""Disposable FAT32 readback regression; only temporary regular-file .img fixtures."""
import hashlib
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from image_audit import SECTOR
from test_image_audit import fixture, START
from esp_readback import audit_boot_efi

DATA_LBA = START + 32 + 2 * 600
PAYLOAD = b'A' * SECTOR + b'B' * 188
FILE_SHA = hashlib.sha256(PAYLOAD).hexdigest()


def _dir_entry(name, attributes, cluster, size=0):
    row = bytearray(32)
    row[:11] = name
    row[11] = attributes
    struct.pack_into('<H', row, 20, cluster >> 16)
    struct.pack_into('<H', row, 26, cluster & 0xffff)
    struct.pack_into('<I', row, 28, size)
    return row


def add_synthetic_boot_file(path):
    """Populate synthetic 8.3 EFI/BOOT/BOOTX64.EFI; not an executable bootloader."""
    with path.open('r+b') as fp:
        # Mirror the synthetic FAT allocation in both FAT tables.
        for table in (START + 32, START + 32 + 600):
            for cluster, nxt in ((3, 0x0fffffff), (4, 0x0fffffff),
                                 (5, 6), (6, 0x0fffffff)):
                fp.seek(table * SECTOR + cluster * 4)
                fp.write(struct.pack('<I', nxt))
        for cluster, name, attr, child, size in (
                (2, b'EFI        ', 0x10, 3, 0),
                (3, b'BOOT       ', 0x10, 4, 0),
                (4, b'BOOTX64 EFI', 0x20, 5, len(PAYLOAD))):
            fp.seek((DATA_LBA + cluster - 2) * SECTOR)
            fp.write(_dir_entry(name, attr, child, size))
        fp.seek((DATA_LBA + 5 - 2) * SECTOR)
        fp.write(PAYLOAD[:SECTOR])
        fp.seek((DATA_LBA + 6 - 2) * SECTOR)
        fp.write(PAYLOAD[SECTOR:])


def image_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


class FAT32BootReadbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.img = Path(self.temp.name) / 'synthetic.img'
        fixture(self.img)
        add_synthetic_boot_file(self.img)

    def inspect(self, file_sha=FILE_SHA):
        return audit_boot_efi(self.img, image_sha(self.img), file_sha)

    def test_multicluster_boot_file_matches_operator_supplied_hash(self):
        result = self.inspect()
        self.assertTrue(result['file_hash_match'], result)
        self.assertEqual(result['file_bytes_checked'], len(PAYLOAD))
        self.assertFalse(result['physical_readback_verified'])
        self.assertFalse(result['boot_verified'])
        self.assertFalse(result['safe_to_flash'])

    def test_file_bytes_changed_with_recomputed_image_digest_are_rejected(self):
        with self.img.open('r+b') as fp:
            fp.seek((DATA_LBA + 6 - 2) * SECTOR + 15)
            fp.write(b'X')
        self.assertFalse(self.inspect()['file_hash_match'])

    def test_cyclic_fat_chain_is_rejected(self):
        with self.img.open('r+b') as fp:
            for table in (START + 32, START + 32 + 600):
                fp.seek(table * SECTOR + 5 * 4)
                fp.write(struct.pack('<I', 5))
        self.assertFalse(self.inspect()['file_hash_match'])

    def test_missing_efi_directory_is_rejected(self):
        with self.img.open('r+b') as fp:
            fp.seek(DATA_LBA * SECTOR)
            fp.write(b'BAD')
        self.assertFalse(self.inspect()['file_hash_match'])

    def test_long_filename_records_fail_closed(self):
        with self.img.open('r+b') as fp:
            fp.seek(DATA_LBA * SECTOR + 32)
            fp.write(_dir_entry(b'A' * 11, 0x0f, 0))
        self.assertFalse(self.inspect()['file_hash_match'])

    def test_wrong_image_hash_fails_before_filesystem_read(self):
        result = audit_boot_efi(self.img, '0' * 64, FILE_SHA)
        self.assertFalse(result['file_hash_match'])
        self.assertFalse(result['safe_to_flash'])


if __name__ == '__main__':
    unittest.main()
