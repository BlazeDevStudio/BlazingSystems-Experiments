"""Synthetic ordinary-file GPT fixture tests. Never accesses physical disks."""
import hashlib
import os
import struct
import sys
import tempfile
import unittest
import uuid
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import image_audit
from image_audit import audit_image, ESP_TYPE, SECTOR

SECTORS = 81920
START, END = 2048, 73727
DISK_GUID = uuid.UUID('00000000-1111-2222-3333-444444444444').bytes_le


def make_header(current, backup, table_lba, table, first=34, last=SECTORS-34):
    raw = bytearray(SECTOR)
    raw[:8] = b'EFI PART'
    struct.pack_into('<IIII', raw, 8, 0x10000, 92, 0, 0)
    struct.pack_into('<QQQQ', raw, 24, current, backup, first, last)
    raw[56:72] = DISK_GUID
    struct.pack_into('<QIII', raw, 72, table_lba, 128, 128, zlib.crc32(table))
    struct.pack_into('<I', raw, 16, zlib.crc32(raw[:92]))
    return raw


def fixture(path, *, hybrid=False, overlap=False, duplicate_guid=False, invalid_bpb=False, wrong_mbr_span=False):
    table = bytearray(128 * 128)
    table[:16] = ESP_TYPE
    table[16:32] = uuid.UUID('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee').bytes_le
    struct.pack_into('<QQ', table, 32, START, END)
    if overlap:
        table[128:144] = uuid.UUID('0fc63daf-8483-4772-8e79-3d69d8477de4').bytes_le
        table[144:160] = uuid.UUID('bbbbbbbb-bbbb-cccc-dddd-eeeeeeeeeeee').bytes_le
        struct.pack_into('<QQ', table, 160, END - 20, END + 20)
    if duplicate_guid:
        table[128:144] = uuid.UUID('0fc63daf-8483-4772-8e79-3d69d8477de4').bytes_le
        table[144:160] = table[16:32]
        struct.pack_into('<QQ', table, 160, END + 1, END + 50)
    with path.open('wb') as fp:
        fp.truncate(SECTORS * SECTOR)
        mbr = bytearray(SECTOR)
        mbr[446 + 4] = 0xee
        struct.pack_into('<II', mbr, 446 + 8, 1, SECTORS - (2 if wrong_mbr_span else 1))
        if hybrid:
            mbr[462 + 4] = 0x07
        mbr[510:512] = bytes.fromhex('55aa')
        fp.seek(0); fp.write(mbr)
        fp.seek(SECTOR); fp.write(make_header(1, SECTORS-1, 2, table))
        fp.seek(2*SECTOR); fp.write(table)
        fp.seek((SECTORS-33)*SECTOR); fp.write(table)
        fp.seek((SECTORS-1)*SECTOR); fp.write(make_header(SECTORS-1, 1, SECTORS-33, table))
        boot = bytearray(SECTOR)
        boot[:3] = bytes.fromhex('eb5890')
        struct.pack_into('<H', boot, 11, 512 if not invalid_bpb else 1024)
        boot[13] = 1
        struct.pack_into('<H', boot, 14, 32)
        boot[16] = 2
        boot[21] = 0xf8
        struct.pack_into('<I', boot, 32, END - START + 1)
        struct.pack_into('<I', boot, 36, 600)
        struct.pack_into('<I', boot, 44, 2)
        struct.pack_into('<HH', boot, 48, 1, 6)
        boot[510:512] = bytes.fromhex('55aa')
        fp.seek(START*SECTOR); fp.write(boot)
        # Populate synthetic FAT32 metadata: this still is NOT a usable
        # filesystem, EFI loader, or a physical disk image acceptance test.
        info = bytearray(SECTOR)
        struct.pack_into('<I', info, 0, 0x41615252)
        struct.pack_into('<III', info, 484, 0x61417272, 0xffffffff, 0xffffffff)
        struct.pack_into('<I', info, 508, 0xaa550000)
        fp.seek((START + 1) * SECTOR); fp.write(info)
        fp.seek((START + 6) * SECTOR); fp.write(boot)
        fp.seek((START + 7) * SECTOR); fp.write(info)
        fat_head = struct.pack('<III', 0x0ffffff8, 0x0fffffff, 0x0fffffff)
        for sector in (32, 32 + 600):
            fp.seek((START + sector) * SECTOR); fp.write(fat_head)
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ImageAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'disposable.img'
        self.digest = fixture(self.path)

    def check(self, expected=True):
        report = audit_image(self.path, hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(report['esp_boot_sector_plausible'], expected, report)
        self.assertFalse(report['physical_readback_verified'])
        self.assertFalse(report['filesystem_verified'])
        self.assertFalse(report['boot_verified'])
        self.assertFalse(report['safe_to_flash'])
        self.assertEqual(report['audit_complete'], expected)
        return report

    def test_valid_synthetic_gpt_and_bpb_are_not_boot_proof(self):
        self.check()

    def test_wrong_independent_hash_fails(self):
        self.assertFalse(audit_image(self.path, '0'*64)['image_integrity_passed'])

    def test_missing_hash_fails(self):
        self.assertFalse(audit_image(self.path, '')['image_integrity_passed'])

    def test_primary_header_crc_tamper_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek(SECTOR+56); fp.write(b'X')
        self.check(False)

    def test_backup_table_crc_tamper_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek((SECTORS-33)*SECTOR+10); fp.write(b'X')
        self.check(False)

    def test_hybrid_mbr_fails(self):
        fixture(self.path, hybrid=True)
        self.check(False)

    def test_overlapping_partitions_fail(self):
        fixture(self.path, overlap=True)
        self.check(False)

    def test_invalid_esp_bpb_fails(self):
        fixture(self.path, invalid_bpb=True)
        self.check(False)

    def test_symlink_is_refused(self):
        alias = Path(self.temp.name) / 'alias.img'
        try:
            alias.symlink_to(self.path)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation unavailable')
        self.assertFalse(audit_image(alias, self.digest)['image_integrity_passed'])

    def test_audit_is_read_only(self):
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertTrue(audit_image(self.path, before)['audit_complete'])
        self.assertEqual(before, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_duplicate_partition_guid_rejected(self):
        fixture(self.path, duplicate_guid=True)
        self.check(False)

    def test_protective_mbr_wrong_coverage_rejected(self):
        fixture(self.path, wrong_mbr_span=True)
        self.check(False)


    def test_stale_data_in_unused_partition_entry_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek(2 * SECTOR + 128 + 16)
            fp.write(b'\x01')
        self.check(False)

    def test_primary_table_crc_tamper_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek(2 * SECTOR + 9)
            fp.write(b'\x42')
        self.check(False)

    def test_backup_header_crc_tamper_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek((SECTORS - 1) * SECTOR + 56)
            fp.write(b'\x42')
        self.check(False)

    def test_gpt_header_reserved_trailing_bytes_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek(SECTOR + 100)
            fp.write(b'\x01')
        self.check(False)

    def test_bpb_fat_too_small_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 36)
            fp.write(struct.pack('<I', 1))
        self.check(False)

    def test_bpb_root_cluster_out_of_bounds_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 44)
            fp.write(struct.pack('<I', 80000))
        self.check(False)

    def test_bpb_zero_cluster_size_fails(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 13)
            fp.write(b'\x00')
        self.check(False)

    def test_wrong_image_length_fails(self):
        with self.path.open('ab') as fp:
            fp.write(b'\x00')
        self.check(False)

    def test_non_img_extension_fails(self):
        self.assertFalse(audit_image(self.path.with_suffix('.raw'), self.digest)['image_integrity_passed'])

    def test_mutation_after_initial_hash_detected_even_if_mtime_restored(self):
        original = image_audit.read_exact
        before = self.path.stat()
        mutated = False

        def mutate_once(fp, offset, size, length):
            nonlocal mutated
            if not mutated:
                mutated = True
                # Sector outside metadata: all GPT/BPB checks still pass.
                with self.path.open('r+b') as writer:
                    writer.seek(100 * SECTOR)
                    writer.write(b'X')
                os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))
            return original(fp, offset, size, length)

        with patch.object(image_audit, 'read_exact', side_effect=mutate_once):
            report = audit_image(self.path, self.digest)
        self.assertFalse(report['audit_complete'])
        self.assertFalse(report['image_consistency_passed'])
        self.assertTrue(any('changed since initial SHA-256' in error for error in report['errors']), report)




    def test_gpt_partition_array_below_16k_minimum_rejected(self):
        # Rebuild header checksums to isolate the UEFI 16-KiB minimum.
        with self.path.open('r+b') as fp:
            fp.seek(2 * SECTOR)
            table = fp.read(128 * 128)
            for lba in (1, SECTORS - 1):
                fp.seek(lba * SECTOR)
                raw = bytearray(fp.read(SECTOR))
                struct.pack_into('<I', raw, 80, 1)
                struct.pack_into('<I', raw, 88, zlib.crc32(table[:128]))
                struct.pack_into('<I', raw, 16, 0)
                struct.pack_into('<I', raw, 16, zlib.crc32(raw[:92]))
                fp.seek(lba * SECTOR)
                fp.write(raw)
        self.check(False)

    def test_gpt_usable_range_overlaps_backup_table_rejected(self):
        # Recompute valid CRCs, proving rejection is about table/usable
        # region overlap, not merely a corrupt GPT header checksum.
        with self.path.open('r+b') as fp:
            fp.seek(2 * SECTOR)
            table = fp.read(128 * 128)
            fp.seek(SECTOR)
            fp.write(make_header(1, SECTORS-1, 2, table, last=SECTORS-2))
            fp.seek((SECTORS-1)*SECTOR)
            fp.write(make_header(SECTORS-1, 1, SECTORS-33, table, last=SECTORS-2))
        self.check(False)

    def test_fat12_sized_volume_masquerading_as_fat32_rejected(self):
        # An otherwise plausible BPB cannot call a <65,525-cluster FAT12/16
        # sized volume FAT32. This is only structural plausibility.
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 32)
            fp.write(struct.pack('<I', 4096))
        self.check(False)

    def test_fat32_mirroring_invalid_active_fat_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 40)
            fp.write(struct.pack('<H', 0x82))  # FAT #2 when only 0 and 1 exist
        self.check(False)

    def test_fat32_reserved_flags_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 40)
            fp.write(struct.pack('<H', 0x0100))
        self.check(False)

    def test_fsinfo_sector_outside_reserved_area_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 48)
            fp.write(struct.pack('<H', 33))
        self.check(False)

    def test_backup_boot_overlaps_fsinfo_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 50)
            fp.write(struct.pack('<H', 1))
        self.check(False)

    def test_fat32_total16_nonzero_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 19)
            fp.write(struct.pack('<H', 12))
        self.check(False)

    def test_fat32_nonzero_filesystem_version_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 42)
            fp.write(struct.pack('<H', 1))
        self.check(False)


    def test_spec_correct_fsinfo_trail_at_byte_508_accepted(self):
        with self.path.open('r+b') as fp:
            for sector in (START + 1, START + 7):
                fp.seek(sector * SECTOR + 496)
                fp.write(bytes(4))
                fp.seek(sector * SECTOR + 508)
                fp.write(struct.pack('<I', 0xaa550000))
        self.check(True)

    def test_wrong_actual_fsinfo_trail_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 1) * SECTOR + 508)
            fp.write(bytes(4))
        self.check(False)

    def test_primary_fsinfo_bad_signature_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 1) * SECTOR)
            fp.write(b'FAIL')
        self.check(False)

    def test_primary_fsinfo_impossible_free_count_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 1) * SECTOR + 488)
            fp.write(struct.pack('<I', 90000))
        self.check(False)

    def test_primary_fsinfo_invalid_next_free_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 1) * SECTOR + 492)
            fp.write(struct.pack('<I', 1))
        self.check(False)

    def test_backup_boot_sector_mismatch_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 6) * SECTOR + 11)
            fp.write(b'X')
        self.check(False)

    def test_backup_fsinfo_bad_signature_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 7) * SECTOR + 484)
            fp.write(b'FAIL')
        self.check(False)

    def test_first_fat_reserved_entry_corruption_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 32) * SECTOR)
            fp.write(bytes(8))
        self.check(False)

    def test_second_mirrored_fat_reserved_entry_corruption_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 32 + 600) * SECTOR)
            fp.write(bytes(8))
        self.check(False)

    def test_free_root_cluster_rejected_even_with_valid_reserved_fat(self):
        # FAT[0] and FAT[1] alone cannot prove a formatted FAT32 volume.
        for sector in (32, 32 + 600):
            with self.path.open('r+b') as fp:
                fp.seek((START + sector) * SECTOR + 8)
                fp.write(struct.pack('<I', 0))
        self.check(False)

    def test_bad_root_cluster_marker_rejected(self):
        for sector in (32, 32 + 600):
            with self.path.open('r+b') as fp:
                fp.seek((START + sector) * SECTOR + 8)
                fp.write(struct.pack('<I', 0x0ffffff7))
        self.check(False)

    def test_mirrored_root_directory_entries_must_agree(self):
        with self.path.open('r+b') as fp:
            fp.seek((START + 32 + 600) * SECTOR + 8)
            fp.write(struct.pack('<I', 3))
        self.check(False)

    def test_nondefault_root_cluster_with_allocated_entry(self):
        with self.path.open('r+b') as fp:
            for sector in (START, START + 6):
                fp.seek(sector * SECTOR + 44)
                fp.write(struct.pack('<I', 3))
            for sector in (32, 32 + 600):
                fp.seek((START + sector) * SECTOR + 12)
                fp.write(struct.pack('<I', 0x0fffffff))
        self.check(True)

    def test_root_directory_chain_link_to_valid_next_cluster(self):
        for sector in (32, 32 + 600):
            with self.path.open('r+b') as fp:
                fp.seek((START + sector) * SECTOR + 8)
                fp.write(struct.pack('<I', 3))
        self.check(True)

    def test_disabled_fat_mirroring_checks_selected_active_fat(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 40)
            fp.write(struct.pack('<H', 0x81))
            fp.seek((START + 6) * SECTOR + 40)
            fp.write(struct.pack('<H', 0x81))
            fp.seek((START + 32) * SECTOR)
            fp.write(bytes(8))
        self.check(True)

    def test_fat32_reserved_bpb_bytes_nonzero_rejected(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 52)
            fp.write(b'X')
        self.check(False)


    def test_fsinfo_and_backup_optional_values_are_explicit(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 48)
            fp.write(struct.pack('<HH', 0xffff, 0))
        self.check(True)

    def test_backup_fsinfo_stale_free_count_is_not_false_failure(self):
        # Backup FSInfo is not required to mirror the primary free count.
        with self.path.open('r+b') as fp:
            fp.seek((START + 7) * SECTOR + 488)
            fp.write(struct.pack('<I', 1234))
        self.check(True)

    def test_media_descriptor_disagrees_with_fat_reserved_entry(self):
        with self.path.open('r+b') as fp:
            fp.seek(START * SECTOR + 21)
            fp.write(b'\xf0')
            fp.seek((START + 6) * SECTOR + 21)
            fp.write(b'\xf0')
        self.check(False)


if __name__ == '__main__':
    unittest.main()
