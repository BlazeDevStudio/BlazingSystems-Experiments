#!/usr/bin/env python3
"""Compare file-backed bytes of named sections across two exact ESP32 ELF builds.

The caller supplies section tables captured from the exact pinned Xtensa objdump.
Differences are diagnostic output only; the application-image comparator remains
the release gate and must continue to reject non-identical firmware images.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from inspect_esp32_elf_sections import parse_objdump_sections


def _unique_section(sections: list[dict[str, Any]], name: str) -> dict[str, Any]:
    if not isinstance(sections, list):
        raise TypeError("section table must be a list")
    matches = [section for section in sections if section.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {name} section, found {len(matches)}")
    return matches[0]


def _section_bytes(
    elf: bytes | bytearray | memoryview,
    section: dict[str, Any],
    *,
    label: str,
    section_name: str,
) -> bytes:
    if not isinstance(elf, (bytes, bytearray, memoryview)):
        raise TypeError(f"{label} ELF must be bytes")
    size = section.get("size")
    file_offset = section.get("file_offset")
    for field, value in (("size", size), ("file_offset", file_offset)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{label} {section_name} {field} must be an integer")
    if size <= 0:
        raise ValueError(f"{label} {section_name} is empty")
    if file_offset < 0 or file_offset + size > len(elf):
        raise ValueError(f"{label} {section_name} section exceeds ELF file bounds")
    return bytes(elf[file_offset:file_offset + size])


def _difference_ranges(
    first: bytes,
    second: bytes,
    first_file_offset: int,
    second_file_offset: int,
) -> tuple[list[dict[str, Any]], int, list[dict[str, Any]]]:
    ranges: list[dict[str, Any]] = []
    first_differences: list[dict[str, Any]] = []
    differing_count = 0
    range_start: int | None = None
    previous: int | None = None

    def finish_range(start: int, end: int) -> None:
        prefix_end = min(end + 1, start + 16)
        ranges.append(
            {
                "start": start,
                "end": end,
                "first_elf_offset": first_file_offset + start,
                "second_elf_offset": second_file_offset + start,
                "first_bytes_prefix": first[start:prefix_end].hex(),
                "second_bytes_prefix": second[start:prefix_end].hex(),
                "bytes_prefix_truncated": prefix_end < end + 1,
            }
        )

    for offset, (left, right) in enumerate(zip(first, second)):
        if left == right:
            continue
        differing_count += 1
        if len(first_differences) < 16:
            first_differences.append(
                {
                    "section_offset": offset,
                    "first_elf_offset": first_file_offset + offset,
                    "second_elf_offset": second_file_offset + offset,
                    "first_byte": f"0x{left:02x}",
                    "second_byte": f"0x{right:02x}",
                }
            )
        if range_start is None:
            range_start = offset
        elif previous is not None and offset != previous + 1:
            finish_range(range_start, previous)
            range_start = offset
        previous = offset

    if range_start is not None and previous is not None:
        finish_range(range_start, previous)

    total_ranges = len(ranges)
    return ranges[:64], total_ranges, first_differences


def compare_section_bytes(
    first_elf: bytes | bytearray | memoryview,
    second_elf: bytes | bytearray | memoryview,
    first_sections: list[dict[str, Any]],
    second_sections: list[dict[str, Any]],
    section_name: str,
) -> dict[str, Any]:
    """Compare one unique, file-backed section without assuming equal ELF offsets."""
    if not isinstance(section_name, str) or not section_name:
        raise ValueError("section name must be non-empty text")
    first_section = _unique_section(first_sections, section_name)
    second_section = _unique_section(second_sections, section_name)

    for field in ("size", "vma", "lma"):
        first_value = first_section.get(field)
        second_value = second_section.get(field)
        if first_value != second_value:
            raise ValueError(
                f"{section_name} {field} differs between ELF builds: "
                f"{first_value!r} != {second_value!r}"
            )

    first_bytes = _section_bytes(
        first_elf, first_section, label="first", section_name=section_name
    )
    second_bytes = _section_bytes(
        second_elf, second_section, label="second", section_name=section_name
    )
    if len(first_bytes) != len(second_bytes):
        raise ValueError(f"{section_name} section lengths differ")

    first_offset = first_section["file_offset"]
    second_offset = second_section["file_offset"]
    ranges, range_count, first_differences = _difference_ranges(
        first_bytes, second_bytes, first_offset, second_offset
    )
    differing_count = sum(
        item["end"] - item["start"] + 1 for item in ranges
    )
    # The bounded range list may be truncated; count all differing bytes directly.
    differing_count = sum(left != right for left, right in zip(first_bytes, second_bytes))
    return {
        "section": section_name,
        "size": len(first_bytes),
        "vma": f"0x{first_section['vma']:08x}",
        "lma": f"0x{first_section['lma']:08x}",
        "first_file_offset": first_offset,
        "second_file_offset": second_offset,
        "first_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "second_sha256": hashlib.sha256(second_bytes).hexdigest(),
        "status": "DIFFERENT" if differing_count else "IDENTICAL",
        "differing_bytes": differing_count,
        "difference_range_count": range_count,
        "difference_ranges": ranges,
        "difference_ranges_truncated": range_count > len(ranges),
        "first_differences": first_differences,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-elf", required=True, type=Path)
    parser.add_argument("--second-elf", required=True, type=Path)
    parser.add_argument("--first-objdump", required=True, type=Path)
    parser.add_argument("--second-objdump", required=True, type=Path)
    parser.add_argument(
        "--section",
        action="append",
        required=True,
        help="section name to compare; repeat for each exact section",
    )
    args = parser.parse_args(argv)

    try:
        first_elf = args.first_elf.read_bytes()
        second_elf = args.second_elf.read_bytes()
        first_sections = parse_objdump_sections(
            args.first_objdump.read_text(encoding="utf-8")
        )
        second_sections = parse_objdump_sections(
            args.second_objdump.read_text(encoding="utf-8")
        )
        results = [
            compare_section_bytes(
                first_elf,
                second_elf,
                first_sections,
                second_sections,
                section_name,
            )
            for section_name in args.section
        ]
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        print(f"PHX-ESP32-ELF-SECTION-COMPARE-RED: {exc}", file=sys.stderr)
        return 1

    for result in results:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    differing = [result for result in results if result["status"] == "DIFFERENT"]
    if differing:
        print(
            "PHX-ESP32-ELF-SECTION-COMPARE-DIFF: "
            f"sections={len(results)} differing_sections={len(differing)} "
            f"differing_bytes={sum(item['differing_bytes'] for item in differing)}"
        )
    else:
        print(
            "PHX-ESP32-ELF-SECTION-COMPARE-IDENTICAL: "
            f"sections={len(results)}"
        )
    # This helper is diagnostic. The caller's strict application-image comparator
    # remains authoritative and fail-closed for any full-image mismatch.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
