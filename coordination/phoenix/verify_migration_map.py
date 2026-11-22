#!/usr/bin/env python3
"""Read-only consistency check for Phoenix SOURCE_INTAKE.json and MIGRATION_MAP.md.

This checks the recorded Git blob identities in the migration table against the
summary counters. It does not fetch Git objects or prove that the recorded
identities match the live source/destination trees.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_ROOTFS_SECTION = "## Migrated OpenWrt overlay files"
_KNOWN_STATUS = ("copied unchanged", "intentionally edited", "locally derived")


@dataclass(frozen=True)
class RootfsEntry:
    source_path: str
    destination_path: str
    source_blob: str
    destination_blob: str
    status: str
    line_number: int


def _cell(value: str) -> str:
    return value.strip().strip(chr(96)).strip()


def parse_rootfs_entries(migration_map: str) -> list[RootfsEntry]:
    """Parse the single rootfs migration table; ignore later test tables."""
    lines = migration_map.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == _ROOTFS_SECTION)
    except StopIteration as exc:
        raise ValueError(f"missing section: {_ROOTFS_SECTION}") from exc

    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    entries: list[RootfsEntry] = []
    for index in range(start + 1, end):
        line = lines[index]
        if not line.lstrip().startswith("|"):
            continue
        cells = [_cell(part) for part in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            raise ValueError(f"malformed rootfs table row at line {index + 1}: expected 5 columns, found {len(cells)}")
        if cells[0].lower().startswith("original source path"):
            continue
        if all(re.fullmatch(r"[-:\s]+", value or " ") for value in cells):
            continue
        if not all(cells):
            raise ValueError(f"incomplete rootfs table row at line {index + 1}")
        entries.append(
            RootfsEntry(
                source_path=cells[0],
                destination_path=cells[1],
                source_blob=cells[2],
                destination_blob=cells[3],
                status=cells[4],
                line_number=index + 1,
            )
        )

    if not entries:
        raise ValueError(f"no rootfs file rows found in {_ROOTFS_SECTION}")
    return entries


def verify_documents(manifest_text: str, migration_map: str) -> tuple[dict[str, int], list[str]]:
    """Return computed counts and all consistency errors without mutating inputs."""
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_text)
    except json.JSONDecodeError as exc:
        return {}, [f"SOURCE_INTAKE.json is invalid JSON: {exc}"]

    summary = manifest.get("summary")
    if not isinstance(summary, dict):
        return {}, ["SOURCE_INTAKE.json is missing an object-valued 'summary'"]

    try:
        entries = parse_rootfs_entries(migration_map)
    except ValueError as exc:
        return {}, [str(exc)]

    seen_source: set[str] = set()
    seen_destination: set[str] = set()
    identical = 0
    derived = 0

    for entry in entries:
        prefix = f"MIGRATION_MAP.md:{entry.line_number}"
        if entry.source_path in seen_source:
            errors.append(f"{prefix}: duplicate source path {entry.source_path}")
        if entry.destination_path in seen_destination:
            errors.append(f"{prefix}: duplicate destination path {entry.destination_path}")
        seen_source.add(entry.source_path)
        seen_destination.add(entry.destination_path)

        for label, blob in (
            ("source", entry.source_blob),
            ("destination", entry.destination_blob),
        ):
            if not _SHA1.fullmatch(blob):
                errors.append(f"{prefix}: invalid {label} Git blob SHA-1 for {entry.source_path}: {blob!r}")

        same_blob = entry.source_blob == entry.destination_blob
        if same_blob:
            identical += 1
        else:
            derived += 1

        status = entry.status.strip().lower()
        matched_statuses = [
            token for token in _KNOWN_STATUS
            if token in status
        ]
        if not matched_statuses:
            errors.append(f"{prefix}: unrecognized migration status for {entry.source_path}: {entry.status!r}")
        elif len(matched_statuses) != 1 or status.count(matched_statuses[0]) != 1:
            errors.append(f"{prefix}: ambiguous migration status for {entry.source_path}: {entry.status!r}")
        elif not status.startswith(matched_statuses[0]):
            errors.append(
                f"{prefix}: migration status must begin with one recognized classification "
                f"for {entry.source_path}: {entry.status!r}"
            )
        elif matched_statuses[0] == "copied unchanged" and not same_blob:
            errors.append(f"{prefix}: marked copied unchanged but source/destination blobs differ: {entry.source_path}")
        elif matched_statuses[0] in ("intentionally edited", "locally derived") and same_blob:
            errors.append(f"{prefix}: marked derived but source/destination blobs are identical: {entry.source_path}")

    computed = {"rootfs_rows": len(entries), "byte_identical": identical, "derived": derived}
    expected_fields = (
        ("original_rootfs_file_count", len(entries)),
        ("recovered_rootfs_file_count", len(entries)),
        ("recovered_byte_identical_count", identical),
        ("locally_derived_files", derived),
    )
    for field, actual in expected_fields:
        expected = summary.get(field)
        if not isinstance(expected, int) or isinstance(expected, bool):
            errors.append(f"summary.{field} must be an integer; found {expected!r}")
        elif expected != actual:
            errors.append(f"summary.{field}={expected}, but MIGRATION_MAP.md Git blob identities compute {actual}")

    return computed, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only check of SOURCE_INTAKE.json counters against MIGRATION_MAP.md rootfs blob records."
    )
    parser.add_argument("manifest", type=Path, help="path to Pisowifi/SOURCE_INTAKE.json")
    parser.add_argument("migration_map", type=Path, help="path to Pisowifi/MIGRATION_MAP.md")
    args = parser.parse_args()

    computed, errors = verify_documents(
        args.manifest.read_text(encoding="utf-8"),
        args.migration_map.read_text(encoding="utf-8"),
    )
    if computed:
        print(
            "Rootfs records: {rootfs_rows}; byte-identical: {byte_identical}; derived: {derived}".format(
                **computed
            )
        )
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("PASS: manifest summary agrees with the migration table's recorded Git blob identities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
