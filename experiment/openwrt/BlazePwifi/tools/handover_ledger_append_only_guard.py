#!/usr/bin/env python3
"""Temporary test-first stub for the append-only handover ledger guard.

The regression suite must fail until the byte-prefix invariant is implemented.
"""
from __future__ import annotations

import argparse


def check_append_only(base: bytes, candidate: bytes) -> tuple[bool, str]:
    # Deliberately unsafe baseline: the RED tests must catch acceptance of edits.
    return True, "test-first stub accepted candidate without comparing bytes"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    with open(args.base, "rb") as stream:
        base = stream.read()
    with open(args.candidate, "rb") as stream:
        candidate = stream.read()
    ok, detail = check_append_only(base, candidate)
    print(("CHANGE_LEDGER_APPEND_ONLY_PASS " if ok else "CHANGE_LEDGER_APPEND_ONLY_FAIL ") + detail)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
