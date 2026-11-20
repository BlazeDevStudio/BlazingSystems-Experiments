#!/usr/bin/env python3
"""Attribute ESP32 image drift addresses to symbols in a pinned ELF section.

The caller supplies text captured from the exact installed Xtensa nm/objdump
binaries. This helper never searches PATH, opens an ELF, downloads tools, or
changes firmware. It reports containing symbols and a bounded nearest
predecessor; a predecessor alone is not proof that the symbol owns the byte.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from inspect_esp32_elf_sections import (
    map_address as map_section_address,
    parse_objdump_sections,
)

_NM_POSIX_ROW = re.compile(
    r"^(?P<name>\S+)\s+(?P<type>[A-Za-z?])\s+"
    r"(?P<value>(?:0[xX])?[0-9a-fA-F]+)"
    r"(?:\s+(?P<size>(?:0[xX])?[0-9a-fA-F]+|\?))?$"
)
_ADDRESS_SPEC = re.compile(
    r"(?P<label>[A-Za-z][A-Za-z0-9_.-]*)=(?P<address>0[xX][0-9a-fA-F]+)"
)


def _hex_value(value: str) -> int:
    return int(value[2:] if value.lower().startswith("0x") else value, 16)


def parse_nm_symbols(output: str) -> list[dict[str, Any]]:
    """Parse GNU nm POSIX rows emitted with --print-size; reject ambiguity."""
    if not isinstance(output, str):
        raise TypeError("nm output must be text")

    symbols: list[dict[str, Any]] = []
    for line_number, line in enumerate(output.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        match = _NM_POSIX_ROW.fullmatch(stripped)
        if match is None:
            raise ValueError(f"malformed POSIX nm row at line {line_number}")

        value = _hex_value(match.group("value"))
        raw_size = match.group("size")
        size = None if raw_size in (None, "?") else _hex_value(raw_size)
        if value > 0xFFFFFFFF or (size is not None and size > 0xFFFFFFFF):
            raise ValueError(f"nm symbol exceeds 32-bit address space at line {line_number}")
        if size is not None and value + size > 0x100000000:
            raise ValueError(f"nm symbol range overflows 32-bit address space at line {line_number}")

        symbols.append(
            {
                "name": match.group("name"),
                "type": match.group("type"),
                "value": value,
                "size": size,
            }
        )

    if not symbols:
        raise ValueError("nm output contains no defined symbols")
    return sorted(symbols, key=lambda item: (item["value"], item["name"], item["type"]))


def map_address(
    sections: list[dict[str, Any]],
    symbols: list[dict[str, Any]],
    address: int,
    section_name: str = ".flash.rodata",
) -> dict[str, Any]:
    """Map an address to containing symbols or a nearest same-section predecessor."""
    if isinstance(address, bool) or not isinstance(address, int) or not 0 <= address <= 0xFFFFFFFF:
        raise ValueError("address must be an unsigned 32-bit integer")
    if not isinstance(section_name, str) or not section_name:
        raise ValueError("section name must be non-empty text")

    named_sections = [
        section for section in sections
        if section["name"] == section_name and section["size"] > 0
    ]
    if len(named_sections) != 1:
        raise ValueError(
            f"expected exactly one non-empty {section_name} section, found {len(named_sections)}"
        )
    section = named_sections[0]
    address_matches = [
        item for item in map_section_address(sections, address)
        if item["name"] == section_name
    ]
    if len(address_matches) > 1:
        raise ValueError(f"address maps ambiguously to {section_name}")
    if not address_matches:
        return {
            "address": f"0x{address:08x}",
            "section": {
                "name": section_name,
                "vma": f"0x{section['vma']:08x}",
                "lma": f"0x{section['lma']:08x}",
                "size": section["size"],
            },
            "status": "ADDRESS_NOT_IN_SECTION",
            "containing_symbols": [],
            "nearest_preceding": [],
        }

    mapped = address_matches[0]
    target_offset = mapped["offset"]
    candidates: list[dict[str, Any]] = []

    for symbol in symbols:
        symbol_offsets: set[int] = set()
        if section["vma"] <= symbol["value"] < section["vma"] + section["size"]:
            symbol_offsets.add(symbol["value"] - section["vma"])
        if section["lma"] <= symbol["value"] < section["lma"] + section["size"]:
            symbol_offsets.add(symbol["value"] - section["lma"])
        if not symbol_offsets:
            continue
        if len(symbol_offsets) != 1:
            raise ValueError(f"symbol address maps ambiguously within {section_name}: {symbol['name']}")
        symbol_offset = next(iter(symbol_offsets))
        candidates.append(
            {
                "name": symbol["name"],
                "type": symbol["type"],
                "value": f"0x{symbol['value']:08x}",
                "section_offset": symbol_offset,
                "size": symbol["size"],
                "offset": target_offset - symbol_offset if target_offset >= symbol_offset else None,
            }
        )

    containing: list[dict[str, Any]] = []
    preceding: list[dict[str, Any]] = []
    for item in candidates:
        symbol_offset = item["section_offset"]
        size = item["size"]
        if size is not None and size > 0 and symbol_offset <= target_offset < symbol_offset + size:
            containing.append(item)
        if symbol_offset <= target_offset:
            preceding.append(item)

    containing.sort(key=lambda item: (item["size"], item["name"], item["type"]))
    if preceding:
        nearest_offset = max(item["section_offset"] for item in preceding)
        nearest = [
            {
                **item,
                "distance": target_offset - item["section_offset"],
            }
            for item in preceding
            if item["section_offset"] == nearest_offset
        ]
        nearest.sort(key=lambda item: (item["name"], item["type"]))
    else:
        nearest = []

    status = (
        "CONTAINED" if containing
        else "NEAREST_ONLY" if nearest
        else "NO_SYMBOL_AT_OR_BEFORE_ADDRESS"
    )
    return {
        "address": f"0x{address:08x}",
        "section": {
            "name": section_name,
            "basis": mapped["basis"],
            "vma": f"0x{section['vma']:08x}",
            "lma": f"0x{section['lma']:08x}",
            "size": section["size"],
            "section_offset": target_offset,
            "file_offset": mapped["file_offset"],
        },
        "status": status,
        "containing_symbols": containing[:12],
        "containing_symbol_count": len(containing),
        "nearest_preceding": nearest[:12],
        "nearest_preceding_count": len(nearest),
    }


def parse_address_spec(value: str) -> dict[str, Any]:
    """Parse a stable label=0xADDRESS argument."""
    if not isinstance(value, str):
        raise TypeError("address specification must be text")
    match = _ADDRESS_SPEC.fullmatch(value)
    if match is None:
        raise ValueError("address must use label=0xHEX with a simple label")
    address = _hex_value(match.group("address"))
    if address > 0xFFFFFFFF:
        raise ValueError("ESP32 address exceeds the 32-bit address space")
    return {"label": match.group("label"), "address": address}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nm-output",
        required=True,
        type=Path,
        help="UTF-8 text captured from the pinned Xtensa nm --format=posix --print-size command",
    )
    parser.add_argument(
        "--objdump-output",
        required=True,
        type=Path,
        help="UTF-8 text captured from the pinned Xtensa objdump -h command",
    )
    parser.add_argument(
        "--section",
        default=".flash.rodata",
        help="ELF section containing the image drift addresses (default: .flash.rodata)",
    )
    parser.add_argument(
        "--address",
        action="append",
        default=[],
        metavar="LABEL=0xADDRESS",
        help="observed ESP image load address to attribute; repeat per byte/range boundary",
    )
    args = parser.parse_args(argv)

    try:
        symbols = parse_nm_symbols(args.nm_output.read_text(encoding="utf-8"))
        sections = parse_objdump_sections(args.objdump_output.read_text(encoding="utf-8"))
        mapped: list[dict[str, Any]] = []
        for raw_spec in args.address:
            spec = parse_address_spec(raw_spec)
            result = map_address(sections, symbols, spec["address"], args.section)
            mapped.append({"label": spec["label"], **result})
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        print(f"PHX-ESP32-ELF-SYMBOL-RED: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {"section": args.section, "symbol_count": len(symbols), "addresses": mapped},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    print(
        f"PHX-ESP32-ELF-SYMBOL-PASS: section={args.section} "
        f"symbols={len(symbols)} addresses={len(mapped)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
