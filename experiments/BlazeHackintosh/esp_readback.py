"""Read one short-name EFI/BOOT/BOOTX64.EFI from a local FAT32 disk image.

READ-ONLY and limited to a regular .img file. Does not establish filesystem
integrity, publisher authenticity, valid EFI executable or physical boot.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
import struct

from archive_integrity import _same_opened_file
from image_audit import ESP_TYPE, SECTOR, audit_image, read_exact, read_gpt

MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_DIRECTORY_CLUSTERS = 128
BOOT_PATH = (b'EFI        ', b'BOOT       ', b'BOOTX64 EFI')
SHA256 = re.compile(r'[0-9a-fA-F]{64}\Z')


def _hash_file(fp):
    fp.seek(0)
    digest = hashlib.sha256()
    for block in iter(lambda: fp.read(1024 * 1024), b''):
        digest.update(block)
    return digest.hexdigest()


def audit_boot_efi(path, image_sha256, boot_file_sha256):
    """Check a pinned 8.3 EFI boot file's bytes, never read a device or write.

    Long filenames and unusually large directory chains are intentionally
    unsupported; they fail closed rather than being interpreted heuristically.
    """
    report = dict(file_hash_match=False, file_bytes_checked=0,
                  image_hash_match=False, physical_readback_verified=False,
                  filesystem_verified=False, boot_verified=False,
                  safe_to_flash=False, errors=[])
    try:
        if not all(isinstance(x, str) and SHA256.fullmatch(x)
                   for x in (image_sha256, boot_file_sha256)):
            raise ValueError('Both 64-character SHA-256 pins are required')
        image = Path(path)
        if (image.suffix.lower() != '.img' or image.is_symlink() or
                (hasattr(image, 'is_junction') and image.is_junction())):
            raise ValueError('Only nonlinked regular .img files accepted')
        scanned = audit_image(image, image_sha256)
        if not scanned['audit_complete']:
            raise ValueError('Existing GPT/ESP structural audit failed: ' +
                             '; '.join(scanned['errors']))
        before = image.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('Image is not a regular file')
        flags = (os.O_RDONLY | getattr(os, 'O_BINARY', 0) |
                 getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        fd = os.open(image, flags)
        with os.fdopen(fd, 'rb') as fp:
            opened = os.fstat(fp.fileno())
            if not _same_opened_file(before, opened):
                raise ValueError('Image path/handle identity changed')
            length = opened.st_size
            if _hash_file(fp) != image_sha256.lower():
                raise ValueError('Opened image SHA-256 differs from pin')
            report['image_hash_match'] = True

            gpt = read_gpt(fp, 1, length)
            start, end = None, None
            for i in range(gpt['count']):
                row = gpt['table'][i*gpt['entry_size']:(i+1)*gpt['entry_size']]
                if row[:16] == ESP_TYPE:
                    if start is not None:
                        raise ValueError('Multiple EFI System Partitions')
                    start, end = struct.unpack_from('<QQ', row, 32)
            if start is None:
                raise ValueError('No EFI System Partition')

            boot = read_exact(fp, start * SECTOR, SECTOR, length)
            sectors_per_cluster = boot[13]
            reserved = struct.unpack_from('<H', boot, 14)[0]
            fats = boot[16]
            fat_sectors = struct.unpack_from('<I', boot, 36)[0]
            total_sectors = struct.unpack_from('<I', boot, 32)[0]
            root = struct.unpack_from('<I', boot, 44)[0]
            fat_flags = struct.unpack_from('<H', boot, 40)[0]
            cluster_bytes = sectors_per_cluster * SECTOR
            data_lba = start + reserved + fats * fat_sectors
            clusters = (total_sectors - reserved - fats * fat_sectors) // sectors_per_cluster
            mirrored = not fat_flags & 0x80
            active_fats = range(fats) if mirrored else (fat_flags & 0xf,)

            def next_cluster(cluster):
                if not 2 <= cluster < clusters + 2 or (cluster + 1) * 4 > fat_sectors * SECTOR:
                    raise ValueError('FAT cluster outside bounded table')
                entries = [
                    struct.unpack('<I', read_exact(
                        fp, (start + reserved + index * fat_sectors) * SECTOR +
                        cluster * 4, 4, length))[0] & 0x0fffffff
                    for index in active_fats
                ]
                if len(set(entries)) != 1:
                    raise ValueError('Mirrored FAT chains disagree')
                return entries[0]

            def cluster_bytes_at(cluster):
                if not 2 <= cluster < clusters + 2:
                    raise ValueError('Invalid data cluster')
                lba = data_lba + (cluster - 2) * sectors_per_cluster
                if lba + sectors_per_cluster > end + 1:
                    raise ValueError('Cluster outside ESP')
                return read_exact(fp, lba * SECTOR, cluster_bytes, length)

            def find_short_name(root_cluster, expected, is_directory):
                visited = set()
                cluster = root_cluster
                found = None
                for _ in range(MAX_DIRECTORY_CLUSTERS):
                    if cluster in visited:
                        raise ValueError('Directory FAT chain cycle')
                    visited.add(cluster)
                    data = cluster_bytes_at(cluster)
                    for pos in range(0, len(data), 32):
                        row = data[pos:pos+32]
                        if row[0] == 0:
                            if found is None:
                                raise ValueError('EFI short-name path absent')
                            return found
                        if row[0] == 0xe5:
                            continue
                        attr = row[11]
                        if attr == 0x0f:
                            raise ValueError('Long filename entry unsupported')
                        if attr & 0x08:
                            continue  # Volume label, not a file.
                        if row[:11] == expected:
                            if found is not None:
                                raise ValueError('Duplicate EFI short-name entry')
                            if bool(attr & 0x10) != is_directory or attr & 0xc0:
                                raise ValueError('EFI entry has invalid type')
                            target = (struct.unpack_from('<H', row, 20)[0] << 16 |
                                      struct.unpack_from('<H', row, 26)[0])
                            size = struct.unpack_from('<I', row, 28)[0]
                            if target < 2 or (is_directory and size):
                                raise ValueError('Invalid EFI directory entry')
                            found = (target, size)
                    nxt = next_cluster(cluster)
                    if nxt >= 0x0ffffff8:
                        if found is None:
                            raise ValueError('EFI short-name path absent')
                        return found
                    cluster = nxt
                raise ValueError('Directory FAT chain exceeds readback limit')

            current = root
            for name in BOOT_PATH[:2]:
                current, _ = find_short_name(current, name, True)
            current, file_size = find_short_name(current, BOOT_PATH[2], False)
            if not 0 < file_size <= MAX_FILE_BYTES:
                raise ValueError('EFI file size outside limit')

            needed = (file_size + cluster_bytes - 1) // cluster_bytes
            digest = hashlib.sha256()
            visited = set()
            remaining = file_size
            for i in range(needed):
                if current in visited:
                    raise ValueError('EFI file FAT chain cycle')
                visited.add(current)
                data = cluster_bytes_at(current)
                used = min(remaining, len(data))
                digest.update(data[:used])
                remaining -= used
                nxt = next_cluster(current)
                if i + 1 == needed:
                    if nxt < 0x0ffffff8:
                        raise ValueError('EFI file chain exceeds declared size')
                elif nxt >= 0x0ffffff8:
                    raise ValueError('EFI file chain ends before declared size')
                current = nxt
            if digest.hexdigest() != boot_file_sha256.lower():
                raise ValueError('EFI file content SHA-256 mismatch')
            if _hash_file(fp) != image_sha256.lower():
                raise ValueError('Image changed while reading EFI file')
            final = os.fstat(fp.fileno())
            if (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns) != (
                    opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns):
                raise ValueError('Image changed during readback')
            report.update(file_hash_match=True, file_bytes_checked=file_size)
    except (ValueError, OSError, OverflowError, struct.error) as exc:
        report['errors'].append(str(exc))
    return report
