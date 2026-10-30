"""Read-only regular-file GPT/ESP image structural and SHA-256 audit.

NEVER writes physical disks. GPT/FAT BPB plausibility does not establish FAT
filesystem integrity, EFI contents, publisher provenance or bootability.
"""
from __future__ import annotations
import argparse
import hashlib
import os
import json
from pathlib import Path
import re
import stat
import struct
import uuid
import zlib
from archive_integrity import _same_opened_file

SECTOR = 512
MAX_IMAGE = 64 * 1024**3
MAX_ENTRIES_BYTES = 16 * 1024 * 1024
# Microsoft FAT specification: FAT32 starts at 65,525 data clusters.
FAT32_MIN_CLUSTERS = 65525
ESP_TYPE = uuid.UUID('c12a7328-f81f-11d2-ba4b-00a0c93ec93b').bytes_le


def read_exact(fp, offset, size, length):
    if offset < 0 or size < 0 or offset + size > length:
        raise ValueError('Image read outside bounds')
    fp.seek(offset)
    data = fp.read(size)
    if len(data) != size:
        raise ValueError('Truncated image read')
    return data


def read_gpt(fp, lba, length):
    raw = read_exact(fp, lba * SECTOR, SECTOR, length)
    if raw[:8] != b'EFI PART':
        raise ValueError('Missing GPT signature')
    revision, size, checksum, reserved = struct.unpack_from('<IIII', raw, 8)
    if revision != 0x10000 or not 92 <= size <= SECTOR or reserved:
        raise ValueError('Unsupported GPT header')
    if any(raw[size:]):
        raise ValueError('GPT header reserved trailing bytes are nonzero')
    checked = bytearray(raw[:size])
    checked[16:20] = bytes(4)
    if zlib.crc32(checked) != checksum:
        raise ValueError('GPT header CRC mismatch')
    current, backup, first, last = struct.unpack_from('<QQQQ', raw, 24)
    disk_guid = raw[56:72]
    table_lba, count, entry_size, entries_crc = struct.unpack_from('<QIII', raw, 72)
    sectors = length // SECTOR
    if current != lba or backup >= sectors or backup == current:
        raise ValueError('GPT header location mismatch')
    if not 2 <= first <= last < sectors - 1 or disk_guid == bytes(16):
        raise ValueError('Invalid GPT usable range or disk GUID')
    if (count < 1 or entry_size < 128 or entry_size & (entry_size - 1) or
            count * entry_size < 16384 or count * entry_size > MAX_ENTRIES_BYTES):
        raise ValueError('Invalid GPT entry table size')
    table_size = count * entry_size
    table_sectors = (table_size + SECTOR - 1) // SECTOR
    if table_lba < 2 or table_lba + table_sectors > sectors:
        raise ValueError('GPT entry table out of bounds')
    if not (table_lba + table_sectors <= first or table_lba > last):
        raise ValueError('GPT entry table overlaps usable space')
    table = read_exact(fp, table_lba * SECTOR, table_size, length)
    if zlib.crc32(table) != entries_crc:
        raise ValueError('GPT partition table CRC mismatch')
    return dict(current=current, backup=backup, first=first, last=last,
                guid=disk_guid, table=table, count=count, entry_size=entry_size,
                table_lba=table_lba)


