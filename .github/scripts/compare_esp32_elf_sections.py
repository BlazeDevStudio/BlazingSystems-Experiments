#!/usr/bin/env python3
"""Compare file-backed bytes of one named section across two exact ELF builds."""
from __future__ import annotations

from typing import Any


def _unique_section(sections: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [section for section in sections if section.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {name} section, found {len(matches)}")
    return matches[0]


def compare_section_bytes(
    first_elf: bytes,
    second_elf: bytes,
    first_sections: list[dict[str, Any]],
    second_sections: list[dict[str, Any]],
    section_name: str,
) -> dict[str, Any]:
    first = _unique_section(first_sections, section_name)
    second = _unique_section(second_sections, section_name)
    for key in ("size", "vma", "lma"):
        if first.get(key) != second.get(key):
            raise ValueError(f"{section_name} {key} differs between ELF builds")
    size = first["size"]
    if size <= 0:
        raise ValueError(f"{section_name} is empty")
    for label, data, section in (
        ("first", first_elf, first),
        ("second", second_elf, second),
    ):
        start = section["file_offset"]
        if start < 0 or start + size > len(data):
            raise ValueError(f"{label} {section_name} section exceeds ELF file bounds")

    first_start = first["file_offset"]
    # Initial implementation intentionally exercises the different-file-offset regression.
    # The second slice must use second["file_offset"], not first_start.
    left = first_elf[first_start:first_start + size]
    right = second_elf[first_start:first_start + size]
    if len(left) != size or len(right) != size:
        raise ValueError(f"{section_name} section could not be read completely")

    differing = [index for index, pair in enumerate(zip(left, right)) if pair[0] != pair[1]]
    ranges: list[dict[str, int]] = []
    for index in differing:
        if not ranges or index > ranges[-1]["end"] + 1:
            ranges.append({"start": index, "end": index})
        else:
            ranges[-1]["end"] = index
    return {
        "section": section_name,
        "size": size,
        "status": "DIFFERENT" if differing else "IDENTICAL",
        "differing_bytes": len(differing),
        "difference_ranges": ranges,
    }
