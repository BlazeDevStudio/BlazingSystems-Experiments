#!/usr/bin/env python3
"""Map ESP32 ELF VMA/LMA addresses to sections from a pinned objdump -h capture.

The caller is responsible for invoking the objdump binary supplied by the
selected, pinned ESP32 toolchain. This helper deliberately does not search PATH
or choose a toolchain implicitly; it parses the captured section table only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


_SECTION_ROW = re.compile(
    r"^\s*(?P<index>\d+)\s+"
    r"(?P<name>\S+)\s+"
    r"(?P<size>[0-9a-fA-F]+)\s+"
    r"(?P<vma>[0-9a-fA-F]+)\s+"
    r"(?P<lma>[0-9a-fA-F]+)\s+"
    r"(?P<file_offset>[0-9a-fA-F]+)\s+"
    r"(?P<alignment>\S+)\s*$"
)
_ADDRESS_SPEC = re.compile(
    r"(?P<label>[A-Za-z][A-Za-z0-9_.-]*)=(?P<address>0[xX][0-9a-fA-F]+)"
)


def parse_objdump_sections(output: str) -> list[dict[str, Any]]:
    """Parse GNU/ESP objdump -h rows; reject malformed or duplicate indexes."""
    if not isinstance(output, str):
        raise TypeError("objdump output must be text")

    sections: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    for line_number, line in enumerate(output.splitlines(), start=1):
        stripped = line.lstrip()
        if not stripped:
            continue
        first = stripped.split(maxsplit=1)[0]
        if not first.isdecimal():
            continue

        match = _SECTION_ROW.fullmatch(line)
        if match is None:
            raise ValueError(f"malformed objdump section row at line {line_number}")

        index = int(match.group("index"), 10)
        if index in seen_indexes:
            raise ValueError(f"duplicate objdump section index {index}")
        seen_indexes.add(index)

        size = int(match.group("size"), 16)
        vma = int(match.group("vma"), 16)
        lma = int(match.group("lma"), 16)
        file_offset = int(match.group("file_offset"), 16)
        alignment = match.group("alignment")
        if not match.group("name"):
            raise ValueError(f"empty section name at line {line_number}")
        if any(value > 0xFFFFFFFF for value in (size, vma, lma, file_offset)):
            raise ValueError(f"section field exceeds 32-bit ELF address space at line {line_number}")
        if vma + size > 0x100000000 or lma + size > 0x100000000:
            raise ValueError(f"section address range overflows 32-bit space at line {line_number}")

        sections.append(
            {
                "index": index,
                "name": match.group("name"),
                "size": size,
                "vma": vma,
                "lma": lma,
                "file_offset": file_offset,
                "alignment": alignment,
            }
        )

    if not sections:
        raise ValueError("objdump output contains no section rows")
    return sections


def map_address(sections: list[dict[str, Any]], address: int) -> list[dict[str, Any]]:
    """Return every half-open VMA/LMA section candidate containing address."""
    if isinstance(address, bool) or not isinstance(address, int) or not 0 <= address <= 0xFFFFFFFF:
        raise ValueError("address must be an unsigned 32-bit integer")

    matches: list[dict[str, Any]] = []
    for section in sections:
        size = section["size"]
        if size <= 0:
            continue
        vma = section["vma"]
        lma = section["lma"]
        if vma <= address < vma + size:
            basis = "VMA/LMA" if vma == lma else "VMA"
            matches.append(
                {
                    "index": section["index"],
                    "name": section["name"],
                    "basis": basis,
                    "offset": address - vma,
                    "file_offset": section["file_offset"] + address - vma,
                }
            )
        if lma != vma and lma <= address < lma + size:
            matches.append(
                {
                    "index": section["index"],
                    "name": section["name"],
                    "basis": "LMA",
                    "offset": address - lma,
                    "file_offset": section["file_offset"] + address - lma,
                }
            )

    return sorted(matches, key=lambda item: (item["index"], item["basis"], item["offset"]))


def parse_address_spec(value: str) -> dict[str, Any]:
    """Parse a stable label=0xADDRESS argument for a byte-drift address."""
    if not isinstance(value, str):
        raise TypeError("address specification must be text")
    match = _ADDRESS_SPEC.fullmatch(value)
    if match is None:
        raise ValueError("address must use label=0xHEX with a simple label")
    address = int(match.group("address"), 16)
    if address > 0xFFFFFFFF:
        raise ValueError("ESP32 address exceeds the 32-bit address space")
    return {"label": match.group("label"), "address": address}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--objdump-output",
        required=True,
        type=Path,
        help="UTF-8 text captured from the pinned Xtensa objdump -h command",
    )
    parser.add_argument(
        "--address",
        action="append",
        default=[],
        metavar="LABEL=0xADDRESS",
        help="address to map; repeat for each observed ESP image segment byte",
    )
    args = parser.parse_args(argv)

    try:
        sections = parse_objdump_sections(args.objdump_output.read_text(encoding="utf-8"))
        mapped: list[dict[str, Any]] = []
        for raw_spec in args.address:
            spec = parse_address_spec(raw_spec)
            candidates = map_address(sections, spec["address"])
            mapped.append(
                {
                    "label": spec["label"],
                    "address": f"0x{spec['address']:08x}",
                    "matches": candidates,
                    "status": "MAPPED" if candidates else "UNMAPPED",
                }
            )
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        print(f"PHX-ESP32-ELF-SECTION-RED: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {"section_count": len(sections), "sections": sections, "addresses": mapped},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    print(f"PHX-ESP32-ELF-SECTION-PASS: sections={len(sections)} addresses={len(mapped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