def _validate_fat32_esp(fp, length, start, end):
    """Check ESP FAT32 metadata only; this does not validate directory contents."""
    boot = read_exact(fp, start * SECTOR, SECTOR, length)
    bps = struct.unpack_from('<H', boot, 11)[0]
    cluster, reserved, fats = boot[13], struct.unpack_from('<H', boot, 14)[0], boot[16]
    root_entries = struct.unpack_from('<H', boot, 17)[0]
    total16 = struct.unpack_from('<H', boot, 19)[0]
    fs_version = struct.unpack_from('<H', boot, 42)[0]
    fat16 = struct.unpack_from('<H', boot, 22)[0]
    total, fat32 = struct.unpack_from('<II', boot, 32)
    root_cluster = struct.unpack_from('<I', boot, 44)[0]
    fat_flags = struct.unpack_from('<H', boot, 40)[0]
    media = boot[21]
    fsinfo_sector, backup_boot_sector = struct.unpack_from('<HH', boot, 48)
    # Bit 7 disables FAT mirroring; then the low nibble selects
    # the active FAT. All other FAT32 flags bits are reserved.
    fat_flags_valid = not (fat_flags & 0xff70) and (
        not (fat_flags & 0x80) or (fat_flags & 0xf) < fats)
    fsinfo_valid = fsinfo_sector == 0xffff or 0 < fsinfo_sector < reserved
    backup_boot_valid = backup_boot_sector in (0, 0xffff) or (
        0 < backup_boot_sector and backup_boot_sector + 2 < reserved and
        backup_boot_sector != fsinfo_sector and
        (fsinfo_sector == 0xffff or backup_boot_sector + fsinfo_sector < reserved))
    data_sectors = total - reserved - fats * fat32
    cluster_count = data_sectors // cluster if cluster else 0
    fat_entry_capacity = fat32 * SECTOR // 4
    if (boot[510:512] != bytes.fromhex('55aa') or boot[0] not in (0xe9, 0xeb) or
            bps != SECTOR or cluster not in (1, 2, 4, 8, 16, 32, 64, 128) or
            reserved < 1 or fats not in (1, 2) or root_entries or total16 or fat16 or fs_version or
            (media != 0xf0 and not 0xf8 <= media <= 0xff) or any(boot[52:64]) or
            not fat_flags_valid or not fsinfo_valid or not backup_boot_valid or
            fat32 < 1 or root_cluster < 2 or not 0 < total <= end - start + 1 or
            reserved + fats * fat32 >= total or
            cluster_count < FAT32_MIN_CLUSTERS or
            not 2 <= root_cluster < cluster_count + 2 or
            fat_entry_capacity < cluster_count + 2):
        raise ValueError('ESP FAT32 BPB structurally implausible')
    # Read-only cross-checks of the FAT32 reserved region. These are
    # metadata checks, NOT a FAT-chain walk or filesystem verification.
    def inspect_fsinfo(sector):
        info = read_exact(fp, (start + sector) * SECTOR, SECTOR, length)
        lead, structure = struct.unpack_from('<I', info, 0)[0], struct.unpack_from('<I', info, 484)[0]
        free_count, next_free = struct.unpack_from('<II', info, 488)
        trail = struct.unpack_from('<I', info, 508)[0]
        if (lead != 0x41615252 or structure != 0x61417272 or trail != 0xaa550000 or
                (free_count != 0xffffffff and free_count > cluster_count) or
                (next_free != 0xffffffff and not 2 <= next_free < cluster_count + 2)):
            raise ValueError('FAT32 FSInfo metadata invalid')

    if fsinfo_sector != 0xffff:
        inspect_fsinfo(fsinfo_sector)
    if backup_boot_sector not in (0, 0xffff):
        saved_boot = read_exact(fp, (start + backup_boot_sector) * SECTOR, SECTOR, length)
        if saved_boot != boot:
            raise ValueError('FAT32 backup boot sector differs from primary')
        if fsinfo_sector != 0xffff:
            inspect_fsinfo(backup_boot_sector + fsinfo_sector)

    # FAT[0] and FAT[1] must contain reserved markers. The FAT entry
    # for the root-directory start cluster must also be allocated;
    # otherwise an empty FAT table can masquerade as a formatted ESP.
    # These sampled entries do NOT constitute a full FAT-chain walk.
    active_fats = (range(fats) if not fat_flags & 0x80 else (fat_flags & 0xf,))
    sampled_entries = []
    for fat_index in active_fats:
        fat_start = (start + reserved + fat_index * fat32) * SECTOR
        fat_head = read_exact(fp, fat_start, 8, length)
        entry0, entry1 = struct.unpack('<II', fat_head)
        root_entry = struct.unpack('<I', read_exact(fp, fat_start + root_cluster * 4, 4, length))[0] & 0x0fffffff
        if ((entry0 & 0x0fffff00) != 0x0fffff00 or
                (entry0 & 0xff) != media or
                (entry1 & 0x0fffffff) < 0x0ffffff8 or
                not (2 <= root_entry < cluster_count + 2 or root_entry >= 0x0ffffff8)):
            raise ValueError('FAT32 reserved or root-directory FAT entry invalid')
        sampled_entries.append((entry0 & 0x0fffffff, entry1 & 0x0fffffff, root_entry))
    if len(sampled_entries) > 1 and len(set(sampled_entries)) != 1:
        raise ValueError('Mirrored FAT metadata entries disagree')


