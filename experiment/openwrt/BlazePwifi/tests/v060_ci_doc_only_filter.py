#!/usr/bin/env python3
"""HND-0700: guard GitHub path filters against doc-only CI loops.

No third-party YAML parser: inspect the simple workflow event/path shape.
Only compare a finite set of representative source/docs paths. This is an
additional regression, never a substitute for GitHub's actual trigger rules.
"""
from __future__ import annotations

import fnmatch
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / ".github/workflows/blazepwifi-build.yml"
raw = WORKFLOW.read_text(encoding="utf-8")
assert raw.startswith("name: BlazePwifi build\n"), "wrong workflow"
assert re.search(r"^  workflow_dispatch:\s*$", raw, re.M), "manual full gate missing"
assert "sh experiment/openwrt/BlazePwifi/tests/handover_gate.sh" in raw
assert "sh experiment/openwrt/BlazePwifi/tests/handover_gate_regression.sh" in raw


def get_event_patterns(name: str) -> list[str]:
    # This workflow uses top-level "on:" with two-space event names and
    # four-space paths; fail closed if its shape changes.
    match = re.search(rf"^  {re.escape(name)}:\s*\n(.*?)(?=^  [a-z_]+:|^jobs:|\Z)", raw, re.M | re.S)
    assert match, f"missing {name} event"
    paths = re.search(r"^    paths:\s*\n((?:^      (?:- |#).+\n)+)", match.group(1), re.M)
    assert paths, f"missing {name}.paths"
    patterns = []
    for line in paths.group(1).splitlines():
        value = line.strip()
        if value.startswith("#"):
            continue
        assert value.startswith("- "), "unrecognized paths list line"
        value = value[2:]
        assert len(value) >= 3 and value[0] == value[-1] == "'", "unrecognized path expression"
        patterns.append(value[1:-1])
    return patterns


# GitHub supports ordered positive and negative path patterns. These sample
# paths contain no exotic glob corner cases; fnmatch is sufficient for these
# representative fixtures, while GitHub remains the final trigger authority.
def selected(patterns: list[str], files: list[str]) -> bool:
    def matches(filename: str) -> bool:
        included = False
        for pattern in patterns:
            negated = pattern.startswith("!")
            glob = pattern[1:] if negated else pattern
            if fnmatch.fnmatchcase(filename, glob):
                included = not negated
        return included
    return any(matches(file) for file in files)


root = "experiment/openwrt/BlazePwifi/"
for event in ("push", "pull_request"):
    patterns = get_event_patterns(event)
    required = {
        root + "**",
        "!" + root + "docs/**",
        "!" + root + "PROJECT_HANDOVER.md",
        "!" + root + "AUDIT.md",
        "!" + root + "README.md",
        ".github/workflows/blazepwifi-build.yml",
    }
    assert required.issubset(set(patterns)), f"missing {event} protections: {required - set(patterns)}"
    documents = [
        root + "PROJECT_HANDOVER.md",
        root + "docs/handover/CURRENT_STATE.md",
        root + "docs/handover/CHANGE_LEDGER.md",
        root + "docs/handover/archive/2026-10-10-CURRENT_STATE-before-compact.md",
        root + "docs/LEDGER_TRANSACTION_V060.md",
        root + "AUDIT.md",
        root + "README.md",
    ]
    for doc in documents:
        assert not selected(patterns, [doc]), f"{event}: documentation caused full firmware build: {doc}"
    source_paths = [
        root + "VERSION",
        root + "tests/v060_ci_doc_only_filter.py",
        root + "openwrt/rootfs/usr/lib/blazepwifi/member.sh",
        root + "openwrt/rootfs/usr/lib/blazepwifi/rental.sh",
        root + "tools/v060_journal_authority_native.c",
        ".github/workflows/blazepwifi-build.yml",
        ".github/workflows/blazepwifi-v053-release.yml",
    ]
    for code in source_paths:
        assert selected(patterns, [code]), f"{event}: source or workflow build wrongly excluded: {code}"
    for doc in documents:
        assert selected(patterns, [doc, source_paths[2]]), f"{event}: source+docs skipped: {doc}"
    assert not selected(patterns, documents), f"{event}: all-docs pull/push still schedules builds"
print("HND-0700 PASS: docs-only ignored; money/source/tests/workflow and mixed changes retain full validation")
