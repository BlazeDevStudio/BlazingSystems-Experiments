"""Synthetic regression tests for verify_migration_map.py."""
from __future__ import annotations

import json
import unittest

from verify_migration_map import parse_rootfs_entries, verify_documents


SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


def manifest(total: int, identical: int, derived: int) -> str:
    return json.dumps(
        {
            "summary": {
                "original_rootfs_file_count": total,
                "recovered_rootfs_file_count": total,
                "recovered_byte_identical_count": identical,
                "locally_derived_files": derived,
            }
        }
    )


def migration_map(rows: list[tuple[str, str, str, str, str]]) -> str:
    tick = chr(96)
    lines = [
        "# Migration map",
        "",
        "## Migrated OpenWrt overlay files",
        "",
        "| Original source path (relative to pinned project root) | New destination path | Source Git blob SHA | Destination Git blob SHA | Migration status |",
        "|---|---|---|---|---|",
    ]
    lines.extend(
        "| " + " | ".join(f"{tick}{value}{tick}" if index < 4 else value for index, value in enumerate(row)) + " |"
        for row in rows
    )
    lines.extend(["", "## Migrated tests", "", "| Test | Status |", "|---|---|", f"| {tick}tests/example.sh{tick} | derived |"])
    return "\n".join(lines)


class MigrationMapVerificationTests(unittest.TestCase):
    def test_matching_summary_passes(self) -> None:
        rows = [
            ("a.sh", "Pisowifi/a.sh", SHA_A, SHA_A, "copied unchanged; source retained"),
            ("b.sh", "Pisowifi/b.sh", SHA_B, SHA_C, "intentionally edited; source retained"),
        ]
        computed, errors = verify_documents(manifest(2, 1, 1), migration_map(rows))
        self.assertEqual(computed, {"rootfs_rows": 2, "byte_identical": 1, "derived": 1})
        self.assertEqual(errors, [])

    def test_summary_off_by_one_is_reported(self) -> None:
        rows = [
            ("a.sh", "Pisowifi/a.sh", SHA_A, SHA_A, "copied unchanged; source retained"),
            ("b.sh", "Pisowifi/b.sh", SHA_B, SHA_C, "intentionally edited; source retained"),
        ]
        _, errors = verify_documents(manifest(2, 2, 0), migration_map(rows))
        self.assertTrue(any("recovered_byte_identical_count=2" in error for error in errors))
        self.assertTrue(any("locally_derived_files=0" in error for error in errors))

    def test_unchanged_label_cannot_hide_different_blobs(self) -> None:
        rows = [("a.sh", "Pisowifi/a.sh", SHA_A, SHA_B, "copied unchanged; source retained")]
        _, errors = verify_documents(manifest(1, 0, 1), migration_map(rows))
        self.assertTrue(any("marked copied unchanged" in error for error in errors))

    def test_derived_label_requires_different_blobs(self) -> None:
        rows = [("a.sh", "Pisowifi/a.sh", SHA_A, SHA_A, "intentionally edited; source retained")]
        _, errors = verify_documents(manifest(1, 1, 0), migration_map(rows))
        self.assertTrue(any("marked derived" in error for error in errors))

    def test_duplicate_destination_is_rejected(self) -> None:
        rows = [
            ("a.sh", "Pisowifi/shared.sh", SHA_A, SHA_A, "copied unchanged"),
            ("b.sh", "Pisowifi/shared.sh", SHA_B, SHA_C, "locally derived"),
        ]
        _, errors = verify_documents(manifest(2, 1, 1), migration_map(rows))
        self.assertTrue(any("duplicate destination path" in error for error in errors))

    def test_malformed_blob_id_is_rejected(self) -> None:
        rows = [("a.sh", "Pisowifi/a.sh", "not-a-sha", SHA_A, "intentionally edited")]
        _, errors = verify_documents(manifest(1, 0, 1), migration_map(rows))
        self.assertTrue(any("invalid source Git blob SHA-1" in error for error in errors))

    def test_missing_rootfs_section_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing section"):
            parse_rootfs_entries("# no migration table\n")

    def test_incomplete_table_row_is_rejected(self) -> None:
        text = migration_map([("a.sh", "Pisowifi/a.sh", SHA_A, "", "copied unchanged")])
        with self.assertRaisesRegex(ValueError, "incomplete rootfs table row"):
            parse_rootfs_entries(text)

    def test_manifest_json_error_is_reported(self) -> None:
        _, errors = verify_documents("{bad json", migration_map([]))
        self.assertTrue(any("invalid JSON" in error for error in errors))

    def test_observed_61_row_off_by_one_is_reported(self) -> None:
        rows = []
        for index in range(46):
            blob = f"{index + 1:040x}"
            rows.append((f"src/{index}.sh", f"Pisowifi/{index}.sh", blob, blob, "copied unchanged"))
        for index in range(15):
            source = f"{index + 100:040x}"
            destination = f"{index + 200:040x}"
            rows.append((f"src/derived-{index}.sh", f"Pisowifi/derived-{index}.sh", source, destination, "intentionally edited"))
        _, errors = verify_documents(manifest(61, 47, 14), migration_map(rows))
        self.assertTrue(any("recovered_byte_identical_count=47" in error and "compute 46" in error for error in errors))
        self.assertTrue(any("locally_derived_files=14" in error and "compute 15" in error for error in errors))

    def test_status_label_must_be_leading_classification(self) -> None:
        rows = [("a.sh", "Pisowifi/a.sh", SHA_A, SHA_A, "note: copied unchanged; source retained")]
        _, errors = verify_documents(manifest(1, 1, 0), migration_map(rows))
        self.assertTrue(any("must begin with" in error for error in errors), errors)

    def test_conflicting_status_labels_are_rejected_as_ambiguous(self) -> None:
        rows = [("a.sh", "Pisowifi/a.sh", SHA_A, SHA_A, "copied unchanged; intentionally edited")]
        _, errors = verify_documents(manifest(1, 1, 0), migration_map(rows))
        self.assertTrue(any("ambiguous migration status" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