def audit_image(path, expected_sha256):
    result = dict(audit_complete=False, image_integrity_passed=False, gpt_structure_passed=False,
                  esp_boot_sector_plausible=False, image_consistency_passed=False, physical_readback_verified=False,
                  filesystem_verified=False, boot_verified=False, safe_to_flash=False,
                  errors=[], notice='Regular-file readback only; NOT proof of safe flashing or boot')
    try:
        if not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-fA-F]{64}', expected_sha256):
            raise ValueError('Expected full SHA-256 digest required')
        image = Path(path)
        if image.suffix.lower() != '.img' or image.is_symlink() or (
                hasattr(image, 'is_junction') and image.is_junction()):
            raise ValueError('Only non-linked .img regular files accepted')
        st = image.lstat()
        if not stat.S_ISREG(st.st_mode) or not (SECTOR * 128 <= st.st_size <= MAX_IMAGE) or st.st_size % SECTOR:
            raise ValueError('Not a bounded sector-aligned regular image')
        if getattr(st, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
            raise ValueError('Reparse-point image refused')
        # Open the same regular file we inspected, without following links on
        # platforms that support O_NOFOLLOW. O_NONBLOCK avoids FIFO hangs if
        # a pathname is maliciously swapped between lstat and open.
        flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0)
        flags |= getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        fd = os.open(image, flags)
        with os.fdopen(fd, 'rb') as fp:
            opened = os.fstat(fp.fileno())
            if not _same_opened_file(st, opened):
                raise ValueError('Image changed between pathname and open handle')
            length = opened.st_size
            digest = hashlib.sha256()
            for chunk in iter(lambda: fp.read(1024 * 1024), b''):
                digest.update(chunk)
            if digest.hexdigest() != expected_sha256.lower():
                raise ValueError('Image SHA-256 mismatch')
            result['image_integrity_passed'] = True
            mbr = read_exact(fp, 0, SECTOR, length)
            if mbr[510:512] != bytes.fromhex('55aa'):
                raise ValueError('Invalid protective MBR signature')
            sectors = length // SECTOR
            slots = [mbr[446 + 16*i:462 + 16*i] for i in range(4)]
            if (slots[0][4] != 0xee or any(any(slot) for slot in slots[1:]) or
                    struct.unpack_from('<I', slots[0], 8)[0] != 1 or
                    struct.unpack_from('<I', slots[0], 12)[0] != min(sectors - 1, 0xffffffff)):
                raise ValueError('Missing protective MBR or hybrid MBR detected')
            sectors = length // SECTOR
            primary, backup = read_gpt(fp, 1, length), read_gpt(fp, sectors - 1, length)
            if (primary['backup'] != sectors - 1 or backup['backup'] != 1 or
                    any(primary[k] != backup[k] for k in ('first', 'last', 'guid', 'count', 'entry_size', 'table'))):
                raise ValueError('Primary/backup GPT mismatch')
            if (primary['table_lba'] != 2 or
                    backup['table_lba'] + (len(backup['table']) + SECTOR - 1) // SECTOR != sectors - 1):
                raise ValueError('Noncanonical GPT table locations')
            table_sectors = (len(primary['table']) + SECTOR - 1) // SECTOR
            if (primary['first'] < primary['table_lba'] + table_sectors or
                    primary['last'] >= backup['table_lba']):
                raise ValueError('GPT usable range overlaps partition tables')
            partitions, esp, partition_guids = [], [], set()
            for i in range(primary['count']):
                row = primary['table'][i*primary['entry_size']:(i+1)*primary['entry_size']]
                if row[:16] == bytes(16):
                    if any(row):
                        raise ValueError('Unused GPT entry contains stale nonzero data')
                    continue
                start, end = struct.unpack_from('<QQ', row, 32)
                if (row[16:32] == bytes(16) or row[16:32] in partition_guids or
                        not primary['first'] <= start <= end <= primary['last']):
                    raise ValueError('Invalid or duplicate partition GUID or bounds')
                partition_guids.add(row[16:32])
                if any(not (end < a or start > b) for a, b in partitions):
                    raise ValueError('Overlapping GPT partitions')
                partitions.append((start, end))
                if row[:16] == ESP_TYPE:
                    esp.append((start, end))
            if len(esp) != 1:
                raise ValueError('Expected exactly one EFI System Partition')
            result['gpt_structure_passed'] = True
            start, end = esp[0]
            _validate_fat32_esp(fp, length, start, end)
            result['esp_boot_sector_plausible'] = True
            # A mutable image can change after its initial digest and before
            # structural reads. Re-hash the SAME opened handle to detect such
            # ordinary in-place changes, even when timestamps are restored.
            fp.seek(0)
            second_digest = hashlib.sha256()
            for chunk in iter(lambda: fp.read(1024 * 1024), b''):
                second_digest.update(chunk)
            if second_digest.hexdigest() != expected_sha256.lower():
                raise ValueError('Image changed since initial SHA-256 verification')
            final = os.fstat(fp.fileno())
            if (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns) != (
                    opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns):
                raise ValueError('Image changed during audit')
            result['image_consistency_passed'] = True
            result['audit_complete'] = True
    except (ValueError, OSError, OverflowError, struct.error) as exc:
        result['errors'].append(str(exc))
        result['audit_complete'] = False
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read-only regular-file GPT/ESP image audit')
    parser.add_argument('--image', required=True)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    report = audit_image(args.image, args.expected_sha256)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['audit_complete'] else 2)
