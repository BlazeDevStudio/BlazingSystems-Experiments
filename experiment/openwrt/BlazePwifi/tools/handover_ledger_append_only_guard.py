#!/usr/bin/env python3
"""Fail closed unless a candidate ledger preserves the exact base bytes as a prefix."""
from __future__ import annotations

import argparse
from pathlib import Path


def check_append_only(base: bytes, candidate: bytes) -> tuple[bool, str]:
    """Return whether candidate is the unchanged base followed only by new bytes."""
    if not base:
        return False, "base ledger is empty; preservation cannot be established"
    if not candidate.startswith(base):
        common = 0
        limit = min(len(base), len(candidate))
        while common < limit and base[common] == candidate[common]:
            common += 1
        return False, (
            "candidate does not preserve the base byte-for-byte "
            f"(common_prefix_bytes={common} base_bytes={len(base)} "
            f"candidate_bytes={len(candidate)})"
        )

    suffix = candidate[len(base):]
    if suffix and not base.endswith((b"\n", b"\r")) and not suffix.startswith((b"\n", b"\r")):
        return False, "appended content is not separated from the preserved base by a newline"
    return True, f"base_bytes={len(base)} appended_bytes={len(suffix)}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Require a hardware change ledger to preserve its exact base as a byte prefix."
    )
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    args = parser.parse_args()

    try:
        base = args.base.read_bytes()
        candidate = args.candidate.read_bytes()
    except OSError as exc:
        print(f"CHANGE_LEDGER_APPEND_ONLY_FAIL read_error={exc}")
        return 2

    ok, detail = check_append_only(base, candidate)
    print(("CHANGE_LEDGER_APPEND_ONLY_PASS " if ok else "CHANGE_LEDGER_APPEND_ONLY_FAIL ") + detail)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
