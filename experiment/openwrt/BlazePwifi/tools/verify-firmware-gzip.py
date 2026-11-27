#!/usr/bin/env python3
"""Read-only gzip CRC check; allow precisely framed OpenWrt fwtool suffixes.

This verifies structure only. It does not authenticate a firmware signature,
verify device compatibility, or authorize flashing/customer release.
"""
import sys
import struct
import zlib
from pathlib import Path


def verify(path):
    stream = zlib.decompressobj(wbits=31)
    expanded = 0
    trailer = b""
    with Path(path).open("rb") as source:
        while raw := source.read(65536):
            while raw:
                chunk = stream.decompress(raw, 1024 * 1024)
                expanded += len(chunk)
                if expanded > 64 * 1024**3:
                    raise ValueError("decompressed size exceeds inspection ceiling")
                if stream.eof:
                    trailer = stream.unused_data + source.read()
                    break
                raw = stream.unconsumed_tail
            if stream.eof:
                break

    if not stream.eof or not expanded:
        raise ValueError("truncated or empty gzip stream")
    if trailer:
        if len(trailer) > 65536:
            raise ValueError("OpenWrt fwtool suffix exceeds limit")
        remaining = len(trailer)
        end = Path(path).stat().st_size
        count = 0
        while remaining:
            if remaining < 16:
                raise ValueError("unframed data following gzip stream")
            with Path(path).open("rb") as source:
                source.seek(end - 16)
                magic, expected_crc, record_type, pad, length = struct.unpack(">4sIB3sI", source.read(16))
                if (magic != b"FWx0" or record_type not in (0, 1) or
                        pad != b"\0\0\0" or not 16 <= length <= remaining):
                    raise ValueError("malformed OpenWrt fwtool trailer")
                crc = 0
                limit = end - 16
                source.seek(0)
                while limit:
                    block = source.read(min(1024 * 1024, limit))
                    if not block:
                        raise ValueError("short read during fwtool CRC verification")
                    crc = zlib.crc32(block, crc)
                    limit -= len(block)
                if (crc ^ 0xffffffff) != expected_crc:
                    raise ValueError("OpenWrt fwtool CRC mismatch")
            end -= length
            remaining -= length
            count += 1
        return expanded, f"{count} fwtool record(s) CRC-valid (signature NOT verified)"
    return expanded, "no trailer"


def main(argv):
    if len(argv) != 2:
        print("usage: verify-firmware-gzip.py image.img.gz", file=sys.stderr)
        return 2
    try:
        size, suffix = verify(argv[1])
    except (OSError, ValueError, zlib.error) as error:
        print(f"FIRMWARE-GZIP BLOCKED: {error}", file=sys.stderr)
        return 9
    print(f"FIRMWARE-GZIP PASS: CRC valid; expanded_bytes={size}; {suffix}; no flash authorization")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
