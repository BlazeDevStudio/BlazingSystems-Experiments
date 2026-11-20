#!/usr/bin/env python3
"""Read-only structural gate for COE Pisowifi/SOURCE_INTAKE.json.

Usage: python3 coordination/phoenix/verify_source_intake_manifest.py /path/to/SOURCE_INTAKE.json
No network, Git writes, payment operations or release authorization.
"""
import argparse
from collections import Counter
import json
import sys

IDENTICAL = "byte_identical"
DERIVED = "derived_cleanup_review_required_real_router_test"
VALID_STATUSES = frozenset({IDENTICAL, DERIVED})


def verify(data):
    """Validate internal manifest structure; never claims live Git parity."""
    if not isinstance(data, dict):
        return ["manifest root must be an object"]

    errors = []
    summary = data.get("summary", {})
    runtime = data.get("runtime", [])
    if not isinstance(runtime, list) or not isinstance(summary, dict):
        return ["summary must be an object and runtime must be an array"]

    paths = []
    statuses = Counter()
    for index, entry in enumerate(runtime):
        if not isinstance(entry, dict):
            errors.append(f"runtime[{index}] must be an object")
            continue
        path = entry.get("path")
        if (not isinstance(path, str) or not path or path.startswith("/")
                or "\\" in path or any(ord(char) < 32 or ord(char) == 127 for char in path)
                or any(part in ("", ".", "..") for part in path.split("/"))):
            errors.append(f"runtime[{index}] unsafe or invalid path")
        else:
            paths.append(path)

        src, dst = entry.get("source_git_blob"), entry.get("destination_git_blob")
        blobs_valid = all(
            isinstance(value, str) and len(value) == 40
            and all(char in "0123456789abcdef" for char in value)
            for value in (src, dst)
        )
        if not blobs_valid:
            errors.append(f"runtime[{index}] invalid blob identity")

        status = entry.get("status")
        if not isinstance(status, str) or status not in VALID_STATUSES:
            errors.append(f"runtime[{index}] missing or unknown status")
        else:
            statuses[status] += 1
            if blobs_valid and ((status == IDENTICAL) != (src == dst)):
                errors.append(f"runtime[{index}] status contradicts recorded blob identities")

    if len(paths) != len(set(paths)):
        errors.append("duplicate runtime path")

    for key, actual in (
        ("recovered_rootfs_file_count", len(runtime)),
        ("recovered_byte_identical_count", statuses[IDENTICAL]),
        ("locally_derived_files", statuses[DERIVED]),
    ):
        if type(summary.get(key)) is not int or summary[key] != actual:
            errors.append(f"summary.{key}: expected {actual}, recorded {summary.get(key)!r}")

    original = summary.get("original_rootfs_file_count")
    unrecovered = summary.get("unrecovered_rootfs_file_count")
    recovered = summary.get("recovered_rootfs_file_count")
    counts_valid = all(type(value) is int and value >= 0 for value in (original, recovered, unrecovered))
    if not counts_valid:
        errors.append("summary original/recovered/unrecovered counts must be nonnegative integers")
    elif original != recovered + unrecovered:
        errors.append(
            "summary.original_rootfs_file_count must equal recovered_rootfs_file_count "
            "+ unrecovered_rootfs_file_count"
        )
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="pinned COE SOURCE_INTAKE.json path")
    args = parser.parse_args()
    with open(args.manifest, encoding="utf-8") as handle:
        data = json.load(handle)
    errors = verify(data)
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    if errors:
        print(f"BLOCKED: {len(errors)} structural errors; no source/destination blob verification", file=sys.stderr)
        return 1
    print("PASS: manifest internal structure only; NOT actual Git blob, license, test or release verification")
    return 0


if __name__ == "__main__":
    sys.exit(main())
